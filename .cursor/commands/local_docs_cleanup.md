# Python Local Documentation Cleanup

Your task is to validate and fix documentation in a python script(s).

First, ask me which python file(s) require documentation cleanup. You can suggest active files to me as options.

Specifically, do the following:

- Add type annotations if any are missing (all variables must also have type annotations).
- Ensure that module, class, method and function (and all other) docstrings have not diverged from the code (i.e. the documentation is still consistent with the code that it is describing).
- Ensure that in-line code comments have not diverged from the code itself (i.e. the comments still align with what the code is actually doing).
- Ask me if I'd like you to run `uv run ty check` on the required files to check that the type annotations are correct.
- Add `typing.NewType`s and update type annotations to become self-documenting e.g. `dict[UserId, UserMetadata]` rather than `dict[str, dict]`
