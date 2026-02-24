# Save Context

Your task now is to persist your current context into a planning asset which other developers can read to replicate your understanding of your current task/feature.

## Objective

Persist a complete, structured checkpoint of:

- Your current understanding
- All decisions made
- Task/feature status
- Relevant files
- Open questions
- Architectural constraints
- Known risks
- Next actions

Write this to:

```
.current_agent_context/context_checkpoint.md
```

---

## CRITICAL RULES

1. **Do NOT read any additional files.**
2. **Do NOT modify any code.**
3. **Do NOT run tools.**
4. Only use information currently in your context window.
5. If anything is unclear about this instruction, ask me before proceeding.

---

## REQUIRED STRUCTURE

Follow this exact structure in the checkpoint file.

### 1. High-Level Task Summary

- What problem are we solving?
- Why does it exist?
- What is the intended outcome?

### 2. Current Phase (research → ideate → spec → plan → execute → review)

- Identify which phase we are in.
- Brief explanation of why.

### 3. Requirements (Explicit + Implied)

- Confirmed requirements
- Assumptions made
- Constraints (performance, tests, architectural, etc.)

### 4. Relevant Files

- List of all files related to this task. All related files (e.g. code files, data files, URLs, documentation etc.). Absolute filepaths.
- A brief explanation of how these files related to the task/feature, and how they relate to each other.

### 5. Architectural Context

- Relevant architecture principles
- Patterns being followed
- Any deviations (intentional or accidental)
- Items that must be monitored (practice_id=31, 32)

### 6. Task Decomposition Status

If a `.current_agent_context/features_list.json` exists or if a decomposition of this current task/feature was discussed or implemented:

- List each feature (unit of work partition)
- Status (not started / in progress / blocked / complete)
- Dependencies
- What remains

### 7. Decisions Made

For each decision:

- What was decided
- Why
- Alternatives considered (if any)
- Tradeoffs

### 8. File Changes Made

- Files modified
- Purpose of changes
- Any temporary or questionable implementations

### 9. Test Status (TDD Compliance)

- Were tests written first?
- Any tests skipped?
- Any test modifications?
- Known weaknesses in test coverage
- Test performance concerns

### 10. Known Issues / Risks

- Technical debt introduced
- Incomplete work
- Fragile logic
- Edge cases not handled

### 11. Open Questions for the User

List anything that requires clarification before further progress.

### 12. Recommended Next Actions (for the next fresh developer)

Provide a small, well-scoped next task/feature, or a clean multi-step plan.

---

## Writing Instructions

- Be concise but information-dense.
- No narrative fluff.
- Use bullet points.
- Prefer explicitness over brevity where ambiguity could occur.

---

## Final Step

After generating the content:

1. Ask me for permission to write it to `.current_agent_context/context_checkpoint.md`. Do not write to this file until I confirm.

---

This checkpoint must enable a completely fresh agent to resume work with minimal ambiguity and no hidden assumptions.

If anything is ambiguous or conflicting about these instructions, ask me before proceeding.
