# ResearchOps MCP

ResearchOps MCP is a learning project for building a production-style Model Context Protocol server in Python over a 14-day roadmap. The goal is to understand MCP deeply while delivering a portfolio-quality server that can search papers, expose paper context, manage reading lists and notes, and later support secure remote access.

## Current Status

The project is in Day 7 of the roadmap. The server now supports both local `stdio` and Streamable HTTP transport, includes a Docker-based deployment path, and the Python MCP client can talk to the same server over either transport.

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

## Streamable HTTP

Run the server over Streamable HTTP:

```powershell
python src/server.py --transport streamable-http --host 127.0.0.1 --port 8765 --stateless-http
```

Use the client against the HTTP server:

```powershell
python client/cli.py --connection-mode http --server-url http://127.0.0.1:8765/mcp discover
python client/cli.py --connection-mode http --server-url http://127.0.0.1:8765/mcp list-tools
```

## Docker

Build the container image:

```powershell
docker build -t researchops-mcp .
```

Run the container locally:

```powershell
docker run --rm -p 8000:8000 -e PORT=8000 -e DATABASE_PATH=/tmp/researchops.db researchops-mcp
```

## Render Deployment Prep

This repository now includes:
- `Dockerfile` for Streamable HTTP serving
- `render.yaml` for a free Render web service
- env-aware server startup using Render-style `PORT`
- explicit temporary staging DB path via `DATABASE_PATH=/tmp/researchops.db`

Important limitation:
- Render free web services use an ephemeral filesystem
- `DATABASE_PATH=/tmp/researchops.db` is staging-only and disposable
- reading lists and notes will not survive redeploys, restarts, or idle spin-down

### Recommended Render Setup

Use a Render `Web Service` with:
- Runtime: `Docker`
- Plan: `Free`
- Repo root `Dockerfile`
- Public MCP path: `/mcp`

### Manual Render Steps

1. Push the current branch to GitHub.
2. Sign in to Render.
3. Create a new `Web Service`.
4. Connect the GitHub repository.
5. Choose `Docker` as the runtime.
6. Use the free plan.
7. Confirm these environment variables:
   - `DATABASE_PATH=/tmp/researchops.db`
   - `MCP_TRANSPORT=streamable-http`
   - `MCP_HOST=0.0.0.0`
   - `MCP_STATELESS_HTTP=true`
   - `MCP_STREAMABLE_HTTP_PATH=/mcp`
8. Deploy the service.
9. After deploy, note the Render URL, which should look like:
   - `https://<your-service-name>.onrender.com/mcp`
10. Verify it with the client:

```powershell
python client/cli.py --connection-mode http --server-url https://<your-service-name>.onrender.com/mcp discover
python client/cli.py --connection-mode http --server-url https://<your-service-name>.onrender.com/mcp list-tools
```

### What Still Remains To Fully Finish Day 7

- Deploy the real Render staging instance
- Verify the non-local Render MCP URL
- Test the remote URL with MCP Inspector
- Connect that URL to a supported AI host
