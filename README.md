# ResearchOps MCP

ResearchOps MCP is a learning project for building a production-style Model Context Protocol server in Python over a 14-day roadmap. The goal is to understand MCP deeply while delivering a portfolio-quality server that can search papers, expose paper context, manage reading lists and notes, and later support secure remote access.

## Current Status

The project is in Day 4 of the roadmap. The local MCP server already uses OpenAlex for real paper search and lookup, and the next step is to add resources and prompt templates on top of the read-only paper server.

## Planned Capabilities

- Search research papers
- Retrieve paper metadata and abstracts
- Maintain reading lists
- Add and update research notes
- Compare papers with reusable prompts
- Export citations in BibTeX
- Run longer-running literature workflows

## Roadmap References

- Curriculum: [MCP_Industry_Learning_Roadmap.md](/C:/Users/kaush/OneDrive/Desktop/Work/MCP/MCP_Industry_Learning_Roadmap.md)
- Progress: [tracker.md](/C:/Users/kaush/OneDrive/Desktop/Work/MCP/docs/tracker.md)
- Learning notes: [learning.md](/C:/Users/kaush/OneDrive/Desktop/Work/MCP/docs/learning.md)
- Decisions: [decisions.md](/C:/Users/kaush/OneDrive/Desktop/Work/MCP/docs/decisions.md)
- Questions: [questions.md](/C:/Users/kaush/OneDrive/Desktop/Work/MCP/docs/questions.md)


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


