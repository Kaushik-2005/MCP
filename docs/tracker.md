# MCP Learning Tracker

## Current Position

- Current module: Module 2 - Context and Persistence
- Current day: Day 6 - Build an MCP client
- Current task: Build a small Python MCP client that discovers capabilities, reads resources, calls tools, and shows write intent clearly
- Next milestone: Create a Python CLI client for ResearchOps MCP with discovery, reads, tool calls, and basic approval flow
- Active blockers: None

## Roadmap Progress

| Day | Module | Main Topic | Status | Deliverable | Verification | Confidence |
|---|---|---|---|---|---|---|
| 1 | Foundations | Protocol fundamentals | Completed | Project specification, architecture diagram, and threat-model outline | `docs/project-spec.md` and `docs/threat-model.md` created; Day 1 theory reviewed interactively; learner explained host/client/server roles, JSON-RPC basics, statelessness, primitive boundaries, and approval vs authorization | 4 |
| 2 | Foundations | First local MCP server | Completed | Working local MCP server with `health_check`, `search_papers`, `get_paper` | `pytest` passed; SDK client listed and invoked all tools; MCP Inspector connected successfully and verified all three tools interactively | 4 |
| 3 | Foundations | Production-quality tool design | Completed | Dependable read-only OpenAlex-backed research-paper server | `pytest` passed; MCP Inspector verified `search_papers`, `get_paper`, and `export_bibtex`; exact-mode MCP query returned relevant MCP papers; empty-result and invalid-query cases verified; learner explained empty results, stable identifiers, service-layer separation, and separate export tooling | 5 |
| 4 | Context and Persistence | Resources and prompts | Completed | Discoverable paper and reading-list resources plus reusable prompts | `pytest` passed with 10 tests; MCP Inspector verified Day 4 resources and prompts interactively; in-process MCP client listed resource templates and prompts, read `reading-list://starter-mcp`, and rendered `compare_papers`; learner explained tool vs resource vs prompt boundaries and why context-size limits matter | 4 |
| 5 | Context and Persistence | Storage and write operations | Completed | Persistent SQLite-backed MCP application with write safety | `pytest` passed with 14 tests; Inspector verified `create_reading_list`, `add_paper_to_list`, `add_note`, `update_note`, and `delete_note`; learner explained repository/service split, idempotency, optimistic concurrency, and stable interface shape | 4 |
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





### 2026-08-20

- Topics studied: focused tool boundaries, action-oriented tool naming, parameter limits, structured outputs, stable identifiers, pagination, actionable errors, and search relevance strategy
- Work implemented: Added OpenAlex client and paper service layer, upgraded search_papers and get_paper to real API-backed behavior, added export_bibtex, and tightened search quality with an exact-first strategy plus stricter OpenAlex paper ID validation
- Tests executed: pytest; live Python checks for OpenAlex-backed search_papers, get_paper, and export_bibtex; MCP-level verification for empty results and invalid input; MCP Inspector verification for all three tools
- Results: Real OpenAlex integration works; BibTeX export works; invalid query returns a clear tool error; empty-result search returns a valid empty list with pagination metadata
- Results: MCP Inspector confirmed search_papers, get_paper, and export_bibtex behave correctly; exact-mode search for Model Context Protocol returned relevant MCP papers rather than unrelated long-tail matches
- Results: Learner can explain why empty results are valid, why stable identifiers matter, why dependency logic belongs in a service layer, and why export_bibtex is a separate tool
- Problems encountered: OpenAlex can resolve misleading IDs like W0000000000 to W0, so missing-paper tests must use truly nonexistent IDs
- Decisions made: Use OpenAlex as the Day 3 paper source instead of CORE; keep citation export as a separate tool rather than overloading get_paper
- Topics to revisit: Additional ranking heuristics if OpenAlex still returns weak long-tail matches for ambiguous queries
- Next action: Begin Day 4 by adding resources and prompt templates on top of the read-only paper server

### 2026-08-21

- Topics studied: service versus repository boundaries, SQLite persistence, transactions, idempotency keys, optimistic note updates, read/write separation, and confirmation-gated deletes
- Work implemented: Added a SQLite repository layer, durable reading lists and notes, audit/idempotency tables, persistent `reading-list://{list_id}` resources, and new write tools: `create_reading_list`, `add_paper_to_list`, `add_note`, `update_note`, and `delete_note`
- Tests executed: `pytest`; MCP Inspector verification for Day 5 write tools and persistent resource reads
- Results: 14 tests passed; service-level tests verified idempotency, optimistic concurrency conflicts, and note preconditions; MCP-level tests verified persistent write flows and stable reading-list resource reads
- Results: MCP Inspector confirmed the Day 5 write tools behave as expected, including retry safety, version checks, and delete confirmation
- Work implemented: Design documentation added in `docs/design.md` with architecture, database, and request-flow diagrams
- Results: Learner can explain repository versus service layers, idempotency versus optimistic concurrency, and why the `reading-list://{list_id}` interface stayed stable while the backing store changed
- Problems encountered: One Day 4 MCP test still expected the old reading-list payload shape after persistence landed; the test was updated to the new persistent resource structure
- Decisions made: Use SQLite via the Python standard library for local persistence and keep the `reading-list://{list_id}` resource shape stable while changing only the backing implementation
- Topics to revisit: How to evolve the SQLite local design into the later remote multi-user architecture
- Next action: Begin Day 6 by building a small Python MCP client for discovery, reads, and tool calls




