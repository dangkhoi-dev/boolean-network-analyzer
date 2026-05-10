"""
Parser for `.bnet` files.

The bnet format (compatible with PyBoolNet / BoolNet) is a plain-text format
where each non-empty, non-comment line declares the update rule of one node:

    target, expression

Expressions support:
    - Variables  : valid Python-style identifiers
    - Constants  : 0, 1, true, false, True, False
    - Operators  : ! (not), & (and), | (or), parentheses
    - Whitespace and inline comments starting with `#`
    - The header line `targets, factors` is ignored.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple


class BNetParseError(ValueError):
    """Raised when a `.bnet` source cannot be parsed."""


_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_RESERVED = {"and", "or", "not", "True", "False"}
_HEADER_RE = re.compile(r"^\s*targets\s*,\s*factors\s*$", re.IGNORECASE)


@dataclass
class ParsedRule:
    """A single update rule extracted from a bnet source."""

    target: str
    expression: str  # original expression (unchanged, with bnet operators)
    python_expression: str  # Python-evaluatable form using `and`, `or`, `not`
    inputs: Tuple[str, ...]  # variable names referenced (deduplicated)


def _tokenize_expression(expr: str) -> List[str]:
    """Split an expression into a flat list of tokens preserving structure."""
    tokens: List[str] = []
    i = 0
    n = len(expr)
    while i < n:
        c = expr[i]
        if c.isspace():
            i += 1
            continue
        if c in "()":
            tokens.append(c)
            i += 1
            continue
        if c in "&|!":
            # also accept `&&` and `||`
            if i + 1 < n and expr[i + 1] == c and c in "&|":
                tokens.append(c * 2)
                i += 2
            else:
                tokens.append(c)
                i += 1
            continue
        m = _IDENT_RE.match(expr, i)
        if m:
            tokens.append(m.group(0))
            i = m.end()
            continue
        if c.isdigit():
            tokens.append(c)
            i += 1
            continue
        raise BNetParseError(f"Unexpected character {c!r} in expression: {expr!r}")
    return tokens


def _to_python(expr: str) -> Tuple[str, Tuple[str, ...]]:
    """Convert a bnet expression into a Python expression and collect identifiers.

    Returns (python_expression, sorted_unique_input_names).
    """
    tokens = _tokenize_expression(expr)
    out: List[str] = []
    inputs: Set[str] = set()
    for tok in tokens:
        if tok in ("&", "&&"):
            out.append(" and ")
        elif tok in ("|", "||"):
            out.append(" or ")
        elif tok == "!":
            out.append(" not ")
        elif tok in ("(", ")"):
            out.append(tok)
        elif tok in ("0",):
            out.append("False")
        elif tok in ("1",):
            out.append("True")
        elif _IDENT_RE.fullmatch(tok):
            low = tok.lower()
            if low in {"true", "false"}:
                out.append("True" if low == "true" else "False")
            elif low == "and":
                out.append(" and ")
            elif low == "or":
                out.append(" or ")
            elif low == "not":
                out.append(" not ")
            else:
                if tok in _RESERVED:
                    raise BNetParseError(
                        f"Reserved word {tok!r} cannot be used as variable name"
                    )
                inputs.add(tok)
                out.append(tok)
        else:
            raise BNetParseError(f"Unrecognized token {tok!r}")
    py_expr = "".join(out).strip()
    if not py_expr:
        raise BNetParseError("Empty expression")
    return py_expr, tuple(sorted(inputs))


def parse_bnet(source: str) -> Dict[str, ParsedRule]:
    """Parse a bnet source string into a mapping target_name -> ParsedRule.

    Raises ``BNetParseError`` on malformed input.
    """
    rules: Dict[str, ParsedRule] = {}
    for raw_lineno, raw_line in enumerate(source.splitlines(), start=1):
        # strip inline comments
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if _HEADER_RE.match(line):
            continue
        if "," not in line:
            raise BNetParseError(
                f"Line {raw_lineno}: expected 'target, expression' but got {raw_line!r}"
            )
        target_part, expr_part = line.split(",", 1)
        target = target_part.strip()
        expr = expr_part.strip()
        if not target:
            raise BNetParseError(f"Line {raw_lineno}: missing target name")
        if not _IDENT_RE.fullmatch(target):
            raise BNetParseError(
                f"Line {raw_lineno}: invalid target name {target!r}"
            )
        if target in _RESERVED:
            raise BNetParseError(
                f"Line {raw_lineno}: target name {target!r} is reserved"
            )
        if not expr:
            raise BNetParseError(f"Line {raw_lineno}: missing expression for {target}")
        if target in rules:
            raise BNetParseError(
                f"Line {raw_lineno}: duplicate update rule for {target!r}"
            )
        py_expr, inputs = _to_python(expr)
        # validate by attempting to compile
        try:
            compile(py_expr, "<bnet>", "eval")
        except SyntaxError as exc:
            raise BNetParseError(
                f"Line {raw_lineno}: invalid expression for {target!r}: {exc.msg}"
            ) from exc
        rules[target] = ParsedRule(
            target=target,
            expression=expr,
            python_expression=py_expr,
            inputs=inputs,
        )
    if not rules:
        raise BNetParseError("No update rules found in source")
    # cross-check: every input must be a declared target (or accept dangling inputs?)
    declared = set(rules.keys())
    for rule in rules.values():
        for inp in rule.inputs:
            if inp not in declared:
                raise BNetParseError(
                    f"Variable {inp!r} appears in rule for {rule.target!r} "
                    f"but has no update rule of its own"
                )
    return rules
