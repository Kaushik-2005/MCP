"""Local verification script for the Day 2 MCP server scaffold."""

from __future__ import annotations

import asyncio

from mcp import Client

from researchops_mcp.server import server


async def main() -> None:
    async with Client(server) as client:
        tools = await client.list_tools()
        print("tools:", [tool.name for tool in tools.tools])

        health = await client.call_tool("health_check", arguments={})
        print("health_check:", health.structured_content)

        search = await client.call_tool(
            "search_papers",
            arguments={"query": "mcp", "limit": 2},
        )
        print("search_papers:", search.structured_content)


if __name__ == "__main__":
    asyncio.run(main())
