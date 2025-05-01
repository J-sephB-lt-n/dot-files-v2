#!/usr/bin/env python3
r"""
Function which reads files contents for a full codebase from a markdown file, creates the required folders and files, \
and populates the files contents.

File content in the input markdown file must contain mutiple fenced code blocks in this format:

relative/path/to/file.extension
```language
<file contents here>
```

Example usage:
$ populate_files --content files_contents.md          # files created relative to where this command is run

Place this script (without .py) in /usr/local/bin/ to make this script globally available
(might also need `sudo chmod +x /usr/local/bin/populate_files`
"""

import argparse
import re
from pathlib import Path


def populate_files(
    files_contents: str,
    pause_for_user_confirmation: bool,
) -> None:
    """
    Populates files contents as described in `files_contents`.
    Everything is created relative to the current folder.
    """
    markdown_blocks: list[tuple] = re.findall(
        r"([a-zA-Z0-9\/\-\_]+\.[a-z]{1,10})[^a-zA-Z0-9\/\-\_\.]{0,5}\s*\n{1,2}```([a-z]+)\n(.*?)\n```",
        files_contents,
        re.DOTALL,
    )

    if pause_for_user_confirmation:
        print(
            "The following files and folders will be created/overwritten in the",
            f"current folder {Path.cwd()}:",
        )
        for filepath in sorted([x[0] for x in markdown_blocks]):
            print("\t", filepath)
        confirm: bool = (
            input(
                "\nCreate these files/folders? (anything other than 'yes' will cancel)\n"
            )
            == "yes"
        )
        if not confirm:
            print("...exiting")
            exit()

    for filepath, language, file_content in markdown_blocks:
        print(f"writing {filepath} ({language})", end="")
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(Path(filepath), "w") as file:
            file.write(file_content)
        print(" ...done")


if __name__ == "__main__":
    # if this script is being run as a CLI tool #
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "-f",
        "--files_contents",
        help="Path to markdown file containing required path and contents of each file",
        required=True,
        type=Path,
    )
    args = arg_parser.parse_args()

    with open(args.files_contents, "r") as file:
        files_contents: str = file.read()

    populate_files(
        files_contents=files_contents,
        pause_for_user_confirmation=True,
    )
