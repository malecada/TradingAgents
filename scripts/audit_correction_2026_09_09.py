"""One immutable, preregistered development-only audit correction; no fits.

Run from the clean committed audit checkout with --source-data pointing at the
preserved original predlab data directory. No historical result is overwritten.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from tradingagents.predlab import registry, pp, features, losses, runner
from tradingagents.accounting import archive_returns
from tradingagents.predlab.meanstats import stationary_bootstrap_means
from scripts.predlab_run_battery import _resolve_names

KEY = 'audit_correction_2026_09_09'
DEV = ('2021-01-01', '2025-03-31')
CUTOFF = pd.Timestamp('2025-04-01', tz='UTC')


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for part in iter(lambda: fh.read(1024 * 1024), b''): h.update(part)
    return h.hexdigest()


def read_development(path: Path, hashes: dict) -> pd.DataFrame:
    """Filter before materialization; no holdout values are read into a frame."""
    hashes[str(path)] = sha256(path)
    schema = pq.ParquetFile(path).schema_arrow
    pandas_meta = json.loads(schema.metadata[b'pandas'])
    index = pandas_meta['index_columns']
    field = 'ts' if 'ts' in schema.names else index[0]
    if not isinstance(field, str): raise ValueError(f'No explicit time index: {path}')
    frame = pd.read_parquet(path, filters=[(field, '<', CUTOFF)])
    if 'ts' in frame.columns: frame = frame.set_index('ts')
    frame.index = pd.DatetimeIndex(frame.index)
    if frame.index.tz is None: raise ValueError(f'Naive timestamp in {path}')
    if not frame.index.is_monotonic_increasing or frame.index.has_duplicates:
        raise ValueError(f'Nonunique or unsorted clock in {path}')
    if len(frame) and frame.index.max() >= CUTOFF: raise ValueError('Holdout leakage')
    return frame


def infer_saved_enet_failures(series: pd.DataFrame, saved: pd.DataFrame,
                              refit_every: int, target: str) -> pd.Series:
    """Reconstruct deterministic availability, never estimate model coefficients.

    Original ENet could return its zero sentinel for unavailable model (<60
    complete training examples) or selected features. A valid zero prediction
    is preserved unless one of these conditions is independently established.
    """
    locations = series.index.get_indexer(saved.index)
    if (locations < 0).any(): raise ValueError('Saved forecast clock absent from input series')
    if not np.allclose(series.y.iloc[locations], saved.y_true, equal_nan=True):
        raise ValueError('Saved targets disagree with reconstructed original series')
    complete = np.isfinite(series.to_numpy(dtype=float)).all(axis=1)
    prefix = np.r_[0, np.cumsum(complete)]
    unavailable = np.zeros(len(saved), dtype=bool)
    fit_available = False
    for i, loc in enumerate(locations):
        if i % refit_every == 0: fit_available = prefix[loc] >= 60  # h=1 train_end=origin
        unavailable[i] = not fit_available or not np.isfinite(series.iloc[loc, 1:].to_numpy(dtype=float)).all()
    sentinel = .02 if target == 'T2_dir' else 0.
    if not np.allclose(saved.pred.to_numpy()[unavailable], sentinel, rtol=0, atol=0):
        raise ValueError('Failure sentinel differs: original fit/feature provenance cannot be established')
    return pd.Series(unavailable, index=saved.index)


def _plain(value):
    if isinstance(value, dict): return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [_plain(v) for v in value]
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (np.integer,)): return int(value)
    if isinstance(value, (np.bool_,)): return bool(value)
    return value


def require_strategy_clock(series: pd.Series, frequency: str, name: str) -> None:
    expected = pd.date_range(DEV[0], DEV[1], freq=frequency, tz="UTC")
    if not series.index.equals(expected) or not np.isfinite(series.to_numpy()).all():
        raise ValueError(f"{name}: incomplete original strategy clock or unavailable observations")


def strategies(source: Path, output: Path, hashes: dict, original: dict) -> dict:
    rv_day = read_development(source/'predlab/rv_1d/BTCUSDT.parquet', hashes)
    rv_hour = read_development(source/'predlab/rv_1h/BTCUSDT.parquet', hashes)
    def fc(cell, model):
        return read_development(source/f'predlab/forecasts/predlab_p2_ml/{cell}/{model}.parquet', hashes)
    variance = {m: fc('BTCUSDT_24h_T3_rv', m).pred for m in ('harq', 'har_levels')}
    variance['naive20'] = rv_day.rv.rolling(20).mean().shift(1)
    day_clock = pd.date_range(*DEV, freq="D", tz="UTC")
    hour_clock = pd.date_range(*DEV, freq="h", tz="UTC")
    require_strategy_clock(rv_day.ret.reindex(day_clock), "D", "S2 returns")
    require_strategy_clock(rv_hour.ret.reindex(hour_clock), "h", "S3 returns")
    rows, reports = {}, {'S2': {}, 'S3': {}}
    for name in ('harq', 'har_levels', 'naive20'):
        f = variance[name].loc[lambda x: (x.index >= DEV[0]) & (x.index <= pd.Timestamp(DEV[1], tz='UTC'))].dropna()
        require_strategy_clock(f, "D", f"S2 {name} forecast")
        assert pp.TAKER_BP == 5.0, "registered fee changed"
        r = pp.run_s2(f, np.expm1(rv_day.ret), target_ann=.20, lev_cap=3.)
        rows[name] = r
        reports['S2'][name] = {'original': original['S2'][name], 'corrected':
            {k: r[k] for k in ('sr_net','maxdd','tracking_err','avg_pos')},
            'n_days': len(r['rets']), 'first': str(r['rets'].index.min()), 'last': str(r['rets'].index.max())}
        archive_returns(r['rets'].rename('net').to_frame()).to_parquet(output/f's2_{name}.parquet')
    comparisons = {}
    for base in ('har_levels', 'naive20'):
        a = (rows['harq']['roll_vol']-.20)**2
        b = (rows[base]['roll_vol']-.20)**2
        paired = pd.concat({'harq': a,'base': b},axis=1).dropna()
        boot = stationary_bootstrap_means((paired.base-paired.harq).to_numpy(), n_boot=2000,mean_block=21,seed=0)
        reduction = 100*(rows[base]['tracking_err']-rows['harq']['tracking_err'])/rows[base]['tracking_err']
        p = float(np.mean(boot <= 0))
        checks = {'te_reduction_ge15pct': reduction >= 15, 'bootstrap_p_lt05':p < .05,
                  'sr_not_worse':rows['harq']['sr_net'] >= rows[base]['sr_net'],
                  'maxdd_not_worse':rows['harq']['maxdd'] <= rows[base]['maxdd']}
        comparisons[base] = {'n_paired_volatility_windows':len(paired), 'te_reduction_pct':reduction,
                             'p_harq_better':p,'checks':checks,'all_pass':all(checks.values())}
    reports['S2_criteria']={'original_rule':'HARQ TE reduction >=15% versus BOTH baselines, bootstrap p<.05, SR and MaxDD not worse',
                           'comparisons':comparisons,'passes_specific_gate':all(v['all_pass'] for v in comparisons.values()),
                           'validation_status':'No strategy validation; development-only accounting correction.'}
    prob=fc('BTCUSDT_1h_T2_dir','logit_lags5').pred
    # Preserve the original exact endpoint, including its midnight end on March31.
    prob=prob[(prob.index>=DEV[0]) & (prob.index<=pd.Timestamp(DEV[1],tz='UTC'))]
    require_strategy_clock(prob, "h", "S3 probability forecast")
    for threshold in (.50,.52):
        for smooth in (1,24):
            key=f's3_t{threshold}_h{smooth}'
            r=pp.run_s3(prob,np.expm1(rv_hour.ret),threshold,smooth)
            reports['S3'][key]={'original':original['S3'][key], 'corrected':
                {k:r[k] for k in ('sr_net','maxdd','time_in_mkt')},'n_hours':r['n_hours'],
                'sr_floor_pass':r['sr_net']>=1., 'eligible_to_graduate':False,
                'reason':'Original registration: exploratory forecast claim failed; cannot graduate past development this cycle.'}
            archive_returns(r['rets'].rename('net').to_frame()).to_parquet(output/f'{key}.parquet')
    reports['scope']='All 7 original cells. No S1 rerun, no parameter selection, no holdout. DSR across 13 legacy cells is not recomputed from invalidated S1 evidence; no candidate promotion.'
    return reports


def saved_enet(source: Path, output: Path, hashes: dict, gate: dict) -> list[dict]:
    result=[]
    proto=gate['protocol']
    frames={}
    for sym in ('BTCUSDT','ETHUSDT'):
        for grid,folder in (('1h','rv_1h'),('24h','rv_1d')):
            try:
                rv=read_development(source/f'predlab/{folder}/{sym}.parquet',hashes)
                # Original battery _clip used an inclusive midnight March31 cap.
                rv=rv.loc[rv.index <= pd.Timestamp(DEV[1], tz='UTC')]
                oi=read_development(source/f'predlab/oi_5m/{sym}.parquet',hashes)
                funding=read_development(source/f'predlab/funding/{sym}.parquet',hashes).fundingRate
                base=features.build_features(rv,grid)
                frames[sym,grid]=(rv,base.join(features.oi_features(oi,grid)).join(features.funding_features(funding,base.index)))
            except (FileNotFoundError, ValueError, KeyError) as exc:
                frames[sym,grid] = exc
    for cell in gate['cells']:
        sym,grid,tgt=cell['symbol'],cell['horizon'],cell['target']
        if sym not in ('BTCUSDT','ETHUSDT') or grid not in ('1h','24h') or tgt not in ('T1_ret','T2_dir','T3_rv','T4_vol'): continue
        record={'cell':cell['cell'],'model':'enet','baseline':cell['strong_baseline'],'status':'uncomputed'}
        try:
            if isinstance(frames[sym,grid], Exception):
                raise frames[sym,grid]
            rv,feat=frames[sym,grid]
            y=rv.ret if tgt in ('T1_ret','T2_dir') else rv.rv if tgt=='T3_rv' else np.log(rv.quote_volume.replace(0.,np.nan))
            key='T1T2' if tgt in ('T1_ret','T2_dir') else tgt
            selected=_resolve_names(gate['feature_sets'][key],grid)
            series=feat[selected].copy();series.insert(0,'y',y);series=series.dropna(subset=['y'])
            directory=source/'predlab/forecasts/predlab_p2_ml'/cell['cell'].replace('|','_')
            saved=read_development(directory/'enet.parquet',hashes)
            baseline=read_development(directory/f'{cell["strong_baseline"]}.parquet',hashes)
            if not saved.index.equals(baseline.index) or not np.allclose(saved.y_true,baseline.y_true,equal_nan=True):
                raise ValueError('Model and baseline clocks/targets differ')
            locations=series.index.get_indexer(saved.index)
            expected=series.index[proto['min_train'][grid]:]
            expected=expected[expected>=pd.Timestamp(cell['eval_start'],tz='UTC')]
            if not expected.equals(saved.index): raise ValueError('Full original forecast clock not reproducible')
            unavailable=infer_saved_enet_failures(series,saved,proto['refit_every'][grid],tgt)
            raw=saved.pred.copy();raw[unavailable]=np.nan
            loss=proto['loss'][tgt.split('_')[0]]
            loss_cell={}
            if loss=='mase':
                loss_cell['_mase_scale']=losses.mase_scale(series.y.iloc[:proto['min_train'][grid]].to_numpy(),m=24 if grid=='1h' else 7)
            diagnostic=runner.forecast_frame(saved.y_true.to_numpy(),raw.to_numpy(),baseline.pred.to_numpy(),loss,loss_cell)
            diagnostic.index=saved.index
            diagnostic['saved_pred']=saved.pred
            diagnostic['reconstructed_unavailable']=unavailable
            effective_loss=runner._loss_vector(loss,saved.y_true.to_numpy(),diagnostic.pred.to_numpy(),loss_cell)
            original_loss=runner._loss_vector(loss,saved.y_true.to_numpy(),saved.pred.to_numpy(),loss_cell)
            base_loss=runner._loss_vector(loss,saved.y_true.to_numpy(),baseline.pred.to_numpy(),loss_cell)
            scoreable=diagnostic.scoreable.to_numpy()
            record.update(status='diagnostic_complete',loss=loss,n_saved=len(saved),n_scoreable=int(scoreable.sum()),
                n_reconstructed_unavailable=int(unavailable.sum()),n_fallback=int((diagnostic.fallback_used & diagnostic.scoreable).sum()),
                raw_valid_coverage=float(diagnostic.raw_valid[scoreable].mean()),n_original_finite_loss=int(np.isfinite(original_loss).sum()),
                original_loss_mean=float(np.nanmean(original_loss)),corrected_loss_mean=float(np.mean(effective_loss[scoreable])),
                baseline_loss_mean=float(np.mean(base_loss[scoreable])),
                n_saved_sentinel_without_reconstructed_failure=int(((saved.pred==(.02 if tgt=='T2_dir' else 0.)) & ~unavailable).sum()),
                interpretation='Diagnostic replacement with the declared baseline; valid boundary/zero forecasts are preserved. No refit, selection, significance verdict or strategy validation.')
            diagnostic.to_parquet(output/(cell['cell'].replace('|','_')+'_enet.parquet'))
        except (FileNotFoundError,ValueError,KeyError) as exc:
            record.update(status='stopped_missing_or_inconsistent_provenance',reason=str(exc))
        result.append(record)
    if len(result)!=16: raise ValueError(f'Registered 16 forecast cells required; got {len(result)}')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-data',type=Path,required=True)
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    provenance=registry.preflight(KEY,DEV)
    gate=registry.get_experiment(KEY)
    output=ROOT/'data/predlab'/KEY
    if output.exists(): raise RuntimeError('Immutable correction output already exists; no rerun permitted')
    source=args.source_data.resolve()
    hashes={}
    for name,expected in gate['original_artifacts_sha256'].items():
        p=source/'predlab'/name
        found=sha256(p)
        if found!=expected: raise RuntimeError(f'Original artifact hash changed: {name}')
        hashes[str(p)]=found
    if not args.execute:
        print(json.dumps({'preflight':'passed','provenance':provenance,'execute':False}));return
    output.mkdir(parents=True,exist_ok=False)
    result={'experiment':KEY,**provenance,'window':DEV,'holdout_read':False,'models_refit':False,
            'registered_gate':gate,'source_data':str(source),'status':'running'}
    original=json.loads((source/'predlab/pp_dev_results.json').read_text())
    original_gates=json.loads((source/'predlab/gates.json').read_text())
    try:
        result['strategies']=strategies(source,output,hashes,original)
        result['enet']=saved_enet(source,output,hashes,original_gates['predlab_p2_ml'])
        result['status']='completed_with_qualifications' if any(r['status']!='diagnostic_complete' for r in result['enet']) else 'completed'
    except Exception as exc:
        result['status']='stopped';result['error']=f'{type(exc).__name__}: {exc}'
        raise
    finally:
        result['input_sha256']=hashes
        result['input_unchanged_after_run']=all(sha256(Path(p))==h for p,h in hashes.items())
        if not result['input_unchanged_after_run']: result['status']='invalid_input_changed'
        result['output_sha256']={p.name:sha256(p) for p in output.glob('*.parquet')}
        with (output/'result.json').open('x') as fh: json.dump(_plain(result),fh,indent=2,allow_nan=False)
        registry.log_trial(KEY,'all_registered_cells','fixed_saved_forecast_correction',gate,DEV,{'status':result['status'],'strategy_cells':7,'forecast_cells':16})
    print(json.dumps(_plain({'status':result['status'],'strategies':result.get('strategies'), 'enet':result.get('enet')}),indent=2))


if __name__=='__main__': main()
