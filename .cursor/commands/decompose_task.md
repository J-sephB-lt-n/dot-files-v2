# Decompose Task

We are adding a piece of functionality to the current codebase.

You task is to assist me with partitioning this large and/or complex feature into smaller logical self-contained units of work.

Do the following (in exactly this order):

1. Remind me that this prompt needs work (it was added as a placeholder). You can use these exact words when you address me.
2. Ask me for:
   - A high level summary of the code we're adding - _what_ and _why_.
   - Link(s) to requirements documentation (don't read it, but suggest `docs/PRD.md` and/or `.current_agent_context/requirements.md` to me if they exist)
   - Links to any other documentation which provides context to this task. Suggest to me:
     - `README.md` (if it exists). Ask my permission before reading it.
     - `docs/**/*` (if this folder exists). Ask my permission before reading any of these files.
     - `.current_agent_context/*/**` (if this folder exists). Ask my permission before reading any of these.
3. Ask me whether I want to decompose this task into sequential units of work (later pieces depend on prior pieces to be finished) or parallel units of work (pieces can be developed in parallel).
4. Ask me clarifying questions if there is anything about your task that is ambiguous or conflicting.
5. Discuss with me the right number of units of work (features) that we want to divide the work into. Provide a recommendation. User stories is a possible approach we might consider. It is important that each unit of work results in a new testable piece of application.
6. Once we've settled on our final partitioning, suggest to me that we write our agreed breakdown of work to `.current_agent_context/features_list.json`, with the following format:

```json
[
  {
    "id": "unique feature id",
    "name": "short unique name",
    "description": "short feature description",
    "status": "NOT_STARTED | IN_PROGRESS | COMPLETED",
    "last_updated_at": "timezone-aware ISO 8601 format", // use the CLI to get the system time
    "dependencies": ["...", ...] // list of IDs of features which must be finished before this one
  },
  ...
]
```
