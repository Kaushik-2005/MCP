import json

import pytest
from mcp.client import Client

from researchops_mcp.server import server


@pytest.mark.anyio
async def test_server_exposes_day4_resource_templates_and_prompts() -> None:
    async with Client(server) as client:
        templates = await client.list_resource_templates()
        template_uris = {template.uri_template for template in templates.resource_templates}
        assert "paper://{paper_id}" in template_uris
        assert "reading-list://{list_id}" in template_uris

        prompts = await client.list_prompts()
        prompt_names = {prompt.name for prompt in prompts.prompts}
        assert "compare_papers" in prompt_names
        assert "generate_literature_review" in prompt_names


@pytest.mark.anyio
async def test_server_reads_reading_list_resource_and_renders_compare_prompt() -> None:
    async with Client(server) as client:
        resource_result = await client.read_resource("reading-list://starter-mcp")
        reading_list_payload = json.loads(resource_result.contents[0].text)
        assert reading_list_payload["list_id"] == "starter-mcp"
        assert reading_list_payload["paper_resources"]

        prompt_result = await client.get_prompt(
            "compare_papers",
            arguments={
                "paper_id_a": "W7129030749",
                "paper_id_b": "W4417069007",
                "focus": "security trade-offs",
            },
        )
        assert "paper://W7129030749" in prompt_result.messages[0].content.text
        assert "security trade-offs" in prompt_result.messages[0].content.text
