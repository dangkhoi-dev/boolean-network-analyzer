"""
bnanalyzer - Boolean Network Analyzer

A toolkit for parsing, simulating, and analyzing Boolean networks.
"""

from .network import BooleanNetwork
from .parser import parse_bnet, BNetParseError
from .stg import (
    synchronous_successor,
    asynchronous_successors,
    build_state_transition_graph,
)
from .attractors import find_attractors, classify_attractor

__all__ = [
    "BooleanNetwork",
    "parse_bnet",
    "BNetParseError",
    "synchronous_successor",
    "asynchronous_successors",
    "build_state_transition_graph",
    "find_attractors",
    "classify_attractor",
]

__version__ = "1.0.0"
