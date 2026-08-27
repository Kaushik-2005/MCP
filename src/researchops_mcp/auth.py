"""Day 8 authentication helpers for the ResearchOps MCP server."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any

from pydantic import AnyHttpUrl
from starlette.datastructures import Headers
from starlette.types import ASGIApp, Receive, Scope, Send

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.routes import build_resource_metadata_url
from mcp.server.auth.settings import AuthSettings

from researchops_mcp.repositories.sqlite import DEFAULT_USER_ID

ALL_SCOPES = ["papers:read", "lists:read", "lists:write", "notes:write"]
DEFAULT_AUTH_ENABLED = os.getenv("MCP_AUTH_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
DEFAULT_AUTH_ISSUER_URL = os.getenv("MCP_AUTH_ISSUER_URL", "https://auth.researchops.example.com")
DEFAULT_RESOURCE_SERVER_URL = os.getenv("MCP_RESOURCE_SERVER_URL", "http://127.0.0.1:8000/mcp")
DEFAULT_LOCAL_USER_ID = os.getenv("MCP_LOCAL_USER_ID", DEFAULT_USER_ID)

DEFAULT_DEMO_TOKENS: dict[str, dict[str, Any]] = {
    "researchops-alice-full": {
        "client_id": "researchops-cli",
        "subject": "alice",
        "scopes": ALL_SCOPES,
    },
    "researchops-alice-read": {
        "client_id": "researchops-cli",
        "subject": "alice",
        "scopes": ["papers:read", "lists:read"],
    },
    "researchops-bob-full": {
        "client_id": "researchops-cli",
        "subject": "bob",
        "scopes": ALL_SCOPES,
    },
    "researchops-bob-read": {
        "client_id": "researchops-cli",
        "subject": "bob",
        "scopes": ["papers:read", "lists:read"],
    },
}

TOOL_SCOPES = {
    "search_papers": "papers:read",
    "get_paper": "papers:read",
    "export_bibtex": "papers:read",
    "create_reading_list": "lists:write",
    "add_paper_to_list": "lists:write",
    "add_note": "notes:write",
    "update_note": "notes:write",
    "delete_note": "notes:write",
}

PROMPT_SCOPES = {
    "compare_papers": "papers:read",
    "generate_literature_review": "papers:read",
}


class AuthError(Exception):
    """Base auth error."""


class ForbiddenError(AuthError):
    """Raised when the caller lacks required permission."""


@dataclass(frozen=True, slots=True)
class RequestIdentity:
    user_id: str
    scopes: frozenset[str]
    is_authenticated: bool
    client_id: str | None = None
    issuer: str | None = None
    resource: str | None = None


class DemoTokenVerifier(TokenVerifier):
    """Small Day 8 demo token verifier for local and staging auth learning."""

    def __init__(
        self,
        *,
        issuer_url: str = DEFAULT_AUTH_ISSUER_URL,
        resource_server_url: str = DEFAULT_RESOURCE_SERVER_URL,
        token_map: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self._issuer_url = issuer_url
        self._resource_server_url = resource_server_url
        self._token_map = token_map or load_demo_token_map()

    async def verify_token(self, token: str) -> AccessToken | None:
        payload = self._token_map.get(token)
        if payload is None:
            return None

        expires_at = payload.get("expires_at")
        if expires_at is not None and int(expires_at) < int(time.time()):
            return None

        resource = str(payload.get("resource") or self._resource_server_url)
        if resource != self._resource_server_url:
            return None

        subject = str(payload.get("subject") or "").strip()
        client_id = str(payload.get("client_id") or subject or "researchops-client")
        if not subject:
            return None

        return AccessToken(
            token=token,
            client_id=client_id,
            scopes=list(payload.get("scopes") or []),
            expires_at=int(expires_at) if expires_at is not None else None,
            resource=resource,
            subject=subject,
            claims={"iss": str(payload.get("issuer") or self._issuer_url)},
        )


def load_demo_token_map() -> dict[str, dict[str, Any]]:
    raw = os.getenv("MCP_AUTH_TOKENS")
    if not raw:
        return DEFAULT_DEMO_TOKENS
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("MCP_AUTH_TOKENS must be a JSON object mapping token strings to token metadata.")
    return {str(token): normalize_token_record(record) for token, record in payload.items()}


def normalize_token_record(record: Any) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("Each MCP_AUTH_TOKENS entry must be a JSON object.")
    scopes = record.get("scopes")
    if not isinstance(scopes, list) or not scopes or not all(isinstance(scope, str) and scope for scope in scopes):
        raise ValueError("Each token entry must include a non-empty scopes list.")
    subject = record.get("subject")
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("Each token entry must include a non-empty subject.")
    normalized = dict(record)
    normalized["subject"] = subject.strip()
    normalized["scopes"] = [scope.strip() for scope in scopes]
    return normalized


def build_auth_settings(*, issuer_url: str = DEFAULT_AUTH_ISSUER_URL, resource_server_url: str = DEFAULT_RESOURCE_SERVER_URL) -> AuthSettings:
    return AuthSettings(
        issuer_url=AnyHttpUrl(issuer_url),
        resource_server_url=AnyHttpUrl(resource_server_url),
        required_scopes=[],
    )


def current_identity() -> RequestIdentity:
    access_token = get_access_token()
    if access_token is None:
        return RequestIdentity(
            user_id=DEFAULT_LOCAL_USER_ID,
            scopes=frozenset(ALL_SCOPES),
            is_authenticated=False,
            client_id="local-stdio",
            issuer=None,
            resource=None,
        )

    issuer = None
    if access_token.claims:
        issuer = access_token.claims.get("iss")
        if issuer is not None:
            issuer = str(issuer)

    user_id = access_token.subject or access_token.client_id or DEFAULT_LOCAL_USER_ID
    return RequestIdentity(
        user_id=user_id,
        scopes=frozenset(access_token.scopes),
        is_authenticated=True,
        client_id=access_token.client_id,
        issuer=issuer,
        resource=access_token.resource,
    )


def current_user_id() -> str:
    return current_identity().user_id


def require_scope(scope: str) -> None:
    identity = current_identity()
    if scope not in identity.scopes:
        raise ForbiddenError(f"Forbidden: missing required scope '{scope}'.")


def token_subjects() -> list[str]:
    seen: list[str] = []
    for record in load_demo_token_map().values():
        subject = str(record.get("subject") or "").strip()
        if subject and subject not in seen:
            seen.append(subject)
    return seen


def resource_metadata_url(resource_server_url: str = DEFAULT_RESOURCE_SERVER_URL) -> str:
    return str(build_resource_metadata_url(AnyHttpUrl(resource_server_url)))


def required_scope_for_headers(headers: Headers) -> str | None:
    method = (headers.get("mcp-method") or "").strip()
    name = (headers.get("mcp-name") or "").strip()

    if method == "tools/call":
        return TOOL_SCOPES.get(name)
    if method == "prompts/get":
        return PROMPT_SCOPES.get(name)
    if method == "resources/read":
        uri = (headers.get("mcp-param-uri") or "").strip()
        if uri.startswith("paper://"):
            return "papers:read"
        if uri.startswith("reading-list://"):
            return "lists:read"
    return None


class ScopeEnforcementMiddleware:
    """HTTP middleware enforcing per-operation scopes before MCP dispatch."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        token_verifier: TokenVerifier,
        resource_server_url: str = DEFAULT_RESOURCE_SERVER_URL,
    ) -> None:
        self.app = app
        self._token_verifier = token_verifier
        self._resource_metadata_url = resource_metadata_url(resource_server_url)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        headers = Headers(raw=scope.get("headers") or [])
        required_scope = required_scope_for_headers(headers)
        if required_scope is None:
            await self.app(scope, receive, send)
            return

        auth_header = headers.get("authorization")
        if not auth_header or not auth_header.lower().startswith("bearer "):
            await self.app(scope, receive, send)
            return

        token = auth_header[7:]
        access_token = await self._token_verifier.verify_token(token)
        if access_token is None:
            await self.app(scope, receive, send)
            return

        if required_scope not in access_token.scopes:
            await self._send_forbidden(send, required_scope)
            return

        await self.app(scope, receive, send)

    async def _send_forbidden(self, send: Send, required_scope: str) -> None:
        body = json.dumps(
            {
                "error": "insufficient_scope",
                "error_description": f"Required scope: {required_scope}",
            }
        ).encode("utf-8")
        www_authenticate = (
            "Bearer "
            f'error="insufficient_scope", error_description="Required scope: {required_scope}", '
            f'resource_metadata="{self._resource_metadata_url}", scope="{required_scope}"'
        )
        await send(
            {
                "type": "http.response.start",
                "status": 403,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("ascii")),
                    (b"www-authenticate", www_authenticate.encode("utf-8")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})


def seed_known_users(repository) -> None:
    with repository.transaction() as conn:
        repository.ensure_user(conn, user_id=DEFAULT_LOCAL_USER_ID, display_name="Local Learner")
        for subject in token_subjects():
            repository.ensure_user(conn, user_id=subject, display_name=subject.title())
