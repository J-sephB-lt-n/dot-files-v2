# Targeted Code Review

You are completing a code review on specific new aspects of the codebase.

First, ask me whether I want to compare the current local git branch to `main` branch (or some other trunk branch), the files in the last git commit, or whether I have specific files I'd like reviewed.
If I want the current branch to be compared to a trunk branch, then you can use `git diff <trunk-branch-name>...HEAD` (e.g. `git diff main..HEAD` ) to see the diff between the 2 branches.

Confirm with me the files you are going to review before proceeding with the code review.

Then, ask me which of the following aspects I want included in the code review:
(you can number them for me for easy selection)

- Adherence to the application architecture (ask me if you are unclear what the chosen codebase architecture is and what the application architecture goals are).
- Does the code documentation align with what the code is actually doing?
- Does the new code do what was stated in the requirements? (ask me for the requirements documents)

Once I've told you which aspects I want included, confirm the list with me again. Then, perform the code review on these aspects.

Structure your review document as follows:

1. Review title
2. Short summary of the code changes, including a simple mermaid diagram showing how affected modules/objects relate
3. List of review findings ranked from most critical to least critical. Each review comment with filepath(s) and line number(s).

When you are finished, ask me where I'd like the review document saved to. You can suggest a filename of the format `agent_review_{{ review_description }}.md`.
