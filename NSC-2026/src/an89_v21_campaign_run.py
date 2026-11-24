"""Session 38: run the campaign in stages, checkpointing after every trial.

    --stage screen    all 27 core configs, B1+B2, two seeds, against a two-seed control
    --stage confirm   the configurations the written rule selects, five seeds, all six blocks
    --stage refine    follow-up ids chosen from the confirmation table

A trial that raises is recorded with its traceback and the run continues -- one broken
configuration is not a reason to abandon the wave. A trial that has already been written to the
ledger is skipped under `--resume`, and a config-digest mismatch refuses the resume rather than
silently mixing two definitions of the same id.

The screen is triage only. Nothing is adopted from it, and its control is refitted at the SAME two
seeds as the candidates rather than compared against the cached five-seed member.

    .venv/Scripts/python.exe src/an89_v21_campaign_run.py --stage screen --resume
"""
import argparse
import json
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an47_v21_forward_benchmark as a47
import an59_v21_candidate_contract as c
import an76_v21_level_shape as a76
import v21_campaign_registry as reg
import v21_campaign_models as cm

OUT = ROOT / 'outputs' / 'campaign_v21_s38'
FROZEN = ROOT / 'outputs' / 'audit_v21_s27' / 'preds_v21_increment.pkl'
TOL = 1e-9


def contexts(g, y, blocks, feats):
    """Per-block context plus the cached member frames, built once and reused by every trial."""
    models_l2 = list(fp.MODELS_L2)
    cache15 = a47.load_cache(a76.CACHE_15, a76.MANIFEST_15)
    out = []
    want = set(blocks)
    for name, blk in cache15.loc[cache15.scope == 'outer'].groupby('block', sort=False):
        if name not in want:
            continue
        d = blk.sort_values('datetime')
        O, V, _o = a76.base_frames(cache15, name, models_l2)
        ctx = a76.block_context(g, y, name, d, feats)
        gh = g.loc[g.index <= ctx['horizon_end']]
        ctx['mask'] = a47.train_mask_before(g, gh, y, ctx['origin'])
        ctx['yh'] = y.reindex(gh.index)
        V = V.copy()
        V['tod'] = ctx['F'].loc[ctx['idx'], 'tod'].to_numpy()
        out.append(dict(name=name, family='15d', d=d, O=O, V=V, ctx=ctx))
    if 'H1_last7d' in want or 'H2_last14d' in want or 'H3_last21d' in want:
        cache7 = a76.load_validated(a76.CACHE_7, a76.MANIFEST_7, '7-day forward')
        oof7 = a76.load_validated(a76.OOF7, a76.OOF7_MANIFEST, 'rebuilt 7-day OOF')
        for name, blk in cache7.loc[cache7.scope == 'outer'].groupby('block', sort=False):
            if name not in want:
                continue
            d = blk.sort_values('datetime')
            V = pd.DataFrame({m: d['m_' + m].to_numpy() for m in models_l2},
                             index=pd.DatetimeIndex(d.datetime))
            V['y'] = d.y.to_numpy()
            ctx = a76.block_context(g, y, name, d, feats)
            gh = g.loc[g.index <= ctx['horizon_end']]
            ctx['mask'] = a47.train_mask_before(g, gh, y, ctx['origin'])
            ctx['yh'] = y.reindex(gh.index)
            V['tod'] = ctx['F'].loc[ctx['idx'], 'tod'].to_numpy()
            out.append(dict(name=name, family='7d', d=d, O=O if False else oof7[name],
                            V=V, ctx=ctx))
    return out


def solve_arm(blk, q, terms):
    V = blk['V'].copy()
    V['hbt'] = np.clip(q, *cm.CLIP)
    level = a47.stack_on(blk['O'], V, list(fp.MODELS_L2))
    return level, a47.solve(level, blk['ctx']['idx'], terms)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', default='screen',
                    choices=('screen', 'confirm', 'refine', 'stability'))
    ap.add_argument('--ids', nargs='*', default=None)
    ap.add_argument('--resume', action='store_true')
    ap.add_argument('--out', default=str(OUT))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    ledger_path = out / ('ledger_%s.csv' % a.stage)
    preds_path = out / ('preds_%s.pkl' % a.stage)

    # Every wave the registry knows about, so `--ids J02` resolves. The screen's DEFAULT is
    # still the session-38 core wave -- a later wave must be asked for by id rather than
    # silently joining a re-run of the screen.
    lookup = reg.by_id(reg.all_trials())
    if a.stage == 'screen':
        ids = a.ids or [t['id'] for t in reg.core_trials()]
        blocks = list(reg.SCREEN_BLOCKS)
        seeds_hbt, seeds_inc = reg.SCREEN_HBT_SEEDS, a47.SEEDS_INC[:2]
    else:
        if a.stage == 'stability':
            # Section 8's second seed block. Same configurations, different seeds, so a gain that
            # is really seed noise shows up as one that does not repeat.
            ids = a.ids or []
            assert ids, 'name the ids to re-check on the second seed block'
        elif a.stage == 'refine':
            # Family I points come from the written rules in the registry, not from the
            # confirmation selection file -- reusing that list would silently re-run confirm.
            ids = a.ids or [t['id'] for t in reg.refine_trials()]
        else:
            sel = json.loads((out / 'confirm_selection.json').read_text()) \
                if (out / 'confirm_selection.json').exists() else {}
            ids = a.ids or sel.get('ids', [])
        assert ids, 'no ids to run; run the screen and the reporter first'
        blocks = ['B1_last15d', 'B2_prev15d', 'B3_shift7d',
                  'H1_last7d', 'H2_last14d', 'H3_last21d']
        if a.stage == 'stability':
            seeds_hbt = reg.STABILITY_HBT_SEEDS
            seeds_inc = tuple(x + 100 for x in a47.SEEDS_INC)
        else:
            seeds_hbt, seeds_inc = reg.CONFIRM_HBT_SEEDS, a47.SEEDS_INC

    done = set()
    if a.resume and ledger_path.exists():
        prev = pd.read_csv(ledger_path)
        for r in prev.itertuples():
            stored = lookup.get(r.id)
            if stored is not None and reg.config_digest(stored) != r.config_digest:
                raise ValueError('resume refused: %s has a different config digest on disk' % r.id)
        done = set(prev.loc[prev.status == 'ok'].id) if 'status' in prev else set(prev.id)
        print('resuming; %d trials already recorded' % len(done), flush=True)

    g = fp.load_grid()
    y = g[fp.TARGET]
    grid_start = g.index.min()
    frozen = pd.read_pickle(FROZEN)
    feats, view_cache = {}, {}
    blks = contexts(g, y, blocks, feats)
    print('stage=%s  blocks=%s  hbt seeds=%s  inc seeds=%s'
          % (a.stage, [b['name'] for b in blks], list(seeds_hbt), list(seeds_inc)), flush=True)

    # ---- control at the SAME seeds, plus the frozen-artifact check where it applies ----------
    ctrl = {}
    for blk in blks:
        t0 = time.time()
        q, terms = cm.zero_change(g, y, blk['ctx'], seeds_hbt, seeds_inc)
        level, z = solve_arm(blk, q, terms)
        ctrl[blk['name']] = dict(q=q, z=z, level=level, terms=terms)
        note = ''
        if blk['family'] == '15d' and tuple(seeds_hbt) == tuple(reg.CONFIRM_HBT_SEEDS) \
                and tuple(seeds_inc) == tuple(a47.SEEDS_INC):
            ref = frozen.loc[(frozen.block == blk['name']) & (frozen.scope == 'outer')] \
                .sort_values('datetime')
            e = float(np.max(np.abs(z - ref.recon.to_numpy())))
            assert e < TOL, '%s: the control does not reproduce the frozen v21 recon (%.3g)' \
                % (blk['name'], e)
            note = ' (reproduces frozen v21)'
        print('  control %-12s z %.6f  [%.0f s]%s'
              % (blk['name'], fp.rmse(blk['d'].y, z), time.time() - t0, note), flush=True)

    rows, per_row = [], []
    if a.resume and ledger_path.exists():
        rows = pd.read_csv(ledger_path).to_dict('records')
        if preds_path.exists():
            per_row = [pd.read_pickle(preds_path)]

    for tid in ids:
        if tid in done:
            continue
        trial = lookup[tid]
        t0 = time.time()
        try:
            for blk in blks:
                q, terms, info = cm.run_trial(trial, g, y, blk['ctx'], seeds_hbt, seeds_inc,
                                              grid_start, view_cache)
                level, z = solve_arm(blk, q, terms)
                yv = blk['d'].y.to_numpy(float)
                base = ctrl[blk['name']]
                rows.append(dict(id=tid, family=trial['family'], component=trial['component'],
                                 kind=trial['kind'], block=blk['name'],
                                 block_family=blk['family'], stage=a.stage,
                                 config_digest=reg.config_digest(trial),
                                 n=len(blk['d']), status='ok',
                                 rmse_member=fp.rmse(yv, np.clip(q, *cm.CLIP)),
                                 rmse_member_ctrl=fp.rmse(yv, np.clip(base['q'], *cm.CLIP)),
                                 rmse_z=fp.rmse(yv, z), rmse_z_ctrl=fp.rmse(yv, base['z']),
                                 d_vs_ctrl=fp.rmse(yv, z) - fp.rmse(yv, base['z']),
                                 seconds=round(time.time() - t0, 1),
                                 info=json.dumps(info, default=str)))
                per_row.append(pd.DataFrame(dict(
                    id=tid, family=trial['family'], block=blk['name'],
                    block_family=blk['family'], stage=a.stage,
                    datetime=blk['ctx']['idx'], y=yv, q=np.clip(q, *cm.CLIP),
                    q_ctrl=np.clip(base['q'], *cm.CLIP), z=z, z_ctrl=base['z'],
                    origin=blk['ctx']['origin'], horizon_end=blk['ctx']['horizon_end'],
                    score=blk['d'].score.to_numpy())))
            got = [r for r in rows if r['id'] == tid and r['stage'] == a.stage]
            print('  %-4s %-14s %s  [%.0f s]'
                  % (tid, trial['component'],
                     '  '.join('%s %+.5f' % (r['block'][:2], r['d_vs_ctrl']) for r in got),
                     time.time() - t0), flush=True)
        except Exception as exc:                                  # one trial must not stop the wave
            rows.append(dict(id=tid, family=trial['family'], component=trial['component'],
                             kind=trial['kind'], block='', block_family='', stage=a.stage,
                             config_digest=reg.config_digest(trial), n=0, status='error',
                             seconds=round(time.time() - t0, 1),
                             info=json.dumps(dict(error=str(exc),
                                                  trace=traceback.format_exc()[-2000:]))))
            print('  %-4s FAILED: %s' % (tid, exc), flush=True)
        pd.DataFrame(rows).to_csv(ledger_path, index=False)
        if per_row:
            pd.concat(per_row, ignore_index=True).to_pickle(preds_path)

    L = pd.DataFrame(rows)
    L.to_csv(ledger_path, index=False)
    if per_row:
        pd.concat(per_row, ignore_index=True).to_pickle(preds_path)
    c.write_json(out / ('manifest_%s.json' % a.stage), dict(
        created=pd.Timestamp.now().isoformat(timespec='seconds'), stage=a.stage,
        ids=list(ids), blocks=blocks, seeds_hbt=list(seeds_hbt), seeds_inc=list(seeds_inc),
        registry=reg.registry_manifest(),
        inputs=a47.input_hashes(), code=a47.code_hashes(),
        helper_code={p: a47.md5(ROOT / p) for p in
                     ('src/v21_campaign_registry.py', 'src/v21_campaign_models.py',
                      'src/v21_joint_level_loss.py', 'src/v21_sensor_masking.py',
                      'src/an89_v21_campaign_run.py')}))
    ok = L.loc[L.status == 'ok']
    if len(ok):
        piv = ok.pivot_table(index='id', columns='block', values='d_vs_ctrl')
        print('\n' + piv.round(5).to_string())
    print('\nwrote %s' % ledger_path)


if __name__ == '__main__':
    main()
