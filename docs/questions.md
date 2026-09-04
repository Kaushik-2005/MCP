# Questions and Revision

## Question

- Date: 2026-08-18
- Related day: Day 1
- Question: Where should the boundary sit between a tool result and a resource in ResearchOps MCP?
- Current understanding: Tools should handle actions and bounded retrieval, while resources should expose stable, identifiable context that may be read repeatedly.
- Correct explanation: Tools should perform actions or bounded on-demand retrieval, while resources should expose stable, identifiable context that can be read repeatedly by URI. In ResearchOps, `search_papers` and `get_paper` are tools because they perform retrieval actions with arguments, while `paper://{paper_id}` and `reading-list://{list_id}` are resources because they represent reusable, addressable context.
- Revisit on: Day 8
- Status: Understood

## Question

- Date: 2026-08-27
- Related day: Day 8
- Question: Why can Bob have `lists:read` and still be blocked from reading Alice's private list?
- Current understanding: Scope is not enough by itself; ownership still matters.
- Correct explanation: `lists:read` is a coarse permission that allows list-reading operations in general, but authorization must still verify that the specific `list_id` belongs to the authenticated user or tenant. Bob is authenticated and has a read scope, but he is not authorized for Alice's list because ownership fails.
- Revisit on: Day 10
- Status: Understood

## Question

- Date: 2026-08-29
- Related day: Day 9
- Question: Why is rate limiting a security control even when a caller is already authenticated?
- Current understanding: It helps with load balancing when handling multiple users and multiple requests.
- Correct explanation: Authentication answers who the caller is. Rate limiting controls how much and how often that caller can use the server. It helps prevent abuse, brute-force probing, upstream exhaustion, and denial-of-service pressure, even when the caller has a valid token.
- Revisit on: Day 11
- Status: Understood

## Question

- Date: 2026-08-29
- Related day: Day 9
- Question: Why do we preserve hostile prompt text in `compare_papers` instead of stripping it out entirely?
- Current understanding: It can be used to manipulate the model, so it is treated as untrusted.
- Correct explanation: The text is still relevant input data and may explain the caller's requested comparison focus. ResearchOps preserves it as data but wraps the prompt with an explicit security warning so the model treats it as untrusted evidence rather than instructions to obey.
- Revisit on: Day 11
- Status: Understood

## Question

- Date: 2026-09-01
- Related day: Day 10
- Question: Why is cached fallback appropriate for `get_paper` but not automatically for `search_papers`?
- Current understanding: `get_paper` results are deterministic as it uses a stable id and `search_papers` results are not deterministic.
- Correct explanation: `get_paper` is tied to one stable identifier, so stale fallback still refers to the same paper and can be marked clearly. `search_papers` depends on query text, ranking, pagination, and upstream freshness, so automatic stale fallback is more misleading unless explicit search-cache semantics are designed.
- Revisit on: Day 12
- Status: Understood

## Question

- Date: 2026-09-01
- Related day: Day 10
- Question: Why should the circuit breaker open after repeated failures instead of letting every request keep retrying forever?
- Current understanding: It stops sending more traffic to an already failing service for some duration.
- Correct explanation: The circuit breaker remembers repeated dependency failure across requests and fails fast for a reset window. That protects latency, upstream quota, and server resources instead of letting each new request repeat the same expensive failure cycle.
- Revisit on: Day 12
- Status: Understood


## Question

- Date: 2026-09-02
- Related day: Day 11
- Question: Why is a breaking `tools/list` schema change primarily a contract regression problem rather than only a negative-test problem?
- Current understanding: MCP tool schemas and descriptions directly affect model behavior.
- Correct explanation: In MCP, tool schemas, descriptions, and discovery metadata are part of the interface contract. A breaking schema change can disrupt client behavior and model tool selection even if the underlying business logic still works, so it should be caught by contract regression tests rather than only by generic negative-path tests.
- Revisit on: Day 13
- Status: Understood

## Question

- Date: 2026-09-04
- Related day: Day 12
- Question: Why does a vague `tools/list` description weaken MCP behavior even when the backend tools still work?
- Current understanding: Because the model uses tool names and descriptions to decide which capability to call.
- Correct explanation: In MCP, discovery metadata is operational interface data. If descriptions become vague, the model has weaker evidence for distinguishing tools, prompts, and resources, so selection quality and argument extraction degrade even though the backend implementation is unchanged.
- Revisit on: Day 14
- Status: Understood
