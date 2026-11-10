# Tool design

## What a tool is
- Tool = metadata (name, description, parameter schema) + a function your code runs.
- The LLM sees ONLY the metadata. It does not run the tool. It writes a call, YOUR code runs it, and YOU pass the result back as an observation.
- Most tool bugs come from unclear wording, not a dumb model.

## Checklist for each tool
- Clear name, description and parameters; include examples.
- Parameters explicit: say exactly what format (city name? "Chicago, Illinois"? zip?).
- Not too broad. Few parameters, especially few optional ones (small models struggle).
- Return no more and no less than needed (an LLM pays tokens for every word, unlike a human who skims).
- Return errors as readable text or a structured error so the agent can retry. Never disguise failure as success.
- Validate arguments in code before running anything.
- Read-only and read-write are separate tools. Put guardrails (confirmation, allowed paths) inside the tool.
- Tool metadata is always in context. More tools is NOT better. Overlap hurts more than count (a team with ~50 overlapping tools: the LLM could not choose).
- Many tools (50 to 1000)? Embed the tool descriptions and retrieve only the few relevant ones (RAG for tools).

## Robot test (write the result in WORKFLOW.md section 5)
Pretend you only have the tool names and descriptions. Could you always tell which tool to use? If the honest answer is "it depends on the context", fix the tools. If the agent keeps picking the wrong tool, fix descriptions BEFORE reaching for a better model.

## MCP vs your own tool
- MCP standardizes how tools connect to LLMs (server provides tools, client runs them, LLM chooses). The company that owns the API ships and maintains the server (GitHub, Slack, Datadog...).
- Prefer an existing MCP server over writing your own connection. Write your own tool when there is no server or you need custom guardrails.

## Skills vs tools
- A skill gives instructions (SKILL.md + optional bundled files), not actions.
- Loaded in layers: metadata always (~100 tokens), instructions only when used (keep under ~5,000 tokens), bundled files only if needed.
- Bundled scripts run outside the context: only the output enters it. Use them for deterministic jobs (validation, conversion).
- Warning: tools, skills and connections all eat context all the time.

## Tool spec snippet
```
name: read_project_file
description: Read one text file inside the project folder and return its contents.
required params: path (relative to project root)
allowed paths: inside the project root only; deny .env and secrets
if missing: return {"error":"not_found","path":...}
returns: file text, truncated at N characters with a note
why read-only: it cannot change anything; writing is a separate write_project_file tool with confirmation
```
