#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "tree-sitter",
#   "tree-sitter-python",
#   "tree-sitter-javascript",
#   "tree-sitter-typescript",
# ]
# ///

"""
CLI tool giving a concise summary of a python, js or ts file by listing its imports,
function definitions, class definitions, class method definitions, and
function/method calls (using tree-sitter).

To make available globally:
    1. chmod +x script_summary.py
    2. ln -s /home/josephbbolton/command_line_tools/script_summary.py ~/.local/bin/script_summary
    3. Now you can run `script_summary --help` from any folder
"""

import argparse
import json
from pathlib import Path

import tree_sitter_javascript as _tsjs
import tree_sitter_python as _tspy
import tree_sitter_typescript as _tsts
from tree_sitter import Language, Node, Parser


_LANGUAGES: dict[str, Language] = {
    "python": Language(_tspy.language()),
    "javascript": Language(_tsjs.language()),
    "typescript": Language(_tsts.language_typescript()),
    "tsx": Language(_tsts.language_tsx()),
}

LANG_BY_SUFFIX: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
}


def get_parser(lang: str) -> Parser:
    """Return a Tree-sitter Parser configured for the given language name.

    Args:
        lang: One of the keys in LANG_BY_SUFFIX values (e.g. "python").

    Returns:
        A configured Parser instance.

    Raises:
        KeyError: If lang is not a recognised language name.
    """
    assert lang in _LANGUAGES, f"Unknown language: {lang!r}"
    return Parser(_LANGUAGES[lang])


def text(src: bytes, node: Node) -> str:
    """Decode the source bytes spanned by node.

    Args:
        src: Full file bytes.
        node: A Tree-sitter Node.

    Returns:
        The UTF-8 text of the node, with replacement characters for bad bytes.
    """
    return src[node.start_byte : node.end_byte].decode("utf-8", "replace")


def child_by_field(node: Node, name: str) -> Node | None:
    """Return a node's named field child, or None if absent.

    Args:
        node: Parent node.
        name: Field name (e.g. "name", "parameters").

    Returns:
        The child Node for that field, or None.
    """
    return node.child_by_field_name(name)


def named_children_of_type(node: Node, *types: str) -> list[Node]:
    """Return named children whose type is in types.

    Args:
        node: Parent node.
        *types: Accepted node type strings.

    Returns:
        List of matching child Nodes.
    """
    return [c for c in node.named_children if c.type in types]


# Node types whose text value should be truncated if long.
_TRUNCATE_TYPES: frozenset[str] = frozenset(
    {
        # Python
        "string",
        "list",
        "dictionary",
        "tuple",
        "set",
        # JS/TS
        "string",
        "template_string",
        "array",
        "object",
    }
)

# How many characters of an argument value to show before truncating.
_TRUNCATE_HEAD = 8
_TRUNCATE_TAIL = 8
_TRUNCATE_THRESHOLD = 20


def truncate_value(raw: str) -> str:
    """Truncate a stringified argument value if it exceeds the threshold.

    Values whose length exceeds _TRUNCATE_THRESHOLD are shown as:
        <head>..<N chars omitted>..<tail>

    Args:
        raw: The stringified argument value.

    Returns:
        The original string if short enough, otherwise a truncated form.
    """
    if len(raw) <= _TRUNCATE_THRESHOLD:
        return raw
    omitted = len(raw) - _TRUNCATE_HEAD - _TRUNCATE_TAIL
    return f"{raw[:_TRUNCATE_HEAD]}..{omitted} chars omitted..{raw[-_TRUNCATE_TAIL:]}"


def format_args(src: bytes, args_node: Node) -> str:
    """Render the argument list of a call as a compact, truncated string.

    Positional args are rendered as their (possibly truncated) value.
    Keyword args (Python) are rendered as ``name=value``.

    Args:
        src: Raw source bytes of the file.
        args_node: The argument_list / arguments Node.

    Returns:
        A string like ``(arg1, name=arg2)``.
    """
    parts: list[str] = []
    for child in args_node.named_children:
        if child.type == "keyword_argument":
            # Python: keyword_argument has fields "name" and "value"
            kw_name = child.child_by_field_name("name")
            kw_val = child.child_by_field_name("value")
            name_str = text(src, kw_name) if kw_name else "?"
            if kw_val:
                val_raw = text(src, kw_val)
                val_str = (
                    truncate_value(val_raw)
                    if kw_val.type in _TRUNCATE_TYPES
                    else val_raw
                )
            else:
                val_str = "?"
            parts.append(f"{name_str}={val_str}")
        else:
            raw = text(src, child)
            parts.append(truncate_value(raw) if child.type in _TRUNCATE_TYPES else raw)
    return "(" + ", ".join(parts) + ")"


type _Summary = tuple[list[str], list[dict], list[dict], list[dict], list[dict]]


def py_summary(src: bytes, root: Node) -> _Summary:
    """Extract imports, functions, methods, classes, and calls from a Python AST.

    Methods are distinguished from standalone functions by checking whether their
    parent block belongs to a class_definition.

    Args:
        src: Raw source bytes of the file.
        root: Root node of the parsed Tree-sitter tree.

    Returns:
        A tuple of (imports, functions, methods, classes, calls).
    """
    imports: list[str] = []
    funcs: list[dict] = []
    methods: list[dict] = []
    classes: list[dict] = []
    calls: list[dict] = []

    def _visit(n: Node, class_name: str | None) -> None:
        if n.type in {"import_statement", "import_from_statement"}:
            imports.append(text(src, n).strip())

        elif n.type == "class_definition":
            name_node = child_by_field(n, "name")
            supers = child_by_field(n, "superclasses")
            cls_name = text(src, name_node) if name_node else "<anonymous>"
            classes.append(
                {
                    "name": cls_name,
                    "args": text(src, supers) if supers else "",
                    "line": n.start_point[0] + 1,
                }
            )
            for child in n.children:
                _visit(child, cls_name)
            return  # children already visited above

        elif n.type == "function_definition":
            name_node = child_by_field(n, "name")
            params = child_by_field(n, "parameters")
            entry = {
                "name": text(src, name_node) if name_node else "<anonymous>",
                "args": text(src, params) if params else "()",
                "line": n.start_point[0] + 1,
            }
            if class_name is not None:
                methods.append({**entry, "class": class_name})
            else:
                funcs.append(entry)

        elif n.type == "call":
            fn = child_by_field(n, "function")
            args_node = child_by_field(n, "arguments")
            if fn:
                calls.append(
                    {
                        "name": text(src, fn).strip(),
                        "args": format_args(src, args_node) if args_node else "()",
                        "line": n.start_point[0] + 1,
                    }
                )

        for child in n.children:
            _visit(child, class_name)

    _visit(root, class_name=None)
    return imports, funcs, methods, classes, calls


def js_ts_summary(src: bytes, root: Node) -> _Summary:
    """Extract imports, functions, methods, classes, and calls from a JS/TS AST.

    Methods (method_definition, public_field_definition) are always children of
    a class_body, so the enclosing class name is tracked via recursive descent.

    Args:
        src: Raw source bytes of the file.
        root: Root node of the parsed Tree-sitter tree.

    Returns:
        A tuple of (imports, functions, methods, classes, calls).
    """
    imports: list[str] = []
    funcs: list[dict] = []
    methods: list[dict] = []
    classes: list[dict] = []
    calls: list[dict] = []

    def _visit(n: Node, class_name: str | None) -> None:
        if n.type == "import_statement":
            imports.append(text(src, n).strip())

        elif n.type == "class_declaration":
            name_node = child_by_field(n, "name")
            heritage = child_by_field(n, "superclass")
            cls_name = text(src, name_node) if name_node else "<anonymous>"
            classes.append(
                {
                    "name": cls_name,
                    "args": f"extends {text(src, heritage)}" if heritage else "",
                    "line": n.start_point[0] + 1,
                }
            )
            for child in n.children:
                _visit(child, cls_name)
            return  # children already visited above

        elif n.type == "variable_declarator":
            # Attach the declarator name to a directly-assigned arrow or function
            # expression, e.g. `const foo = (x) => x` or `const foo = function() {}`.
            value = child_by_field(n, "value")
            if value and value.type in {"arrow_function", "function_expression"}:
                var_name = child_by_field(n, "name")
                # Prefer the inline function name (e.g. `function named()`) but fall
                # back to the variable name, then to <anonymous>.
                fn_name_node = child_by_field(value, "name")
                name = (
                    text(src, fn_name_node)
                    if fn_name_node
                    else (text(src, var_name) if var_name else "<anonymous>")
                )
                params = child_by_field(value, "parameters") or child_by_field(
                    value, "parameter"
                )
                funcs.append(
                    {
                        "name": name,
                        "args": text(src, params) if params else "()",
                        "line": value.start_point[0] + 1,
                    }
                )
                # Recurse into the function body only, skipping the function node
                # itself so it isn't double-counted by the arrow_function branch.
                for child in value.children:
                    _visit(child, class_name)
                return  # children already visited above

        elif n.type in {
            "function_declaration",
            "function_expression",
            "generator_function_declaration",
        }:
            name_node = child_by_field(n, "name")
            params = child_by_field(n, "parameters")
            funcs.append(
                {
                    "name": text(src, name_node) if name_node else "<anonymous>",
                    "args": text(src, params) if params else "()",
                    "line": n.start_point[0] + 1,
                }
            )

        elif n.type in {"method_definition", "public_field_definition"}:
            name_node = child_by_field(n, "name")
            params = child_by_field(n, "parameters")
            if name_node:
                entry = {
                    "name": text(src, name_node),
                    "args": text(src, params) if params else "()",
                    "line": n.start_point[0] + 1,
                }
                if class_name is not None:
                    methods.append({**entry, "class": class_name})
                else:
                    funcs.append(entry)

        elif n.type == "arrow_function":
            params = child_by_field(n, "parameters") or child_by_field(n, "parameter")
            funcs.append(
                {
                    "name": "<arrow_function>",
                    "args": text(src, params) if params else "()",
                    "line": n.start_point[0] + 1,
                }
            )

        elif n.type == "call_expression":
            fn = child_by_field(n, "function")
            args_node = child_by_field(n, "arguments")
            if fn:
                calls.append(
                    {
                        "name": text(src, fn).strip(),
                        "args": format_args(src, args_node) if args_node else "()",
                        "line": n.start_point[0] + 1,
                    }
                )

        elif n.type == "new_expression":
            ctor = child_by_field(n, "constructor")
            args_node = child_by_field(n, "arguments")
            if ctor:
                calls.append(
                    {
                        "name": f"new {text(src, ctor).strip()}",
                        "args": format_args(src, args_node) if args_node else "()",
                        "line": n.start_point[0] + 1,
                    }
                )

        for child in n.children:
            _visit(child, class_name)

    _visit(root, class_name=None)
    return imports, funcs, methods, classes, calls


def unique(items: list) -> list:
    """Return items with duplicates removed, preserving order.

    Args:
        items: A list of JSON-serialisable values.

    Returns:
        Deduplicated list in original order.
    """
    seen: set[str] = set()
    out = []
    for item in items:
        key = json.dumps(item, sort_keys=True)
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def main() -> None:
    """Entry point: parse arguments, run analysis, and print the summary."""
    ap = argparse.ArgumentParser(
        description="Summarize one Python/JS/TS file using Tree-sitter.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("file", type=Path)
    ap.add_argument(
        "--json", action="store_true", default=False, help="Emit JSON instead of text"
    )
    ap.add_argument(
        "--include-calls",
        action="store_true",
        default=False,
        help="Include the 'Functions/methods called' section in output",
    )
    args = ap.parse_args()

    path = args.file
    lang = LANG_BY_SUFFIX.get(path.suffix.lower())
    if not lang:
        raise SystemExit(f"Unsupported suffix: {path.suffix}")

    src = path.read_bytes()

    tree = get_parser(lang).parse(src)
    root = tree.root_node

    if lang == "python":
        imports, funcs, methods, classes, calls = py_summary(src, root)
    else:
        imports, funcs, methods, classes, calls = js_ts_summary(src, root)

    result = {
        "file": str(path),
        "language": lang,
        "imports": unique(imports),
        "functions": unique(funcs),
        "methods": unique(methods),
        "classes": unique(classes),
    }
    if args.include_calls:
        result["calls"] = unique(calls)

    if args.json:
        print(json.dumps(result, indent=2))
        return

    print(f"# Summary: {path}\n")
    print("## Imports")

    print("\n".join(f"- {x}" for x in result["imports"]) or "- None")

    print("\n## Function definitions")
    print(
        "\n".join(
            f"- {f['name']}{f['args']}  [line {f['line']}]" for f in result["functions"]
        )
        or "- None"
    )

    print("\n## Class definitions")
    print(
        "\n".join(
            f"- {c['name']}{c['args']}  [line {c['line']}]" for c in result["classes"]
        )
        or "- None"
    )

    print("\n## Class method definitions")
    print(
        "\n".join(
            f"- {m['class']}.{m['name']}{m['args']}  [line {m['line']}]"
            for m in result["methods"]
        )
        or "- None"
    )

    if args.include_calls:
        print("\n## Functions/methods called")
        print(
            "\n".join(
                f"- {c['name']}{c['args']}  [line {c['line']}]" for c in result["calls"]
            )
            or "- None"
        )


if __name__ == "__main__":
    main()
