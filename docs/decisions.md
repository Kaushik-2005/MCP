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
