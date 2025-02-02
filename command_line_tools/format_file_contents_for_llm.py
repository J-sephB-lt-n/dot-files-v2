#!/usr/bin/env python3
r"""
Example usage:
$ format_file_contents_for_llm --dry_run '.*\.md' '.*llm.*'
$ format_file_contents_for_llm '.*\.md' '.*llm.*'

Place this script (without .py) in /usr/local/bin/ to make this script globally available
(might also need `sudo chmod +x /usr/local/bin/format_file_contents_for_llm`
"""

import argparse
import re
from pathlib import Path

def format_file_contents_for_llm(
    start_dir: str = ".",
    regex_patterns: list[str] = [".*"],
    dry_run: bool = False,
) -> str:
    """Finds all filepaths matching one or more of the regex patterns \
then formats their contents as markdown for inclusion in a LLM prompt"""
    filepaths_to_include: list[Path] = []
    for path in Path(start_dir).rglob("*"):
        if path.is_file() and any(
            [re.search(pattern, str(path)) for pattern in regex_patterns]
        ):
            filepaths_to_include.append(path)

    if dry_run:
        print("The following files would be processed:")
        for filepath in filepaths_to_include:
            print("\t", filepath)
        exit()

    output_str = ""

    for filepath in filepaths_to_include:
        with open(filepath, "r", encoding="utf-8") as file:
            file_contents: str = file.read()
        output_str += f"""
[{filepath.name}]({filepath})
```
{file_contents}
```
"""

    return output_str


if __name__ == "__main__":
    # if this script is being run as a CLI tool #
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "-d",
        "--dry_run",
        help="Describe what would be run but doesn't actually run it",
        action="store_true",
    )
    arg_parser.add_argument("regex_patterns", nargs=argparse.REMAINDER)
    args = arg_parser.parse_args()

    output: str
    if args.regex_patterns:
        output = format_file_contents_for_llm(
            dry_run=args.dry_run, regex_patterns=args.regex_patterns
        )
    else:
        output = format_file_contents_for_llm(
            dry_run=args.dry_run,
        )
    print(output)
