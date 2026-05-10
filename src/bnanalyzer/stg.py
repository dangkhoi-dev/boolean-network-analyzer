"""
State Transition Graph (STG) construction under synchronous and
asynchronous update schemes.
"""

from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple

import networkx as nx

from .network import BooleanNetwork, State


def synchronous_successor(net: BooleanNetwork, state: Sequence[bool]) -> State:
    """Single-step successor under fully synchronous update.

    Every node's rule is evaluated on the SAME current state and all values
    update at once.
    """
    return net.evaluate_all(state)


def asynchronous_successors(
    net: BooleanNetwork, state: Sequence[bool]
) -> List[State]:
    """All possible single-step successors under fully asynchronous update.

    For each node whose rule output differs from its current value, emit one
    successor state in which only that node has been flipped. If no node
    would change, the state is a fixed point and we return [state] itself
    (a self-loop) so the resulting STG is total.
    """
    next_full = net.evaluate_all(state)
    diffs = [i for i, (a, b) in enumerate(zip(state, next_full)) if a != b]
    if not diffs:
        return [tuple(state)]
    out: List[State] = []
    state_t = tuple(state)
    for i in diffs:
        new = list(state_t)
        new[i] = not new[i]
        out.append(tuple(new))
    return out


def build_state_transition_graph(
    net: BooleanNetwork, scheme: str = "synchronous", states: Iterable[State] | None = None
) -> nx.DiGraph:
    """Build the full STG under the given update scheme.

    Parameters
    ----------
    net : BooleanNetwork
    scheme : "synchronous" | "asynchronous"
    states : optional iterable of starting states. If None, the entire 2**n
        state space is enumerated.

    Returns
    -------
    nx.DiGraph
        Nodes are state tuples; edges represent transitions. Node labels
        (``label`` attribute) carry the binary string. For synchronous mode,
        each node has exactly one outgoing edge; for asynchronous, one or
        more (self-loop on fixed points).
    """
    if scheme not in ("synchronous", "asynchronous"):
        raise ValueError(f"Unknown scheme {scheme!r}")
    g = nx.DiGraph()
    if states is None:
        states_iter: Iterable[State] = net.all_states()
    else:
        states_iter = states
    for s in states_iter:
        g.add_node(s, label=net.state_to_str(s))
    if scheme == "synchronous":
        for s in list(g.nodes):
            t = synchronous_successor(net, s)
            if t not in g:
                g.add_node(t, label=net.state_to_str(t))
            g.add_edge(s, t)
    else:
        for s in list(g.nodes):
            for t in asynchronous_successors(net, s):
                if t not in g:
                    g.add_node(t, label=net.state_to_str(t))
                g.add_edge(s, t)
    return g
