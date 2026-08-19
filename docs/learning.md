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

#### Role in our project

- MCP gives ResearchOps a model-facing layer for paper search, reading-list operations, and later prompts/resources.
- Day 1 decides where boundaries belong before code is written.
- The project uses explicit identifiers and bounded tool outputs because stateless MCP works best when state is represented clearly instead of hidden in a session.

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

#### Failure modes

- A client assumes an older session-style MCP flow and fails against a newer stateless server.
- The server exposes tools without narrow descriptions or schemas, causing poor model tool selection.
- Application state is hidden instead of being represented by explicit IDs, making later requests fragile.
- Tool outputs are too large, which wastes context or causes downstream confusion.

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
   Answer: MCP is the model-facing protocol layer, while ordinary APIs remain the business or data interfaces underneath. MCP standardizes discovery and use of capabilities for AI hosts; it does not replace backend APIs.

2. What is the difference between the host and the client?
   Answer: The host owns user interaction, approval, and policy. The client is the MCP-speaking component inside the host that discovers capabilities, sends requests, and receives results from one or more servers.

3. Why did the newer spec move away from protocol-level sessions?
   Answer: Stateless requests simplify remote deployment, horizontal scaling, and compatibility because each request can be handled independently without hidden transport session state.

4. When should ResearchOps use a tool instead of a resource?
   Answer: Use a tool when the server needs to perform an operation now using arguments. Use a resource when the system should expose stable, identifiable context that can be read repeatedly.

5. Why does stateless MCP still allow reading lists and notes?
   Answer: Because the state lives in application storage, such as the database, and later requests refer to that state through explicit identifiers like `list_id` or `note_id`.

6. Why is host approval not enough on its own?
   Answer: Host approval only decides whether an action should be allowed from the user-experience side. The server must still enforce authorization so callers cannot access or modify data they do not own.

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

#### Learning objectives

- Understand the current official MCP Python SDK server API for local development.
- Understand server name, version, metadata, and instructions.
- Understand tool registration with inferred schemas from Python type hints.
- Understand why stdio requires strict separation between protocol output and logs.
- Distinguish MCP/protocol errors from tool-level execution errors.

#### Core concepts

- The current official Python SDK v2 uses `MCPServer`, which replaces the older `FastMCP` name used in earlier examples.
- `@server.tool()` registers a Python function as a tool and derives its input schema from type hints and its description from the docstring.
- Local MCP development typically uses stdio transport, where the client spawns the server as a subprocess and exchanges protocol messages over `stdin` and `stdout`.
- Structured tool results can be returned directly from Python dictionaries when the SDK can infer the schema.
- Tool failures are surfaced to the client as tool results marked with `is_error=True`, rather than always raising protocol-level exceptions.

#### How it works

1. Create an `MCPServer` with a stable name, version, and instructions.
2. Register tools with `@server.tool()`.
3. Run the server locally over stdio.
4. A client connects, lists tools, reads the generated schemas, and calls tools with validated arguments.
5. The SDK returns structured content for successful tool calls and error results for tool-level failures.

#### Example

- `health_check` returns a simple readiness payload.
- `search_papers` searches mock paper data by query and returns bounded results.
- `get_paper` returns one paper by stable identifier or an error if the identifier is unknown.
- MCP Inspector can connect to the local stdio server, list the registered tools, and invoke them interactively.

#### Role in our project

- Day 2 turns the Day 1 design into a real local MCP server.
- The mock tools prove that ResearchOps can expose model-facing capabilities before any real external paper API is integrated.
- The local server becomes the baseline that later days will harden with stronger schemas, real dependencies, resources, prompts, persistence, and auth.

#### Why it is designed this way

- Using mock data isolates protocol learning from external API debugging.
- Type-hint-driven schema generation reduces hand-written JSON Schema work while keeping contracts explicit.
- Stdio transport makes local development fast because there is no separate HTTP deployment surface yet.
- Clear tool names and small schemas make model tool selection easier and safer.

#### Alternatives and trade-offs

- Older `FastMCP` examples:
  - Still useful for understanding older tutorials.
  - Do not match the current official SDK v2 naming.
- Real API integration on Day 2:
  - More realistic.
  - Adds network, rate-limit, and dependency failures too early.
- Direct low-level MCP implementation:
  - Good for protocol depth.
  - Slower for learning server basics than the high-level SDK.

#### Failure modes

- Using `@server.tool` instead of `@server.tool()` prevents correct tool registration.
- Printing logs to `stdout` corrupts the stdio protocol stream.
- Overly loose tool arguments allow empty queries or unreasonable limits.
- A healthy stdio server is misdiagnosed as broken because it is silent when no client is connected.
- Installing SDK dependencies into a shared global environment creates package conflicts that would not happen in an isolated virtual environment.

#### Common mistakes

- Using `@server.tool` instead of `@server.tool()`.
- Printing logs to `stdout` and corrupting the stdio protocol stream.
- Mixing protocol-level errors with normal application failures.
- Making Day 2 tools too broad before the tool boundaries are validated.
- Assuming a silent `python src/server.py` means the server failed to start.

#### Security considerations

- Even mock tools should validate inputs and bound result size.
- Tool descriptions and outputs are still part of the model-facing surface and should stay explicit and narrow.
- Local stdio is easier to reason about than remote HTTP, but it does not remove the need for good validation and safe error messages.
- Mock data can hide real-world dependency failures, so the absence of network risk in Day 2 does not mean later production risks disappear.

#### Interview explanation

A first local MCP server is usually a small stdio-based process that declares its metadata and registers tools with the official SDK. In the current Python SDK v2, `MCPServer` replaces the older `FastMCP` name, and tool schemas are inferred from type hints and docstrings. This lets a client list and call tools locally before introducing remote transport and authentication complexity.

#### Questions for revision

1. Why is mock data the right choice for the first local MCP server?
   Answer: Mock data isolates protocol learning from external API failures, rate limits, and network debugging, so Day 2 can focus on MCP server behavior, schemas, and local transport.

2. Why must logs go to `stderr` instead of `stdout` for stdio transport?
   Answer: In local stdio transport, `stdout` carries the MCP protocol stream. Normal logs there can corrupt messages, so logs should go to `stderr` instead.

3. What does `@server.tool()` do for a Python function?
   Answer: It registers the function as an MCP tool and lets the SDK derive the tool name, description, and input schema from the function name, docstring, and type hints.

4. Why can a tool failure come back as `is_error=True` instead of a raised protocol exception?
   Answer: Because the MCP request itself can be valid even when the tool operation fails. A missing paper is an application-level failure, so the client gets a tool result marked `is_error=True` rather than a protocol error.

5. Why was a silent `python src/server.py` not automatically a bug?
   Answer: Because a stdio MCP server is expected to start and wait quietly for a client. It is not a normal interactive CLI and should not print to `stdout` unless it is sending protocol messages.

6. What did MCP Inspector prove beyond the plain unit test and inline client script?
   Answer: It proved that an external MCP client could launch the server over stdio, discover the tools, and invoke them interactively, which is closer to how a real MCP host behaves.

7. Why should future installs use a virtual environment instead of the shared global Python?
   Answer: The Day 2 install introduced a `fastapi` / `starlette` conflict risk in the global environment. A project-specific virtual environment avoids polluting unrelated tools and makes dependency behavior reproducible.

#### Active recall review

1. Question: Why can a silent `python src/server.py` still indicate a healthy local MCP server?
   Answer: A stdio MCP server normally starts and waits quietly for a client. It is not an interactive CLI, and it should avoid printing normal logs to `stdout` because `stdout` carries the MCP protocol stream.

2. Question: What did MCP Inspector prove for the Day 2 server?
   Answer: It proved that the local stdio server could be launched by an external MCP client, that its tools were discoverable, and that `health_check`, `search_papers`, and `get_paper` could be invoked with expected success and failure behavior.

3. Question: Why is a tool-level failure like "paper not found" better represented as a tool error than as a protocol-level failure?
   Answer: Because the request itself is valid and the protocol is functioning correctly. The failure is in the application logic for that specific tool call, so it should come back as a tool error rather than implying the MCP protocol exchange itself was malformed.

#### References

- MCP Python SDK docs index: https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/index.md
- MCP SDK v2 changes: https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/whats-new.md
- First steps with `MCPServer`: https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/get-started/first-steps.md
- Tools in the Python SDK: https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/servers/tools.md
- Transport reference: https://modelcontextprotocol.io/specification/2025-06-18/basic/transports

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
