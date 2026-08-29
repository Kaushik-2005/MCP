# ResearchOps MCP Threat Model

## Scope

This started as the Day 1 threat-model outline for the ResearchOps MCP project.
It has now been extended through Day 9 to reflect authenticated remote access, scoped authorization, trust labeling, outbound restrictions, request-size enforcement, and rate limiting.

## Assets

- User identity and authorization context
- Reading lists and research notes
- API credentials for external research providers
- Server configuration and secrets
- Audit records
- Availability of the MCP service
- Prompt and resource content presented to the model

## Entry Points

- Local `stdio` requests
- Remote Streamable HTTP requests
- Tool arguments
- Resource reads
- Prompt arguments
- External research API responses
- Deployment logs and audit output

## Trust Boundaries

- Between the host and the MCP client
- Between the MCP client and the MCP server
- Between the MCP server and external APIs
- Between the MCP server and persistent storage
- Between operators and deployed infrastructure
- Between model-facing context and model control instructions

## Threats

### Prompt injection and tool poisoning

- Malicious paper titles, abstracts, or notes may try to manipulate the model.
- Tool descriptions, prompt arguments, or returned content may be over-trusted by the host or model.
- Hostile focus text may try to override the reusable prompt template.

### Unauthorized access

- A caller may attempt to read another user's lists or notes.
- A caller may attempt writes without approval or correct scope.
- A caller may present a valid token for the wrong resource server.
- A caller may have a broad read scope but still target another tenant's private data.

### Input abuse

- Oversized queries, notes, or prompt arguments may try to exhaust memory, storage, or context.
- Unexpected fields or malformed identifiers may probe validation weaknesses.
- Large HTTP request bodies may try to pressure parsing or request handling.

### External dependency abuse

- SSRF-like behavior can occur if later tools accept arbitrary URLs.
- Research APIs may return hostile or malformed data.
- Upstream dependencies may be used as an amplifier if request volume is not controlled.

### Secrets and data leakage

- Logs may accidentally capture credentials, idempotency keys, or private notes.
- Returned content may expose more data than necessary.
- Prompt templates could accidentally surface untrusted content without warning.

### Availability risks

- Upstream timeouts and rate limits may stall requests.
- Expensive or repeated searches may create backpressure or denial-of-service conditions.
- One authenticated caller may monopolize the service without additional abuse controls.

## Initial Mitigations

- Use explicit schemas with constrained inputs
- Enforce authorization in server handlers and persistence layer
- Bound request and response sizes
- Add outbound allowlists for external domains
- Redact secrets and sensitive fields in logs
- Add timeouts and safe retry rules
- Audit every consequential write

## Day 8 Auth State

- Remote HTTP access now requires bearer-token authentication when auth is enabled.
- The current learning implementation uses deterministic demo tokens for Alice and Bob instead of a full external OAuth provider.
- Scopes currently enforced:
  - `papers:read`
  - `lists:read`
  - `lists:write`
  - `notes:write`
- Ownership is enforced at the repository query level so a caller cannot read or mutate another user's lists or notes just by having a coarse scope.
- Verified Day 8 behaviors:
  - missing or invalid bearer token returns `401 Unauthorized`
  - insufficient scope returns `403 Forbidden`
  - cross-user reading-list access is denied

## Day 9 Security State

### Controls Added

- outbound allowlist enforcement for the OpenAlex client
- request-size middleware for Streamable HTTP requests
- fixed-window in-memory rate limiting by caller token or client address
- stricter length bounds for search queries, prompt focus and objective, list metadata, and note content
- `content_trust` and `security_warning` fields on model-facing resources
- security note injection in prompt templates
- recursive redaction for sensitive log fields

### Verified Behaviors On August 29, 2026

- `paper://W7129030749` returns truncated paper context plus `content_trust=untrusted_external_data`
- paper resources and prompt templates include explicit warnings that external metadata and user notes are untrusted
- hostile focus text passed into `compare_papers` is preserved as data but framed with a security warning
- repeated authenticated requests can be rejected by the configured HTTP rate limit
- oversized request bodies are rejected by middleware in automated tests
- non-allowlisted outbound targets are rejected in automated tests

## Remaining Day 10+ Security Gaps

- The demo token verifier is not a production identity system.
- The current rate limiter is not shared across multiple service instances.
- The CLI still collapses some raw HTTP auth or rate-limit failures into generic transport errors.
- No external API gateway, WAF, or distributed abuse-control layer is in place yet.
- The outbound allowlist currently protects the OpenAlex client only; future networked tools will need the same discipline.

## Open Questions

- How much user identity will be trusted from the host versus verified directly?
- Which operations need human approval in the client versus strict denial in the server?
- When the project becomes multi-instance, which shared store should back rate limiting and broader abuse controls?
