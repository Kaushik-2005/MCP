from researchops_mcp.client_cli import WRITE_TOOLS, build_config, build_parser, parse_key_value_pairs, parse_scalar


def test_parse_key_value_pairs_converts_scalar_types() -> None:
    parsed = parse_key_value_pairs(
        [
            "query=Model Context Protocol",
            "limit=2",
            "confirm=true",
            "score=1.5",
            "payload={\"a\": 1}",
        ]
    )

    assert parsed == {
        "query": "Model Context Protocol",
        "limit": 2,
        "confirm": True,
        "score": 1.5,
        "payload": {"a": 1},
    }


def test_parse_key_value_pairs_rejects_invalid_argument() -> None:
    try:
        parse_key_value_pairs(["missing-separator"])
    except ValueError as exc:
        assert "Expected KEY=VALUE pair" in str(exc)
    else:
        raise AssertionError("Expected ValueError for malformed argument")


def test_parse_scalar_preserves_leading_zero_strings() -> None:
    assert parse_scalar("00123") == "00123"


def test_write_tool_policy_contains_day5_writes() -> None:
    assert WRITE_TOOLS == {
        "create_reading_list",
        "add_paper_to_list",
        "add_note",
        "update_note",
        "delete_note",
    }


def test_build_config_defaults_to_stdio_mode() -> None:
    args = build_parser().parse_args(["discover"])
    config = build_config(args)

    assert config.connection_mode == "stdio"
    assert config.server_command == "python"
    assert config.server_args == ["src/server.py"]
    assert config.server_url == "http://127.0.0.1:8000/mcp"


def test_build_config_accepts_http_mode() -> None:
    args = build_parser().parse_args([
        "--connection-mode",
        "http",
        "--server-url",
        "http://127.0.0.1:8765/mcp",
        "discover",
    ])
    config = build_config(args)

    assert config.connection_mode == "http"
    assert config.server_url == "http://127.0.0.1:8765/mcp"
