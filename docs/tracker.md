# MCP Learning Tracker

## Current Position

- Current module: Module 1 - MCP Foundations
- Current day: Day 3 - Production-quality tool design
- Current task: Replace mock-only behavior with stronger tool contracts and prepare real API integration
- Next milestone: Connect `search_papers` to a real paper API and tighten tool schemas, limits, and errors
- Active blockers: None

## Roadmap Progress

| Day | Module | Main Topic | Status | Deliverable | Verification | Confidence |
|---|---|---|---|---|---|---|
| 1 | Foundations | Protocol fundamentals | Completed | Project specification, architecture diagram, and threat-model outline | `docs/project-spec.md` and `docs/threat-model.md` created; Day 1 theory reviewed interactively; learner explained host/client/server roles, JSON-RPC basics, statelessness, primitive boundaries, and approval vs authorization | 4 |
| 2 | Foundations | First local MCP server | Completed | Working local MCP server with `health_check`, `search_papers`, `get_paper` | `pytest` passed; SDK client listed and invoked all tools; MCP Inspector connected successfully and verified all three tools interactively | 4 |
| 3 | Foundations | Production-quality tool design | Not Started | Dependable read-only research-paper server | — | — |
| 4 | Context and Persistence | Resources and prompts | Not Started | Discoverable resources and reusable prompts | — | — |
| 5 | Context and Persistence | Storage and write operations | Not Started | Persistent MCP application with write safety | — | — |
| 6 | Client and Remote Transport | Build an MCP client | Not Started | Python CLI client for ResearchOps MCP | — | — |
| 7 | Client and Remote Transport | Streamable HTTP and deployment | Not Started | Remotely accessible staging MCP server | — | — |
| 8 | Security and Reliability | Authentication and authorization | Not Started | Authenticated multi-user remote server | — | — |
| 9 | Security and Reliability | MCP security | Not Started | Security checklist, threat model, adversarial tests | — | — |
| 10 | Security and Reliability | Reliability engineering | Not Started | Predictable behavior during dependency failures | — | — |
| 11 | Testing and Production | Protocol and application testing | Not Started | Automated tests and MCP Inspector report | — | — |
| 12 | Testing and Production | Model and tool-selection evaluation | Not Started | Measurable evaluation report | — | — |
| 13 | Testing and Production | Observability and scaling | Not Started | Observable production candidate | — | — |
| 14 | Testing and Production | Advanced features and final release | Not Started | Portfolio-ready MCP project | — | — |

## Session Log

### 2026-08-18

- Topics studied: MCP role, host-client-server architecture, JSON-RPC message types, protocol-version changes, capability discovery, trust boundaries
- Work implemented: Initialized learning and progress docs; created Day 1 project spec and threat model outline
- Work implemented: Reviewed Day 1 theory interactively and clarified stateless protocol versus stateful application design
- Tests executed: None; Day 1 was a theory and documentation milestone
- Results: Day 1 deliverables are present and reviewed: project specification, architecture diagram, and initial threat model
- Results: Learner can explain MCP versus APIs, host/client/server roles, JSON-RPC basics, `server/discover`, protocol statelessness, primitive boundaries, prompt-injection risk, and host approval versus server authorization
- Problems encountered: Local workspace is not a Git repository; shell sandbox helper failed and required unsandboxed reads
- Decisions made: Start with specification-first documentation before writing server code
- Topics to revisit: Exact boundary between tools, resources, prompts, and Tasks once the schema is concrete
- Next action: Begin Day 2 by scaffolding a local FastMCP server and adding mock tools



### 2026-08-19

- Topics studied: MCP Python SDK v2, MCPServer rename from FastMCP, tool registration, stdio transport, structured results, tool-level errors
- Work implemented: Added pyproject.toml, local server scaffold, mock paper data, roadmap entry point, and unit test
- Tests executed: pytest; inline Python verification of direct tool calls; inline SDK client verification for tool listing and invocation
- Results: pytest passed; client listed health_check, search_papers, and get_paper; success and failure cases behaved as expected
- Problems encountered: Sandbox helper failed again; global environment install introduced a `fastapi`/`starlette` dependency conflict risk
- Decisions made: Use current official SDK v2 naming (MCPServer) while documenting the roadmap's older FastMCP term
- Topics to revisit: MCP Inspector workflow and how stdio transport is wired in practice
- Next action: Begin Day 3 by tightening tool design and connecting `search_papers` to a real research API




