# Scorecard (qualitative guidance, not laws; measure your own)

| System | Context | Reliability | Cost | Other |
|---|---|---|---|---|
| Workflow | Bounded, good | Great (gates, test each step) | Controlled | Low adaptability |
| Single agent | Worse (one window holds all) | Slightly worse (unknown steps) | Worse than workflow, better than multi | Adaptability is the big win |
| Sequential | Better (own context per agent) | Errors compound; validate handoffs | Usually cheapest multi-agent | Latency stacks |
| Parallelization | Good | Voting better via redundancy | High | Merge step is a single point of failure |
| Dispatcher | Good | Bottlenecked on the classifier; bad routes hard to recover | Cheapest multi-agent | Fork, not decomposition |
| Evaluator-optimizer | Grows each round | Super strong | High, fast | Most likely to loop forever |
| Supervisor | Excellent | Strong | Very high (~15x chat tokens) | Needs one capable model; rubber-stamp risk |
| Peer-to-peer | Bad | Usually worse | Very expensive | Hardest to debug; last resort |

Note: both the dispatcher (easy work goes to small models) and sequential are described as "the cheapest multi-agent" pattern. Do not rank them against each other without measuring.

Numbers to remember (context-specific, not universal): agent ~4x chat tokens, multi-agent ~15x; Self-Refine ~20% gain over 7 tasks; start evals with 20 to 50 tasks.

Caveat: none of this is law. Good, bad, cheap and reliable depend on model, task, prompt, tools and implementation. It is a guess until you measure it in your own system (WORKFLOW.md section 12). Reliability goes UP with feedback loops and DOWN with handoffs; a more sophisticated system is not automatically more reliable.
