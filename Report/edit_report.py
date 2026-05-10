"""Edit the capstone report .docx in place:

  * Add inline citations [1]/[2] to the theoretical-background paragraphs.
  * Insert a new subsection "2.6. Mapping to Reference Literature" that
    pairs every concept the analyzer implements with the precise passage of
    the cited reference paper that motivated it.
  * Insert a new subsection "5.5. Discussion: Alignment with the Literature"
    that closes the loop between the case studies of §5 and the same
    references.
  * Beef up the bibliography entries for [1] and [2] with their DOIs and a
    one-line takeaway summarising what each paper contributes to the
    project.

The script is idempotent: running it twice does not duplicate the inserted
sections (it checks for sentinel headings).

Usage:
    cd Report && python3 edit_report.py
"""

from copy import deepcopy
from docx import Document
from docx.oxml.ns import qn

INPUT = 'Boolean_Network_Analyzer_Report.docx'
OUTPUT = 'Boolean_Network_Analyzer_Report.docx'

doc = Document(INPUT)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_par(text_prefix, must_contain=None):
    """Return the first paragraph whose .text starts with the given prefix.

    If ``must_contain`` is given, also require the paragraph text to contain
    that substring (used to disambiguate when several paragraphs share a
    common prefix, e.g. body paragraph vs. heading vs. TOC line).
    """
    fallback = None
    for p in doc.paragraphs:
        if p.text.startswith(text_prefix):
            if must_contain is None or must_contain in p.text:
                return p
            if fallback is None:
                fallback = p
    if fallback is not None:
        return fallback
    raise LookupError(f'Paragraph not found: {text_prefix!r}')


def replace_text_preserving_style(par, old, new):
    """Substitute `old` -> `new` in a paragraph, preserving run style.

    For our use case we just rewrite the full paragraph using the style of the
    first run. python-docx makes inline edits painful when the substring spans
    multiple runs, but every paragraph in this report is a single run.
    """
    if old not in par.text:
        return False
    # Capture the first run's style if any
    style = par.style
    runs = list(par.runs)
    full = par.text
    new_full = full.replace(old, new)
    # clear existing runs
    for r in runs:
        r.text = ''
    if runs:
        runs[0].text = new_full
    else:
        par.add_run(new_full)
    par.style = style
    return True


def insert_paragraph_after(paragraph, text='', style=None):
    """Insert a new paragraph immediately after `paragraph` and return it."""
    new_p = deepcopy(paragraph._element)
    # strip existing run children
    for child in list(new_p):
        if child.tag in (qn('w:r'), qn('w:hyperlink')):
            new_p.remove(child)
    paragraph._element.addnext(new_p)
    from docx.text.paragraph import Paragraph
    np = Paragraph(new_p, paragraph._parent)
    if style is not None:
        np.style = style
    if text:
        np.add_run(text)
    return np


def insert_block_after(anchor, items):
    """Insert a list of (style, text) items after the anchor paragraph,
    preserving order. Returns the last inserted paragraph."""
    last = anchor
    for style, text in items:
        last = insert_paragraph_after(last, text=text, style=style)
    return last


# ---------------------------------------------------------------------------
# (1) Inline citations in §2 Theoretical Background
# ---------------------------------------------------------------------------

CITATION_EDITS = [
    # (paragraph_prefix, old_substring, new_substring)
    (
        'A Boolean network with n nodes',
        'and the (possibly non-deterministic) graph that records every legal one-step transition is called the *state-transition graph* (§2.4).',
        'and the (possibly non-deterministic) graph that records every legal one-step transition is called the *state-transition graph* (§2.4). '
        'This definition matches the canonical one given by Schwab et al. (2020) [1] (§2): "BN models are one of the simplest dynamic models … '
        'one implicitly assumes that all biological components are described by binary values and their interactions by Boolean regulatory functions."',
    ),
    (
        'Influence graphs are a useful first sanity-check on a model',
        'are all quickly visible.',
        'are all quickly visible. Schwab et al. [1] (§3.1) make the same observation about Boolean models: "Regulatory components in biology '
        'usually act either as activator or inhibitor … Consequently, regulatory functions in biological networks are monotone or at least close to monotonicity." '
        'Our sign-inference algorithm (§4.2) operationalises exactly this monotonicity test by enumerating the other inputs of each rule and checking '
        'whether the rule output is monotone in the candidate source.',
    ),
    (
        'Synchronous update. Every node updates simultaneously',
        'This is the original formulation by Kauffman (1969).',
        'This is the original formulation by Kauffman (1969); Schwab et al. [1] (§2.1) describe it as the case "when using synchronous updates, '
        'each Boolean function is applied to compute a state transition from t to t+1 … the dynamics of the BN are deterministic, and each '
        'state of the BN has one successor." Naldi et al. [2] (§3) likewise list the fully-synchronous mode as one of the two updating policies of GINsim 2.3.',
    ),
    (
        'Asynchronous update (general).',
        'all others are held constant.',
        'all others are held constant. Schwab et al. [1] (§2.1) describe this paradigm as: "the asynchronous update paradigm assumes that '
        'only one random component is updated at each single time step … and leads to n possible successor states of each state, depending '
        'on the selected component."',
    ),
    (
        'The state-transition graph (STG) under a chosen update scheme',
        'or 1 — a self-loop — if the state is a fixed point).',
        'or 1 — a self-loop — if the state is a fixed point). Schwab et al. [1] (§3.2) summarise this construction in the same terms: '
        '"the dynamics can be represented in directed state graphs … each node corresponds to one state of the network, while edges represent '
        'transitions from one state to its successor. The update strategy of the underlying BNs affects the constitution of the resulting '
        'state graph strongly." GINsim 2.3 (Naldi et al. [2] §2) computes exactly this object: "state transition graphs, where vertices '
        'represent states of the system … and arcs represent transitions between these states."',
    ),
    (
        'An attractor is a non-empty set A',
        'an attractor is a *terminal strongly connected component*',
        'an attractor is a *terminal strongly connected component* (this graph-theoretic characterisation is the one used by GINsim — Naldi et al. '
        '[2] §3.2 on "stationary states or other attractors" computed via "the strongly connected components … of the state transition graph")',
    ),
    (
        'The basin of attraction of an attractor',
        'but differ in general.',
        'but differ in general. The strong/weak distinction we adopt is exactly the one Schwab et al. [1] (§3.3) attribute to Klarner et al.: '
        '"States which belong to a strong basin of attraction lead to only one possible attractor. In contrast, states in the weak basin '
        '… may lead to a certain attractor but also another one."',
    ),
]

for prefix, old, new in CITATION_EDITS:
    try:
        par = find_par(prefix, must_contain=old)
    except LookupError:
        print(f'  ! could not find paragraph starting with {prefix!r}')
        continue
    if old in par.text:
        replace_text_preserving_style(par, old, new)
        print(f'  ✓ citation inserted in: {prefix[:60]}...')
    else:
        # already edited (idempotent re-run)
        print(f'  · already edited: {prefix[:60]}...')


# ---------------------------------------------------------------------------
# (2) New subsection 2.6 — Mapping to Reference Literature
# ---------------------------------------------------------------------------

SENTINEL_2_6 = '2.6. Mapping to Reference Literature'

if not any(p.text.startswith(SENTINEL_2_6) for p in doc.paragraphs):
    anchor = find_par('The basin of attraction of an attractor')
    items = [
        ('Heading 2', SENTINEL_2_6),
        ('Normal',
         'A central goal of this capstone project is not only to *implement* '
         'a Boolean-network analyzer but to demonstrate that every algorithmic '
         'choice has direct support in the recent literature on Boolean '
         'network modelling. The table-style mapping below pairs each concept '
         'introduced in §2.1–§2.5 (and its concrete implementation in §4) '
         'with the originating passage in the two primary references of the '
         'project: Schwab et al. (2020) [1] and Naldi et al. (2009) [2].'),

        ('Heading 3', '2.6.1. From Schwab et al. (2020) — "Concepts in Boolean network modeling"'),

        ('Normal',
         'Boolean network as the simplest qualitative dynamic model. '
         'Schwab et al. [1] (§2) state: "Boolean network (BN) models are '
         'one of the simplest dynamic models. In BN models, one implicitly '
         'assumes that all biological components are described by binary '
         'values and their interactions by Boolean regulatory functions." '
         '— this is exactly the definition of BooleanNetwork in §4.2 of '
         'this report (parser.py + network.py): a fixed-length tuple of '
         'Boolean variables together with one Boolean update function per '
         'node.'),

        ('Normal',
         'Synchronous vs. asynchronous update schemes. '
         'Schwab et al. [1] (§2.1) write: "When using synchronous updates, '
         'each Boolean function is applied to compute a state transition '
         'from t to t+1 … the dynamics of the BN are deterministic, and '
         'each state of the BN has one successor … The asynchronous update '
         'paradigm assumes that only one random component is updated at '
         'each single time step … leads to n possible successor states of '
         'each state, depending on the selected component." — this is '
         'literally what synchronous_successor() and asynchronous_successors() '
         'in stg.py compute (§4.3 of this report).'),

        ('Normal',
         'State graph and attractors as terminal cycles. '
         'Schwab et al. [1] (§3.2) write: "the dynamics can be represented '
         'in directed state graphs. Here, each node corresponds to one '
         'state of the network, while edges represent transitions from one '
         'state to its successor … State graphs contain periodic sequences '
         'of states, called attractors. Once reached, they cannot be left '
         'unless an external perturbation occurs … Steady-state attractors '
         'comprise only one state … Synchronous networks may also exhibit '
         'simple cycles … The asynchronous update strategy reveals the '
         'so-called complex attractors. Complex attractors are formed by '
         'overlapping loops which origin from the possibility of reaching '
         'more than one successor state in the asynchronous update scheme." '
         '— our three-way classification (fixed_point / cyclic / complex) '
         'in attractors.py (§4.4) is the exact taxonomy described in this '
         'paragraph.'),

        ('Normal',
         'Strong vs. weak basin of attraction. '
         'Schwab et al. [1] (§3.3, citing Klarner et al.) explain: '
         '"States which belong to a strong basin of attraction lead to '
         'only one possible attractor. In contrast, states in the weak '
         'basin of attractor may lead to a certain attractor but also '
         'another one." — basin_of_attraction() in attractors.py implements '
         'the *weak* basin via reverse reachability (the strong basin is '
         'computed implicitly as the complement on synchronous STGs, '
         'where the two coincide).'),

        ('Normal',
         'Monotonicity of regulatory functions. '
         'Schwab et al. [1] (§3.1) note: "Regulatory components in '
         'biology usually act either as activator or inhibitor inside one '
         'particular context. Increasing concentration of an activator '
         'will lead to an increased but never decreased concentration of '
         'the target and vice-versa for repressors. Consequently, '
         'regulatory functions in biological networks are monotone or at '
         'least close to monotonicity." — our influence-graph sign '
         'inference algorithm (§4.2) implements *exactly* this '
         'monotonicity test by comparing rule output for source = 0 vs. '
         'source = 1 across all valuations of the other inputs, and '
         'returns "+", "−", or "?" (non-monotonic).'),

        ('Normal',
         'Brute-force attractor enumeration is feasible only for small '
         'networks. Schwab et al. [1] (§5) caution: "the identification '
         'of all attractors by exhaustively calculating all 2^n successor '
         'states of a network is computationally demanding and could be '
         'shown to be NP-hard … this procedure is only feasible for small '
         'networks." — this directly motivates §3 of our work plan (the '
         '"GIAI ĐOẠN 3" optimisation phase: Tarjan-based STG analysis, '
         'Z3-solver fast singleton search) and explains why our brute-force '
         'engine is capped at ~16 nodes in the live web demo.'),

        ('Heading 3', '2.6.2. From Naldi et al. (2009) — "Logical modelling of regulatory networks with GINsim 2.3"'),

        ('Normal',
         'Regulatory graph (≡ our influence graph). Naldi et al. [2] '
         'define a regulatory graph as "a labelled directed graph where '
         'nodes represent genes (or, more generally, regulatory '
         'components) and arcs (directed edges) represent interactions '
         'between genes" — this is precisely what BooleanNetwork.influence_'
         'graph() in network.py constructs. They further classify '
         'interactions as activations, repressions, or ambivalent '
         '("bullet arrows") — corresponding one-to-one with our +, −, ? '
         'sign inference (§4.2).'),

        ('Normal',
         'State transition graph. Naldi et al. [2] (§2): "the (discrete) '
         'dynamics of the system can then be represented by state '
         'transition graphs, where vertices represent states of the system '
         '(i.e. n-tuples giving the expression levels of the n genes), '
         'and arcs represent transitions between these states." — this '
         'is *the* object built by stg.build_state_transition_graph() in '
         'our codebase.'),

        ('Normal',
         'Synchronous and asynchronous updating policies. Naldi et al. [2] '
         '(§2): "state transition graphs are generated either on the basis '
         'of a fully synchronous assumption (all updating calls are then '
         'executed simultaneously) or on the basis of a fully asynchronous '
         'approach (all updating calls are then considered independently)." '
         '— our two scheme names ("synchronous" / "asynchronous") and their '
         'semantics are aligned letter-for-letter with this definition.'),

        ('Normal',
         'Stable states and attractor analysis. Naldi et al. [2] (§3.2) '
         'note that "the most frequent questions [for state transition '
         'graphs] deal with the identification of the stationary states or '
         'other attractors, of the corresponding basins of attraction, as '
         'well as with the delineation of transition paths from given '
         'states to specific attractors." — these are *exactly* the four '
         'pieces of output our analyzer produces and shows in the '
         'Streamlit UI: attractors (fixed/cyclic/complex), basins, and '
         'simulated trajectories.'),

        ('Normal',
         'Strongly-connected components for attractor detection. '
         'Naldi et al. [2] (§3.2) specifically mention that "[GINsim] '
         'provides means to determine the strongly connected components '
         '(simple or intertwined cycles) of the state transition graph, '
         'as well as the paths going through specific states." — Tarjan\'s '
         'SCC algorithm is exactly the foundation of our '
         'attractors.find_attractors() function (§4.4) and of the JS port '
         'in the live web demo.'),

        ('Normal',
         'Mutant simulation by clamping a node. Naldi et al. [2] (§4.3) '
         'explain that mutations are simulated "by fixing the value of '
         'the gene in the corresponding cell to a fixed level" — this is '
         'the same mechanism we expose in the simulator tab of the web '
         'demo (the user can lock specific bits of the initial state to '
         'reproduce knock-out / over-expression scenarios).'),

        ('Normal',
         'Exponential growth of the state space; need for selective '
         'exploration. Naldi et al. [2] (§3.2) acknowledge: "the '
         'simulation of a Boolean regulatory graph with n genes can lead '
         'to a transition graph with up to 2^n states. We thus face the '
         'classical problem of the exponential growth of the size of the '
         'state space." — this rationale directly justifies §3 of the work '
         'plan and the optimisations introduced in our system: '
         '(i) sub-graph rendering when |STG| > 512 in the live demo, '
         '(ii) Tarjan-based detection rather than naive cycle search, and '
         '(iii) Z3-Solver integration for fast singleton attractor search.'),
    ]
    insert_block_after(anchor, items)
    print('  ✓ inserted §2.6 "Mapping to Reference Literature"')
else:
    print('  · §2.6 already present, skipped')


# ---------------------------------------------------------------------------
# (3) New subsection 5.5 — Discussion: Alignment with the Literature
# ---------------------------------------------------------------------------

SENTINEL_5_5 = '5.5. Discussion: Alignment with the Literature'

if not any(p.text.startswith(SENTINEL_5_5) for p in doc.paragraphs):
    # anchor on the last paragraph of §5.4
    anchor = find_par('Faure et al. (2006) presented a 10-node Boolean model')
    items = [
        ('Heading 2', SENTINEL_5_5),
        ('Normal',
         'The four case studies above (§5.1–§5.4) are not arbitrary '
         'choices: each one validates a specific theoretical prediction '
         'from the reference papers and demonstrates that our '
         'implementation reproduces the published behaviour.'),

        ('Normal',
         'Bistable toggle (§5.1). Schwab et al. [1] (§3.2) describe '
         'fixed-point attractors as the "Steady-state attractors" that '
         '"comprise only one state … occur in both synchronous and '
         'asynchronous BNs." Our analyzer reports exactly two such '
         'attractors, (1,0) and (0,1), in agreement with the steady-state '
         'theory of mutual repression. The synchronous-only spurious '
         'cycle (0,0)↔(1,1) — which our analyzer also detects — '
         'illustrates Schwab et al.\'s warning [1] (§5.1) that "stability '
         'analysis of attractors in synchronous Boolean networks showed '
         'that many of them are artefacts from the synchronous update '
         'scheme." This confirms the value of running both schemes side-'
         'by-side.'),

        ('Normal',
         'Repressilator (§5.2). The length-6 synchronous cycle is a '
         '"simple cycle" in the sense of Schwab et al. [1] (§3.2): '
         '"Simple cycles are attractors which are formed by a sequence '
         'of states of a certain length which are periodically repeated." '
         'Our visualisation makes this concrete by colour-coding all six '
         'cyclic states in the STG drawing.'),

        ('Normal',
         'Fission yeast cell cycle (§5.3). The 9-node Davidich–Bornholdt '
         'model is a textbook example of a biological BN whose dominant '
         'attractor (the G1 state) has a very large basin of attraction. '
         'Schwab et al. [1] (§5.1) explicitly note that "the larger the '
         'basin of attraction is the more the attractor is likely to be '
         'biologically meaningful" — which is exactly what our analyzer '
         'reports (one fixed-point attractor with a basin covering the '
         'overwhelming majority of the 2^9 = 512 states).'),

        ('Normal',
         'Mammalian cell cycle (§5.4). The complex attractor reported by '
         'Faure et al. (2006) under asynchronous update is recovered by '
         'our analyzer with the structure described in Schwab et al. [1] '
         '(§3.2): "Complex attractors are formed by overlapping loops '
         'which origin from the possibility of reaching more than one '
         'successor state in the asynchronous update scheme." Our '
         'classify_attractor() function (§4.4) detects this branching '
         'inside the SCC and tags the attractor as "complex" rather than '
         '"cyclic".'),

        ('Normal',
         'Methodological alignment with GINsim. Naldi et al. [2] state '
         'that GINsim 2.3 supports "stationary states or other attractors, '
         'of the corresponding basins of attraction" and uses "strongly '
         'connected components" to compute them. Our pipeline '
         '(parser → BooleanNetwork → STG → Tarjan/condensation → '
         'attractors → basins) follows the same architectural shape, with '
         'two restrictions for pedagogical clarity: '
         '(i) we focus on Boolean (max_i = 1) variables instead of the '
         'multi-valued logic that GINsim supports, and '
         '(ii) our update schemes are pure synchronous and pure '
         'asynchronous, omitting the priority-class refinements introduced '
         'in GINsim 2.3 (Naldi et al. [2] §3) — those are a natural '
         'extension and are listed as future work in §7.'),
    ]
    insert_block_after(anchor, items)
    print('  ✓ inserted §5.5 "Discussion: Alignment with the Literature"')
else:
    print('  · §5.5 already present, skipped')


# ---------------------------------------------------------------------------
# (4) Strengthen the bibliography entries for [1] and [2]
# ---------------------------------------------------------------------------

REF_EDITS = [
    (
        '[1] Schwab, J. D., Kühlwein, S. D.',
        '[1] Schwab, J. D., Kühlwein, S. D., Ikonomi, N., Kühl, M., & Kestler, H. A. (2020). Concepts in Boolean network modeling: What do they all mean? Computational and Structural Biotechnology Journal, 18, 571–582.',
        '[1] Schwab, J. D., Kühlwein, S. D., Ikonomi, N., Kühl, M., & Kestler, H. A. (2020). Concepts in Boolean network modeling: What do they all mean? Computational and Structural Biotechnology Journal, 18, 571–582. https://doi.org/10.1016/j.csbj.2020.03.001 — comprehensive review of Boolean network theory; the source of our update-scheme taxonomy (§2.1), the formal definition of state graphs and attractor classes (§3.2), the strong/weak basin distinction (§3.3), the monotonicity-based sign convention for influence graphs, and the NP-hardness rationale for our optimisation phase.',
    ),
    (
        '[2] Naldi, A., Berenguier, D.,',
        '[2] Naldi, A., Berenguier, D., Fauré, A., Lopez, F., Thieffry, D., & Chaouiya, C. (2009). Logical modelling of regulatory networks with GINsim 2.3. BioSystems, 97(2), 134–139.',
        '[2] Naldi, A., Berenguier, D., Fauré, A., Lopez, F., Thieffry, D., & Chaouiya, C. (2009). Logical modelling of regulatory networks with GINsim 2.3. BioSystems, 97(2), 134–139. https://doi.org/10.1016/j.biosystems.2009.04.008 — reference paper for the GINsim toolchain. Provides the formal definitions of regulatory graph and state-transition graph that our influence_graph() and build_state_transition_graph() implementations directly mirror, the SCC-based attractor analysis we replicate with Tarjan, and the mutant-clamping methodology our simulator exposes.',
    ),
]

for prefix, old, new in REF_EDITS:
    try:
        par = find_par(prefix)
    except LookupError:
        print(f'  ! reference paragraph not found: {prefix!r}')
        continue
    if old in par.text:
        replace_text_preserving_style(par, old, new)
        print(f'  ✓ reference enriched: {prefix[:40]}...')
    else:
        print(f'  · reference already enriched: {prefix[:40]}...')

print('--- finished REF_EDITS ---', flush=True)

# We deliberately skip the table of contents.  Earlier attempts to patch
# it programmatically caused python-docx to abort silently mid-run; the
# section reorder is small enough that the user can refresh the TOC by
# editing two lines by hand if desired.

# ---------------------------------------------------------------------------
print('--- entering save step ---', flush=True)
import traceback as _tb
try:
    doc.save(OUTPUT)
    print(f'Saved -> {OUTPUT}', flush=True)
except Exception as _exc:
    print('SAVE FAILED:', _exc, flush=True)
    _tb.print_exc()
y mid-run; the
# section reorder is small enough that the user can refresh the TOC by
# editing two lines by hand if desired.

# ---------------------------------------------------------------------------
print('--- entering save step ---', flush=True)
import traceback as _tb
try:
    doc.save(OUTPUT)
    print(f'Saved -> {OUTPUT}', flush=True)
except Exception as _exc:
    print('SAVE FAILED:', _exc, flush=True)
    _tb.print_exc()
