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
