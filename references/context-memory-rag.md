# Knowledge, memory and context

An agent has three groups of parts: what it CAN DO (tools, MCP, skills), what it KNOWS (RAG, context, memory), how it THINKS (planning, reflection). WORKFLOW.md section 6 is the "knows" part.

## Context
- Context is finite. Competing for space: system prompt, tool definitions and skill metadata, conversation (agents are verbose), info about other agents.
- "Lost in the middle": models do worse on facts buried in a huge context.
- Single agent: the transcript grows every loop. The user said "stay in South Carolina" 40,000 tokens ago and it gets lost.

## Ways to protect context
1. RAG: pull only what relates to the query.
2. Re-ranker: RAG finds what is RELATED; a re-ranker checks what is HELPFUL for this question (Seabiscuit is related to horses, not helpful for "showing horses").
3. Compaction: lossless (move the transcript to a database/cache) or lossy (an LLM summarizes at a threshold; tell it what to keep). You may lose something important.
4. MMR (maximal marginal relevance): relevance minus similarity to what you already picked, to drop repeats.

## RAG in 6 steps
ingest, chunk (phrase to a few sentences), embed (same model for query and documents), store, retrieve, augment.
- RAG lowers hallucination only when retrieval is right. When retrieval is wrong the model answers confidently with wrong info. Keep source IDs with chunks, test retrieval (correct source? correct section, not merely related? enough surrounding context? no near-duplicates? answer stays within the evidence?).
- RAG is not fine-tuning: RAG works at query time, fine-tuning changes the model beforehand.
- Cost is mostly embedding everything once plus one embedding call and one database call per query.

## Memory
- LLMs are stateless; the app resends history.
- Short-term (working) memory: the agent's running state (goal, tried steps, tool results). Context is rebuilt from it every turn.
- Long-term: semantic (facts, usually "RAG"), episodic (what happened: past tickets, lessons), procedural (how to do things: system prompt, tool definitions, skills, code).
- Where to store episodic memory: full transcripts in a database, end-of-session summaries, a vector database of past messages, logs of agent runs, plain notes files.
- Getting memory back: always loaded (small profile, last summaries) or on demand (a "search memory" tool; can fail like any search).
- Memory cycle: retrieve what is relevant, think, act, save what is worth keeping.
- Keep the transcript in storage; do not inject all of it into every call.

## Checkpoint snippet
```json
{"task_id":"task-123","goal":"Investigate a failing test","status":"in_progress",
 "completed":["read test output","located failing function"],
 "pending":["inspect implementation","propose a fix","rerun tests"],
 "last_observation":"Assertion failed: expected 200, received 500","attempt":1}
```
Update after each successful tool call: completed, pending, last_observation, attempt, status. Store task facts separately from free-form reasoning. A resumed task must not repeat unsafe actions.

## Handoff contents (multi-step agents)
Pass a small structured object plus the original input, not the previous agent's whole transcript (no tool calls, steps or reasoning). Validate it before the next stage.
