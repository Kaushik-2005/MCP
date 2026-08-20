# MCP Industry-Level Learning Roadmap

## Goal

Learn Model Context Protocol (MCP) by building a production-style project over 14 days.

**Recommended time:** 2–3 hours per day  
**Primary language:** Python  
**Suggested SDK:** Official MCP Python SDK / FastMCP  
**Current specification:** `2026-07-28`

> MCP is a protocol for connecting AI applications to external tools and context. It is not an agent framework and does not replace normal APIs. An MCP server usually wraps existing APIs, databases, files, or business services in a standard model-facing interface.

## Capstone Project: ResearchOps MCP

Build an MCP server that allows an AI assistant to:

- Search for research papers.
- Retrieve paper metadata and abstracts.
- Maintain reading lists.
- Add and update research notes.
- Compare papers using reusable prompts.
- Export citations in BibTeX format.
- Run longer literature-search jobs.

### Proposed MCP interface

| Primitive | Examples |
|---|---|
| Tools | `search_papers`, `get_paper`, `create_reading_list`, `add_note`, `export_bibtex` |
| Resources | `paper://{paper_id}`, `reading-list://{list_id}` |
| Prompts | `compare_papers`, `generate_literature_review` |
| Tasks | Long-running literature searches or citation exports |

### Technology stack

- Python and FastMCP
- Semantic Scholar, OpenAlex, or Crossref API
- SQLite for local development
- PostgreSQL for deployment
- Pydantic/JSON Schema validation
- Docker
- OAuth 2.1 for remote access
- OpenTelemetry for tracing
- Pytest for testing
- MCP Inspector for protocol testing

---

# Module 1: MCP Foundations — Days 1–3

## Day 1: Protocol fundamentals

### Learn

- MCP versus APIs, function calling, RAG, tools, and agent frameworks.
- Host–client–server architecture.
- JSON-RPC requests, responses, notifications, and errors.
- Protocol versions and compatibility.
- Capability discovery and negotiation.
- Stateless request handling in the current MCP specification.
- Local and remote MCP servers.

### Build

- Write the project requirements.
- Identify tools, resources, prompts, and long-running operations.
- Draw the end-to-end data flow.
- Define user roles and system trust boundaries.
- Write an initial threat model.

### Deliverable

Project specification, architecture diagram, and threat-model outline.

## Day 2: First local MCP server

### Learn

- Official Python SDK and FastMCP basics.
- Server name, version, metadata, and instructions.
- Tool registration.
- Input and output JSON schemas.
- Structured content versus text content.
- MCP errors versus application errors.
- Local `stdio` transport.

### Build

- Create the server entry point.
- Add `health_check`.
- Add `search_papers` using mock data.
- Add `get_paper` using mock data.
- Connect through MCP Inspector.

### Deliverable

A working local MCP server that can list and invoke tools.

## Day 3: Production-quality tool design

### Learn

- Focused, goal-oriented tool boundaries.
- Action-oriented tool names.
- Clear descriptions that help models select tools.
- Required and optional parameters.
- Enums, numerical limits, and `additionalProperties`.
- Structured output schemas.
- Read-only, destructive, idempotent, and open-world annotations.
- Stable identifiers, pagination, and result limits.
- Actionable error messages.

### Build

- Connect `search_papers` to a real research API such as OpenAlex.
- Add pagination and maximum result limits.
- Add timeouts and dependency error handling.
- Add `export_bibtex`.
- Improve search relevance with an exact-first or otherwise explicit search strategy.
- Test invalid queries, missing IDs, and empty results.

### Deliverable

A dependable read-only research-paper server with stable IDs, bounded results, and citation export.

---

# Module 2: Context and Persistence — Days 4–5

## Day 4: Resources and prompts

### Learn

- Tools versus resources.
- Resource URIs and resource templates.
- MIME types and embedded resources.
- Resource discovery and reading.
- Reusable prompt templates.
- Typed prompt arguments.
- Context-size management.
- Returning references instead of duplicating large content.

### Build

- Add `paper://{paper_id}`.
- Add `reading-list://{list_id}`.
- Add a `compare_papers` prompt.
- Add a `generate_literature_review` prompt.
- Limit large abstracts and result collections safely.

### Deliverable

The client can discover and read research context without treating every operation as a tool.

## Day 5: Storage and write operations

### Learn

- Service, repository, and transport layers.
- Database schema design.
- Transactions.
- Idempotency keys.
- Optimistic concurrency.
- User ownership and tenant isolation.
- Separating read and write tools.
- Confirmation for consequential operations.

### Build

- Create tables for users, papers, reading lists, notes, and audit events.
- Add `create_reading_list`.
- Add `add_paper_to_list`.
- Add `add_note` and `update_note`.
- Add `delete_note` with confirmation requirements.
- Protect writes against duplicate execution.

### Deliverable

A persistent MCP application rather than a thin API wrapper.

---

# Module 3: MCP Client and Remote Transport — Days 6–7

## Day 6: Build an MCP client

### Learn

- Server and capability discovery.
- Listing and invoking tools.
- Reading resources.
- Retrieving prompt templates.
- Handling protocol and tool errors.
- Client-side approval policies.
- Multiple-server isolation.
- Tool filtering and lazy loading.

### Build

- Create a small Python CLI client.
- Connect it to ResearchOps MCP.
- Show tool arguments before write operations.
- Add approval or denial controls.
- Record tool name, status, and latency.

### Deliverable

A client that demonstrates understanding of both sides of MCP.

## Day 7: Streamable HTTP and deployment

### Learn

- Streamable HTTP transport.
- Request headers and protocol lifecycle.
- Stateless servers.
- Cancellation and timeouts.
- TLS, reverse proxies, CORS, and origin validation.
- Containerization.
- SDK and specification-version pinning.
- Backward compatibility.

### Build

- Add Streamable HTTP support.
- Containerize the application.
- Deploy a staging instance.
- Test it remotely with MCP Inspector.
- Connect it to a supported AI host.

### Deliverable

A remotely accessible staging MCP server.

---

# Module 4: Authentication, Security, and Reliability — Days 8–10

## Day 8: Authentication and authorization

### Learn

- Authentication versus authorization.
- OAuth 2.1 roles and flows.
- PKCE.
- Protected resource metadata.
- Authorization-server discovery.
- Resource indicators and token audience validation.
- Short-lived access tokens and refresh tokens.
- Scopes and least privilege.
- Tenant authorization inside every handler.
- Credentials for local `stdio` versus remote HTTP servers.

### Build

- Protect the remote server.
- Introduce scopes such as:
  - `papers:read`
  - `lists:read`
  - `lists:write`
  - `notes:write`
- Validate resource ownership at the database layer.
- Return correct `401 Unauthorized` and `403 Forbidden` responses.

### Deliverable

An authenticated, multi-user remote server.

## Day 9: MCP security

### Learn

- Direct and indirect prompt injection.
- Tool poisoning.
- Malicious tool descriptions and returned content.
- Tool shadowing and cross-server attacks.
- Rug-pull metadata changes.
- Confused-deputy attacks.
- Data exfiltration through legitimate tool calls.
- SSRF, path traversal, and command injection.
- Over-scoped credentials.
- Secret leakage through logs or model context.
- Third-party MCP supply-chain risk.
- Human approval for sensitive operations.

### Build

- Allowlist outbound API domains.
- Validate all inputs and outputs.
- Add result-size and request-size limits.
- Redact secrets and sensitive fields from logs.
- Add rate limiting.
- Enforce authorization per tool.
- Create an audit record for every write.
- Add adversarial prompt-injection tests.

### Deliverable

A security checklist, threat model, and adversarial test suite.

## Day 10: Reliability engineering

### Learn

- Timeout budgets.
- Exponential backoff with jitter.
- Retrying only safe or idempotent operations.
- Circuit breakers.
- API rate-limit handling.
- Partial failures and graceful degradation.
- Caching and cache invalidation.
- Database connection pooling.
- Pagination and backpressure.
- Request cancellation.
- Duplicate write prevention.

### Build

- Cache paper metadata.
- Retry transient research-API failures.
- Add a circuit breaker.
- Enforce request deadlines.
- Simulate unavailable dependencies and rate limits.

### Deliverable

A server that behaves predictably during dependency failures.

---

# Module 5: Testing, Evaluation, and Production — Days 11–14

## Day 11: Protocol and application testing

### Learn

- Unit tests for tool handlers.
- Contract tests for schemas.
- Integration tests with real MCP messages.
- Golden-response tests.
- Authentication and authorization tests.
- Negative and fuzz testing.
- Metadata regression tests.
- Compatibility testing.
- External API mocking.

### Evaluation cases

- Direct requests that should call one specific tool.
- Indirect requests expressing the same intent.
- Requests that should not invoke a tool.
- Ambiguous requests.
- Multi-step workflows.
- Unauthorized actions.
- Prompt-injection attempts.
- External dependency failures.

### Deliverable

Automated tests and an MCP Inspector test report.

## Day 12: Model and tool-selection evaluation

### Learn

- Tool-call precision and recall.
- Argument correctness.
- Task-completion rate.
- Unauthorized-action rate.
- Hallucinated-tool rate.
- Result-grounding accuracy.
- P50 and P95 latency.
- Token and infrastructure cost per completed task.

### Build

- Create a 40–50 prompt evaluation dataset.
- Record expected tool, actual tool, arguments, result, and latency.
- Compare alternative tool names and descriptions.
- Define minimum quality thresholds.
- Add regression evaluation to CI.

### Deliverable

A measurable evaluation report.

## Day 13: Observability and scaling

### Learn

- Structured logging.
- Request and correlation IDs.
- Metrics per tool.
- Success and failure rates.
- P50, P95, and P99 latency.
- Dependency latency.
- Authentication and rate-limit metrics.
- Distributed tracing.
- PII-safe telemetry.
- Health and readiness checks.
- Horizontal scaling.
- Graceful shutdown.
- Database migrations.
- Deployment rollback.
- SLOs and alerting.

### Build

- Add OpenTelemetry tracing.
- Add service and per-tool metrics.
- Add health and readiness endpoints.
- Create a latency and error dashboard.
- Add CI for linting, tests, evaluation, and image building.

### Deliverable

An observable and deployable production candidate.

## Day 14: Advanced features and final release

### Learn

- Elicitation for requesting missing user information.
- Long-running Tasks.
- MCP Apps and UI resources.
- Extensions and capability discovery.
- Tool-list caching.
- Multi-server orchestration and isolation.
- Enterprise policy enforcement.
- Private networking and secure tunnels.
- Server registries and distribution.
- Protocol deprecation and compatibility strategy.

### Finish

- Deploy the production version.
- Run all tests and evaluations.
- Perform a final security review.
- Record a 3–5 minute demonstration.
- Publish setup instructions and architecture.
- Publish evaluation results and known limitations.

### Deliverable

A portfolio-ready, industry-style MCP project.

---

# Recommended Repository Structure

```text
researchops-mcp/
├── src/
│   ├── server.py
│   ├── tools/
│   ├── resources/
│   ├── prompts/
│   ├── services/
│   ├── repositories/
│   ├── auth/
│   ├── security/
│   └── observability/
├── client/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── security/
│   └── evals/
├── migrations/
├── Dockerfile
├── pyproject.toml
├── threat-model.md
├── evaluation-report.md
└── README.md
```

# Final Knowledge Checklist

By the end of the two weeks, you should understand:

- MCP architecture and JSON-RPC.
- Protocol versions and feature discovery.
- Tools, resources, prompts, and Tasks.
- Input and output JSON Schema design.
- Local `stdio` and remote Streamable HTTP.
- MCP server and client development.
- OAuth, scopes, identity, and tenant isolation.
- Human approval and safe write operations.
- Prompt injection and MCP-specific attacks.
- Validation, sandboxing, and secret management.
- Timeouts, retries, caching, and idempotency.
- Testing with MCP Inspector.
- Tool-selection and task-completion evaluations.
- Logging, metrics, and distributed tracing.
- Docker, CI/CD, scaling, migrations, and rollback.
- Elicitation, MCP Apps, extensions, and private networking.

# What Not to Spend Too Much Time On

- Collecting dozens of third-party MCP servers.
- Copying tutorial servers without understanding the protocol.
- Adding many overlapping tools.
- Building UI before tool behavior is reliable.
- Connecting sensitive accounts before authorization is implemented.
- Treating a successful tool call as sufficient production testing.

One well-designed, secured, evaluated, and deployed MCP server is more valuable than several toy integrations.

# Primary References

- [Current MCP Specification](https://modelcontextprotocol.io/specification/latest)
- [MCP 2026-07-28 Release Overview](https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/)
- [OpenAI MCP and Connectors Guide](https://developers.openai.com/api/docs/guides/tools-connectors-mcp)
- [Building an MCP Server](https://developers.openai.com/plugins/build/mcp-server)
- [Official MCP Inspector](https://github.com/modelcontextprotocol/inspector)
- [OWASP MCP Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html)


