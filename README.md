# ResearchOps MCP

ResearchOps MCP is a learning project for building a production-style Model Context Protocol server in Python over a 14-day roadmap. The goal is to understand MCP deeply while delivering a portfolio-quality server that can search papers, expose paper context, manage reading lists and notes, and later support secure remote access.

## Current Status

The project is in Day 6 of the roadmap. The local MCP server now supports OpenAlex-backed paper tools, stable paper and reading-list resources, reusable prompt templates, SQLite-backed write tools for reading lists and notes, and a local Python MCP client for discovery, resource reads, prompts, and approval-gated tool calls.

## Planned Capabilities

- Search research papers
- Retrieve paper metadata and abstracts
- Maintain reading lists
- Add and update research notes
- Compare papers with reusable prompts
- Export citations in BibTeX
- Run longer-running literature workflows

## Roadmap References

- Curriculum: `MCP_Industry_Learning_Roadmap.md`
- Progress: `docs/tracker.md`
- Learning notes: `docs/learning.md`
- Decisions: `docs/decisions.md`
- Design: `docs/design.md`


## Local Development

Install the project in editable mode:

```powershell
python -m pip install -e .[dev]
```

Run the unit tests:

```powershell
pytest
```

Run the local server entry point:

```powershell
python src/server.py
```

Run the server through MCP Inspector:

```powershell
npx @modelcontextprotocol/inspector@latest python src/server.py
```

Run the local client for capability discovery:

```powershell
python client/cli.py discover
```

List tools:

```powershell
python client/cli.py list-tools
```

Read a paper resource:

```powershell
python client/cli.py read-resource paper://W7129030749
```

Call a write tool with explicit approval bypass for scripted use:

```powershell
python client/cli.py --yes call-tool create_reading_list --arg name=MyList --arg idempotency_key=my-key-1
```

