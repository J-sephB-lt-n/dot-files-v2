# Targeted Code Review

You are completing a code review on specific new aspects of the codebase.

First, do the following:

1. Ask me whether I want to compare the current local git branch to `main` branch (or some other trunk branch), the files in the last git commit, or whether I have specific files I'd like reviewed.
   - If I want the current branch to be compared to a trunk branch, then you can use `git diff <trunk-branch-name>...HEAD` (e.g. `git diff main..HEAD` ) to see the diff between the 2 branches.
2. Ask me which application documentation (if any) is applicable to the code under review (i.e. documents which give context to the project codebase in general or to the code under review specifically). Recommend to me the root project `README.md`, the files in `docs/` (if there are any) and the files in (`.current_agent_context/`) as possible options. Number them for me for easy selection.

Confirm with me the files you are going to review before proceeding with the code review.

Then, ask me which of the following aspects I want included in the code review:
(you can number them for me for easy selection)

- Architecture: adherence to the application architecture (ask me if you are unclear what the chosen codebase architecture is and what the application architecture goals are).
- Code correctness: does the new code do what was stated in the requirements? (ask me for the requirements documents)
- Conformist: adherence to the existing patterns in the codebase.
- External documentation: the new code does not contradict or diverge from the formal documentation in the codebase (ask me which files are applicable).
- Internal documentation: documentation in the code itself (e.g. docstrings, comments) accurately describes what the code is doing.
- Adherence to the requirements in AGENTS.md
- Ask me whether there is anything else specific that I should review for.

Once I've told you which aspects I want included, confirm the list with me again. Then, perform the code review on these aspects.

Structure your review document as follows:

1. Review title
2. Short summary of the code changes, including a simple mermaid diagram showing how affected modules/objects relate
3. List of review findings ranked from most critical to least critical. Each review comment with filepath(s) and line number(s).

When you are finished, ask me where I'd like the review document saved to. You can suggest the location `.current_agent_context/agent_review_{{ review_num }}_{{ review_description }}.md`.
