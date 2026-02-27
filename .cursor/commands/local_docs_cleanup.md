# Python Local Documentation Cleanup

Your task is to validate and fix documentation in a python script(s).

First, ask me which python file(s) require documentation cleanup. You can suggest active and recent files to me as options.

Please do not modify any files other than the ones that we've agreed upon.

For each file do the following:

- Add type annotations if any are missing (all variables must also have type annotations).
- Ensure that module, class, method and function (and all other) docstrings have not diverged from the code (i.e. the documentation is still consistent with the code that it is describing).
- Ensure that in-line code comments have not diverged from the code itself (i.e. the comments still align with what the code is actually doing).
- Ask me if I'd like you to run `uv run ty check` on the required files to check that the type annotations are correct.
- Add `typing.NewType`s and update type annotations to become self-documenting e.g. `dict[UserId, UserMetadata]` rather than `dict[str, dict]`
- Ask me which project docs exist which this code should align with/adhere to. Then check that this python script(s) has not diverged from what is described/mandated in that documentation. Suggest to me `README.md`, files in `docs/` (list the files for me) and files in `.current_agent_context/` (list the files for me) as potential options.
- All class attributes whose names are not trivially self-documenting should have a description (e.g. use pydantic.Field in a pydantic.BaseModel)

Bear in mind that documentation in code should never simply repeat what can be read from the immediate code itself. Code documentation/comments should only:

1. Document things in the code which cannot be inferred by reading the code adjacent to the documentation.
2. Document at a high level what a large amount of code is doing (so that users need only read the interface documentation and not implementation itself).

Please ask me for permission before doing any of the following:

- Reading a file
- Inspecting git history
- Running any commands

If any part of this task is ambiguous, conflicting or unclear, ask me clarifying questions (until the task is crystal clear) before proceeding.
