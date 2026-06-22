#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "tree-sitter",
#   "tree-sitter-python",
#   "tree-sitter-javascript",
#   "tree-sitter-typescript",
#   "tree-sitter-c-sharp",
# ]
# ///

"""
CLI tool giving a concise summary of a python, js, ts, or C# file by listing its imports,
function definitions, class definitions, class method definitions,
function/method calls and attached code comments/docstrings (using tree-sitter).

To make available globally:
    1. chmod +x script_summary.py
    2. ln -s /home/josephbbolton/command_line_tools/script_summary.py ~/.local/bin/script_summary
    3. Now you can run `script_summary --help` from any folder
"""

import argparse
import json
from pathlib import Path

import tree_sitter_c_sharp as _tscs
import tree_sitter_javascript as _tsjs
import tree_sitter_python as _tspy
import tree_sitter_typescript as _tsts
from tree_sitter import Language, Node, Parser


_LANGUAGES: dict[str, Language] = {
    "python": Language(_tspy.language()),
    "javascript": Language(_tsjs.language()),
    "typescript": Language(_tsts.language_typescript()),
    "tsx": Language(_tsts.language_tsx()),
    "csharp": Language(_tscs.language()),
}

LANG_BY_SUFFIX: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".cs": "csharp",
    ".csx": "csharp",
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
                        if (
                            raw.startswith(q)
                            and raw.endswith(q)
                            and len(raw) > 2 * len(q) - 1
                        ):
                            return raw[len(q) : -len(q)].strip()
                    return raw.strip()
        break  # docstring must be the very first statement
    return None


def _js_file_doc(src: bytes, root: Node) -> str | None:
    """Return the file-level JSDoc comment from a JS/TS program node, or None.

    Scans forward through the root's named children and returns the first
    ``/** ... */`` block comment that appears before any import or declaration,
    skipping only shebangs (``hash_bang_line``).

    Args:
        src: Raw source bytes of the file.
        root: The ``program`` root node.

    Returns:
        The stripped JSDoc text (without ``/** */`` delimiters), or None.
    """
    for child in root.named_children:
        if child.type == "hash_bang_line":
            continue
        raw = text(src, child).strip()
        if child.type == "comment" and raw.startswith("/**") and raw.endswith("*/"):
            inner = raw[3:-2].strip()
            lines = [ln.strip().lstrip("* ").lstrip("*") for ln in inner.splitlines()]
            return "\n".join(lines).strip() or None
        break  # first non-shebang, non-comment node — no file-level doc
    return None


def _jsdoc_comment(src: bytes, node: Node) -> str | None:
    """Return the JSDoc comment text for a JS/TS node, or None.

    Walks backwards through the node's preceding siblings to find an
    immediately adjacent ``/** ... */`` block comment. Also checks the
    parent ``export_statement``'s preceding siblings, so that JSDoc on
    ``export function foo()`` / ``export class Bar`` is correctly resolved.

    Args:
        src: Raw source bytes of the file.
        node: The function, class, method, or type declaration node.

    Returns:
        The stripped JSDoc text (without the /** */ delimiters), or None.
    """
    def _extract_jsdoc(raw: str) -> str | None:
        if raw.startswith("/**") and raw.endswith("*/"):
            inner = raw[3:-2].strip()
            lines = [ln.strip().lstrip("* ").lstrip("*") for ln in inner.splitlines()]
            return "\n".join(lines).strip() or None
        return None

    def _scan_siblings(target: Node) -> str | None:
        parent = target.parent
        if parent is None:
            return None
        siblings = parent.children
        idx = next((i for i, c in enumerate(siblings) if c.id == target.id), None)
        if idx is None:
            return None
        # Scan backwards; skip unnamed whitespace nodes; stop on any named
        # node that is not a comment (e.g. another declaration).
        for i in range(idx - 1, -1, -1):
            sib = siblings[i]
            if not sib.is_named:
                continue  # unnamed whitespace/punctuation — skip
            raw = text(src, sib).strip()
            if sib.type == "comment":
                result = _extract_jsdoc(raw)
                if result:
                    return result
                break  # non-JSDoc comment (e.g. //) — stop
            break  # any other named node — stop
        return None

    # First try the node itself, then its parent export_statement (if any)
    result = _scan_siblings(node)
    if result is None and node.parent and node.parent.type == "export_statement":
        result = _scan_siblings(node.parent)
    return result


def _cs_xml_doc(src: bytes, node: Node) -> str | None:
    """Return the XML doc comment text immediately preceding a C# node, or None.

    Collects consecutive ``///`` single-line comment siblings that appear
    directly before the node (skipping no named nodes in between), strips the
    ``///`` prefix from each line, and joins them into a single string.

    Args:
        src: Raw source bytes of the file.
        node: The declaration node (class, method, property, enum, …).

    Returns:
        The joined doc-comment text, or None if no ``///`` block precedes the node.
    """
    parent = node.parent
    if parent is None:
        return None
    siblings = parent.children
    idx = next((i for i, c in enumerate(siblings) if c.id == node.id), None)
    if idx is None:
        return None
    # Collect consecutive /// comment siblings immediately before this node.
    doc_lines: list[str] = []
    for i in range(idx - 1, -1, -1):
        sib = siblings[i]
        if not sib.is_named:
            continue  # skip whitespace tokens
        raw = text(src, sib).strip()
        if sib.type == "comment" and raw.startswith("///"):
            # Strip leading /// and optional single space
            line = raw[3:]
            if line.startswith(" "):
                line = line[1:]
            doc_lines.append(line)
        else:
            break  # non-doc-comment named node — stop
    if not doc_lines:
        return None
    doc_lines.reverse()
    return _cs_strip_xml_tags("\n".join(doc_lines)) or None


def _cs_file_doc(src: bytes, root: Node) -> str | None:
    """Return the file-level doc comment from a C# compilation_unit, or None.

    Accepts two forms, both of which must appear after all ``using`` directives
    and before the first ``namespace`` or type declaration:

    1. Consecutive ``///`` single-line XML doc comments (existing behaviour).
    2. A single ``/* ... */`` block comment (e.g. a SignalR message-flow doc or
       any other intentional file-level prose).  Block comments that appear
       inside method or class bodies are excluded by the position constraint —
       only a ``/* */`` node that is a direct child of ``compilation_unit``
       after the ``using`` directives qualifies.

    Args:
        src: Raw source bytes of the file.
        root: The ``compilation_unit`` root node.

    Returns:
        The stripped doc-comment text, or None.
    """
    _NON_DOC_TYPES = {
        "namespace_declaration",
        "file_scoped_namespace_declaration",
        "class_declaration",
        "interface_declaration",
        "enum_declaration",
        "record_declaration",
        "struct_declaration",
    }
    doc_lines: list[str] = []
    block_doc: str | None = None

    for child in root.children:
        if not child.is_named:
            continue
        if child.type == "using_directive":
            # Skip past using directives before looking for a doc comment.
            # Reset any partial /// accumulation — usings may not precede ///.
            doc_lines = []
            block_doc = None
            continue
        raw = text(src, child).strip()
        if child.type == "comment" and raw.startswith("///"):
            line = raw[3:]
            if line.startswith(" "):
                line = line[1:]
            doc_lines.append(line)
        elif child.type == "comment" and raw.startswith("/*") and raw.endswith("*/") and not doc_lines:
            # Single /* */ block comment — treat as file-level doc.
            inner = raw[2:-2].strip()
            block_doc = inner or None
        else:
            break  # first non-comment named node (namespace / type) — stop

    if doc_lines:
        return _cs_strip_xml_tags("\n".join(doc_lines)) or None
    if block_doc:
        return block_doc
    return None


def _cs_strip_xml_tags(text_: str) -> str:
    """Strip XML tags from a string, keeping their text content."""
    import re
    return re.sub(r"<[^>]+>", "", text_).strip()


def _cs_attributes(src: bytes, node: Node) -> list[str]:
    """Return a list of attribute strings for a C# declaration node.

    Collects all ``attribute_list`` children of the node and renders each
    attribute as its full source text (e.g. ``[HttpGet]``,
    ``[Route("users")]``).

    Args:
        src: Raw source bytes of the file.
        node: The declaration node whose attributes to collect.

    Returns:
        List of attribute strings, each including the surrounding brackets.
    """
    attrs: list[str] = []
    for child in node.children:
        if child.type == "attribute_list":
            attrs.append(text(src, child).strip())
    return attrs


def _cs_modifiers(src: bytes, node: Node) -> list[str]:
    """Return all modifier keywords for a C# declaration node.

    Args:
        src: Raw source bytes of the file.
        node: The declaration node.

    Returns:
        List of modifier strings, e.g. ``["public", "async"]``.
    """
    mods: list[str] = []
    for child in node.children:
        if child.type == "modifier":
            mods.append(text(src, child).strip())
    return mods


def cs_summary(src: bytes, root: Node, include_docstrings: bool = True) -> _Summary:
    """Extract imports, functions, methods, classes, and properties from a C# AST.

    Captures (per the C# summary checklist):
    - ``using`` directives as imports
    - Class / interface / enum / record / struct declarations (with attributes,
      base list, modifiers, XML doc)
    - Public/protected constructors and methods (with return type, parameters,
      attributes, modifiers, XML doc)
    - Public/protected properties (with type, accessor shape, attributes, XML doc)
    - Enum members (with values)

    Private members and method bodies are intentionally omitted.

    Args:
        src: Raw source bytes of the file.
        root: Root node of the parsed Tree-sitter tree.
        include_docstrings: When True, attach XML doc comments to entries.

    Returns:
        A tuple of (imports, functions, methods, classes, calls).
        ``functions`` holds public/protected top-level or standalone members.
        ``calls`` is always empty (not extracted for C#).
    """
    imports: list[str] = []
    funcs: list[dict] = []
    methods: list[dict] = []
    classes: list[dict] = []
    calls: list[dict] = []  # not extracted for C#

    _PUBLIC_LIKE = {"public", "protected", "protected internal"}

    def _is_visible(node: Node) -> bool:
        mods = set(_cs_modifiers(src, node))
        return bool(mods & _PUBLIC_LIKE)

    def _maybe_doc(node: Node) -> dict:
        if include_docstrings:
            doc = _cs_xml_doc(src, node)
            if doc:
                return {"docstring": doc}
        return {}

    def _visit(n: Node, class_name: str | None) -> None:
        # ── using directives ──────────────────────────────────────────────────
        if n.type == "using_directive":
            imports.append(text(src, n).strip())

        # ── type declarations ─────────────────────────────────────────────────
        elif n.type in {
            "class_declaration",
            "interface_declaration",
            "enum_declaration",
            "record_declaration",
            "struct_declaration",
        }:
            name_node = n.child_by_field_name("name")
            cls_name = text(src, name_node) if name_node else "<anonymous>"

            mods = _cs_modifiers(src, n)
            kw = n.type.replace("_declaration", "")  # "class", "interface", …

            base_list_node = next(
                (c for c in n.children if c.type == "base_list"), None
            )
            bases = text(src, base_list_node).lstrip(": ").strip() if base_list_node else ""

            type_params_node = n.child_by_field_name("type_parameters")
            generic = text(src, type_params_node) if type_params_node else ""

            attrs = _cs_attributes(src, n)

            entry: dict = {
                "name": cls_name + generic,
                "kind": kw,
                "modifiers": mods,
                "bases": bases,
                "attributes": attrs,
                "line": n.start_point[0] + 1,
                **_maybe_doc(n),
            }

            # For enums, capture members inline
            if n.type == "enum_declaration":
                body = n.child_by_field_name("body")
                if body:
                    members: list[dict] = []
                    for child in body.children:
                        if child.type == "enum_member_declaration":
                            m_name = child.child_by_field_name("name")
                            m_val = child.child_by_field_name("value")
                            m_entry: dict = {
                                "name": text(src, m_name) if m_name else "?",
                            }
                            if m_val:
                                m_entry["value"] = text(src, m_val).strip()
                            if include_docstrings:
                                m_doc = _cs_xml_doc(src, child)
                                if m_doc:
                                    m_entry["docstring"] = m_doc
                            members.append(m_entry)
                    entry["members"] = members

            classes.append(entry)

            # Recurse into body
            body_field = n.child_by_field_name("body")
            if body_field:
                for child in body_field.children:
                    _visit(child, cls_name)
            return

        # ── constructors ──────────────────────────────────────────────────────
        elif n.type == "constructor_declaration":
            if not _is_visible(n):
                return
            name_node = n.child_by_field_name("name")
            params_node = n.child_by_field_name("parameters")
            entry = {
                "name": text(src, name_node) if name_node else "<ctor>",
                "args": text(src, params_node).strip() if params_node else "()",
                "modifiers": _cs_modifiers(src, n),
                "attributes": _cs_attributes(src, n),
                "line": n.start_point[0] + 1,
                **_maybe_doc(n),
            }
            if class_name is not None:
                methods.append({**entry, "class": class_name, "kind": "constructor"})
            else:
                funcs.append({**entry, "kind": "constructor"})

        # ── methods ───────────────────────────────────────────────────────────
        elif n.type == "method_declaration":
            if not _is_visible(n):
                return
            name_node = n.child_by_field_name("name")
            params_node = n.child_by_field_name("parameters")
            ret_node = n.child_by_field_name("returns")
            type_params_node = n.child_by_field_name("type_parameters")
            generic = text(src, type_params_node) if type_params_node else ""
            entry = {
                "name": (text(src, name_node) if name_node else "<method>") + generic,
                "args": text(src, params_node).strip() if params_node else "()",
                "returns": text(src, ret_node).strip() if ret_node else "",
                "modifiers": _cs_modifiers(src, n),
                "attributes": _cs_attributes(src, n),
                "line": n.start_point[0] + 1,
                **_maybe_doc(n),
            }
            if class_name is not None:
                methods.append({**entry, "class": class_name, "kind": "method"})
            else:
                funcs.append({**entry, "kind": "method"})

        # ── properties ────────────────────────────────────────────────────────
        elif n.type == "property_declaration":
            if not _is_visible(n):
                return
            name_node = n.child_by_field_name("name")
            type_node = n.child_by_field_name("type")
            accessors_node = n.child_by_field_name("accessors")
            # Summarise accessor shape: "{ get; set; }", "{ get; init; }", etc.
            accessors_str = ""
            if accessors_node:
                acc_kws = []
                for c in accessors_node.named_children:
                    if c.type == "get_accessor_declaration":
                        acc_kws.append("get")
                    elif c.type == "set_accessor_declaration":
                        acc_kws.append("set")
                    elif c.type == "init_accessor_declaration":
                        acc_kws.append("init")
                accessors_str = (
                    "{ " + "; ".join(acc_kws) + "; }" if acc_kws
                    else text(src, accessors_node).strip()
                )
            entry = {
                "name": text(src, name_node) if name_node else "<prop>",
                "type": text(src, type_node).strip() if type_node else "",
                "accessors": accessors_str,
                "modifiers": _cs_modifiers(src, n),
                "attributes": _cs_attributes(src, n),
                "line": n.start_point[0] + 1,
                **_maybe_doc(n),
            }
            if class_name is not None:
                methods.append({**entry, "class": class_name, "kind": "property"})
            else:
                funcs.append({**entry, "kind": "property"})

        else:
            for child in n.children:
                _visit(child, class_name)

    _visit(root, class_name=None)
    return imports, funcs, methods, classes, calls


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


def _in_function_body(node: Node) -> bool:
    """Return True if *node* is nested inside a function/method body.

    Walks the ancestor chain and returns True as soon as a ``statement_block``
    is found.  This distinguishes closures defined inside a function body from
    genuine module-level (or class-level) declarations.

    ``class_body`` is intentionally not treated as a function body — methods
    defined directly on a class are always captured regardless.

    Args:
        node: The node to test.

    Returns:
        True if any ancestor is a ``statement_block``, False otherwise.
    """
    n = node.parent
    while n is not None:
        if n.type == "statement_block":
            return True
        n = n.parent
    return False


def js_ts_summary(src: bytes, root: Node, include_docstrings: bool = True) -> _Summary:
    """Extract imports, functions, methods, classes, and calls from a JS/TS AST.

    Methods (method_definition, public_field_definition) are always children of
    a class_body, so the enclosing class name is tracked via recursive descent.
    Closures defined inside a function body (i.e. with a ``statement_block``
    ancestor) are excluded — only module-level and class-level declarations are
    captured.

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

        elif n.type == "interface_declaration":
            name_node = child_by_field(n, "name")
            heritage = child_by_field(n, "extends_clause")
            iface_name = text(src, name_node) if name_node else "<anonymous>"
            type_params = child_by_field(n, "type_parameters")
            generic = text(src, type_params) if type_params else ""
            classes.append(
                {
                    "name": iface_name + generic,
                    "args": text(src, heritage).strip() if heritage else "",
                    "line": n.start_point[0] + 1,
                    **_maybe_doc(n),
                }
            )
            body = child_by_field(n, "body")
            if body:
                for child in body.children:
                    _visit(child, iface_name)
            return

        elif n.type in {"method_signature", "property_signature"}:
            # Interface members (TS)
            name_node = child_by_field(n, "name")
            params = child_by_field(n, "parameters")
            if name_node:
                args = text(src, params) if params else ("" if n.type == "property_signature" else "()")
                entry = {
                    "name": text(src, name_node),
                    "args": args,
                    "line": n.start_point[0] + 1,
                    **_maybe_doc(n),
                }
                if class_name is not None:
                    methods.append({**entry, "class": class_name})
                else:
                    funcs.append(entry)

        elif n.type == "type_alias_declaration":
            # e.g. `type UserId = string` — capture as a class-like entry
            name_node = child_by_field(n, "name")
            type_params = child_by_field(n, "type_parameters")
            generic = text(src, type_params) if type_params else ""
            if name_node:
                classes.append(
                    {
                        "name": text(src, name_node) + generic,
                        "args": "type alias",
                        "line": n.start_point[0] + 1,
                        **_maybe_doc(n),
                    }
                )

        elif n.type == "enum_declaration":
            name_node = child_by_field(n, "name")
            if name_node:
                classes.append(
                    {
                        "name": text(src, name_node),
                        "args": "enum",
                        "line": n.start_point[0] + 1,
                        **_maybe_doc(n),
                    }
                )

        elif n.type == "variable_declarator":
            # Attach the declarator name to a directly-assigned arrow or function
            # expression, e.g. `const foo = (x) => x` or `const foo = function() {}`.
            # Skip closures defined inside a function body — they are implementation
            # details, not module-level interface.
            if _in_function_body(n):
                return
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
            # Skip functions declared inside another function body.
            if _in_function_body(n):
                for child in n.children:
                    _visit(child, class_name)
                return
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
                # public_field_definition is a class property — omit args if no params
                args = text(src, params) if params else ("" if n.type == "public_field_definition" else "()")
                entry = {
                    "name": text(src, name_node),
                    "args": args,
                    "line": n.start_point[0] + 1,
                    **_maybe_doc(n),
                }
                if class_name is not None:
                    methods.append({**entry, "class": class_name})
                else:
                    funcs.append(entry)

        elif n.type == "arrow_function":
            # Skip arrow functions inside a function body (closures / callbacks).
            if _in_function_body(n):
                return
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
        description="Summarize one Python/JS/TS/C# file using Tree-sitter.",
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
        help="Omit docstrings (Python), JSDoc comments (JS/TS), and XML doc comments (C#) from output",
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
        imports, funcs, methods, classes, calls = py_summary(
            src, root, include_docstrings=include_docs
        )
        module_doc = _py_docstring(src, root) if include_docs else None
    elif lang == "csharp":
        imports, funcs, methods, classes, calls = cs_summary(
            src, root, include_docstrings=include_docs
        )
        module_doc = _cs_file_doc(src, root) if include_docs else None
    else:
        imports, funcs, methods, classes, calls = js_ts_summary(
            src, root, include_docstrings=include_docs
        )
        module_doc = _js_file_doc(src, root) if include_docs else None

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
        if lang == "csharp":
            print(f'/// {first_line}\n')
        elif lang in ("javascript", "typescript", "tsx"):
            print(f'/** {first_line} */\n')
        else:
            print(f'"""{first_line}"""\n')

    print("## Imports")
    print("\n".join(f"- {x}" for x in result["imports"]) or "- None")

    def _fmt_doc(doc: str) -> str:
        first_line = doc.splitlines()[0] if doc else ""
        if lang == "python":
            return f'  """{first_line}"""'
        elif lang == "csharp":
            return f"  /// {first_line}"
        else:
            return f"  /** {first_line} */"

    def _fmt_entry(e: dict, prefix: str = "") -> str:
        if lang == "csharp":
            kind = e.get("kind", "")
            attrs = e.get("attributes", [])
            mods = " ".join(e.get("modifiers", []))
            attrs_str = " ".join(attrs) + " " if attrs else ""

            if kind == "property":
                sig = f"{mods} {e.get('type', '')} {prefix}{e['name']} {e.get('accessors', '')}".strip()
            elif kind in ("method", "constructor"):
                ret = e.get("returns", "")
                ret_str = f"{ret} " if ret else ""
                sig = f"{mods} {ret_str}{prefix}{e['name']}{e['args']}".strip()
            else:
                # class / interface / enum / record / struct
                bases = e.get("bases", "")
                bases_str = f" : {bases}" if bases else ""
                sig = f"{mods} {e.get('kind', '')} {prefix}{e['name']}{bases_str}".strip()

            line = f"- {attrs_str}{sig}  [line {e['line']}]"
        else:
            line = f"- {prefix}{e['name']}{e['args']}  [line {e['line']}]"

        if "docstring" in e:
            line += f"\n{_fmt_doc(e['docstring'])}"
        return line

    def _fmt_class_entry(e: dict) -> str:
        lines = [_fmt_entry(e)]
        # For C# enums, show members indented
        if lang == "csharp" and "members" in e:
            for m in e["members"]:
                val_str = f" = {m['value']}" if "value" in m else ""
                doc_str = f"  // {m['docstring'].splitlines()[0]}" if "docstring" in m else ""
                lines.append(f"  - {m['name']}{val_str}{doc_str}")
        return "\n".join(lines)

    print("\n## Function definitions")
    print("\n".join(_fmt_entry(f) for f in result["functions"]) or "- None")

    print("\n## Class definitions")
    print("\n".join(_fmt_class_entry(c) for c in result["classes"]) or "- None")

    print("\n## Class method definitions")
    print(
        "\n".join(
            _fmt_entry(m, prefix=f"{m['class']}." if "class" in m else "")
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
