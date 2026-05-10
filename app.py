"""
Boolean Network Analyzer — Streamlit application.

Run:
    streamlit run app.py

Features
--------
1. Import a Boolean network from a `.bnet` file (upload or pick a sample).
2. Visualize the influence graph (with sign-annotated edges).
3. Build state-transition graphs under synchronous OR asynchronous update.
4. Compute and display all attractors (fixed points, cyclic, complex).
5. Export the influence graph and STG as PNG.
"""

from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import streamlit as st

# Make `src/` importable when running with `streamlit run app.py`.
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bnanalyzer import (  # noqa: E402  -- after sys.path mutation
    BNetParseError,
    BooleanNetwork,
    build_state_transition_graph,
    find_attractors,
)
from bnanalyzer.attractors import basin_of_attraction  # noqa: E402
from bnanalyzer.visualize import (  # noqa: E402
    draw_influence_graph,
    draw_state_transition_graph,
)


# ----------------------------------------------------------------------
# Page setup
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Boolean Network Analyzer",
    page_icon="*",
    layout="wide",
)

st.markdown(
    """
    <style>
      .big-title { font-size: 2.0rem; font-weight: 700; margin-bottom: 0; }
      .subtitle  { color: #64748b; margin-top: 0; }
      .sidebar-section { font-weight: 600; margin-top: 0.5rem; }
      .stButton button { border-radius: 0.5rem; }
      .metric-card { background:#f1f5f9; padding:0.8rem 1rem; border-radius:0.6rem;
                     border:1px solid #e2e8f0; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="big-title">Boolean Network Analyzer</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Capstone project P6 &mdash; HCMUT, Faculty of Computer Science &amp; Engineering</p>',
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------
# Sidebar: load network
# ----------------------------------------------------------------------
st.sidebar.markdown("### 1. Load a Boolean network")

SAMPLE_DIR = ROOT / "samples"
sample_files = []
if SAMPLE_DIR.is_dir():
    sample_files = sorted([p.name for p in SAMPLE_DIR.glob("*.bnet")])

source_mode = st.sidebar.radio(
    "Source",
    ["Sample network", "Upload .bnet file", "Paste source"],
    index=0,
)

bnet_text = None
network_name = "(unnamed)"

if source_mode == "Sample network":
    if not sample_files:
        st.sidebar.warning("No samples found in `samples/`.")
    else:
        chosen = st.sidebar.selectbox("Pick a sample", sample_files, index=0)
        with open(SAMPLE_DIR / chosen, "r", encoding="utf-8") as fp:
            bnet_text = fp.read()
        network_name = chosen
elif source_mode == "Upload .bnet file":
    uploaded = st.sidebar.file_uploader(
        "Upload a .bnet file", type=["bnet", "txt"]
    )
    if uploaded is not None:
        bnet_text = uploaded.getvalue().decode("utf-8")
        network_name = uploaded.name
else:
    bnet_text = st.sidebar.text_area(
        "Paste bnet source",
        height=200,
        placeholder="targets, factors\nA, !B\nB, A",
        key="bnet_paste",
    )
    network_name = "pasted"


if not bnet_text or not bnet_text.strip():
    st.info(
        "Pick a sample on the left, upload a `.bnet` file, or paste source "
        "code to begin."
    )
    st.stop()


# Parse network
try:
    net = BooleanNetwork.from_bnet(bnet_text)
except BNetParseError as exc:
    st.error(f"Failed to parse: {exc}")
    st.stop()

st.sidebar.success(f"Loaded **{network_name}** &mdash; {net.n} nodes")

st.sidebar.markdown("### 2. Update scheme")
scheme = st.sidebar.radio(
    "STG update scheme",
    ["synchronous", "asynchronous"],
    index=0,
    help=(
        "Synchronous = every node's rule is applied at the same time step. "
        "Asynchronous = at each step exactly one node (chosen "
        "non-deterministically) is updated; the STG branches over choices."
    ),
)

st.sidebar.markdown("### 3. STG options")
build_full = st.sidebar.checkbox(
    "Build STG over the full state space (2^n states)",
    value=net.n <= 10,
    help="Disable for large networks; instead, simulate from a single state.",
)
warn_threshold = 12
if build_full and net.n > warn_threshold:
    st.sidebar.warning(
        f"With {net.n} nodes, the full STG has {2**net.n:,} states. This "
        f"may be slow or unreadable; consider disabling 'full state space'."
    )


# ----------------------------------------------------------------------
# Top: rules & metrics
# ----------------------------------------------------------------------
top_left, top_right = st.columns([3, 2], gap="large")

with top_left:
    st.subheader("Update rules")
    rule_rows = [
        {"node": name, "rule": net.rules[name].expression}
        for name in net.nodes
    ]
    st.dataframe(
        pd.DataFrame(rule_rows),
        hide_index=True,
        use_container_width=True,
    )

with top_right:
    st.subheader("Network statistics")
    inf_g = net.influence_graph()
    n_edges = inf_g.number_of_edges()
    pos_e = sum(1 for _, _, d in inf_g.edges(data=True) if d.get("sign") == "+")
    neg_e = sum(1 for _, _, d in inf_g.edges(data=True) if d.get("sign") == "-")
    amb_e = n_edges - pos_e - neg_e
    state_space = 2 ** net.n
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="metric-card"><b>Nodes</b><br>{net.n}</div>',
                    unsafe_allow_html=True)
        st.markdown(f'<div class="metric-card"><b>Edges</b><br>{n_edges}</div>',
                    unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><b>State space</b><br>{state_space:,}</div>',
                    unsafe_allow_html=True)
        st.markdown(
            f'<div class="metric-card"><b>Edge signs</b><br>'
            f'+ {pos_e} &nbsp; - {neg_e} &nbsp; ? {amb_e}</div>',
            unsafe_allow_html=True,
        )


# ----------------------------------------------------------------------
# Tabs
# ----------------------------------------------------------------------
tab_inf, tab_stg, tab_attr, tab_sim, tab_src = st.tabs(
    [
        "Influence graph",
        "State transition graph",
        "Attractors",
        "Simulate trajectory",
        "Source",
    ]
)

with tab_inf:
    st.markdown(
        "The **influence graph** has one edge per regulator-target relation. "
        "Edge signs are inferred from the rule's monotonicity: green `+` "
        "edges mean activation, red `-` edges mean inhibition, and grey `?` "
        "edges mean the influence is non-monotonic."
    )
    fig = draw_influence_graph(inf_g)
    st.pyplot(fig, clear_figure=True)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    st.download_button(
        "Download influence graph (PNG)",
        data=buf.getvalue(),
        file_name=f"{Path(network_name).stem}_influence.png",
        mime="image/png",
    )
    plt.close(fig)


# ----------------------------------------------------------------------
# Build the STG once, cache for both STG tab and attractors tab
# ----------------------------------------------------------------------

@st.cache_data(show_spinner="Building state-transition graph...")
def _cached_stg(bnet_src: str, scheme_: str, full: bool, n: int):
    net_ = BooleanNetwork.from_bnet(bnet_src)
    if full:
        g = build_state_transition_graph(net_, scheme=scheme_)
    else:
        # Build STG only from the all-zero state, expanding reachable states.
        seed = tuple([False] * net_.n)
        g = nx.DiGraph()
        g.add_node(seed, label=net_.state_to_str(seed))
        frontier = [seed]
        seen = {seed}
        while frontier:
            s = frontier.pop()
            if scheme_ == "synchronous":
                successors = [net_.evaluate_all(s)]
            else:
                from bnanalyzer.stg import asynchronous_successors
                successors = asynchronous_successors(net_, s)
            for t in successors:
                if t not in seen:
                    g.add_node(t, label=net_.state_to_str(t))
                    seen.add(t)
                    frontier.append(t)
                g.add_edge(s, t)
        return g
    return g


with tab_stg:
    st.markdown(
        f"Building STG under the **{scheme}** update scheme. "
        + ("Full state space." if build_full else "Reachable from the all-zero state.")
    )
    stg = _cached_stg(bnet_text, scheme, build_full, net.n)
    st.write(
        f"STG: **{stg.number_of_nodes()}** states, "
        f"**{stg.number_of_edges()}** transitions."
    )
    attractors = find_attractors(stg, scheme=scheme)
    attractor_states = [s for a in attractors for s in a.states]
    fig = draw_state_transition_graph(
        stg, net, attractor_states=attractor_states,
        label_states=stg.number_of_nodes() <= 64,
    )
    st.pyplot(fig, clear_figure=True)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=160, bbox_inches="tight")
    st.download_button(
        "Download STG (PNG)",
        data=buf.getvalue(),
        file_name=f"{Path(network_name).stem}_stg_{scheme}.png",
        mime="image/png",
    )
    plt.close(fig)


with tab_attr:
    stg = _cached_stg(bnet_text, scheme, build_full, net.n)
    attractors = find_attractors(stg, scheme=scheme)
    if not attractors:
        st.warning("No attractors found (this should not happen).")
    else:
        st.success(f"Found {len(attractors)} attractor(s).")
        for i, a in enumerate(attractors, start=1):
            with st.expander(
                f"Attractor #{i} — {a.kind} ({len(a.states)} state(s))",
                expanded=(i == 1),
            ):
                labels = a.labels(net)
                st.code("\n".join(labels), language="text")
                # Show as a table mapping each node to its on/off pattern in the attractor
                cols = ["state"] + list(net.nodes)
                rows = []
                for label, st_ in zip(labels, a.states):
                    rows.append([label] + ["1" if v else "0" for v in st_])
                st.dataframe(
                    pd.DataFrame(rows, columns=cols),
                    hide_index=True,
                    use_container_width=True,
                )
                weak_basin = basin_of_attraction(stg, a)
                st.caption(
                    f"Weak basin (states with at least one trajectory reaching "
                    f"this attractor): **{len(weak_basin)}** of {stg.number_of_nodes()}."
                )


with tab_sim:
    st.markdown(
        "Pick an initial state and step the network forward. Under the "
        "asynchronous scheme, only one node is updated per step; you can "
        "choose which (or pick *random*)."
    )
    init_cols = st.columns(min(net.n, 6))
    init_state = []
    for i, name in enumerate(net.nodes):
        with init_cols[i % len(init_cols)]:
            init_state.append(st.checkbox(name, value=False, key=f"init_{name}"))
    init_state = tuple(init_state)
    n_steps = st.slider("Number of steps", min_value=1, max_value=40, value=10)
    sim_scheme = st.radio(
        "Simulation scheme", ["synchronous", "asynchronous"], horizontal=True,
        index=0 if scheme == "synchronous" else 1,
    )

    # Run trajectory deterministically (sync) or pick first changing node (async)
    trajectory = [init_state]
    cur = init_state
    for _ in range(n_steps):
        if sim_scheme == "synchronous":
            cur = net.evaluate_all(cur)
        else:
            from bnanalyzer.stg import asynchronous_successors
            succ = asynchronous_successors(net, cur)
            cur = succ[0]
        trajectory.append(cur)
        # break early if we hit a fixed point
        if sim_scheme == "synchronous" and trajectory[-1] == trajectory[-2]:
            break

    # Build a heat-map style table for the trajectory
    rows = []
    for t, st_ in enumerate(trajectory):
        rows.append({"step": t, **{n: ("1" if v else "0") for n, v in zip(net.nodes, st_)}})
    df = pd.DataFrame(rows)
    st.dataframe(df, hide_index=True, use_container_width=True)


with tab_src:
    st.markdown("### Network source")
    st.code(bnet_text.strip() + "\n", language="text")
    st.download_button(
        "Download .bnet",
        data=bnet_text,
        file_name=Path(network_name).stem + ".bnet",
        mime="text/plain",
    )

st.caption(
    "Boolean Network Analyzer • Capstone P6 • Tran Phan Dang Khoi (2352626) "
    "• HCMUT CSE"
)
