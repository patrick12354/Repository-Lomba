# Next wave, written from the session-38 campaign results

Registered before any new trial runs, as `docs/6.md` §9 Task 4 requires.

## What this wave measured

27 core configurations screened on B1+B2 at two seeds, 10 confirmed at five seeds on all six
blocks, 3 rule-derived refinements, and a second seed block for the four best. No configuration
cleared the promotion bar. The bar was not moved.

## The one direction that is real

`B04` — `hbt` `n_estimators` 900 → 1400, nothing else — improves **every block and every
population, on two independent seed blocks**:

| seed block | pooled | matched | pooled 7d | worst H | member |
|---|---:|---:|---:|---:|---:|
| 0–4 | −0.010732 | −0.016837 | −0.023697 | −0.006254 | −0.040178 |
| 100–104 | −0.013437 | −0.021556 | −0.024821 | −0.006030 | −0.042265 |

It clears eight of the nine gate conditions. It fails only the pooled magnitude, which requires
−0.02. `I01` at 1100 trees improves everything too but by less, so the response is monotone in
tree count over 900 → 1100 → 1400 rather than peaked. **The obvious question this wave did not
ask: where does that curve stop?** 1400 was the largest value in the registry, chosen before any
result, and the campaign rules forbid inventing a larger point after seeing that the largest one
won. That is the first item for the next wave, registered here rather than run now.

## What each family established

| family | best | pooled | reading |
|---|---|---:|---|
| A masking, single view | A04 | +0.0016 | removing the duplication confound did not rescue masking; the view effect measured in §261 is real but too small to matter |
| B hbt capacity | B04 | −0.0107 | more trees helps consistently; less capacity (B01 leaves 7) helps B1 and hurts H1 by +0.107 |
| C history length | C04 | +0.0125 | truncating the label prefix is clearly harmful; 21 days costs +0.34 pooled on the screen |
| D increment capacity | D01 | −0.0184 | smaller increment trees nearly clear the bar on primary, but H1 worsens +0.0386 on both seed blocks — a real block-dependence, not noise |
| E joint level/change loss | E02 | +0.0900 | the custom-objective path itself costs +0.113 (E00), and the change penalty recovers only part of it; the objective was never the binding problem |
| F inference averaging | F01 | −0.0024 | tiny, consistent, reproduces almost exactly across seed blocks; too small to matter alone |

## Questions worth a wave, in order

1. **Where does the tree-count curve stop?** Register 1400/1800/2400 and a learning-rate pairing
   before running. If the gain is monotone to 2400 the mechanism is underfitting, and that is a
   different story from the one this log has been telling since §258.
2. **Why does D01 help the primary blocks and hurt H1?** The effect repeats on two seed blocks, so
   it is a property of the block, not of the seed. H1 is the most recent 7-day window; if smaller
   increment trees are worse specifically there, that is a measurable regime statement rather than
   a tuning accident.
3. **Do B04, D01 and F01 compose?** They move different components. `docs/6.md` §6 forbids the H
   family unless the parents pass individual confirmation, and none did — so this needs its own
   registered wave with the combination as the hypothesis rather than as a leftover slot.

## What not to do

Do not lower the 0.02 bar so B04 fits under it. Do not add tree counts beyond the registry in this
wave. Do not read family E's failure as evidence about joint supervision — E00 shows most of the
gap is the plumbing, and that control was the point.
