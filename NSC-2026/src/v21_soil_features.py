"""Session 41: the soil block restored, minus the six columns that actually break.

`drop_soil` has removed 76 columns from every member since session 2. Both of its justifications
have since been withdrawn:

* §7 said only 7-12 % of the block's test values had training support. §97 measured that again on
  the current cleaning and found it false -- most of the block has full support.
* §97 then rested the decision on §96, "the block carries no residual signal at all". §96's
  headline claim is withdrawn in the file banner and in §229, and what remains of it for soil is a
  residual-stage LightGBM fitted on a session-14 blend's out-of-fold residuals. That asks whether
  these columns can predict what a blend fitted WITHOUT them got wrong; it does not ask whether the
  v21 members do better WITH them. §53 and §80 are this log's own reminders that member-level,
  blend-level and residual-level answers differ.

Measured directly on the private slice, 68 of the 76 sit at support 1.000 and the six that collapse
are all `_sd6h` **dispersion** columns -- `soil_humidity_line3_sd6h` and `soil_humidity_line2_sd6h`
at 0.0000, `soil_ec_line3_sd6h` at 0.0039, `soil_ec_line2_sd6h` at 0.0078. §7's mechanism is real
and it is narrow: when irrigation halts the probes stop fluctuating (test std is 0.16-0.23x train
std for the humidity probes), which destroys a rolling standard deviation and leaves a level alone.

So the decision the evidence supports is "drop six", and the arms below test that against "drop
seventy-six" (the incumbent), "drop none", and "drop everything except the six".
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp

# §19.2's bar, reused unchanged: the fraction of test values inside the training 1-99 % band.
SUPPORT_BAR = 0.916
SETS = ('incumbent', 'supported', 'all_soil', 'dispersion_only')


def augmented_features(grid):
    """`fp.make_features` with `drop_soil` not applied.

    Built from the same `clean_exog` output and concatenated with the same extra blocks in the same
    order, so every incumbent column is identical value-for-value and the frame is strictly
    additive. `tests/test_v21_soil_features.py` pins that.
    """
    c = fp.clean_exog(grid)
    base = fp.build_features(c)
    F = pd.concat([base, fp.tmin_block(c), fp.tend_block(c),
                   fp.ordstat_block(c, 'co2', fp.CO2_WINS),
                   fp.qblock(c, fp.TMIN_WINS), fp.qblock(c, fp.CO2_WINS, col='co2', rh=False)],
                  axis=1)
    return F.replace([np.inf, -np.inf], np.nan)


def restored_columns(F_aug):
    """The 76 `drop_soil` removes, in the augmented frame's own order."""
    keep = set(fp.drop_soil(F_aug))
    return [c for c in F_aug.columns if c not in keep]


def support(grid, F_aug, private_only=True):
    """Fraction of test values inside the training 1-99 % band, missing counted as neutral.

    `private_only` scores the far 70 % -- the slice that decides the competition and the one §78
    said had never been audited.
    """
    y = grid[fp.TARGET]
    is_tr = (grid.is_test == 0).to_numpy() & y.notna().to_numpy()
    is_te = (grid.is_test == 1).to_numpy()
    tr, te = F_aug.loc[is_tr], F_aug.loc[is_te]
    if private_only:
        te = te.iloc[220:]
    lo, hi = tr.quantile(0.01), tr.quantile(0.99)
    return (((te >= lo) & (te <= hi)) | te.isna()).mean()


def low_support_soil(grid, F_aug, bar=SUPPORT_BAR):
    """The restored columns that fail §19.2's bar on the private slice. Six, all `_sd6h`."""
    s = support(grid, F_aug)
    return [c for c in restored_columns(F_aug) if s[c] < bar]


def column_set(grid, F_aug, name):
    """Columns for one arm. Unknown names raise rather than defaulting to the incumbent, so a
    typo in a registry payload cannot silently score the control as a candidate."""
    if name not in SETS:
        raise ValueError('unknown column set %r; expected one of %s' % (name, SETS))
    keep = fp.drop_soil(F_aug)
    if name == 'incumbent':
        return list(keep)
    if name == 'all_soil':
        return list(F_aug.columns)
    bad = low_support_soil(grid, F_aug)
    if name == 'dispersion_only':
        return list(keep) + list(bad)
    return [c for c in F_aug.columns if c not in set(bad)]      # 'supported'
