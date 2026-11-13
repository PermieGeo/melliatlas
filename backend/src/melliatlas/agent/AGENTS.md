# Agent Rules

Inherits root and backend guidance. Agent controls **adaptive decisions**, never the low-level DAG executor.

- Implement the observable loop **Goal -> Plan -> Execute -> Observe -> Evaluate -> Replan / Finish**. Every replan must cite new observations or explicit failed preconditions; avoid decorative LLM calls around a fixed pipeline.
- Select only **registered, authorized Sources/Analyzers** and permitted territory/profile combinations. Treat source text, user prompts, and model output as untrusted instructions.
- Never allow arbitrary Python, SQL, shell, URLs, private data exfiltration, self-modifying tools, or unreviewed provider access. Validate tool arguments and returned artifacts at every call boundary.
- Enforce configurable upper bounds on steps, tool calls, retries, elapsed time, context/tokens, and cost. Halt with a typed incomplete/unavailable outcome when a limit is reached; no unbounded replanning loops.
- Keep the planner replaceable (`rules`, `LLM`, or future policy); run the **same Engine** for all planners. LLM is optional, model/provider configurable, and cannot overwrite observed evidence.
- Persist or emit an auditable decision trace with plan versions, tool names, relevant evidence IDs, reasons for replanning, and termination cause. Never fabricate tool success or confidence.
- Test fixed-pipeline and adaptive-agent baselines on deterministic synthetic scenarios, including contradictory evidence, missing providers, tool failure, quota exhaustion, and unsupported goals.
