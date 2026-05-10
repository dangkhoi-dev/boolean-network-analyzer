"""Unit tests for the .bnet parser."""

import pytest

from bnanalyzer.parser import BNetParseError, parse_bnet


def test_parses_simple_two_node():
    src = """
    targets, factors
    A, !B
    B, A
    """
    rules = parse_bnet(src)
    assert set(rules) == {"A", "B"}
    assert rules["A"].inputs == ("B",)
    assert rules["B"].inputs == ("A",)
    assert "not" in rules["A"].python_expression


def test_strips_inline_comments():
    src = """
    A, !B  # toggle
    B, A   # cascade
    """
    rules = parse_bnet(src)
    assert rules["A"].expression == "!B"


def test_constants_recognised():
    src = "A, 1\nB, 0"
    rules = parse_bnet(src)
    assert "True" in rules["A"].python_expression
    assert "False" in rules["B"].python_expression


def test_dangling_input_rejected():
    src = "A, B"
    with pytest.raises(BNetParseError):
        parse_bnet(src)


def test_duplicate_target_rejected():
    src = "A, B\nB, A\nA, B"
    with pytest.raises(BNetParseError):
        parse_bnet(src)


def test_empty_source_rejected():
    with pytest.raises(BNetParseError):
        parse_bnet("# only comments\n")


def test_word_operators_supported():
    src = "A, not B\nB, A and not B"
    rules = parse_bnet(src)
    assert rules["A"].inputs == ("B",)


def test_double_operators():
    src = "A, !B\nB, A && !A"  # tautology-ish but must parse
    rules = parse_bnet(src)
    assert "and" in rules["B"].python_expression
