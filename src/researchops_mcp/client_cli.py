"""MCP client for the ResearchOps learning project."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
from dataclasses import dataclass
from typing import Any

import httpx
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.exceptions import MCPError

WRITE_TOOLS = {
    "create_reading_list",
    "add_paper_to_list",
    "add_note",
    "update_note",
    "delete_note",
}


@dataclass(slots=True)
class ClientConfig:
    connection_mode: str
    server_command: str
    server_args: list[str]
    server_cwd: str | None
    server_url: str
    auto_approve: bool
    bearer_token: str | None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ResearchOps MCP CLI client")
    parser.add_argument(
        "--connection-mode",
        choices=["stdio", "http"],
        default="stdio",
        help="How the client should reach the MCP server.",
    )
    parser.add_argument("--server-command", default="python", help="Command used to launch the local stdio MCP server.")
    parser.add_argument(
        "--server-arg",
        action="append",
        default=["src/server.py"],
        help="Argument passed to the stdio server command. Repeat for multiple args.",
    )
    parser.add_argument("--server-cwd", default=None, help="Optional working directory for the stdio server process.")
    parser.add_argument(
        "--server-url",
        default="http://127.0.0.1:8000/mcp",
        help="Base URL for the Streamable HTTP MCP server.",
    )
    parser.add_argument(
        "--bearer-token",
        default=os.getenv("RESEARCHOPS_BEARER_TOKEN"),
        help="Optional bearer token for authenticated HTTP MCP servers.",
    )
    parser.add_argument("--yes", action="store_true", help="Auto-approve write tools.")

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("discover", help="Show server info and capabilities.")
    subparsers.add_parser("list-tools", help="List available tools.")
    subparsers.add_parser("list-resource-templates", help="List resource templates.")
    subparsers.add_parser("list-prompts", help="List available prompts.")

    read_resource = subparsers.add_parser("read-resource", help="Read one resource URI.")
    read_resource.add_argument("uri")

    get_prompt = subparsers.add_parser("get-prompt", help="Render one prompt.")
    get_prompt.add_argument("name")
    get_prompt.add_argument("--arg", action="append", default=[], metavar="KEY=VALUE", help="Prompt argument as KEY=VALUE. Repeat for multiple args.")

    call_tool = subparsers.add_parser("call-tool", help="Call one tool.")
    call_tool.add_argument("name")
    call_tool.add_argument("--arg", action="append", default=[], metavar="KEY=VALUE", help="Tool argument as KEY=VALUE. Repeat for multiple args.")

    return parser


def parse_key_value_pairs(pairs: list[str]) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"Expected KEY=VALUE pair, got: {pair}")
        key, raw_value = pair.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Argument key cannot be empty: {pair}")
        parsed[key] = parse_scalar(raw_value.strip())
    return parsed


def parse_scalar(raw_value: str) -> Any:
    lowered = raw_value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "null":
        return None
    if raw_value.startswith("{") or raw_value.startswith("["):
        try:
            return json.loads(raw_value)
        except json.JSONDecodeError:
            return raw_value
    try:
        if raw_value.startswith("0") and raw_value not in {"0", "0.0"} and not raw_value.startswith("0."):
            return raw_value
        return int(raw_value)
    except ValueError:
        pass
    try:
        return float(raw_value)
    except ValueError:
        return raw_value


def build_config(args: argparse.Namespace) -> ClientConfig:
    return ClientConfig(
        connection_mode=args.connection_mode,
        server_command=args.server_command,
        server_args=args.server_arg,
        server_cwd=args.server_cwd,
        server_url=args.server_url,
        auto_approve=args.yes,
        bearer_token=args.bearer_token,
    )


async def run_cli(args: argparse.Namespace) -> int:
    config = build_config(args)
    if config.connection_mode == "http":
        return await run_http_cli(args, config)
    return await run_stdio_cli(args, config)


async def run_stdio_cli(args: argparse.Namespace, config: ClientConfig) -> int:
    params = StdioServerParameters(command=config.server_command, args=config.server_args, cwd=config.server_cwd)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            if args.command == "discover":
                return await run_discover(session)
            await session.initialize()
            return await dispatch_initialized_command(session, args, auto_approve=config.auto_approve)


async def run_http_cli(args: argparse.Namespace, config: ClientConfig) -> int:
    headers: dict[str, str] | None = None
    if config.bearer_token:
        headers = {"Authorization": f"Bearer {config.bearer_token}"}
    async with httpx.AsyncClient(headers=headers, timeout=30.0) as http_client:
        async with streamable_http_client(config.server_url, http_client=http_client) as parts:
            read, write = parts[0], parts[1]
            async with ClientSession(read, write) as session:
                if args.command == "discover":
                    return await run_discover(session)
                return await dispatch_initialized_command(session, args, auto_approve=config.auto_approve)


async def dispatch_initialized_command(session: ClientSession, args: argparse.Namespace, *, auto_approve: bool) -> int:
    if args.command == "list-tools":
        return await run_list_tools(session)
    if args.command == "list-resource-templates":
        return await run_list_resource_templates(session)
    if args.command == "list-prompts":
        return await run_list_prompts(session)
    if args.command == "read-resource":
        return await run_read_resource(session, args.uri)
    if args.command == "get-prompt":
        prompt_args = parse_key_value_pairs(args.arg)
        return await run_get_prompt(session, args.name, prompt_args)
    if args.command == "call-tool":
        tool_args = parse_key_value_pairs(args.arg)
        return await run_call_tool(session, args.name, tool_args, auto_approve=auto_approve)
    raise ValueError(f"Unknown command: {args.command}")


async def run_discover(session: ClientSession) -> int:
    started = time.perf_counter()
    result = await session.discover()
    payload = {
        "server": result.meta.get("io.modelcontextprotocol/serverInfo", {}),
        "supported_versions": result.supported_versions,
        "capabilities": model_dump(result.capabilities),
        "instructions": result.instructions,
        "latency_ms": elapsed_ms(started),
    }
    print_json(payload)
    return 0


async def run_list_tools(session: ClientSession) -> int:
    started = time.perf_counter()
    result = await session.list_tools()
    payload = {
        "count": len(result.tools),
        "latency_ms": elapsed_ms(started),
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
                "is_write": tool.name in WRITE_TOOLS,
            }
            for tool in result.tools
        ],
    }
    print_json(payload)
    return 0


async def run_list_resource_templates(session: ClientSession) -> int:
    started = time.perf_counter()
    result = await session.list_resource_templates()
    payload = {
        "count": len(result.resource_templates),
        "latency_ms": elapsed_ms(started),
        "resource_templates": [
            {
                "name": resource.name,
                "uri_template": resource.uri_template,
                "mime_type": resource.mime_type,
                "description": resource.description,
            }
            for resource in result.resource_templates
        ],
    }
    print_json(payload)
    return 0


async def run_list_prompts(session: ClientSession) -> int:
    started = time.perf_counter()
    result = await session.list_prompts()
    payload = {
        "count": len(result.prompts),
        "latency_ms": elapsed_ms(started),
        "prompts": [
            {
                "name": prompt.name,
                "description": prompt.description,
                "arguments": [{"name": argument.name, "required": argument.required} for argument in (prompt.arguments or [])],
            }
            for prompt in result.prompts
        ],
    }
    print_json(payload)
    return 0


async def run_read_resource(session: ClientSession, uri: str) -> int:
    started = time.perf_counter()
    result = await session.read_resource(uri)
    payload = {
        "uri": uri,
        "status": "ok",
        "latency_ms": elapsed_ms(started),
        "contents": [serialize_content(item) for item in result.contents],
    }
    print_json(payload)
    return 0


async def run_get_prompt(session: ClientSession, name: str, arguments: dict[str, Any]) -> int:
    started = time.perf_counter()
    prompt_arguments = {key: str(value) for key, value in arguments.items()}
    result = await session.get_prompt(name, prompt_arguments or None)
    payload = {
        "name": name,
        "arguments": prompt_arguments,
        "status": "ok",
        "latency_ms": elapsed_ms(started),
        "messages": [serialize_prompt_message(message) for message in result.messages],
    }
    print_json(payload)
    return 0


async def run_call_tool(session: ClientSession, name: str, arguments: dict[str, Any], *, auto_approve: bool) -> int:
    if name in WRITE_TOOLS and not approve_write(name, arguments, auto_approve=auto_approve):
        print_json({"tool": name, "status": "denied", "reason": "Write operation was not approved by the client."})
        return 3

    started = time.perf_counter()
    result = await session.call_tool(name, arguments or None)
    payload = {
        "tool": name,
        "arguments": arguments,
        "status": "error" if getattr(result, "is_error", False) else "ok",
        "latency_ms": elapsed_ms(started),
        "content": [serialize_content(item) for item in result.content],
    }
    print_json(payload)
    return 2 if getattr(result, "is_error", False) else 0


def approve_write(name: str, arguments: dict[str, Any], *, auto_approve: bool) -> bool:
    if auto_approve:
        return True
    print(f"Write tool: {name}")
    print("Arguments:")
    print(json.dumps(arguments, indent=2, sort_keys=True))
    response = input("Approve write? [y/N]: ").strip().lower()
    return response in {"y", "yes"}


def serialize_content(item: Any) -> dict[str, Any]:
    payload = model_dump(item)
    if "blob" in payload and payload["blob"] is not None:
        payload["blob_length"] = len(payload["blob"])
    return payload


def serialize_prompt_message(message: Any) -> dict[str, Any]:
    return {"role": message.role, "content": serialize_content(message.content)}


def model_dump(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", exclude_none=True)
    return value


def elapsed_ms(started: float) -> int:
    return round((time.perf_counter() - started) * 1000)


def print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True))


def summarize_exception(exc: BaseException) -> str:
    if isinstance(exc, BaseExceptionGroup):
        messages: list[str] = []
        stack: list[BaseException] = [exc]
        while stack:
            current = stack.pop()
            if isinstance(current, BaseExceptionGroup):
                stack.extend(reversed(list(current.exceptions)))
                continue
            message = str(current).strip() or current.__class__.__name__
            if message not in messages:
                messages.append(message)
        return "; ".join(messages) if messages else exc.__class__.__name__
    return str(exc).strip() or exc.__class__.__name__


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return asyncio.run(run_cli(args))
    except ValueError as exc:
        parser.error(str(exc))
    except MCPError as exc:
        print_json({"status": "error", "error_type": "mcp", "message": str(exc)})
        return 1
    except BaseExceptionGroup as exc:
        print_json({"status": "error", "error_type": "transport", "message": summarize_exception(exc)})
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

