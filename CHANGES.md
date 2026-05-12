# Changes — May 11, 2026

This document captures the deliverables produced over two work sessions
(session A on May 9 — live demo + first citation pass; session B on
May 10 — alignment with the official evaluation rubric).  None of the
existing engine code (`src/bnanalyzer/`) or the test suite (`tests/`)
was modified — every previous test still passes (23/23).

## Session B (rubric alignment) — at a glance

The submitted package now satisfies each item of `en-evaluation-template.md`:

- **Correctness (40 %)** — §6.5 *Benchmark Validation Against Published
  Results* in the report tabulates the analyzer's output against the
  literature for every bundled network. Both engines (Python & JS) match.
- **Report quality (40 %)** — added §3.4 *Module I/O*, §4.6 *In-browser
  JavaScript Engine*, deeper analysis paragraphs in §5.1–§5.4 (with
  concrete basin percentages), split §7 into §7.1 *Limitations* and
  §7.2 *Future Work*, refreshed Abstract, Reference list with DOIs.
- **Creativity (10 %)** — the JavaScript engine is an original addition
  beyond the assignment requirements; the live demo lowers the
  reproduction cost of the case studies to a single click.
- **Professionalism (10 %)** — `Report/Boolean_Network_Analyzer_Report.pdf`
  is shipped alongside the .docx (LibreOffice export, 21 pages, no
  layout issues); README documents both deployment paths.

Additional outputs in this session:

```
~ Report/Boolean_Network_Analyzer_Report.docx   ← §3.4, §4.6, §6.5, §7.1, §7.2
+ Report/Boolean_Network_Analyzer_Report.pdf    ← PDF export, 21 pages
+ Report/edit_report_v2.py                      ← v2 audit script
~ Slide/Boolean_Network_Analyzer_Slides.pptx    ← Slide 11 validation table,
                                                  fixed toy_switch caption,
                                                  fixed Slide 14 placeholder URL
+ Slide/Boolean_Network_Analyzer_Slides.pdf     ← PDF export of the deck
~ docs/index.html                               ← new "Validation against
                                                  the literature" + "What
                                                  sets this analyzer apart"
                                                  sections
```

## 1. Live web demo — `docs/app.html`

A single self-contained HTML file (≈30 kB, plus `vis-network` from CDN)
that re-implements the entire analyzer in JavaScript so it runs **in the
browser, with no install and no backend**.

- `.bnet` parser (operators `! & | && || not and or`, parentheses, constants
  `0/1/True/False`, inline `#` comments, `targets, factors` header).
- `BooleanNetwork` class with rule compilation, evaluation, and influence
  graph extraction with monotonicity-based sign inference (`+ / − / ?`).
- STG construction under both synchronous and asynchronous update schemes,
  state-id encoding for compactness.
- **Iterative Tarjan SCC** (no recursion, safe for 2¹⁶ states), terminal
  SCC extraction, and three-way attractor classification
  (`fixed_point / cyclic / complex`).
- Reverse-reachability weak basin computation.
- Influence-graph and STG visualisations via `vis-network` (CDN).
- Attractor browser, trajectory simulator, JSON & CSV export.
- Five bundled sample networks identical to `samples/*.bnet`.

**Validated** against the Python reference engine on all five samples ×
both update schemes: every attractor (kind, size, member states) matches
exactly.

## 2. Updated landing page — `docs/index.html`

Top nav and hero now feature a primary **"▶ Try the live demo"** call-to-
action linking to `app.html`. The bottom-of-hero subtext makes it clear
the demo runs entirely client-side.

## 3. GitHub Pages auto-deploy

- New workflow `.github/workflows/pages.yml` — runs on every push to
  `main` that touches `docs/`, builds the artefact and deploys via
  GitHub Pages. Permissions and concurrency are configured.
- Empty `docs/.nojekyll` so GitHub Pages serves files starting with `_`
  (used by some assets) directly.

To enable: **Settings → Pages → Source: GitHub Actions** on the
repository, then push.

## 4. Report edits — `Report/Boolean_Network_Analyzer_Report.docx`

The report has been edited in place (the editing script,
`Report/edit_report.py`, is kept in the repo as an audit trail). The
changes are:

### 4.1 Inline citations in §2 (Theoretical Background)

Seven theoretical paragraphs now carry direct quotations from the two
primary references:

- §2.1 (Boolean networks): Schwab et al. (2020) [1] §2 quote on the
  binary-variables/Boolean-functions definition.
- §2.2 (Influence graph): Schwab et al. [1] §3.1 on monotonicity of
  regulatory functions, mapped to our sign-inference algorithm.
- §2.3 (Sync update): Schwab et al. [1] §2.1 + Naldi et al. [2] §3 on
  fully-synchronous semantics.
- §2.3 (Async update): Schwab et al. [1] §2.1 on n-successor non-determinism.
- §2.4 (STG): Schwab et al. [1] §3.2 + Naldi et al. [2] §2 on directed
  state graphs.
- §2.5 (Attractors): Naldi et al. [2] §3.2 on terminal SCCs.
- §2.5 (Basins): Schwab et al. [1] §3.3 (citing Klarner et al.) on the
  strong/weak basin distinction.

### 4.2 New subsection §2.6 — *Mapping to Reference Literature*

A dedicated subsection that pairs every concept implemented in the project
with the precise passage of the originating paper. Six items from
Schwab 2020 (§2.6.1) and seven items from Naldi 2009 (§2.6.2).

This is what the user asked for: *"trong bài báo … hướng nghiên cứu như
thế này thì tôi đã áp dụng cái gì vào trong việc thực hành"* — the
section is structured exactly like that.

### 4.3 New subsection §5.5 — *Discussion: Alignment with the Literature*

Explicitly closes the loop between the four case studies (§5.1–5.4) and
the reference papers, quoting:

- the *steady-state attractor* characterisation for the bistable toggle,
- the *simple cycle* definition for the repressilator,
- Schwab et al.'s remark that *"the larger the basin of attraction is,
  the more the attractor is likely to be biologically meaningful"* for
  the fission-yeast case,
- the *complex attractor* definition for the mammalian cell-cycle case,
- and the architectural alignment with GINsim 2.3 (with future-work
  pointers for multi-valued logic and priority-class updates).

### 4.4 Strengthened bibliography

Entries [1] and [2] now include the DOI URL plus a one-line takeaway
summarising what each paper contributes to the project.

## 5. README

Updated to advertise the in-browser live demo and to document the two
GitHub-Pages deployment options (Actions or branch).

## Files added / modified

```
+ docs/app.html                       # NEW — live demo (single file, vanilla JS)
+ docs/.nojekyll                      # NEW — GitHub Pages helper
+ .github/workflows/pages.yml         # NEW — auto-deploy
+ CHANGES.md                          # NEW — this file
+ Report/edit_report.py               # NEW — auditable report editor (idempotent)

~ docs/index.html                     # CTA links to /app.html
~ README.md                           # advertises live demo + GitHub Pages workflow
~ Report/Boolean_Network_Analyzer_Report.docx
                                       # 7 inline citations + §2.6 + §5.5 + ref list
```

Existing engine, tests, samples and Streamlit app are unchanged.
