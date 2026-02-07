# Targeted Code Review

You are completing a code review on specific new aspects of the codebase.

First, do the following:

1. Ask me whether I want to compare the current local git branch to `main` branch (or some other trunk branch), the files in the last git commit, or whether I have specific files I'd like reviewed.
   - If I want the current branch to be compared to a trunk branch, then you can use `git diff <trunk-branch-name>...HEAD` (e.g. `git diff main..HEAD` ) to see the diff between the 2 branches.

Confirm with me the files you are going to review before proceeding with the code review.

Then, ask me which of the following aspects I want included in the code review:
(you can number them for me for easy selection)

- Identification of broad error-handling using try/except
- Generic variable names which should be more descriptive (should be self-documenting)
- Code has not considered all edge cases (e.g. an unintended code path is executed under unexpected conditions)
- Documentation within the code (e.g. module, class, method, function docstrings) are up to date (e.g. describe what the actual code is doing now, not what it used to do)
- There is any use of global state which could have been avoided
- Added code aligns with the patterns, design etc. described in the project documentation (suggest whichever of README.md, docs/**/\*, .current_agent_context/**/\* exists)
- All caught exceptions log the full stack trace
- Python imports are always at the top of the .py script
- There is opaque and/or fragile path handling (e.g. `Path(__file__).parent.parent.parent` or manual string handling of paths or use of `os.getcwd()` or nested `os.path.dirname(os.path.dirname(os.path.dirname(path)))` etc.). Paths should be represented as Path objects and never (os-incompatible) strings.
- Any use of the (no longer required) Dict, List, Tuple, Optional etc. from typing module (should use dict, list, tuple, | None etc.)
- Identification of any usage of exec() or eval()
- Identification of user inputs being used directly without being sanitised (e.g. SQL injection, LLM prompt injection etc.)

Once I've told you which aspects I want included, confirm the list with me again. Then, perform the code review on these aspects.

When you are finished, ask me where I'd like the review document saved to. You can suggest the location `docs/code_reviews/agent_review_joe_criteria_{{ review_num }}_{{ review_description }}.md`.
