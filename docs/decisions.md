# Architectural Decisions

## Decision: Start With Specification-First Day 1 Artifacts

- Date: 2026-08-18
- Status: Accepted
- Context: The repository started with only the roadmap and project instructions. Day 1 requires project requirements, architecture, trust boundaries, and an initial threat model before code.
- Options considered:
  - Start writing server code immediately.
  - Create the specification and security baseline first.
- Decision: Create the project specification, architecture diagram, and initial threat model before implementing the Day 2 server.
- Why: This matches the roadmap order, clarifies MCP primitive boundaries early, and prevents accidental architecture drift.
- Trade-offs: Slower visible coding progress on the first session, but better design clarity.
- Consequences: Day 2 implementation can be reviewed against explicit requirements instead of assumptions.

## Decision: Follow the Roadmap Stack Unless Evidence Forces a Change

- Date: 2026-08-18
- Status: Accepted
- Context: The roadmap already suggests Python, FastMCP, a research-paper API, SQLite for local work, PostgreSQL for deployment, and Docker.
- Options considered:
  - Use the roadmap stack as the default.
  - Re-evaluate every technology up front.
- Decision: Use Python and the official MCP Python SDK/FastMCP as the default implementation path unless a later milestone reveals a concrete reason to change.
- Why: It keeps the learning path aligned with the curriculum and reduces unnecessary early architecture churn.
- Trade-offs: Less initial experimentation across alternative stacks.
- Consequences: Future dependency additions still need explicit justification, but the baseline direction is now clear.

## Decision: Implement Day 2 With Current SDK v2 Naming

- Date: 2026-08-19
- Status: Accepted
- Context: The roadmap uses the term FastMCP, but the current official Python SDK v2 renamed the high-level server class to `MCPServer`.
- Options considered:
  - Follow older FastMCP examples literally.
  - Use the current official SDK v2 API and document the rename.
- Decision: Implement the local server with `MCPServer` and note in the learning materials that this is the current v2 replacement for `FastMCP`.
- Why: It keeps the project aligned with the current official SDK instead of teaching an outdated import path.
- Trade-offs: Some roadmap wording and older tutorials use different names, which adds a small translation cost.
- Consequences: Future code examples in this repository should prefer `MCPServer` unless we explicitly study v1 migration behavior.

## Decision: Use OpenAlex as the Day 3 Read-Only Paper Source

- Date: 2026-08-20
- Status: Accepted
- Context: Day 3 requires a real read-only research API for `search_papers`, `get_paper`, pagination, limits, and actionable dependency error handling.
- Options considered:
  - OpenAlex
  - CORE API
  - Semantic Scholar
- Decision: Use OpenAlex for the Day 3 integration.
- Why: OpenAlex is a strong fit for read-only paper metadata search with straightforward HTTP access and enough metadata to support `search_papers`, `get_paper`, and `export_bibtex` without adding early authentication or full-text workflow complexity.
- Trade-offs: OpenAlex is less focused on open-access full-text retrieval than CORE, so later full-text-oriented features may need an additional source.
- Consequences: Day 3 implementation can focus on production-quality tool design and metadata normalization without introducing early API-key and quota workflow complexity.

## Decision: Expose Reading-List Resources Before Persistence Exists

- Date: 2026-08-21
- Status: Accepted
- Context: Day 4 requires `reading-list://{list_id}` resources and reusable prompt workflows, but durable storage is intentionally scheduled for Day 5.
- Options considered:
  - Delay reading-list resources until the database layer exists.
  - Expose the reading-list resource interface now with a temporary in-memory backing layer.
- Decision: Expose `reading-list://{list_id}` on Day 4 using a small in-memory service and defer persistence to Day 5.
- Why: It preserves the roadmap's separation between MCP interface design and persistence design, allowing us to learn the correct resource boundary before adding database complexity.
- Trade-offs: The Day 4 reading-list data is not durable and is intentionally limited.
- Consequences: Day 5 can replace the backing implementation without changing the externally learned MCP resource shape.

## Decision: Use SQLite and a Repository Layer for Day 5 Local Persistence

- Date: 2026-08-21
- Status: Accepted
- Context: Day 5 requires durable reading lists, notes, transactions, and write-safety boundaries on top of the Day 4 resource and prompt layer.
- Options considered:
  - Keep using in-memory storage longer.
  - Add SQLite with a small repository and service layer.
  - Jump directly to PostgreSQL.
- Decision: Use SQLite from the Python standard library for local persistence, with a repository layer for database operations and a service layer for business rules.
- Why: It matches the roadmap's local-development phase, keeps dependencies minimal, and lets us learn transactions, idempotency, and optimistic concurrency without early deployment complexity.
- Trade-offs: SQLite is not the final deployment database and still assumes a single-user local environment for now.
- Consequences: Later phases can replace or extend the storage backend while preserving the MCP interface and most service-layer behavior.

## Decision: Start The Day 6 Client As A Local Stdio CLI

- Date: 2026-08-25
- Status: Accepted
- Context: Day 6 requires building a client that can discover capabilities, read resources, invoke tools, and gate writes before moving to remote transport on Day 7.
- Options considered:
  - Start directly with remote HTTP client behavior
  - Use only one-off inline scripts for client verification
  - Build a reusable local stdio CLI client first
- Decision: Build a reusable Python CLI client over local stdio first, package the implementation under `src/researchops_mcp/client_cli.py`, and keep `client/cli.py` as a thin entry point.
- Why: This isolates MCP client behavior from remote transport complexity, creates a reusable learning tool, and keeps the Day 6 implementation aligned with the current local server setup.
- Trade-offs: The client uses a temporary explicit local write-tool policy and does not yet exercise remote transport concerns.
- Consequences: Day 7 can build on a working client mental model instead of combining client learning with HTTP deployment changes in one step.

## Decision: Keep One Shared MCP Surface Across Stdio And HTTP

- Date: 2026-08-25
- Status: Accepted
- Context: Day 7 requires adding Streamable HTTP transport without breaking the local development workflow or forcing needless interface churn.
- Options considered:
  - Maintain separate stdio and HTTP registration paths
  - Replace stdio with HTTP entirely
  - Keep one shared server factory and switch transports only at startup
- Decision: Keep one shared `create_server()` capability factory and make startup transport-aware instead of transport-specific at the interface-registration layer.
- Why: This preserves the MCP surface across transport changes, reduces drift risk, and keeps local stdio development intact.
- Trade-offs: The startup code becomes slightly more configurable, and client transport behavior must explicitly account for stdio versus HTTP lifecycle differences.
- Consequences: ResearchOps can evolve transport and deployment shape without redesigning tools, resources, and prompts every time the serving path changes.

## Decision: Use Free Render Staging With Temporary SQLite Storage For Day 7

- Date: 2026-08-25
- Status: Accepted
- Context: Day 7 required a real remotely reachable Streamable HTTP MCP server, but the project is still in the learning and staging phase with a zero-cost hosting goal.
- Options considered:
  - Stop at local HTTP verification only
  - Deploy to a free hosted Docker web service with temporary storage
  - Introduce a paid persistent database and hosting stack immediately
- Decision: Deploy the Streamable HTTP server to Render free hosting with Docker and use `DATABASE_PATH=/tmp/researchops.db` as explicit staging-only storage.
- Why: This satisfies the Day 7 remote deployment learning goal with minimal operational cost while keeping the transport, container, and remote verification work real.
- Trade-offs: Free Render can cold-start and the SQLite file under `/tmp` is ephemeral, so durable remote user state is not guaranteed.
- Consequences: Day 7 can be completed with real public MCP verification, but later phases must replace temporary storage and add stronger production controls.

## Decision: Use SDK-Based Bearer Auth With Demo Tokens Before Full OAuth Integration

- Date: 2026-08-27
- Status: Accepted
- Context: Day 8 required the remote MCP server to enforce authentication, scopes, and per-user authorization, but a full external OAuth deployment would add significant setup and distract from the protocol-learning goal.
- Options considered:
  - Delay auth entirely until a later day
  - Add a custom API-key or ad hoc bearer-header scheme
  - Use the MCP Python SDK auth surface with a small demo token verifier and explicit scopes
- Decision: Use the official MCP Python SDK auth hooks and middleware for remote HTTP protection, with a local demo token verifier that models user identity, scopes, issuer information, and resource-server binding.
- Why: This teaches the correct MCP authorization shape, keeps the server aligned with the spec and SDK, and lets us verify `401`, `403`, scope checks, and tenant ownership without needing a full live authorization server yet.
- Trade-offs: The demo verifier is not a production identity system and does not replace a real OAuth authorization code flow, token refresh flow, or external issuer integration.
- Consequences: The project now has the right transport and handler boundaries for auth, and a later production phase can swap the verifier for a real issuer-backed implementation without redesigning the MCP capability surface.

## Decision: Add Lightweight In-Process Security Controls Before External Gateways

- Date: 2026-08-29
- Status: Accepted
- Context: Day 9 required practical MCP security hardening for the existing authenticated ResearchOps server, but introducing infrastructure such as Redis-backed rate limiting, an API gateway, or a WAF would add deployment and operational complexity ahead of the roadmap.
- Options considered:
  - Delay most security controls until a later production-infrastructure phase
  - Add only proxy-level protections outside the application
  - Implement lightweight in-process controls now and leave distributed controls for later
- Decision: Add request-size limits, fixed-window in-memory rate limiting, outbound-domain allowlisting, trust warnings, and redaction helpers directly in the Python application for Day 9.
- Why: This places the most important security boundaries where the roadmap can teach them clearly, keeps the implementation observable and testable, and improves the current local and staging server immediately without requiring new infrastructure.
- Trade-offs: The current limiter is single-process only, the allowlist is intentionally simple, and some protections will need to move or be duplicated at proxy or platform level in a later production deployment.
- Consequences: The Day 9 server now has meaningful abuse resistance and safer model-facing context handling, while Day 13 or later can upgrade these controls to shared infrastructure without redesigning the MCP surface.
