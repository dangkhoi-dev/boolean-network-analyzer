"""Smoke tests over the bundled sample networks."""

from pathlib import Path

import pytest

from bnanalyzer import (
    BooleanNetwork,
    build_state_transition_graph,
    find_attractors,
)


SAMPLES = Path(__file__).resolve().parents[1] / "samples"


@pytest.mark.parametrize(
    "fname",
    [
        "toy_switch.bnet",
        "bistable_toggle.bnet",
        "repressilator.bnet",
        "fission_yeast.bnet",
        "mammalian_cell_cycle.bnet",
    ],
)
def test_sample_loads_and_has_attractor(fname):
    path = SAMPLES / fname
    net = BooleanNetwork.from_file(str(path))
    assert net.n >= 2
    g = build_state_transition_graph(net, scheme="synchronous")
    attractors = find_attractors(g, scheme="synchronous")
    assert len(attractors) >= 1
    # every state in every attractor must be a state of the STG
    for a in attractors:
        for s in a.states:
            assert s in g
