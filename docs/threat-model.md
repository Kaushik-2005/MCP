# ResearchOps MCP Threat Model

## Scope

This started as the Day 1 threat-model outline for the ResearchOps MCP project.
It has now been extended through Day 8 to reflect authenticated remote access, scoped authorization, and tenant ownership enforcement.

## Assets

- User identity and authorization context
- Reading lists and research notes
- API credentials for external research providers
- Server configuration and secrets
- Audit records
- Availability of the MCP service

## Entry Points

- Local `stdio` requests
- Remote Streamable HTTP requests
- Tool arguments
- Resource reads
- Prompt arguments
- External research API responses

## Trust Boundaries

- Between the host and the MCP client
- Between the MCP client and the MCP server
- Between the MCP server and external APIs
- Between the MCP server and persistent storage
- Between operators and deployed infrastructure

## Threats

### Prompt injection and tool poisoning

- Malicious paper titles, abstracts, or notes may try to manipulate the model.
- Tool descriptions or returned content may be over-trusted by the host or model.

### Unauthorized access

- A caller may attempt to read another user's lists or notes.
- A caller may attempt writes without approval or correct scope.
- A caller may present a valid token for the wrong resource server.
- A caller may have a broad read scope but still target another tenant's private data.

### Input abuse

- Oversized queries may try to exhaust memory or context.
- Unexpected fields or malformed identifiers may probe validation weaknesses.

### External dependency abuse

- SSRF-like behavior can occur if later tools accept arbitrary URLs.
- Research APIs may return hostile or malformed data.

### Secrets and data leakage

- Logs may accidentally capture credentials or private notes.
- Returned content may expose more data than necessary.

### Availability risks

- Upstream timeouts and rate limits may stall requests.
- Expensive searches may create backpressure or denial-of-service conditions.

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

## Remaining Day 9+ Security Gaps

- The demo token verifier is not a production identity system.
- The CLI still collapses some raw HTTP auth failures into a generic transport error.
- Outbound allowlists, request-size limits, log redaction, and adversarial prompt-injection tests are not implemented yet.

## Open Questions

- How much user identity will be trusted from the host versus verified directly?
- Which paper API best balances metadata quality, quotas, and licensing?
- Which operations need human approval in the client versus strict denial in the server?
