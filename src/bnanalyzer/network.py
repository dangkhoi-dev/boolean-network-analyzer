"""
BooleanNetwork class — the central object that wraps a parsed bnet source
and exposes evaluation, influence-graph extraction, and convenience helpers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

import networkx as nx

from .parser import ParsedRule, parse_bnet


State = Tuple[bool, ...]
"""A state is a fixed-length tuple of booleans, ordered by ``BooleanNetwork.nodes``."""


@dataclass
class InfluenceEdge:
    """An edge in the influence graph: ``source`` regulates ``target``."""

    source: str
    target: str
    sign: str  # "+", "-", or "?" (for mixed/unknown)


@dataclass
class BooleanNetwork:
    """A Boolean network with named nodes and Boolean update rules.

    Use :meth:`from_bnet` or :meth:`from_file` to construct.
    """

    nodes: Tuple[str, ...]
    rules: Dict[str, ParsedRule]
    _compiled: Dict[str, "object"] = field(default_factory=dict, repr=False)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @classmethod
    def from_bnet(cls, source: str) -> "BooleanNetwork":
        rules = parse_bnet(source)
        nodes = tuple(rules.keys())
        net = cls(nodes=nodes, rules=rules)
        net._compile_all()
        return net

    @classmethod
    def from_file(cls, path: str) -> "BooleanNetwork":
        with open(path, "r", encoding="utf-8") as fp:
            return cls.from_bnet(fp.read())

    def _compile_all(self) -> None:
        for name, rule in self.rules.items():
            self._compiled[name] = compile(
                rule.python_expression, f"<bnet:{name}>", "eval"
            )

    # ------------------------------------------------------------------
    # Basic accessors
    # ------------------------------------------------------------------

    @property
    def n(self) -> int:
        return len(self.nodes)

    @property
    def index(self) -> Dict[str, int]:
        return {name: i for i, name in enumerate(self.nodes)}

    def state_to_dict(self, state: Sequence[bool]) -> Dict[str, bool]:
        return {name: bool(v) for name, v in zip(self.nodes, state)}

    def dict_to_state(self, d: Mapping[str, bool]) -> State:
        return tuple(bool(d.get(name, False)) for name in self.nodes)

    def state_to_str(self, state: Sequence[bool]) -> str:
        """Compact binary representation, e.g. (True, False, True) -> '101'."""
        return "".join("1" if v else "0" for v in state)

    def str_to_state(self, s: str) -> State:
        if len(s) != self.n:
            raise ValueError(
                f"State string length {len(s)} != number of nodes {self.n}"
            )
        return tuple(c == "1" for c in s)

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def evaluate_node(self, name: str, state: Sequence[bool]) -> bool:
        """Apply node ``name``'s rule to ``state``, returning the new value."""
        ctx = self.state_to_dict(state)
        return bool(eval(self._compiled[name], {"__builtins__": {}}, ctx))

    def evaluate_all(self, state: Sequence[bool]) -> State:
        """Apply every rule to the given state simultaneously, returning the next state."""
        ctx = self.state_to_dict(state)
        result: List[bool] = []
        for name in self.nodes:
            result.append(bool(eval(self._compiled[name], {"__builtins__": {}}, ctx)))
        return tuple(result)

    # ------------------------------------------------------------------
    # Influence graph
    # ------------------------------------------------------------------

    def influence_graph(self) -> nx.DiGraph:
        """Build the influence graph as a directed graph with sign-annotated edges.

        For each pair (source -> target) with source in target's inputs, we
        determine whether the influence is activating, inhibiting, or
        ambiguous by checking how flipping ``source`` changes the rule output
        across all valuations of the other inputs.
        """
        g = nx.DiGraph()
        for name in self.nodes:
            g.add_node(name)
        for target_name, rule in self.rules.items():
            for src in rule.inputs:
                sign = self._infer_edge_sign(target_name, src)
                g.add_edge(src, target_name, sign=sign)
        return g

    def _infer_edge_sign(self, target: str, source: str) -> str:
        """Infer +/-/? for the influence edge source -> target.

        We enumerate over the other inputs of the target's rule and compare
        the rule output when source=False vs source=True. If all comparisons
        agree on increasing (False<True), the edge is "+"; if all agree on
        decreasing, it's "-"; if mixed or non-monotonic, "?".
        """
        rule = self.rules[target]
        other_inputs: List[str] = [v for v in rule.inputs if v != source]
        # compile once
        code = self._compiled[target]
        increases = False
        decreases = False
        # iterate over 2^k combinations of remaining inputs
        k = len(other_inputs)
        for mask in range(1 << k):
            ctx = {
                v: bool((mask >> j) & 1) for j, v in enumerate(other_inputs)
            }
            ctx[source] = False
            v_off = bool(eval(code, {"__builtins__": {}}, dict(ctx)))
            ctx[source] = True
            v_on = bool(eval(code, {"__builtins__": {}}, dict(ctx)))
            if v_off == v_on:
                continue
            if v_on and not v_off:
                increases = True
            else:
                decreases = True
            if increases and decreases:
                return "?"
        if increases and not decreases:
            return "+"
        if decreases and not increases:
            return "-"
        # neither: source has no effect (rare; keep as "?" to surface the oddity)
        return "?"

    # ------------------------------------------------------------------
    # Iterating over the full state space
    # ------------------------------------------------------------------

    def all_states(self) -> Iterable[State]:
        """Yield every state in canonical lexicographic order. Up to 2**n states."""
        n = self.n
        for k in range(1 << n):
            yield tuple(bool((k >> i) & 1) for i in range(n))

    # ------------------------------------------------------------------
    # Pretty representation
    # ------------------------------------------------------------------

    def summary(self) -> str:
        lines = [f"BooleanNetwork with {self.n} nodes:"]
        for name in self.nodes:
            r = self.rules[name]
            lines.append(f"  {name} = {r.expression}")
        return "\n".join(lines)
