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

#### Learning objectives

- Design tools that map cleanly to user goals instead of mixing unrelated modes.
- Use action-oriented tool names and descriptions that help models choose correctly.
- Define required parameters, optional parameters, limits, and pagination explicitly.
- Return structured output with stable identifiers and predictable fields.
- Distinguish validation failures, empty results, not-found cases, and dependency failures.

#### Core concepts

- Good MCP tools should be narrow and recognizable from their name alone.
- Tool descriptions should explain both what the tool does and when it should be used.
- Explicit parameter limits make model behavior safer and easier to validate.
- Stable identifiers matter because later tool calls and resources depend on them.
- Empty results are not the same thing as an error: a valid query can legitimately return no matches.
- A production search tool may need multiple search strategies, such as exact-first or title-focused behavior, to improve relevance without changing the user-facing tool boundary.

#### How it works

1. Validate user-facing inputs before calling the dependency.
2. Call the external paper source through a small service/client layer instead of mixing HTTP directly into the tool handler.
3. Normalize the upstream response into a stable project-level shape.
4. Return bounded, structured results with pagination metadata.
5. Convert missing-data or dependency failures into actionable tool-level errors.

#### Example

- `search_papers(query="model context protocol", limit=2, page=1)` returns a bounded list plus `has_more` and `next_page`.
- `search_papers(..., search_mode="balanced")` prefers exact matches first and falls back to broader search only when needed.
- `get_paper(paper_id="W7129030749")` returns one normalized paper.
- `export_bibtex(paper_id="W7129030749")` returns a BibTeX entry for a stable paper identifier.
- `search_papers(query="zzzxxyyqqqnonexistentpaperterm", limit=1, page=1)` returns zero results without being treated as an error.

#### Role in our project

- Day 3 upgrades the Day 2 mock server into a real read-only research paper server.
- The OpenAlex client and `PaperService` create the first transport/business/dependency separation in the codebase.
- The output shape from Day 3 becomes the baseline that later resources, prompts, caching, and persistence will build on.

#### Why it is designed this way

- A service layer makes dependency handling testable and keeps the MCP tool handlers focused.
- Stable normalized results protect the rest of the system from upstream API shape changes.
- Pagination and hard limits prevent oversized responses from crowding model context.
- Adding `export_bibtex` now proves we can build another user-goal-aligned tool without turning `get_paper` into a multipurpose mode switch.

#### Alternatives and trade-offs

- Keep using mock data:
  - Simpler and more predictable.
  - Does not test real dependency behavior or normalization.
- Put HTTP calls directly inside tool functions:
  - Fewer files at the beginning.
  - Harder to test, mock, and extend cleanly.
- Use CORE instead of OpenAlex:
  - Better for open-access/full-text-oriented workflows.
  - Adds earlier API-key and quota workflow complexity than needed for Day 3.

#### Failure modes

- Broad search parameters return low-relevance results because upstream search semantics are looser than expected.
- A misleading identifier such as `W0000000000` may resolve unexpectedly upstream instead of behaving like a missing paper.
- Excessive result sizes overwhelm context or hide the most relevant items.
- Dependency errors become confusing if they are not converted into actionable tool messages.

#### Common mistakes

- Designing one generic paper tool with unrelated modes instead of separate tools.
- Treating empty results as an exception instead of a valid outcome.
- Returning raw upstream payloads instead of stable project-shaped data.
- Skipping result-size limits and pagination metadata.
- Using identifiers inconsistently between search results and lookup tools.

#### Security considerations

- External paper metadata is still untrusted even when it comes from a reputable scholarly source.
- Query limits protect both context size and upstream dependency load.
- Dependency failures should not leak internal stack traces or implementation details.
- The server should normalize and constrain upstream content before it reaches the model.

#### Interview explanation

Production-quality MCP tool design means turning a rough tool idea into a narrow, predictable, model-friendly contract. In Day 3, that means explicit argument limits, stable identifiers, structured outputs, pagination metadata, and clean separation between tool handlers and the external OpenAlex dependency. The result is a read-only research paper server that behaves predictably for both success and failure cases.

#### Questions for revision

1. Why is a service layer useful between MCP tools and the external API?
   Answer: It separates transport from dependency logic, makes testing easier, and gives the project one place to normalize upstream data and handle dependency-specific errors.

2. Why should empty search results not be treated as an error?
   Answer: Because a valid query can legitimately return no matches. That is a normal business outcome, not a broken protocol or broken tool invocation.

3. Why are stable identifiers important in Day 3?
   Answer: Search results feed later operations such as `get_paper`, `export_bibtex`, and later resources. Those flows only stay reliable if the identifier format is consistent and stable.

4. Why is `export_bibtex` its own tool instead of an optional mode on `get_paper`?
   Answer: It represents a distinct user goal and output format. Keeping it separate avoids turning `get_paper` into a generic mode-driven tool with mixed responsibilities.

5. Why do pagination and hard limits matter even for a read-only tool?
   Answer: They keep responses bounded, improve model usability, and reduce dependency load. Unbounded output is bad both for context management and for operational reliability.

#### Active recall review

1. Question: Why is export_bibtex modeled as its own tool instead of adding an output_format flag to get_paper?
   Answer: Because citation export is a separate user goal with a different output contract. Keeping it separate preserves clean tool boundaries, makes model selection easier, and avoids turning get_paper into a mode-heavy multipurpose tool.

2. Question: Why was the Inspector result showing an MCP paper title a good sign rather than a bug?
   Answer: Because search_papers is supposed to search a scholarly paper source, not MCP server docs. For the query Model Context Protocol, the correct behavior is to return research papers about MCP if they exist.

3. Question: What did the exact search mode prove during live verification?
   Answer: It proved the search layer can tighten relevance for precise queries, returning directly MCP-related papers instead of broader or weakly related results.

4. Question: Why is paper://{paper_id} a better future resource shape than returning huge paper payloads from every tool?
   Answer: It gives the project a stable reference for reusable context. Tools can return identifiers, and later reads can fetch the paper resource only when needed, which keeps tool outputs smaller and cleaner.
#### References

- OpenAlex docs: https://docs.openalex.org/
- OpenAlex API entity overview: https://docs.openalex.org/api-entities/works
- OpenAlex API guide: https://docs.openalex.org/how-to-use-the-api/api-overview

## Module 2: Context and Persistence

### Day 4: Resources and Prompts

#### Learning objectives

- Distinguish clearly between tools, resources, and prompts in MCP.
- Understand why stable context should be exposed through resource URIs instead of repeated tool calls.
- Understand resource templates and why they are better than pre-registering every individual resource instance.
- Understand prompt templates as reusable reasoning scaffolds with typed arguments.
- Understand why context-size limits matter for model-facing resources and prompts.

#### Core concepts

- A tool is for performing an operation now.
- A resource is for reading stable, identifiable context.
- A prompt is for reusable instruction scaffolding that helps the model work with context.
- Resource templates such as `paper://{paper_id}` let the server expose a whole family of resources without registering each concrete instance in advance.
- Model-facing context should be bounded. A paper resource should not dump unbounded raw upstream payloads.

#### How it works

1. A client discovers available resource templates and prompts from the server.
2. The client reads a resource by URI, such as `paper://W7129030749`.
3. The server resolves the URI template, validates its parameters, and returns structured resource content.
4. The client gets a prompt by name with arguments, such as `compare_papers` with two paper IDs.
5. The server renders reusable prompt messages that point the model at the right context and reasoning task.

#### Example

- `search_papers` stays a tool because searching is an action.
- `paper://W7129030749` is a resource because one paper is stable, identifiable context.
- `reading-list://starter-mcp` is a resource because a reading list is stable context that can be re-read.
- `compare_papers(paper_id_a, paper_id_b, focus)` is a prompt because it gives reusable reasoning structure instead of performing a backend action.

#### Role in our project

- Day 4 turns the Day 3 paper server into a context server instead of only a tool server.
- Paper resources make later workflows cleaner because tools can return identifiers and URIs instead of repeating full paper payloads.
- Reading-list resources establish the interface shape now, while real persistence is intentionally deferred to Day 5.
- Prompt templates establish reusable comparison and literature-review workflows without inflating the tool surface.

#### Why it is designed this way

- Stable URIs let clients and models refer back to the same context predictably.
- Resource templates avoid manual registration of every paper or list.
- Prompt templates reduce repetitive free-form prompting and make higher-level workflows more consistent.
- Bounded resource content protects token budget and keeps important content from being buried.

#### Alternatives and trade-offs

- Keep using only tools:
  - Simpler initially.
  - Repeats the same context fetches and mixes action and context responsibilities.
- Return full paper payloads from every tool:
  - Convenient in small demos.
  - Wasteful, harder to reuse, and worse for context-size discipline.
- Delay reading-list resources until persistence exists:
  - Avoids temporary mock state.
  - Slows learning of the MCP interface boundary that Day 4 is meant to teach.

#### Failure modes

- A server exposes stable context only through tools, causing repeated and unnecessary calls.
- Resource content grows too large and crowds out the useful part of the context.
- Prompt templates become pseudo-tools that do too much backend work instead of staying reusable reasoning scaffolds.
- Resource URIs are unstable, making later references brittle.

#### Common mistakes

- Treating a resource as just another tool with no URI identity.
- Returning raw upstream payloads inside resources.
- Putting write behavior behind resources.
- Making prompt templates too vague or too overloaded.
- Forgetting that prompt arguments should stay simple and explicit.

#### Security considerations

- Resource parameters are still untrusted input and must be validated.
- Resource contents are still untrusted model-facing data, even when sourced from scholarly APIs.
- Prompt templates should not assume resource content is safe or complete.
- Context-size limits are also a safety measure because oversized context can hide important warnings or constraints.

#### Interview explanation

In MCP, a tool performs an action, a resource exposes stable context through a URI, and a prompt provides reusable reasoning scaffolding. In Day 4, ResearchOps keeps search as a tool, exposes papers and reading lists as resources, and adds comparison and literature-review prompts so clients can discover context and workflows without overloading the tool surface.

#### Questions for revision

1. Why is `paper://{paper_id}` better modeled as a resource than repeated calls to `get_paper`?
   Answer: Because one paper is stable, identifiable context. A resource URI gives the client a reusable handle for that context instead of treating every read as a fresh action.

2. Why is `compare_papers` a prompt instead of a tool?
   Answer: Because it provides reusable reasoning structure for the model. It does not need to perform a backend side effect or external computation on its own.

3. What problem do resource templates solve?
   Answer: They let the server expose a family of resources like `paper://{paper_id}` or `reading-list://{list_id}` without pre-registering every individual instance.

4. Why do context-size limits matter for resources and prompts?
   Answer: Because they are model-facing. Oversized abstracts, lists, or prompt bodies waste tokens, make tool or resource use harder, and can bury the important parts of the context.

5. Why was the temporary in-memory `reading-list://{list_id}` layer acceptable on Day 4?
   Answer: Because Day 4 is about MCP interface shape, not persistence. The stable resource contract can be learned now, while durable storage is intentionally introduced on Day 5.

#### Active recall review

1. Question: If a paper can already be fetched by `get_paper`, why still add `paper://{paper_id}`?
   Answer: Because the resource URI is a reusable context handle. It separates stable context access from action-oriented tools and makes later workflows cleaner.

2. Question: Why is it dangerous to let paper resources return huge raw payloads?
   Answer: It wastes context budget, makes the useful signal harder to find, and couples the model to unstable upstream response shapes.

3. Question: Why did Day 4 use temporary in-memory reading lists instead of waiting for the database layer?
   Answer: Because the learning goal was to establish the correct resource boundary first. Persistence is a separate concern that belongs to Day 5.

4. Question: What is the key difference between a prompt argument and a resource URI?
   Answer: A prompt argument configures how a prompt is rendered, while a resource URI identifies the stable context the client can read.

#### References

- MCP resources concept: https://modelcontextprotocol.io/specification/latest
- MCP prompts concept: https://modelcontextprotocol.io/specification/latest
- MCP Python SDK server decorators: https://py.sdk.modelcontextprotocol.io/
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








