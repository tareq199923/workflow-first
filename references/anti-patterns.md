# Anti-patterns and cheaper fixes

## Anti-patterns
- Supervisor for steps that depend on each other, or for a coding agent (shared context, many dependencies)
- Peer-to-peer in production (hard to debug, mostly a distraction)
- Keeping a voting multi-agent setup after the models consistently agree (use one agent; keep counts)
- Skipping stop conditions
- Long self-critique prompts with no external signal (can make answers worse)
- Agents trusting each other's output with no check ("no one verified it")
- Paying a large model to build a menu you already know (use a dispatcher)
- Stacked supervisors that validate each other's hallucinations (rubber stamps) with no real check on tangible things
- Planning with a huge model and acting with a tiny one and assuming it is cheaper (not guaranteed)
- Asking a model to write its own tests and then trusting reflection as if the tests were human-written (weaker signal)
- Reflection loops with no cap: every reflection carries the whole trajectory (easy way to triple the bill; stop after 3 to 5 tries)
- Starting on a cheap small model that needs extra steps and retries (one large-model call can beat 3 to 5 small-model calls; prototype on the most capable model, then swap cheaper models in one step at a time)
- Trusting retrieval: when RAG picks the wrong passage the answer is confidently wrong
- Choosing an architecture because it sounds advanced

## Try these BEFORE moving right
1. Fix tool names and descriptions; remove overlapping tools (do this before blaming the model)
2. Add a gate or schema check between steps
3. Try one stronger model on the failing step (one large-model call can beat 3 to 5 small-model calls)
4. Shrink or summarize the context; use RAG or a re-ranker if retrieval is the problem
5. Add an external signal (a test) and retry within the user's retry budget
6. Only then: a single agent for that one step, inside the workflow
7. Only then: more agents, and pick the pattern on purpose

## When something is failing, ask for
- Which eval tasks fail, and how often (run more than once)
- Where in the trajectory it goes wrong
- Cost and latency of the simple version vs the proposed one
