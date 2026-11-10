# Decision guide (ask top to bottom, stop at the first "yes")

| # | Question to ask the user | If yes, use |
|---|---|---|
| 1 | Can plain code do it (no LLM)? | **Plain code** |
| 2 | Do you know every step in advance? | **Workflow** (chain, router, parallel, evaluator-optimizer) |
| 3 | Does each step depend on the previous step's output? | **Prompt chaining** (workflow) or **Sequential** (agents) |
| 4 | Does the input fall into a few clear categories? | **Routing** (workflow) or **Dispatcher** (agents). Cheapest multi-agent pattern |
| 5 | Are there independent subtasks, or do you want redundancy? | **Parallelization** (sectioning / voting). Aggregator should be plain code if possible |
| 6 | Is there a clear test to check results against? | **Evaluator-optimizer** (always add a stop condition) |
| 7 | Can you not predict the subtasks (like code edits)? | **Orchestrator-workers** (edge of workflow/agent) |
| 8 | Do you know all the paths but not which one a request needs (chatbots)? | **Single agent (ReAct)** |
| 9 | Does the task split cleanly up front and never change? | **Plan-and-Execute** (cheaper, cannot adapt). If you know all the steps in advance, ask again why not a workflow: a workflow gives more control |
| 10 | Might the plan change as results come back (coding)? | **ReAct** |
| 11 | Want one code block to do many tool calls, and can you build a sandbox? | **CodeAct** |
| 12 | Too much context for one agent, work splittable, correctness matters, budget allows ~15x tokens? | **Supervisor**. Ask: is this task worth ~15 chats' worth of tokens? Good for important breadth-first research. Bad for FAQ bots and coding (shared context, many dependencies) |
| 13 | No hierarchy and unknown decomposition? | **Peer-to-peer** (last resort) |

## Routing details (when row 4 says yes)
- Route by topic/intent, by cost or difficulty (easy work to a small model, hard work to a big one), or by confidence (not confident: ask the user or escalate to a human).
- Small classification models are cheap now (cents per call), so a router is the cheapest multi-agent pattern.
- Always include a "confused / ask the user" route. Bad routes are very hard to recover from.
- The advisor strategy (small model runs the task, calls a bigger one when stuck) can work, but small models struggle to know WHEN they cannot handle something.

## Parallel details (when row 5 says yes)
- Sectioning = different subtasks at once. Voting = same task several times. Use different models/providers for voting; same family wastes money.
- Aggregator as plain code if possible. Keep counts. If voting agents always agree, switch to one agent.

## Useful extra questions
- Who is the user, and what happens when the answer is wrong? (healthcare, banking: prefer workflow)
- Does it need low latency? (chaining and sequential stack latency)
- What is the budget per request?
- Which tools are read-only and which can change things?
- Can a wrong output be caught by a plain-code check?

## Ladder: who draws the arrows
- Workflow (any): you, in code
- Single agent: model picks from paths/tools you defined
- Sequential, Parallelization: you
- Dispatcher: you write the paths, a classifier picks one
- Evaluator-optimizer: you build the loop, the model decides when to stop
- Supervisor: the model, at runtime
- Peer-to-peer: the models, at runtime (you gave up every arrow)
