# ResearchOps MCP

ResearchOps MCP is a learning project for building a production-style Model Context Protocol server in Python over a 14-day roadmap. The goal is to understand MCP deeply while delivering a portfolio-quality server that can search papers, expose paper context, manage reading lists and notes, and later support secure remote access.

## Current Status

The project is in Day 6 of the roadmap. The local MCP server now supports OpenAlex-backed paper tools, stable paper and reading-list resources, reusable prompt templates, and SQLite-backed write tools for reading lists and notes. The next step is to build a Python MCP client on top of the completed local server.

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









