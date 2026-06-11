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


def _py_docstring(src: bytes, body: Node) -> str | None:
    """Return the docstring text from a Python function/class body node, or None.

    The docstring is the first expression_statement child whose value is a
    string literal.

    Args:
        src: Raw source bytes of the file.
        body: The block / suite node that is the function or class body.

    Returns:
        The stripped docstring text, or None if no docstring is present.
    """
    for child in body.named_children:
        if child.type == "expression_statement":
            for sub in child.named_children:
                if sub.type == "string":
                    raw = text(src, sub)
                    # Strip surrounding quotes (""", ''', ", ')
                    for q in ('"""', "'''", '"', "'"):
                        if raw.startswith(q) and raw.endswith(q) and len(raw) > 2 * len(q) - 1:
                            return raw[len(q) : -len(q)].strip()
                    return raw.strip()
        break  # docstring must be the very first statement
    return None


def _jsdoc_comment(src: bytes, node: Node) -> str | None:
    """Return the JSDoc comment text for a JS/TS node, or None.

    Walks backwards through the node's preceding siblings to find an
    immediately adjacent ``/** ... */`` block comment.

    Args:
        src: Raw source bytes of the file.
        node: The function, class, or method declaration node.

    Returns:
        The stripped JSDoc text (without the /** */ delimiters), or None.
    """
    parent = node.parent
    if parent is None:
        return None
    siblings = parent.children
    idx = next((i for i, c in enumerate(siblings) if c.id == node.id), None)
    if idx is None:
        return None
    # Scan backwards; skip only whitespace/newline nodes (unnamed)
    for i in range(idx - 1, -1, -1):
        sib = siblings[i]
        if sib.is_named:
            break  # named non-comment node — no JSDoc
        raw = text(src, sib).strip()
        if raw.startswith("/**") and raw.endswith("*/"):
            inner = raw[3:-2].strip()
            # Strip leading " * " from each line
            lines = [ln.strip().lstrip("* ").lstrip("*") for ln in inner.splitlines()]
            return "\n".join(lines).strip()
    return None


def py_summary(src: bytes, root: Node, include_docstrings: bool = True) -> _Summary:
    """Extract imports, functions, methods, classes, and calls from a Python AST.

    Methods are distinguished from standalone functions by checking whether their
    parent block belongs to a class_definition.

    Args:
        src: Raw source bytes of the file.
        root: Root node of the parsed Tree-sitter tree.
        include_docstrings: When True, attach docstrings to entries.

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
            entry: dict = {
                "name": cls_name,
                "args": text(src, supers) if supers else "",
                "line": n.start_point[0] + 1,
            }
            if include_docstrings:
                body = child_by_field(n, "body")
                doc = _py_docstring(src, body) if body else None
                if doc:
                    entry["docstring"] = doc
            classes.append(entry)
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
            if include_docstrings:
                body = child_by_field(n, "body")
                doc = _py_docstring(src, body) if body else None
                if doc:
                    entry["docstring"] = doc
            if class_name is not None:
                methods.append({**entry, "class": class_name})
            else:
                funcs.append(entry)

        elif n.type == "lambda":
            # Resolve the name from the enclosing assignment if possible,
            # e.g. `f = lambda x: x` → name "f"; otherwise "<lambda>".
            params = child_by_field(n, "parameters")
            # lambda_parameters has no surrounding parens, so add them.
            args_str = f"({text(src, params)})" if params else "()"
            name = "<lambda>"
            parent = n.parent
            if parent is not None and parent.type == "assignment":
                left = child_by_field(parent, "left")
                if left is not None:
                    name = text(src, left)
            entry = {
                "name": name,
                "args": args_str,
                "line": n.start_point[0] + 1,
            }
            if class_name is not None:
                methods.append({**entry, "class": class_name})
            else:
                funcs.append(entry)
            return  # don't recurse — lambda body has no nested defs of interest

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


def js_ts_summary(src: bytes, root: Node, include_docstrings: bool = True) -> _Summary:
    """Extract imports, functions, methods, classes, and calls from a JS/TS AST.

    Methods (method_definition, public_field_definition) are always children of
    a class_body, so the enclosing class name is tracked via recursive descent.

    Args:
        src: Raw source bytes of the file.
        root: Root node of the parsed Tree-sitter tree.
        include_docstrings: When True, attach JSDoc comments to entries.

    Returns:
        A tuple of (imports, functions, methods, classes, calls).
    """
    imports: list[str] = []
    funcs: list[dict] = []
    methods: list[dict] = []
    classes: list[dict] = []
    calls: list[dict] = []

    def _maybe_doc(node: Node) -> dict:
        if include_docstrings:
            doc = _jsdoc_comment(src, node)
            if doc:
                return {"docstring": doc}
        return {}

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
                    **_maybe_doc(n),
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
                # JSDoc lives on the parent variable_declaration, not the declarator
                doc_node = n.parent if n.parent else n
                funcs.append(
                    {
                        "name": name,
                        "args": text(src, params) if params else "()",
                        "line": value.start_point[0] + 1,
                        **(_maybe_doc(doc_node)),
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
                    **_maybe_doc(n),
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
                    **_maybe_doc(n),
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
                    **_maybe_doc(n),
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
    ap.add_argument(
        "--no-docs",
        action="store_true",
        default=False,
        help="Omit docstrings (Python) and JSDoc comments (JS/TS) from output",
    )
    ap.add_argument(
        "--include-anonymous",
        action="store_true",
        default=False,
        help="Include anonymous lambdas (<lambda>) and arrow functions (<arrow_function>) in output",
    )
    args = ap.parse_args()

    include_docs = not args.no_docs

    path = args.file
    lang = LANG_BY_SUFFIX.get(path.suffix.lower())
    if not lang:
        raise SystemExit(f"Unsupported suffix: {path.suffix}")

    src = path.read_bytes()

    tree = get_parser(lang).parse(src)
    root = tree.root_node

    if lang == "python":
        imports, funcs, methods, classes, calls = py_summary(src, root, include_docstrings=include_docs)
        module_doc = _py_docstring(src, root) if include_docs else None
    else:
        imports, funcs, methods, classes, calls = js_ts_summary(src, root, include_docstrings=include_docs)
        module_doc = None

    _ANONYMOUS_NAMES = {"<lambda>", "<arrow_function>"}
    if not args.include_anonymous:
        funcs = [f for f in funcs if f["name"] not in _ANONYMOUS_NAMES]
        methods = [m for m in methods if m["name"] not in _ANONYMOUS_NAMES]

    result: dict = {
        "file": str(path),
        "language": lang,
    }
    if module_doc:
        result["module_docstring"] = module_doc
    result.update(
        {
            "imports": unique(imports),
            "functions": unique(funcs),
            "methods": unique(methods),
            "classes": unique(classes),
        }
    )
    if args.include_calls:
        result["calls"] = unique(calls)

    if args.json:
        print(json.dumps(result, indent=2))
        return

    print(f"# Summary: {path}\n")

    if module_doc:
        first_line = module_doc.splitlines()[0] if module_doc else ""
        print(f'"""{first_line}"""\n')

    print("## Imports")
    print("\n".join(f"- {x}" for x in result["imports"]) or "- None")

    def _fmt_doc(doc: str) -> str:
        first_line = doc.splitlines()[0] if doc else ""
        if lang == "python":
            return f'  """{first_line}"""'
        else:
            return f"  /** {first_line} */"

    def _fmt_entry(e: dict, prefix: str = "") -> str:
        line = f"- {prefix}{e['name']}{e['args']}  [line {e['line']}]"
        if "docstring" in e:
            line += f"\n{_fmt_doc(e['docstring'])}"
        return line

    print("\n## Function definitions")
    print(
        "\n".join(_fmt_entry(f) for f in result["functions"])
        or "- None"
    )

    print("\n## Class definitions")
    print(
        "\n".join(_fmt_entry(c) for c in result["classes"])
        or "- None"
    )

    print("\n## Class method definitions")
    print(
        "\n".join(
            _fmt_entry(m, prefix=f"{m['class']}.")
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
