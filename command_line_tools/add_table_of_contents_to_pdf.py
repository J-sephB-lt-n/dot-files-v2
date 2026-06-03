#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pymupdf",
# ]
# ///

"""
Python command line script for adding a Table of Contents (bookmarks) to an
existing PDF.

To make available globally:
    1. chmod +x add_table_of_contents_to_pdf.py
    2. ln -s /home/josephbbolton/command_line_tools/add_table_of_contents_to_pdf.py ~/.local/bin/add_table_of_contents_to_pdf
    3. Now you can run `add_table_of_contents_to_pdf --help` from any folder
"""

import argparse
import json
import sys

import pymupdf


TOC_EXAMPLE = """\
Example TOC JSON file (toc.json):
  [
    [1, "Introduction",       1],
    [1, "Chapter 1",          5],
    [2, "Section 1.1",        7],
    [2, "Section 1.2",       12],
    [1, "Chapter 2",         20],
    [2, "Section 2.1",       22]
  ]

Each entry is a JSON array of exactly three elements:
  [level (int), title (str), page (int)]

  level  - heading depth: 1 = top-level chapter, 2 = section, 3 = subsection, etc.
  title  - bookmark label shown in the PDF viewer
  page   - 1-based page number the bookmark points to
"""


def main():
    parser = argparse.ArgumentParser(
        description="Add a table of contents to a PDF.",
        epilog=TOC_EXAMPLE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--in", dest="input", required=True, help="Input PDF path")
    parser.add_argument("--out", dest="output", required=True, help="Output PDF path")
    parser.add_argument(
        "--toc",
        required=True,
        help="Path to a JSON file containing the TOC (see format below)",
    )
    args = parser.parse_args()

    with open(args.toc, "r") as f:
        toc = json.load(f)

    # Validate TOC structure: list of [level, title, page]
    for i, entry in enumerate(toc):
        if (
            not isinstance(entry, list)
            or len(entry) != 3
            or not isinstance(entry[0], int)
            or not isinstance(entry[1], str)
            or not isinstance(entry[2], int)
        ):
            print(f"Error: TOC entry {i} is invalid: {entry}", file=sys.stderr)
            print(
                "Each entry must be [level (int), title (str), page (int)]",
                file=sys.stderr,
            )
            sys.exit(1)

    doc = pymupdf.open(args.input)
    doc.set_toc(toc)
    doc.save(args.output)
    doc.close()

    print(f"Saved '{args.output}' with {len(toc)} TOC entries.")


if __name__ == "__main__":
    main()
