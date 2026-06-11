#!/usr/bin/env python3
r"""
Example usage:
    ls *.py | format_file_contents_for_llm
    ls *.py | format_file_contents_for_llm | clip.exe # on WSL, pipe straight to clipboard
    find ./somedir ./some/other/path -type f \( -name '*.md' -or -name '*.txt' \) | format_file_contents_for_llm
    find . -type f | fzf -m | format_file_contents_for_llm

Place this script (without .py) in /usr/local/bin/ to make this script globally available
(might also need `sudo chmod +x /usr/local/bin/format_file_contents_for_llm`
"""

import sys
from pathlib import Path
from typing import Sequence


def format_file_contents_for_llm(filepaths: Sequence[Path]) -> str:
    """
    Return a single string containing the combined text content
    of each file in `filepaths`, which each file's text content enclosed
    in <filename>...</filename> tags.
    """
    return "\n\n".join(
        f"""
<file path="{filepath}">
{filepath.read_text(encoding='utf-8')}
</file>
"""
        for filepath in filepaths
    )


if __name__ == "__main__":
    # if this script is being run as a CLI tool #
    filepath_strings: list[str] = [
        s for s in sys.stdin.read().splitlines() if s.strip()
    ]
    filepaths: list[Path] = [Path(s) for s in filepath_strings]
    output: str = format_file_contents_for_llm(filepaths)
    print(output)
