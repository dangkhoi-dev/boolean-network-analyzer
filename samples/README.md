# Sample Boolean Networks

This folder contains five `.bnet` files that ship with the analyzer for
quick exploration and demos.

| File                          | Nodes | Notes                                                                 |
|-------------------------------|------:|-----------------------------------------------------------------------|
| `toy_switch.bnet`             |     3 | Tiny pedagogical example with a single fixed-point attractor.         |
| `bistable_toggle.bnet`        |     2 | Mutual repression — two stable steady states (Gardner *et al.* 2000). |
| `repressilator.bnet`          |     3 | Cyclic mutual repression — synchronous cycle of length 6.             |
| `fission_yeast.bnet`          |     9 | Reduced *S. pombe* cell-cycle model (Davidich & Bornholdt, 2008).     |
| `mammalian_cell_cycle.bnet`   |    10 | Reduced mammalian cell-cycle model (Faure *et al.*, 2006).            |

The `.bnet` format is a plain-text format (compatible with PyBoolNet /
BoolNet) where each non-empty, non-comment line declares one update rule:

    target, expression

Expressions support the operators `!` (NOT), `&` (AND), `|` (OR), and
parentheses; constants `0`/`1` and `True`/`False` are also recognized.
A header line `targets, factors` is optional and ignored.
