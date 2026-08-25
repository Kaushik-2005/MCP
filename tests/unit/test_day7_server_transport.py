from researchops_mcp.server import (
    DEFAULT_DB_PATH,
    DEFAULT_HOST,
    DEFAULT_PORT,
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
        ]
    )

    assert args.transport == "streamable-http"
    assert args.host == "0.0.0.0"
    assert args.port == 9000
    assert args.streamable_http_path == "/remote-mcp"
    assert args.json_response is True
    assert args.stateless_http is True


def test_create_streamable_http_app_has_expected_path() -> None:
    app = create_streamable_http_app(streamable_http_path="/remote-mcp", stateless_http=True)
    paths = sorted(route.path for route in app.routes)

    assert "/remote-mcp" in paths


def test_default_database_path_is_present() -> None:
    assert DEFAULT_DB_PATH
