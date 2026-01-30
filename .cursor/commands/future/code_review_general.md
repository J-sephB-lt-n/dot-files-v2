# General code review

You are reviewing a Pull Request.
Compare the current local branch (which is the PR feature branch) to the main branch using `git diff main...HEAD`
Before you start, confirm with me which is the main/master branch which we're comparing against.

Specifically, review for the following:

- Does the code do what it says it does?
- Are edge-cases handled?
- Does the code violate any of the project patterns described in README.md?
- Does the code follow the conventions already present in the codebase?
- Are there appropriate tests added? Are the tests complete?
- Is there any use of bare try/except (should not happen)?
- Are there unclear names and interfaces? (i.e. as a new dev I should be able pick up and use any of the new modules, functions, classes etc. by only reading their public interfaces e.g. docstring and function signature without having to read the inner code).
- This new code is not duplicating existing code in the codebase
- Hasn't added new dependencies unnecessarily (the application needs to stay lean)
- Is the code modular? i.e. easy to maintain
- Are there any obvious performance inefficiencies?
- Are there any obvious security issues? (e.g. use of exec() or using user inputs directly in LLM prompts or SQL queries)
- Is the PR focused and small? Are there unrelated changes included in the PR?

Write your findings into a `PR_review_<your-review-name>.md` file, with at least 1 comment for each of these review areas.

Please link each review comment to a specific file(s) and line number(s).
