# MCP Learning Tracker

## Current Position

- Current module: Module 4 - Authentication, Security, and Reliability
- Current day: Day 9 - MCP security
- Current task: Day 9 formally completed and documented
- Next milestone: Begin Day 10 reliability engineering
- Active blockers: None

## Roadmap Progress

| Day | Module | Main Topic | Status | Deliverable | Verification | Confidence |
|---|---|---|---|---|---|---|
| 1 | Foundations | Protocol fundamentals | Completed | Project specification, architecture diagram, and threat-model outline | `docs/project-spec.md` and `docs/threat-model.md` created; Day 1 theory reviewed interactively; learner explained host/client/server roles, JSON-RPC basics, statelessness, primitive boundaries, and approval vs authorization | 4 |
| 2 | Foundations | First local MCP server | Completed | Working local MCP server with `health_check`, `search_papers`, `get_paper` | `pytest` passed; SDK client listed and invoked all tools; MCP Inspector connected successfully and verified all three tools interactively | 4 |
| 3 | Foundations | Production-quality tool design | Completed | Dependable read-only OpenAlex-backed research-paper server | `pytest` passed; MCP Inspector verified `search_papers`, `get_paper`, and `export_bibtex`; exact-mode MCP query returned relevant MCP papers; empty-result and invalid-query cases verified; learner explained empty results, stable identifiers, service-layer separation, and separate export tooling | 5 |
| 4 | Context and Persistence | Resources and prompts | Completed | Discoverable paper and reading-list resources plus reusable prompts | `pytest` passed with 10 tests; MCP Inspector verified Day 4 resources and prompts interactively; in-process MCP client listed resource templates and prompts, read `reading-list://starter-mcp`, and rendered `compare_papers`; learner explained tool vs resource vs prompt boundaries and why context-size limits matter | 4 |
| 5 | Context and Persistence | Storage and write operations | Completed | Persistent SQLite-backed MCP application with write safety | `pytest` passed with 14 tests; Inspector verified `create_reading_list`, `add_paper_to_list`, `add_note`, `update_note`, and `delete_note`; learner explained repository/service split, idempotency, optimistic concurrency, and stable interface shape | 4 |
| 6 | Client and Remote Transport | Build an MCP client | Completed | Python CLI client for ResearchOps MCP | `pytest` passed with 18 tests; CLI verified discovery, tool listing, resource reads, tool-error handling, denied write approval, and approved write execution on 2026-08-25; learner explained why discovery stays separate from the initialized request flow | 5 |
| 7 | Client and Remote Transport | Streamable HTTP and deployment | Completed | Remotely accessible staging MCP server | `pytest` passed with 24 tests; stdio and local HTTP both verified; Render deployment at `https://researchops-mcp.onrender.com/mcp` passed remote `discover`, `list-tools`, `health_check`, and `search_papers` on 2026-08-25; Inspector and CLI both validated the Streamable HTTP MCP surface | 5 |
| 8 | Security and Reliability | Authentication and authorization | Completed | Authenticated multi-user remote server | `pytest` passed with 32 tests; dedicated Day 8 HTTP auth tests verified `401` for missing and invalid tokens and `403` for insufficient scope; manual local HTTP checks verified Bob cannot write notes with a read-only token and cannot read Alice's list | 4 |
| 9 | Security and Reliability | MCP security | Completed | Security checklist, threat model, and adversarial tests | `pytest tests/unit/test_day9_security.py` passed with 8 tests and full `pytest` passed with 40 tests on 2026-08-29; manual HTTP checks verified untrusted-content warnings on `paper://W7129030749`, prompt hardening on `compare_papers`, ownership denial for Bob reading Alice's list, and rate limiting after repeated authenticated requests | 4 |
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

### 2026-08-23

- Topics studied: Day 6 kickoff; MCP client responsibilities, discovery flow, client-side approval, tool invocation, resource reads, and error handling
- Work implemented: Started Module 3 and reviewed the Day 6 milestone against the current server state
- Tests executed: None yet
- Results: Day 6 has been formally started; implementation pending
- Problems encountered: None
- Decisions made: Begin with a local Python CLI client over stdio before adding remote transport on Day 7
- Topics to revisit: Multiple-server isolation and lazy loading once the first client path works
- Next action: Teach Day 6 concepts, validate understanding, then scaffold the client

### 2026-08-25

- Topics studied: Day 6 client responsibilities, discovery versus initialized request flow, client-side approval, tool-error versus protocol-error handling, and local latency reporting
- Work implemented: Added a reusable Python CLI client in `client/cli.py` and `src/researchops_mcp/client_cli.py`; added a packaged `researchops-client` entry point; added client parsing tests
- Tests executed: `pytest`; `python client/cli.py discover`; `python client/cli.py list-tools`; `python client/cli.py read-resource paper://W7129030749`; `python client/cli.py call-tool get_paper --arg paper_id=W999999999999999`; denied and approved `create_reading_list` client runs; formal close-out verification with `python client/cli.py --yes call-tool create_reading_list --arg name=Day6FormalClose --arg idempotency_key=day6-formal-close-1`
- Results: 18 tests passed; discovery returns server info and capabilities; resource reads work; tool errors are surfaced as tool-level failures; write approval can deny execution; approved writes succeed and return stable list URIs
- Results: Formal Day 6 completion verification passed on 2026-08-25 with `pytest`, successful `discover`, and a successful approved `create_reading_list` client call
- Results: Learner can explain the Day 6 protocol nuance that `discover` must stay separate from the initialized request flow in this local setup
- Problems encountered: The first client version called `initialize()` before `discover()`, which caused a protocol-level error on the local connection; the flow was corrected by keeping `discover` separate from initialized operations
- Decisions made: Keep the Day 6 client on local stdio; use a small explicit write-tool approval policy until richer server-side annotations exist; keep the packaged implementation under `src/` and leave `client/cli.py` as a thin entry point
- Topics to revisit: Multiple-server isolation, lazy loading, and whether later server metadata should replace the local write-tool policy table
- Next action: Begin Day 7 by adding Streamable HTTP transport and preparing for remote-style verification

### 2026-08-25 Day 7 Kickoff

- Topics studied: Day 7 kickoff; Streamable HTTP transport, stateless remote serving, containerization, and deployment prerequisites
- Work implemented: Reviewed the roadmap, current server transport shape, packaging, and missing deployment files before starting Day 7
- Tests executed: None yet for Day 7
- Results: Confirmed Day 7 starts from a stdio-only server; no `Dockerfile` exists yet
- Problems encountered: None
- Decisions made: Start by teaching the Day 7 transport model before adding HTTP server code
- Topics to revisit: Exact SDK HTTP serving API and how to test remote Inspector against the local staging shape
- Next action: Teach Day 7 concepts, validate understanding, then add Streamable HTTP support
- Work implemented: Added Render deployment preparation including `render.yaml`, env-aware `PORT` and `DATABASE_PATH` settings, and `.dockerignore` for a smaller Docker build context
- Tests executed: `pytest`; `python src/server.py --help`; generated `render.yaml` reviewed for free Docker web-service settings
- Results: 24 tests passed; server now reads Render-style environment variables; the container and server startup are ready for a free Render web service using temporary SQLite at `/tmp/researchops.db`
- Topics to revisit: Real non-local Render URL verification and supported AI host connection still remain before Day 7 can be marked complete

### 2026-08-25 Day 7 Closeout

- Topics studied: Remote Streamable HTTP verification, free-host cold starts, Render staging behavior, and ephemeral deployment storage boundaries
- Work implemented: Completed Day 7 deployment verification against the public Render endpoint at `https://researchops-mcp.onrender.com/mcp`
- Tests executed: `pytest`; `python client/cli.py --connection-mode http --server-url https://researchops-mcp.onrender.com/mcp discover`; `python client/cli.py --connection-mode http --server-url https://researchops-mcp.onrender.com/mcp list-tools`; `python client/cli.py --connection-mode http --server-url https://researchops-mcp.onrender.com/mcp call-tool health_check`; `python client/cli.py --connection-mode http --server-url https://researchops-mcp.onrender.com/mcp call-tool search_papers --arg "query=Model Context Protocol" --arg "limit=2"`
- Results: Remote discovery returned server `researchops-mcp`, version `0.5.0`, and protocol `2026-07-28`; remote tool listing exposed the expected 9 tools with schemas and read/write boundaries
- Results: Remote `health_check` confirmed OpenAlex plus SQLite with staging database path `/tmp/researchops.db`; remote `search_papers` returned live OpenAlex results through the deployed MCP server
- Problems encountered: Early retries intermittently returned `Not Found` before later succeeding, consistent with free Render cold-start or routing wake-up behavior rather than a persistent MCP routing defect
- Decisions made: Accept temporary `/tmp/researchops.db` storage for Day 7 staging only and carry persistent remote storage as a later production concern
- Topics to revisit: Supported AI host connection and persistent remote database strategy after authentication work begins
- Next action: Start Day 8 by adding authentication and authorization boundaries for remote access

### 2026-08-27 Day 8 Kickoff

- Topics studied: Authentication versus authorization, OAuth 2.1 roles, protected resource metadata, scopes, token audience, and tenant ownership boundaries
- Work implemented: Reviewed the roadmap, current tracker state, current learning notes, and current code paths for user ownership and remote transport
- Tests executed: None yet for Day 8
- Results: Confirmed the repository already stores `user_id`, but the service still uses one default local user and the remote server does not yet enforce real authentication, scopes, or `401` and `403` responses
- Problems encountered: None
- Decisions made: Start Day 8 from the existing single-user ownership hooks rather than redesigning persistence from scratch
- Topics to revisit: Exact SDK support for auth middleware, protected resource metadata exposure, and how strict the first local auth simulation should be
- Next action: Teach Day 8 concepts, validate understanding, then implement the first authenticated request path

### 2026-08-27 Day 8 Closeout

- Topics studied: Authentication versus authorization, OAuth 2.1 roles, PKCE, protected resource metadata, resource indicators, scopes, and tenant ownership enforcement
- Work implemented: Added Day 8 auth helpers, demo bearer-token verification, per-scope enforcement, HTTP auth configuration, and user-aware list and note ownership checks through the service and repository layers
- Work implemented: Extended the CLI to send bearer tokens for HTTP transport and added dedicated Day 8 auth tests for `401` and `403` behavior
- Tests executed: `pytest tests/unit/test_day8_auth.py`; `pytest`; local HTTP CLI checks with `researchops-bob-read`, `researchops-alice-read`, `researchops-alice-full`, and no token
- Results: 32 tests passed; missing or invalid bearer tokens return `401`; insufficient write scope returns `403`; cross-user list access is blocked; authenticated owners can still read and write their own data
- Results: Learner can explain authentication versus authorization, `401` versus `403`, and why scope alone is not enough without ownership checks
- Problems encountered: The CLI currently summarizes some raw HTTP auth failures as generic transport errors instead of always surfacing the exact HTTP status cleanly
- Decisions made: Use the official MCP SDK auth surface with demo tokens now, and keep ownership enforcement in the repository layer rather than only at the MCP boundary
- Topics to revisit: Full external OAuth provider integration, token refresh, and cleaner client-side surfacing of remote auth failures
- Next action: Begin Day 9 security hardening with outbound controls, validation limits, audit review, and adversarial testing

### 2026-08-29 Day 9 Kickoff

- Topics studied: Day 9 kickoff; prompt injection, tool poisoning, tool shadowing, confused-deputy attacks, SSRF, data exfiltration, validation, rate limiting, and audit boundaries
- Work implemented: Reviewed the roadmap, tracker, learning notes, current Day 8 auth state, and current codebase before starting security hardening
- Tests executed: None yet for Day 9
- Results: Confirmed Day 8 is complete and the earliest incomplete milestone is Day 9 MCP security
- Problems encountered: None
- Decisions made: Start Day 9 from the current authenticated multi-user server instead of redesigning transport or auth again
- Topics to revisit: Which protections belong in transport middleware versus tool handlers versus downstream services
- Next action: Teach Day 9 security concepts, validate understanding, then implement the first hardening slice

### 2026-08-29 Day 9 Closeout

- Topics studied: prompt injection, tool poisoning, confused deputy, outbound allowlists, request-size limits, rate limiting, logging hygiene, and trust labeling for model-facing content
- Work implemented: Added `security.py` with outbound-domain checks, request-size middleware, rate limiting middleware, and log redaction helpers; tightened OpenAlex, prompt, resource, and note validation; added untrusted-content warnings to paper and reading-list resources and prompt templates; fixed HTTP startup to mount the ASGI app with custom middleware via `uvicorn`
- Tests executed: `pytest tests/unit/test_day9_security.py`; `pytest`; manual HTTP CLI checks against `http://127.0.0.1:8012/mcp` for `read-resource paper://W7129030749`, `get-prompt compare_papers`, repeated `discover` calls with a short rate-limit window, and prior Day 8 ownership and scope checks under auth
- Results: 8 dedicated Day 9 security tests passed and the full suite passed with 40 tests; paper resources now mark external metadata as untrusted, prompt templates add an explicit security note, oversize input is rejected, and non-OpenAlex outbound targets are blocked
- Results: Manual verification confirmed `paper://W7129030749` includes `content_trust=untrusted_external_data` and a `security_warning`; `compare_papers` preserved the hostile focus string as data while warning not to follow untrusted content as instructions; repeated authenticated requests hit the configured rate limit and were rejected at the HTTP layer
- Results: Learner can explain why host approval is not enough, how ownership and scope differ, why rate limiting is about abuse control rather than identity, and why paper metadata and notes must be treated as untrusted content
- Problems encountered: The first Day 9 HTTP startup attempt incorrectly passed custom middleware settings into `MCPServer.run(...)`, which raised `TypeError: MCPServer.run_streamable_http_async() got an unexpected keyword argument 'max_http_body_bytes'`; the server entry point was corrected to create the ASGI app and run it with `uvicorn`
- Decisions made: Keep Day 9 hardening lightweight and in-process for now instead of introducing Redis, a WAF, or an external API gateway before the roadmap requires them
- Topics to revisit: Replace in-memory rate limiting with a distributed limiter for multi-instance production deployment and improve CLI surfacing of raw HTTP 429 responses
- Next action: Begin Day 10 by making dependency failures, retries, and degradation paths predictable
