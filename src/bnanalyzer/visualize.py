"""
Plotting helpers for influence and state-transition graphs.

These helpers produce ``matplotlib`` figures suitable for both saving to
files and rendering inside Streamlit.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import networkx as nx

from .attractors import Attractor
from .network import BooleanNetwork, State


# ----------------------------------------------------------------------
# Influence graph
# ----------------------------------------------------------------------


def draw_influence_graph(
    g: nx.DiGraph,
    figsize: tuple = (8, 6),
    seed: int = 7,
) -> "plt.Figure":
    fig, ax = plt.subplots(figsize=figsize)
    pos = nx.spring_layout(g, seed=seed, k=1.2 / max(1, len(g) ** 0.5))

    # Edges by sign
    pos_edges = [(u, v) for u, v, d in g.edges(data=True) if d.get("sign") == "+"]
    neg_edges = [(u, v) for u, v, d in g.edges(data=True) if d.get("sign") == "-"]
    other_edges = [(u, v) for u, v, d in g.edges(data=True)
                   if d.get("sign") not in ("+", "-")]

    nx.draw_networkx_nodes(
        g, pos, node_color="#cfe8ff", edgecolors="#1f77b4",
        linewidths=1.2, node_size=1400, ax=ax
    )
    nx.draw_networkx_labels(g, pos, font_size=10, font_weight="bold", ax=ax)
    if pos_edges:
        nx.draw_networkx_edges(
            g, pos, edgelist=pos_edges, edge_color="#2ca02c",
            arrows=True, arrowstyle="-|>", arrowsize=18,
            connectionstyle="arc3,rad=0.08", width=1.6, ax=ax
        )
    if neg_edges:
        nx.draw_networkx_edges(
            g, pos, edgelist=neg_edges, edge_color="#d62728",
            arrows=True, arrowstyle="-[", arrowsize=18,
            connectionstyle="arc3,rad=0.08", width=1.6, ax=ax
        )
    if other_edges:
        nx.draw_networkx_edges(
            g, pos, edgelist=other_edges, edge_color="#7f7f7f", style="dashed",
            arrows=True, arrowstyle="-|>", arrowsize=18,
            connectionstyle="arc3,rad=0.08", width=1.4, ax=ax
        )

    legend_handles = []
    if pos_edges:
        legend_handles.append(mpatches.Patch(color="#2ca02c", label="activation (+)"))
    if neg_edges:
        legend_handles.append(mpatches.Patch(color="#d62728", label="inhibition (-)"))
    if other_edges:
        legend_handles.append(mpatches.Patch(color="#7f7f7f", label="ambiguous (?)"))
    if legend_handles:
        ax.legend(handles=legend_handles, loc="best", fontsize=9, frameon=True)
    ax.set_title("Influence graph", fontsize=12)
    ax.set_axis_off()
    fig.tight_layout()
    return fig


# ----------------------------------------------------------------------
# State-transition graph
# ----------------------------------------------------------------------


def draw_state_transition_graph(
    g: nx.DiGraph,
    net: BooleanNetwork,
    attractor_states: Optional[Iterable[State]] = None,
    figsize: tuple = (10, 8),
    seed: int = 11,
    label_states: bool = True,
) -> "plt.Figure":
    fig, ax = plt.subplots(figsize=figsize)
    n = g.number_of_nodes()
    layout_seed = seed
    if n <= 64:
        pos = nx.spring_layout(g, seed=layout_seed, k=1.4 / max(1, n ** 0.5))
    else:
        # Hard to lay out clearly beyond ~64 states; use kamada-kawai which
        # handles larger graphs better.
        try:
            pos = nx.kamada_kawai_layout(g)
        except Exception:
            pos = nx.spring_layout(g, seed=layout_seed)

    attr = set(attractor_states or [])
    node_colors = ["#ffd166" if node in attr else "#dbeafe" for node in g.nodes]
    node_edges = ["#cc7a00" if node in attr else "#1f77b4" for node in g.nodes]

    node_size = 700 if n <= 32 else (350 if n <= 128 else 120)
    nx.draw_networkx_nodes(
        g, pos, node_color=node_colors, edgecolors=node_edges,
        linewidths=1.0, node_size=node_size, ax=ax
    )
    if label_states and n <= 64:
        labels = {node: g.nodes[node].get("label", "") for node in g.nodes}
        nx.draw_networkx_labels(g, pos, labels=labels, font_size=8, ax=ax)
    nx.draw_networkx_edges(
        g, pos, arrows=True, arrowstyle="-|>", arrowsize=12,
        connectionstyle="arc3,rad=0.1", edge_color="#666666",
        width=0.8, ax=ax
    )

    # Legend
    handles = [
        mpatches.Patch(color="#ffd166", label="state in an attractor"),
        mpatches.Patch(color="#dbeafe", label="transient state"),
    ]
    ax.legend(handles=handles, loc="best", fontsize=9, frameon=True)
    ax.set_title(
        f"State Transition Graph — {n} states, "
        f"{g.number_of_edges()} transitions",
        fontsize=12,
    )
    ax.set_axis_off()
    fig.tight_layout()
    return fig
