# MCP Learning Notes

## Table of Contents

- Module 1: MCP Foundations
- Module 2: Context and Persistence
- Module 3: MCP Client and Remote Transport
- Module 4: Authentication, Security, and Reliability
- Module 5: Testing, Evaluation, and Production

## Module 1: MCP Foundations

### Day 1: Protocol Fundamentals

#### Learning objectives

- Distinguish MCP from normal APIs, function calling, RAG, and agent frameworks.
- Understand the host-client-server architecture and who enforces security decisions.
- Understand JSON-RPC requests, responses, notifications, and errors.
- Understand why the current MCP specification (`2026-07-28`) is stateless at the protocol layer.
- Map ResearchOps features to MCP primitives: tools, resources, prompts, and Tasks.

#### Core concepts

- MCP is a protocol for exposing tools, resources, prompts, and optional extensions to an AI host in a consistent way.
- MCP does not replace ordinary APIs; it standardizes how an AI-facing client discovers and uses capabilities provided by a server.
- The host is the application that owns the user relationship and approval policy. The client speaks MCP to one or more servers on the host's behalf.
- MCP messages use JSON-RPC 2.0 semantics:
  - Requests expect a response and include an `id`.
  - Responses return either `result` or `error`.
  - Notifications do not include an `id` and do not receive a reply.
- In the current spec, protocol-level sessions and the old `initialize` handshake are removed for the new revision. Capability discovery is handled by `server/discover`, and request metadata carries protocol version and client identity.

#### How it works

1. A host decides which MCP servers are available to the model and under which approval rules.
2. The host-side client can call `server/discover` to learn supported protocol versions and advertised capabilities.
3. The client lists tools, resources, or prompts and decides what the model is allowed to invoke.
4. The model asks to use a capability.
5. The client sends a JSON-RPC request to the server.
6. The server validates input, enforces authorization, performs the operation, and returns structured results or an error.

In ResearchOps MCP, the external research API and local database live behind the MCP server. The model never talks to those dependencies directly.

Important distinction:

- Protocol statelessness does not mean the application cannot keep state.
- ResearchOps can still store reading lists, notes, and cached paper metadata in a database.
- Later MCP requests refer to that stored state using explicit identifiers such as `paper_id`, `list_id`, and `note_id`.
- The protocol stays stateless because requests do not rely on hidden transport session state.

#### Example

Simple example:

- A user asks, "Find recent papers about retrieval-augmented generation."
- The host decides the request may use the `search_papers` tool.
- The client calls the MCP server with a JSON-RPC `tools/call` request.
- The server queries the configured paper source, normalizes the results, and returns a small structured list.
- If the user later wants details for one result, the model can call `get_paper` or read `paper://{paper_id}` once that resource exists.

#### Why it is designed this way

- Separation of concerns: APIs remain business interfaces; MCP is the model-facing contract.
- Capability discovery lets hosts connect to different servers without custom glue for every server.
- Stateless requests make remote deployment simpler because any request can be handled by any compatible server instance.
- Explicit tool and schema design helps models choose safer, narrower operations.

Primitive boundary summary for ResearchOps:

- Tool: use when the server must perform an operation now using arguments, such as `search_papers`.
- Resource: use for stable, identifiable context that can be read repeatedly, such as `paper://{paper_id}`.
- Prompt: use for reusable reasoning scaffolding, such as `compare_papers`.
- Task: use for long-running or asynchronous work that should not be forced into one immediate request-response cycle.

#### Alternatives and trade-offs

- Plain API integration:
  - Simpler if only one application needs the integration.
  - Weaker interoperability across hosts and MCP-aware tools.
- Function calling only:
  - Good inside one model provider's ecosystem.
  - Less portable than MCP across hosts and clients.
- RAG-only approach:
  - Good for retrieval from static corpora.
  - Not enough for structured actions like creating reading lists or notes.
- Agent framework:
  - Useful for orchestration.
  - Not a substitute for the protocol boundary that MCP defines.

#### Common mistakes

- Treating MCP as if it were an agent framework instead of a protocol.
- Assuming the model choosing a tool means the action is authorized.
- Designing one giant tool with many unrelated modes.
- Returning unbounded tool output when a resource reference would be safer.
- Hiding application state in transport assumptions instead of explicit identifiers.

#### Security considerations

- Tool arguments and returned content are untrusted.
- The host and client must enforce approval policy; the server must enforce authorization.
- Remote MCP servers enlarge the trust boundary and need strict validation, logging hygiene, and outbound controls.
- Prompt injection can arrive through external content returned by tools or resources.
- Stateless transport does not remove application state risks; it just makes them explicit through handles and identifiers.

Approval versus authorization:

- Host approval decides whether a sensitive action should proceed from the user-consent side.
- Server authorization checks whether the caller is actually allowed to access or modify the targeted data.
- ResearchOps needs both, because host approval alone cannot prevent cross-user access or forged or replayed requests.

#### Interview explanation

MCP is a standard way for AI hosts to discover and use external capabilities such as tools, resources, and prompts. It sits between the model-facing client and ordinary backend systems. The current protocol uses JSON-RPC messages and, in the `2026-07-28` revision, removes protocol-level session state so requests can be handled independently while capability discovery is done through `server/discover`.

#### Questions for revision

1. Why is MCP not a replacement for ordinary APIs?
2. What is the difference between the host and the client in MCP?
3. Why did the newer spec move away from protocol-level sessions?
4. When should ResearchOps use a tool instead of a resource?


#### Active recall review

1. Question: What role does the client play, and why is a resource different from a tool?
   Answer: The client is the MCP-speaking component inside the host. It discovers capabilities, sends requests to one or more servers, receives results, and applies host policy around approval and use. A resource is stable, identifiable context that can be read repeatedly, while a tool is an action invoked with arguments to make the server perform work now.

2. Question: If a message has no `id`, what kind of JSON-RPC message is it, and why does that matter?
   Answer: It is a notification. Notifications do not expect a reply, and the receiver must not send a response.

3. Question: Why is `server/discover` useful before doing other MCP operations?
   Answer: It lets the client learn supported protocol versions, advertised capabilities, and server identity before making assumptions about what the server can do.

4. Question: Why is it useful to start with a local MCP server before building a remote one?
   Answer: A local server isolates MCP fundamentals from remote transport concerns. It lets us learn tools, schemas, and request flow before adding HTTP, authentication, TLS, deployment, and remote security concerns.

5. Question: Why does protocol-level statelessness not mean the application itself must be stateless?
   Answer: The protocol does not rely on hidden transport session state, but the application can still keep state in storage such as a database. Later requests refer to that state using explicit identifiers like `paper_id`, `list_id`, and `note_id`.

6. Question: Why would one giant `do_everything` tool be bad design for ResearchOps?
   Answer: It would mix unrelated operations into one ambiguous interface, making tool selection, schema validation, authorization, testing, and error handling harder.

7. Question: Why is `compare_papers` a prompt instead of a tool?
   Answer: It provides reusable reasoning scaffolding for comparing already-available paper context, rather than asking the server to perform a backend action.

8. Question: When should ResearchOps use a Task instead of a normal tool call?
   Answer: It should use a Task for long-running or asynchronous work that should not be forced into one immediate request-response cycle, such as large literature scans or bulk export jobs.

9. Question: Why do we treat paper titles, abstracts, and other external metadata as untrusted?
   Answer: External content can be malicious, malformed, or prompt-injecting. It can inform the model, but it must not be treated as trusted control input.

10. Question: Why is authorization still required on the server even if the host already has approval rules?
    Answer: Host approval is not enough. The server must independently enforce access control so callers cannot read or modify other users' data through misconfiguration, replay, or forged requests.

11. Question: What is the difference between host approval and server authorization?
    Answer: Host approval asks whether an action should proceed from the user-consent and policy side. Server authorization checks whether the caller is actually allowed to perform that action on the targeted data.
#### References

- MCP specification and discovery docs: https://modelcontextprotocol.io/specification/latest
- 2026-07-28 spec overview: https://blog.modelcontextprotocol.io/posts/2026-07-28/
- Official Python SDK docs: https://py.sdk.modelcontextprotocol.io/
- OpenAI MCP guide: https://developers.openai.com/api/docs/guides/tools-connectors-mcp
- OWASP MCP Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html

### Day 2: First Local MCP Server

### Day 3: Production-Quality Tool Design

## Module 2: Context and Persistence

### Day 4: Resources and Prompts

### Day 5: Storage and Write Operations

## Module 3: MCP Client and Remote Transport

### Day 6: Build an MCP Client

### Day 7: Streamable HTTP and Deployment

## Module 4: Authentication, Security, and Reliability

### Day 8: Authentication and Authorization

### Day 9: MCP Security

### Day 10: Reliability Engineering

## Module 5: Testing, Evaluation, and Production

### Day 11: Protocol and Application Testing

### Day 12: Model and Tool-Selection Evaluation

### Day 13: Observability and Scaling

### Day 14: Advanced Features and Final Release


