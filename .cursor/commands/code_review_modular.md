# Targeted PR Code Review

You are completing a code review on specific aspects of the code.

First, ask me whether I want to compare the current local git branch to `main` branch (or some other trunk branch) or whether I have specific files I'd like reviewed.
If I want the current branch to be compared to a trunk branch, then you can use `git diff <trunk-branch-name>...HEAD` (e.g. `git diff main..HEAD` ) to see the diff between the 2 branches.

Then, ask me which of the following I want included in the code review:
(you can number them for me for easy selection)

- Code correctness
  - Is the code correct? (does what it says it does)
  - Have boundary conditions (edge-cases) been considered and handled?
- Error-handling:
  - Are errors handled intentionally? (i.e. not blindly swallowed using bare try/except)
  - Are errors handled at the right layer?
  - Do errors give actionable context (without exposing sensitive information)
- Code Readability and Documentation
  - Are things named well? (i.e. I can understand from the module/function/class/method etc. name what the thing does, without opaque abbreviations)
  - Is the code well documented? (i.e. module docstrings, google-style function, class and method docstrings.)
  - Code is easy to scan (well-named abstractions, logical sections)
  - Comments explain why, not what
  - New big technical decisions have been appropriately documented
- Performance
  - Appropriate algorithmic complexity
  - Avoids unnecessary allocations/copies
  - Has approach streaming/batching/pagination for large data
  - Avoids blocking calls in an async context
  - Memory usage is bounded
- Is the scope tight? (i.e. hasn't included unrelated changes in the same PR)
- Any "TODO"/"FIXME" left in the code
- Does it follow the existing patterns and conventions in the codebase? (and possibly documented in README.md)
- Is there unnecessary duplication of existing code?
- Has the new code introduced coupling which could have been avoided?
- Are all python imports at the top of the script?
- Have unnecessary dependencies been added?
- Are public interfaces minimal, coherent and clearly documented?
- Dead code is removed
- Style is consistent with the existing code in the repo
- Avoids unnecessary global state
- Clear separation of concerns
- Is the code extensible?
- Are there any obvious security issues?
- The code must be platform agnostic (e.g. won't only work on windows)
- Are there any silent failures or ignored return values?

Once I've told you which aspects I want included, confirm the list with me again. Then, perform the code review on these aspects.

Write your findings into a `PR_review_<your-review-name>.md` file, with at least 1 comment for each of these review areas I have requested from you.
Rank your findings from most critical to least critical.
Please link each review comment to a specific file(s) and line number(s).
