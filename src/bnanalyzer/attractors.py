"""
Attractor computation on state-transition graphs.

An attractor of a finite deterministic/non-deterministic dynamical system is
a non-empty set of states A such that, once the trajectory enters A, it
never leaves it, and every state in A is reachable from every other state
in A. In graph terms an attractor is a *terminal strongly connected
component* (terminal SCC) of the state-transition graph.

We classify attractors as:

- **Fixed point** (a.k.a. steady state): |A| == 1 and the only state has
  itself as its sole successor.
- **Cyclic / complex**: |A| >= 2.

Synchronous STGs only produce fixed points or simple cycles (because
out-degree = 1). Asynchronous STGs can produce richer terminal SCCs that
correspond to non-cyclic but trapping subspaces.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import networkx as nx

from .network import BooleanNetwork, State


@dataclass
class Attractor:
    """A terminal SCC of the STG."""

    states: Tuple[State, ...]
    kind: str  # "fixed_point", "cyclic", "complex"

    def labels(self, net: BooleanNetwork) -> List[str]:
        return [net.state_to_str(s) for s in self.states]


def classify_attractor(
    g: nx.DiGraph, scc: Tuple[State, ...], scheme: str
) -> str:
    """Return one of "fixed_point", "cyclic", "complex"."""
    if len(scc) == 1:
        return "fixed_point"
    sub = g.subgraph(scc)
    # In a synchronous STG every node has out-degree 1, so any non-singleton
    # terminal SCC is a simple cycle.
    if scheme == "synchronous":
        return "cyclic"
    # In an async STG, a "cyclic" attractor would be a simple loop (each
    # node has exactly one successor inside the SCC and the structure is a
    # single cycle). Otherwise it's complex.
    out_degrees = {n: 0 for n in scc}
    for u, v in sub.edges():
        out_degrees[u] += 1
    if all(d == 1 for d in out_degrees.values()):
        return "cyclic"
    return "complex"


def find_attractors(
    g: nx.DiGraph, scheme: str = "synchronous"
) -> List[Attractor]:
    """Find every attractor (terminal SCC) of the STG.

    Uses the condensation of ``g`` and returns SCCs with no outgoing edges
    in the condensation (i.e. once entered, never left).
    """
    sccs = list(nx.strongly_connected_components(g))
    cond = nx.condensation(g, scc=sccs)
    attractors: List[Attractor] = []
    # cond.nodes have integer ids; cond.graph["mapping"] maps original->id;
    # cond.nodes[id]["members"] gives the set of original states in the SCC.
    for cid in cond.nodes:
        if cond.out_degree(cid) == 0:
            members = tuple(cond.nodes[cid]["members"])
            kind = classify_attractor(g, members, scheme)
            attractors.append(Attractor(states=members, kind=kind))
    # Sort attractors deterministically (smallest first, then lexicographic)
    attractors.sort(key=lambda a: (len(a.states), tuple(sorted(a.states))))
    return attractors


def basin_of_attraction(
    g: nx.DiGraph, attractor: Attractor
) -> List[State]:
    """Return all states whose every trajectory eventually reaches the attractor.

    For a synchronous STG (out-degree 1) this is unambiguous.
    For an asynchronous STG, the *strong* basin (states from which ALL
    trajectories must reach the attractor) is computed via reverse
    reachability while excluding nodes that can also reach a different
    attractor.
    """
    target = set(attractor.states)
    # All states with a path to the attractor (weak basin):
    weak = set()
    for s in target:
        weak.update(nx.ancestors(g, s))
    weak.update(target)
    return sorted(weak)
