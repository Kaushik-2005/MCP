"""Observability helpers for ResearchOps MCP."""

from __future__ import annotations

import json
import logging
import sys
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Iterator

from opentelemetry import trace
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Receive, Scope, Send

from researchops_mcp.security import redact_for_log


REQUEST_ID_HEADER = "x-request-id"


class JsonFormatter(logging.Formatter):
    """Small JSON formatter that keeps logs machine-readable."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            payload.update(redact_for_log(extra))
        return json.dumps(payload, sort_keys=True, ensure_ascii=True)


def configure_json_logging(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("researchops_mcp")
    logger.setLevel(level)
    logger.propagate = False
    if not any(getattr(handler, "_researchops_json", False) for handler in logger.handlers):
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(JsonFormatter())
        handler._researchops_json = True
        logger.addHandler(handler)
    return logger


@dataclass(slots=True)
class OperationStats:
    count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_latency_ms: float = 0.0
    latencies_ms: list[float] = field(default_factory=list)

    def record(self, *, latency_ms: float, success: bool) -> None:
        self.count += 1
        self.total_latency_ms += latency_ms
        self.latencies_ms.append(latency_ms)
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1

    def snapshot(self) -> dict[str, int | float]:
        return {
            "count": self.count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": round(self.success_count / self.count, 3) if self.count else 1.0,
            "failure_rate": round(self.failure_count / self.count, 3) if self.count else 0.0,
            "mean_latency_ms": round(self.total_latency_ms / self.count, 1) if self.count else 0.0,
            "p50_latency_ms": round(percentile(self.latencies_ms, 0.50), 1),
            "p95_latency_ms": round(percentile(self.latencies_ms, 0.95), 1),
            "p99_latency_ms": round(percentile(self.latencies_ms, 0.99), 1),
        }


class ObservabilityRegistry:
    def __init__(self, *, logger: logging.Logger | None = None) -> None:
        self._logger = logger or configure_json_logging()
        self._tracer = trace.get_tracer("researchops_mcp")
        self._lock = Lock()
        self._operations: dict[str, OperationStats] = {}

    @contextmanager
    def observe(self, operation_type: str, operation_name: str, *, request_id: str | None = None) -> Iterator[None]:
        started = time.perf_counter()
        success = False
        try:
            with self._tracer.start_as_current_span(f"{operation_type}.{operation_name}") as span:
                span.set_attribute("researchops.operation_type", operation_type)
                span.set_attribute("researchops.operation_name", operation_name)
                if request_id is not None:
                    span.set_attribute("researchops.request_id", request_id)
                yield
            success = True
        except Exception:
            raise
        finally:
            latency_ms = (time.perf_counter() - started) * 1000
            self.record(
                operation_type=operation_type,
                operation_name=operation_name,
                latency_ms=latency_ms,
                success=success,
                request_id=request_id,
            )

    def record(
        self,
        *,
        operation_type: str,
        operation_name: str,
        latency_ms: float,
        success: bool,
        request_id: str | None = None,
    ) -> None:
        key = f"{operation_type}.{operation_name}"
        with self._lock:
            stats = self._operations.setdefault(key, OperationStats())
            stats.record(latency_ms=latency_ms, success=success)
        self._logger.info(
            "operation_completed",
            extra={
                "extra_fields": {
                    "event": "operation_completed",
                    "operation_type": operation_type,
                    "operation_name": operation_name,
                    "request_id": request_id,
                    "success": success,
                    "latency_ms": round(latency_ms, 1),
                }
            },
        )

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "operations": {key: stats.snapshot() for key, stats in sorted(self._operations.items())},
                "operation_count": sum(stats.count for stats in self._operations.values()),
            }


class RequestIdMiddleware:
    """Attach a correlation ID to every HTTP request and response."""

    def __init__(self, app: ASGIApp, *, registry: ObservabilityRegistry | None = None) -> None:
        self.app = app
        self._registry = registry or ObservabilityRegistry()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        request_id = headers.get(REQUEST_ID_HEADER.encode("ascii"), b"").decode("ascii", errors="ignore") or uuid.uuid4().hex
        scope["researchops.request_id"] = request_id
        started = time.perf_counter()
        status_code = 500

        async def send_with_request_id(message: dict[str, Any]) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message["status"])
                response_headers = MutableHeaders(scope=message)
                response_headers[REQUEST_ID_HEADER] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            self._registry.record(
                operation_type="http",
                operation_name=str(scope.get("path") or "unknown"),
                latency_ms=(time.perf_counter() - started) * 1000,
                success=status_code < 500,
                request_id=request_id,
            )


def percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round((len(ordered) - 1) * ratio)))
    return ordered[index]
