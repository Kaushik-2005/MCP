from starlette.testclient import TestClient

from researchops_mcp.server import create_streamable_http_app


BASE_HEADERS = {
    "accept": "application/json, text/event-stream",
    "content-type": "application/json",
}


def _create_client() -> TestClient:
    app = create_streamable_http_app(
        auth_enabled=True,
        resource_server_url="http://testserver/mcp",
        stateless_http=True,
    )
    return TestClient(app)


def test_streamable_http_requires_authentication() -> None:
    with _create_client() as client:
        response = client.post(
            "/mcp",
            headers=BASE_HEADERS,
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
        )

    assert response.status_code == 401
    assert response.json()["error"] == "invalid_token"
    assert "Authentication required" in response.headers["www-authenticate"]
    assert "resource_metadata=" in response.headers["www-authenticate"]


def test_streamable_http_rejects_invalid_bearer_token() -> None:
    with _create_client() as client:
        response = client.post(
            "/mcp",
            headers={**BASE_HEADERS, "authorization": "Bearer invalid-token"},
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
        )

    assert response.status_code == 401
    assert response.json()["error"] == "invalid_token"


def test_streamable_http_rejects_insufficient_scope() -> None:
    with _create_client() as client:
        response = client.post(
            "/mcp",
            headers={
                **BASE_HEADERS,
                "authorization": "Bearer researchops-bob-read",
                "mcp-method": "tools/call",
                "mcp-name": "add_note",
            },
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {}},
        )

    assert response.status_code == 403
    assert response.json()["error"] == "insufficient_scope"
    assert "scope=\"notes:write\"" in response.headers["www-authenticate"]
