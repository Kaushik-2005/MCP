from starlette.datastructures import Headers

from researchops_mcp.auth import DemoTokenVerifier, current_identity, required_scope_for_headers
from researchops_mcp.server import (
    DEFAULT_AUTH_ENABLED,
    DEFAULT_AUTH_ISSUER_URL,
    DEFAULT_DB_PATH,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_RESOURCE_SERVER_URL,
    DEFAULT_STATELESS_HTTP,
    DEFAULT_STREAMABLE_HTTP_PATH,
    DEFAULT_TRANSPORT,
    build_parser,
    create_streamable_http_app,
)


def test_server_parser_defaults_respect_environment_shape() -> None:
    args = build_parser().parse_args([])

    assert args.transport == DEFAULT_TRANSPORT
    assert args.host == DEFAULT_HOST
    assert args.port == DEFAULT_PORT
    assert args.streamable_http_path == DEFAULT_STREAMABLE_HTTP_PATH
    assert args.stateless_http == DEFAULT_STATELESS_HTTP
    assert args.auth_enabled == DEFAULT_AUTH_ENABLED
    assert args.resource_server_url == DEFAULT_RESOURCE_SERVER_URL
    assert args.auth_issuer_url == DEFAULT_AUTH_ISSUER_URL


def test_server_parser_accepts_streamable_http_flags() -> None:
    args = build_parser().parse_args(
        [
            "--transport",
            "streamable-http",
            "--host",
            "0.0.0.0",
            "--port",
            "9000",
            "--streamable-http-path",
            "/remote-mcp",
            "--json-response",
            "--stateless-http",
            "--auth-enabled",
            "--resource-server-url",
            "https://researchops-mcp.onrender.com/mcp",
            "--auth-issuer-url",
            "https://auth.researchops.example.com",
        ]
    )

    assert args.transport == "streamable-http"
    assert args.host == "0.0.0.0"
    assert args.port == 9000
    assert args.streamable_http_path == "/remote-mcp"
    assert args.json_response is True
    assert args.stateless_http is True
    assert args.auth_enabled is True
    assert args.resource_server_url == "https://researchops-mcp.onrender.com/mcp"
    assert args.auth_issuer_url == "https://auth.researchops.example.com"


def test_create_streamable_http_app_has_expected_path() -> None:
    app = create_streamable_http_app(streamable_http_path="/remote-mcp", stateless_http=True)
    paths = sorted(route.path for route in app.routes)

    assert "/remote-mcp" in paths


def test_default_database_path_is_present() -> None:
    assert DEFAULT_DB_PATH


def test_demo_token_verifier_accepts_known_token() -> None:
    verifier = DemoTokenVerifier(resource_server_url="https://researchops-mcp.onrender.com/mcp")
    token = verifier._token_map["researchops-alice-full"]

    assert token["subject"] == "alice"


def test_required_scope_for_headers_maps_tools_and_resources() -> None:
    tool_headers = Headers({"mcp-method": "tools/call", "mcp-name": "add_note"})
    list_headers = Headers({"mcp-method": "resources/read", "mcp-param-uri": "reading-list://starter-mcp"})
    paper_headers = Headers({"mcp-method": "resources/read", "mcp-param-uri": "paper://W7129030749"})

    assert required_scope_for_headers(tool_headers) == "notes:write"
    assert required_scope_for_headers(list_headers) == "lists:read"
    assert required_scope_for_headers(paper_headers) == "papers:read"


def test_current_identity_defaults_to_local_user_without_token() -> None:
    identity = current_identity()

    assert identity.user_id
    assert "papers:read" in identity.scopes
