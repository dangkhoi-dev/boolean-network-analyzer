"""Tests for STG construction and attractor detection."""

from bnanalyzer import (
    BooleanNetwork,
    build_state_transition_graph,
    find_attractors,
)


def test_bistable_toggle_two_fixed_points():
    """A,!B / B,!A under sync update has 2 fixed points (1,0) and (0,1)
    plus a sync 2-cycle between (0,0) and (1,1)."""
    net = BooleanNetwork.from_bnet("A, !B\nB, !A")
    g = build_state_transition_graph(net, scheme="synchronous")
    attractors = find_attractors(g, scheme="synchronous")
    fixed = [a for a in attractors if a.kind == "fixed_point"]
    cyclic = [a for a in attractors if a.kind == "cyclic"]
    fp_states = {a.states[0] for a in fixed}
    assert (True, False) in fp_states
    assert (False, True) in fp_states
    # the (0,0)<->(1,1) two-cycle
    assert any(set(c.states) == {(False, False), (True, True)} for c in cyclic)


def test_bistable_toggle_async_two_fixed_points():
    """Under async update, only the two fixed points remain — (0,0) and
    (1,1) are not stuck because either node can flip."""
    net = BooleanNetwork.from_bnet("A, !B\nB, !A")
    g = build_state_transition_graph(net, scheme="asynchronous")
    attractors = find_attractors(g, scheme="asynchronous")
    assert len(attractors) == 2
    assert all(a.kind == "fixed_point" for a in attractors)


def test_repressilator_sync_cycle_length_six():
    """A,!C / B,!A / C,!B under sync produces a single 6-cycle attractor
    (after the all-0 -> all-1 -> all-0 short cycle is also accounted for)."""
    net = BooleanNetwork.from_bnet("A, !C\nB, !A\nC, !B")
    g = build_state_transition_graph(net, scheme="synchronous")
    attractors = find_attractors(g, scheme="synchronous")
    # The 8 states partition into a length-6 cycle plus a length-2 cycle.
    sizes = sorted(len(a.states) for a in attractors)
    assert 6 in sizes
    assert 2 in sizes


def test_constant_one_input_yields_fixed_point():
    """A node whose update rule is constant True must end at a state where
    A=True; check that the attractor reflects this."""
    net = BooleanNetwork.from_bnet("A, 1\nB, A")
    g = build_state_transition_graph(net, scheme="synchronous")
    attractors = find_attractors(g, scheme="synchronous")
    assert len(attractors) == 1
    assert attractors[0].kind == "fixed_point"
    assert attractors[0].states[0] == (True, True)


def test_async_self_loop_on_fixed_point():
    """In the async STG, fixed points appear as nodes with a self-loop."""
    net = BooleanNetwork.from_bnet("A, !B\nB, !A")
    g = build_state_transition_graph(net, scheme="asynchronous")
    # (1,0) is a fixed point — must have a self-loop
    assert g.has_edge((True, False), (True, False))


def test_synchronous_outdegree_one():
    net = BooleanNetwork.from_bnet("A, !B\nB, A\nC, B & !A")
    g = build_state_transition_graph(net, scheme="synchronous")
    for n in g.nodes:
        assert g.out_degree(n) == 1
