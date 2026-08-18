# MCP Learning Tracker

## Current Position

- Current module: Module 1 - MCP Foundations
- Current day: Day 2 - First local MCP server
- Current task: Build the first local FastMCP server with mock `health_check`, `search_papers`, and `get_paper` tools
- Next milestone: Create the Day 2 local server entry point and connect it through MCP Inspector
- Active blockers: None

## Roadmap Progress

| Day | Module | Main Topic | Status | Deliverable | Verification | Confidence |
|---|---|---|---|---|---|---|
| 1 | Foundations | Protocol fundamentals | Completed | Project specification, architecture diagram, and threat-model outline | `docs/project-spec.md` and `docs/threat-model.md` created; Day 1 theory reviewed interactively; learner explained host/client/server roles, JSON-RPC basics, statelessness, primitive boundaries, and approval vs authorization | 4 |
| 2 | Foundations | First local MCP server | Not Started | Working local MCP server with `health_check`, `search_papers`, `get_paper` | — | — |
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


