"""Tests for the BooleanNetwork class."""

from bnanalyzer import BooleanNetwork


def test_evaluate_simple_toggle():
    net = BooleanNetwork.from_bnet("A, !B\nB, !A")
    # (False, False) -> A=!False=True, B=!False=True -> (True, True)
    assert net.evaluate_all((False, False)) == (True, True)
    # (True, True) -> A=!True=False, B=!True=False -> (False, False)
    assert net.evaluate_all((True, True)) == (False, False)
    # (True, False) -> A=!False=True, B=!True=False -> (True, False)  fixed point
    assert net.evaluate_all((True, False)) == (True, False)


def test_state_string_round_trip():
    net = BooleanNetwork.from_bnet("A, !B\nB, A\nC, B")
    s = (True, False, True)
    assert net.state_to_str(s) == "101"
    assert net.str_to_state("101") == s


def test_influence_graph_signs():
    net = BooleanNetwork.from_bnet("A, !B\nB, A")
    g = net.influence_graph()
    assert g.has_edge("B", "A")
    assert g["B"]["A"]["sign"] == "-"
    assert g.has_edge("A", "B")
    assert g["A"]["B"]["sign"] == "+"


def test_all_states_count():
    net = BooleanNetwork.from_bnet("A, !B\nB, A")
    states = list(net.all_states())
    assert len(states) == 4
    assert len(set(states)) == 4
