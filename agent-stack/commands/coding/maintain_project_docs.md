# Project Document Maintenance

Your task is to assess whether recent changes to the codebase have caused the code to diverge from the project documentation.

Proceed now as follows:

1. Ask me for guidance on how to identify "recent codebase changes". You can give as options:
   - All changes in the last git commit (or all git commits within the last X hours or days)
   - All differences between the current git branch compared to the trunk branch (e.g. `main`)
   - A specific set of files
   - All files modified within the last X hours/days.
2. Searching only the current project folder, identify if `README.md` exists, and list out all files in `docs/` (if this folder exists). Ask me which of these documents need to be kept aligned with the project code.
3. Summarise discrepancies that have arisen between the project documentation and the codebase. Classify each discrepancy by severity, and return me the list prioritized from highest to lowest priority.
4. For each identified discrepancy, ask me what I want you to do about it (update the doc(s), update the code or ignore the discrepancy).

Please ask me for permission before doing any of the following:

- Reading a file
- Inspecting git history
- Running any commands

If any part of this task is ambiguous, conflicting or unclear, ask me clarifying questions (until the task is crystal clear) before proceeding.
