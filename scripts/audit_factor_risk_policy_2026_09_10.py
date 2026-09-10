"""One immutable fixed-grid risk-policy comparison; default CLI is read-free.

Only committed, pinned saved development targets and control receipts enter.
All state belongs to one sleeve/arm/cost path. No forecast fitting, network,
bootstrap, selection or historical result mutation is implemented.
"""
from __future__ import annotations

import argparse
from datetime import datetime,timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import sys

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.baseline_strategy_v2 import run_coin_backtest
from tradingagents.predlab import registry
from tradingagents.strategies.factor_risk_policy import FactorRiskPolicy,causal_sigma
from tradingagents.strategies import factor_risk_policy_evaluation as ev

KEY='risk_policy_2026_09_10'
WINDOW=('2021-11-07','2025-03-31')
OUTPUT='data/risk-policy/2026-09-10/results'
SOURCE='data/factor-correction/2026-09-10/results'
VARIANTS=ev.VARIANTS
COINS=ev.COINS
ARMS=[dict(id='A00',sizing='saved',reentry='immediate'),dict(id='A10',sizing='daily',reentry='immediate'),
      dict(id='A01',sizing='saved',reentry='new_target_episode'),dict(id='A11',sizing='daily',reentry='new_target_episode')]
REFS=['docs/risk-policy-2026-09-10/'+p for p in ('charter.md','fresh-validation-plan.md','original-gates.json',
    'original/baseline_strategy_v2.py','design-history-review.md','design-engine-review.md','design-evaluation-review.md')]+[
    'tradingagents/accounting.py','tradingagents/strategies/v2_sizing.py',
    'tradingagents/strategies/factor_risk_diagnostics.py','scripts/audit_factor_floor_2026_09_10.py']


def now(): return datetime.now(timezone.utc).isoformat()


def sha(path):
    path=Path(path)
    if path.is_symlink(): raise ValueError('symlink input/output is not admitted')
    before=path.stat(); digest=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):digest.update(chunk)
    after=path.stat()
    if (before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns):
        raise ValueError('input changed during hashing')
    return digest.hexdigest()


def encode_json(value): return (json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()


def write_json(path,value):
    payload=encode_json(value)
    with Path(path).open('xb') as stream:stream.write(payload)


def safe_path(root,name):
    if Path(name).is_absolute() or '..' in Path(name).parts: raise ValueError('unregistered input path')
    path=root/name
    if not path.resolve().is_relative_to(root.resolve()): raise ValueError('input outside checkout')
    return path


def verify_hashes(root,pins):
    for name,digest in pins.items():
        if sha(safe_path(root,name))!=digest: raise ValueError('pinned input mismatch: '+name)


def read_frame(path,date_column,start,end):
    """Clip using Arrow before materializing data, including old string dates."""
    if str(start.tz)!='UTC' or str(end.tz)!='UTC' or end>pd.Timestamp(WINDOW[1],tz='UTC'):
        raise ValueError('unregistered data window')
    dataset=ds.dataset(path,format='parquet'); field=dataset.schema.field(date_column)
    if pa.types.is_timestamp(field.type):
        a=start.tz_localize(None) if field.type.tz is None else start
        b=end.tz_localize(None) if field.type.tz is None else end
        low=pa.scalar(a.to_pydatetime(),type=field.type); high=pa.scalar(b.to_pydatetime(),type=field.type)
    elif pa.types.is_string(field.type) or pa.types.is_large_string(field.type):
        low=start.strftime('%Y-%m-%d'); high=end.strftime('%Y-%m-%dT00:00:00+00:00')
    else: raise ValueError('unsupported stored date schema')
    return dataset.to_table(filter=(ds.field(date_column)>=low)&(ds.field(date_column)<=high)).to_pandas()


def write_frame(path,frame):
    frame=frame.copy(); frame.attrs={}
    with Path(path).open('xb') as stream:frame.to_parquet(stream)


def validate_gate(gate):
    counts=dict(expected_configurations=18,expected_identities=72,expected_index_evaluations=288,
        expected_sleeve_books=576,expected_shadows=72,expected_direct_contrasts=54,
        expected_target_dates=1241,expected_trace_dates=1240)
    if any(gate[k]!=v for k,v in counts.items()):raise ValueError('registered grid denominator mismatch')
    if (gate['arms']!=ARMS or gate['coins']!=list(COINS) or gate['variants']!=list(VARIANTS)
            or gate['policy']!=ev.POLICY or gate['costs']!=ev.COSTS):raise ValueError('unimplemented policy/cost grid')
    expected_reporting=dict(return_annualization=365,zero_variance_ratio=None,formal_inference=False,
        winner_selection=False,periods=ev.PERIODS,direct_arms=['A10','A01','A11'],factorial_effects=['sizing','waiting','interaction'])
    if gate['reporting']!=expected_reporting:raise ValueError('reporting policy differs')
    if (tuple(gate['development_window'])!=WINDOW or gate['return_window']!=['2021-11-08','2025-03-31']
            or gate['allow_holdout'] is not False or gate['models_refit'] is not False or gate['network_allowed'] is not False
            or gate['output_dir']!=OUTPUT or gate['source_result']!=SOURCE+'/result.json'):
        raise ValueError('unregistered run scope')
    expected=[]; pins=set(REFS)|{SOURCE+'/result.json'}
    if len(gate['configurations'])!=18 or len({c['name'] for c in gate['configurations']})!=18:raise ValueError('configuration count mismatch')
    for config in gate['configurations']:
        name=config['name']
        if not name.replace('_','').isalnum():raise ValueError('unsafe configuration name')
        for arm in ARMS:expected.append(dict(id=name+'|'+arm['id'],configuration=config,arm=arm['id'],sizing=arm['sizing'],reentry=arm['reentry']))
        for coin in COINS:pins.add(f'{SOURCE}/{name}-{coin}-targets.parquet')
        for variant in VARIANTS:
            pins.add(f'{SOURCE}/{name}-{variant}-returns.parquet')
            for coin in COINS:pins.add(f'{SOURCE}/{name}-{variant}-{coin}-trace.parquet')
    if gate['cells']!=expected or set(gate['pinned_files'])!=pins or len(pins)!=264:raise ValueError('fixed cells/input set mismatch')
    if gate['control_parity']!=dict(trace_count=144,return_frame_count=72,before_alternatives=True,
        on_failure='stop alternatives; preserve all72 identities as unavailable comparisons'):raise ValueError('control admission differs')
    ledger=gate['financial_ledger']
    if ledger!={'path':'data/predlab/trial_ledger.jsonl','prefix_rows':748,'prefix_bytes':569325,
        'prefix_sha256':'4d176acf273cacc5ada30abd02a0e7317c579968f29b2918196d88ebe3140601','append_rows':72,'final_rows':820}:
        raise ValueError('ledger policy differs')


def check_ledger_prefix(path,spec):
    data=Path(path).read_bytes()
    if (len(data)!=spec['prefix_bytes'] or len(data.splitlines())!=spec['prefix_rows']
            or hashlib.sha256(data).hexdigest()!=spec['prefix_sha256']):raise ValueError('financial ledger prefix mismatch')
    return data


def append_ledger_once(path,receipt,spec):
    if len(receipt.splitlines())!=spec['append_rows']:raise ValueError('prepared ledger denominator mismatch')
    with Path(path).open('r+b') as stream:
        fcntl.flock(stream.fileno(),fcntl.LOCK_EX)
        prefix=stream.read()
        if (len(prefix)!=spec['prefix_bytes'] or len(prefix.splitlines())!=spec['prefix_rows']
                or hashlib.sha256(prefix).hexdigest()!=spec['prefix_sha256']):raise ValueError('financial ledger prefix changed or append already exists')
        if stream.write(receipt)!=len(receipt):raise OSError('partial financial ledger append; recovery review required')
        stream.flush();os.fsync(stream.fileno())


def unavailable(reason):return dict(status='unavailable',reason=str(reason))


def unavailable_variant(reason):return dict(**unavailable(reason),sleeves={c:unavailable(reason) for c in COINS},index=unavailable(reason))


def unavailable_cell(cell,reason):
    return {**cell,'metrics':dict(**unavailable(reason),variants={v:unavailable_variant(reason) for v in VARIANTS},
            log_shadow=unavailable_variant(reason)), 'control_parity':unavailable(reason)}


def metrics_status(metrics):
    if all(v['status']=='complete' for v in metrics['variants'].values()) and metrics['log_shadow']['status']=='complete':
        metrics.update(status='complete')
    else:metrics.update(status='unavailable',reason='one or more required variant/shadow evaluations unavailable')


def prepare_rows(cells,provenance):
    rows=[]
    for cell in cells:
        config={k:cell[k] for k in ('configuration','arm','sizing','reentry')}
        row=dict(**provenance,experiment=KEY,cell=cell['id'],model='fixed_factor_risk_policy',config=config,
            config_hash=hashlib.sha256(json.dumps(config,sort_keys=True,separators=(',',':')).encode()).hexdigest()[:12],
            ts_utc=now(),window=list(WINDOW),metrics=cell['metrics'])
        row['trial_id']=registry.trial_identity(row);rows.append(row)
    return rows,(''.join(json.dumps(r,sort_keys=True,allow_nan=False)+'\n' for r in rows)).encode()


def simulate_sleeve(target,cell,costs,policy):
    controller=FactorRiskPolicy(sizing=cell['sizing'],reentry=cell['reentry'],sigma=causal_sigma(target.Close))
    trace=[]
    equity,_=run_coin_backtest(target.Date.to_numpy(),target.Close.to_numpy(),target.target.to_numpy(),
        policy['initial_nav'],**costs,highs=target.High.to_numpy(),lows=target.Low.to_numpy(),
        price_stop_pct=policy['price_stop_fraction'],trace=trace,target_policy=controller)
    frame=pd.DataFrame(trace);frame['date']=pd.to_datetime(frame.date,utc=True)
    returns=pd.Series(np.asarray(equity)[1:]/np.asarray(equity)[:-1]-1,index=pd.DatetimeIndex(target.Date.iloc[1:],name='Date'))
    ev._equal(returns.to_numpy(),frame.net_return.to_numpy(),'engine equity/trace return',policy['reconciliation_weight_atol'])
    return returns,frame


def summarize_index(frame,gate,*,periods=True):
    expected=pd.date_range(*gate['return_window'],tz='UTC',freq='D',name='Date')
    try:
        # NumPy does not silently skip a missing sleeve when averaging.
        frame['index_return']=frame[list(COINS)].to_numpy(dtype=float).mean(axis=1)
        result=dict(status='complete',metrics=ev.return_metrics(frame.index_return,expected))
        if periods:result['periods']=ev.period_metrics(frame.index_return,gate['reporting']['periods'])
        return result
    except (ValueError,TypeError,ArithmeticError) as exc:
        frame['index_return']=np.nan
        return unavailable('index unavailable: '+str(exc))


def run_variant(cell,variant,targets,gate,output):
    summary=dict(status='complete',sleeves={}); traces={}
    expected=pd.date_range(*gate['return_window'],tz='UTC',freq='D',name='Date')
    saved=pd.DataFrame(index=expected)
    for coin in COINS:
        stem=f"{cell['configuration']['name']}-{cell['arm']}-{variant}-{coin}"
        try:
            ret,trace=simulate_sleeve(targets[coin],cell,ev.cost_variant(gate['costs'],variant),gate['policy'])
            # Preserve successful engine evidence even if a subsequent diagnostic fails.
            write_frame(output/(stem+'-trace.parquet'),trace)
            metric=ev.return_metrics(ret,expected)
            diagnostic=ev.evaluate_trace(targets[coin],trace,cell,gate['policy'])
            write_frame(output/(stem+'-daily.parquet'),diagnostic['daily'])
            write_frame(output/(stem+'-stops.parquet'),diagnostic['events'])
            summary['sleeves'][coin]=dict(status='complete',metrics=metric,
                periods=ev.period_metrics(ret,gate['reporting']['periods']),diagnostics=diagnostic['summary'])
            saved[coin]=ret;traces[coin]=trace
        except (ValueError,TypeError,KeyError,IndexError,ArithmeticError) as exc:
            summary['sleeves'][coin]=unavailable(f'{type(exc).__name__}: {exc}');saved[coin]=np.nan
    if all(s['status']=='complete' for s in summary['sleeves'].values()):
        summary['index']=summarize_index(saved,gate)
        if summary['index']['status']!='complete':summary.update(status='unavailable',reason=summary['index']['reason'])
    else:
        saved['index_return']=np.nan;summary.update(status='unavailable',reason='one or both required sleeves unavailable')
        summary['index']=unavailable('both complete sleeve clocks required; no partial index')
    write_frame(output/f"{cell['configuration']['name']}-{cell['arm']}-{variant}-returns.parquet",saved)
    print(f"Completed {cell['configuration']['name']} {cell['arm']} {variant} ({summary['status']})",flush=True)
    return summary,saved,traces


def make_shadow(cell,traces,gate,output):
    expected=pd.date_range(*gate['return_window'],tz='UTC',freq='D',name='Date')
    frame=pd.DataFrame(index=expected);result=dict(status='complete',sleeves={},qualification='invalid frozen-exposure log accounting; no state replay')
    for coin in COINS:
        try:
            if coin not in traces:raise ValueError('complete primary sleeve unavailable')
            frame[coin]=ev.frozen_log_shadow(traces[coin])
            result['sleeves'][coin]=dict(status='complete',metrics=ev.return_metrics(frame[coin],expected))
        except (ValueError,KeyError,TypeError,ArithmeticError) as exc:
            result['sleeves'][coin]=unavailable(str(exc));frame[coin]=np.nan
    if all(s['status']=='complete' for s in result['sleeves'].values()):
        result['index']=summarize_index(frame,gate,periods=False)
        if result['index']['status']!='complete':result.update(status='unavailable',reason=result['index']['reason'])
    else:
        frame['index_return']=np.nan;result.update(status='unavailable',reason='one or both frozen shadow sleeves unavailable')
        result['index']=unavailable('both shadow sleeves required')
    write_frame(output/f"{cell['configuration']['name']}-{cell['arm']}-invalid-log-shadow.parquet",frame)
    return result


def convention_descriptor(simple,invalid_log):
    """Signs of saved point values/differences, never a valid policy comparison."""
    result={}
    for field in ev.RETURN_FIELDS:
        a,b=simple.get(field),invalid_log.get(field)
        valid=a is not None and b is not None and np.isfinite(a) and np.isfinite(b)
        result[field]=dict(simple=a,invalid_log=b,sign_or_order_changed=bool(np.sign(a)!=np.sign(b)) if valid else None)
    return result


def flatten_summary(cell):
    """Keep sleeve units separate when constructing descriptive scalar differences."""
    out={}
    primary=cell['metrics']['variants']['primary']
    for field in ev.RETURN_FIELDS:out['index.'+field]=primary['index'].get('metrics',{}).get(field)
    for coin in COINS:
        sleeve=primary['sleeves'][coin]; d=sleeve.get('diagnostics',{})
        for f in ev.RETURN_FIELDS:out[coin+'.'+f]=sleeve.get('metrics',{}).get(f)
        for f in ('active_rows','waiting_rows','halted_cash_rows','other_flat_rows','blocked_reentry_opportunities','price_stops','stop_fills_outside_envelope','turnover_dollars'):
            out[coin+'.'+f]=d.get(f)
        for f in ('gross_dollars','funding_dollars','fee_dollars','impact_dollars','net_dollars'):
            out[coin+'.'+f]=d.get('components',{}).get(f)
        for label in ('latent','incoming','applied','closing'):
            for f in ('integrated_absolute','integrated_signed'):out[f'{coin}.{label}.{f}']=d.get('exposures',{}).get(label,{}).get(f)
            for f in ('median','p90','p99','maximum'):out[f'{coin}.{label}.risk_{f}']=d.get('risk_distributions',{}).get(label,{}).get(f)
            for f in ('above_reference','above_nominal_budget','above_leverage_cap'):out[f'{coin}.{label}.{f}']=d.get('risk_counts',{}).get(label,{}).get(f)
    return out


def contrasts(cells,configs):
    indexed={(c['configuration']['name'],c['arm']):c for c in cells};direct=[];factorial=[]
    for config in configs:
        arms={a['id']:flatten_summary(indexed[(config['name'],a['id'])]) for a in ARMS}
        computed=ev.scalar_contrasts(arms)
        shadows={a['id']:{f:indexed[(config['name'],a['id'])]['metrics']['log_shadow']['index'].get('metrics',{}).get(f)
            for f in ev.RETURN_FIELDS} for a in ARMS}
        shadow_deltas=ev.scalar_contrasts(shadows)
        for arm,values in computed['direct'].items():
            ready=all(indexed[(config['name'],a)]['metrics']['variants']['primary']['status']=='complete' for a in (arm,'A00'))
            direct.append(dict(configuration=config['name'],arm=arm,control='A00',status='complete' if ready else 'unavailable',
                reason=None if ready else 'required primary arm unavailable',differences=values,
                convention_diagnostic=convention_descriptor({f:values.get('index.'+f) for f in ev.RETURN_FIELDS},shadow_deltas['direct'][arm])))
        ready=all(indexed[(config['name'],a['id'])]['metrics']['variants']['primary']['status']=='complete' for a in ARMS)
        for effect,values in computed['factorial'].items():factorial.append(dict(configuration=config['name'],effect=effect,
            status='complete' if ready else 'unavailable',reason=None if ready else 'required primary arm unavailable',differences=values))
    return direct,factorial


def execute(root=ROOT):
    root=Path(root);provenance=registry.preflight(KEY,WINDOW);gate=registry.get_experiment(KEY);validate_gate(gate)
    output=root/gate['output_dir'];output.mkdir(parents=True,exist_ok=False)
    write_json(output/'start.json',dict(**provenance,started_utc=now(),registered_gate=gate,
        admission_status='pending',pending_identities=[dict(id=c['id'],status='pending') for c in gate['cells']],
        runtime=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,pyarrow=pa.__version__)))
    ledger=root/gate['financial_ledger']['path'];appended=False
    cells={c['id']:unavailable_cell(c,'not evaluated') for c in gate['cells']}
    try:
        verify_hashes(root,gate['pinned_files']);prefix=check_ledger_prefix(ledger,gate['financial_ledger'])
        originals=json.loads((root/gate['original_gates']).read_text())
        if originals['audit_factor_floor_2026_09_10']['cells']!=gate['configurations']:raise ValueError('original factor configuration mismatch')
        previous=json.loads((root/gate['source_result']).read_text())
        if previous.get('git_commit')!=gate['source_execution_commit']:
            raise ValueError('previous execution identity mismatch')
        # Every admitted payload must be identified by the preceding immutable result.
        for path,digest in gate['pinned_files'].items():
            if path.startswith(SOURCE+'/') and path!=gate['source_result']:
                if previous['output_sha256'].get(Path(path).name)!=digest:raise ValueError('previous output receipt mismatch: '+path)
        expected=pd.date_range(*gate['development_window'],tz='UTC',freq='D')
        targets={};refs={}
        for config in gate['configurations']:
            name=config['name'];targets[name]={}
            for coin in COINS:
                path=root/f'{SOURCE}/{name}-{coin}-targets.parquet'
                targets[name][coin]=ev.validate_targets(read_frame(path,'Date',expected[0],expected[-1]),expected)
            for variant in VARIANTS:
                traces={coin:read_frame(root/f'{SOURCE}/{name}-{variant}-{coin}-trace.parquet','date',expected[0],expected[-1]) for coin in COINS}
                returns=read_frame(root/f'{SOURCE}/{name}-{variant}-returns.parquet','Date',expected[0],expected[-1])
                if 'Date' in returns.columns:returns=returns.set_index('Date')
                returns.index=pd.DatetimeIndex(pd.to_datetime(returns.index,utc=True),name='Date')
                if not returns.index.equals(expected[1:]):raise ValueError('original return clock incomplete')
                for t in traces.values():
                    if not ev.clock(t.date).equals(expected[1:]):raise ValueError('original trace clock incomplete')
                refs[(name,variant)]=(traces,returns)
        write_json(output/'admission.json',dict(status='complete',input_sha256=gate['pinned_files'],prior_receipt_agreement=True,
            financial_prefix_sha256=gate['financial_ledger']['prefix_sha256']))
        parity=[];primary_traces={}
        ordered=[c for c in gate['cells'] if c['arm']=='A00']+[c for c in gate['cells'] if c['arm']!='A00']
        for cell in ordered:
            item={**cell,'metrics':dict(variants={}), 'control_parity':dict(status='complete',reference='all controls passed' if cell['arm']!='A00' else 'saved control')}
            for variant in VARIANTS:
                value,saved,traces=run_variant(cell,variant,targets[cell['configuration']['name']],gate,output)
                item['metrics']['variants'][variant]=value
                if cell['arm']=='A00':
                    if value['status']!='complete':raise ValueError('A00 sleeve/control unavailable: '+cell['id']+' '+variant)
                    old_traces,old_returns=refs[(cell['configuration']['name'],variant)]
                    for coin in COINS:parity.append(dict(cell=cell['id'],variant=variant,coin=coin,
                        **ev.control_trace_parity(traces[coin],old_traces[coin],gate['policy'])))
                    ev.control_return_parity(saved,old_returns,gate['policy'])
                if variant=='primary':primary_traces[cell['id']]=traces
            item['metrics']['log_shadow']=make_shadow(cell,primary_traces.get(cell['id'],{}),gate,output)
            item['metrics']['log_shadow']['versus_simple']=convention_descriptor(
                item['metrics']['variants']['primary']['index'].get('metrics',{}),
                item['metrics']['log_shadow']['index'].get('metrics',{}))
            metrics_status(item['metrics']);cells[cell['id']]=item
            if cell['id']==ordered[len(gate['configurations'])-1]['id']:
                write_json(output/'control-parity.json',dict(status='complete',traces=len(parity),return_frames=len(gate['configurations'])*len(VARIANTS),checks=parity))
        records=[cells[c['id']] for c in gate['cells']]
        direct,factorial=contrasts(records,gate['configurations'])
        verify_hashes(root,gate['pinned_files']);check_ledger_prefix(ledger,gate['financial_ledger'])
        if registry.preflight(KEY,WINDOW)!=provenance:raise ValueError('source/gate/correction policy changed')
        rows,receipt=prepare_rows(records,provenance)
        receipt_path=output/'prepared-ledger.jsonl'
        with receipt_path.open('xb') as f:f.write(receipt)
        after=prefix+receipt
        payload=dict(**provenance,experiment=KEY,status='complete',registered_gate=gate,cells=records,
            direct_contrasts=direct,factorial_contrasts=factorial,control_parity=dict(status='complete',traces=len(parity),return_frames=len(gate['configurations'])*len(VARIANTS)),
            metric_orientation=dict(max_drawdown='nonpositive; higher/closer to zero means less drawdown',costs='positive charges; lower means less charged',risk='nominal proxy, not realized account volatility',contrasts='changed arm minus own A00'),
            holdout_read=False,network_requests=0,models_refit=False,validated_strategies=0,formal_inference=False,winner_selection=False,
            input_sha256=gate['pinned_files'],inputs_unchanged_after_run=True,completed_utc=now(),
            financial_ledger=dict(prefix_rows=gate['financial_ledger']['prefix_rows'],new_rows=len(rows),rows=len(after.splitlines()),
                prefix_sha256=gate['financial_ledger']['prefix_sha256'],sha256_after=hashlib.sha256(after).hexdigest()),
            output_sha256={p.name:sha(p) for p in sorted(output.iterdir()) if p.is_file()},
            limitations=['Spent development history; no statistical or adoption gate.','Proxy prices, assumed daily funding and threshold fills remain qualified.',
                'Separate sleeve return index; no pooled executable capital claim.','Exposure suppression and absorbing cash tails are outcomes, not validation.'])
        encoded=encode_json(payload) # Validate everything before any central append.
        append_ledger_once(ledger,receipt,gate['financial_ledger']);appended=True
        if ledger.read_bytes()!=after:raise ValueError('financial append integrity mismatch; recovery review required')
        with (output/'result.json').open('xb') as f:f.write(encoded)
        return payload
    except Exception as exc:
        reason=f'{type(exc).__name__}: {exc}'
        failed=[unavailable_cell(c,reason) for c in gate['cells']]
        rows,receipt=prepare_rows(failed,provenance)
        with (output/'prepared-failure-ledger.jsonl').open('xb') as f:f.write(receipt)
        safe=False;ledger_error=None
        try:
            check_ledger_prefix(ledger,gate['financial_ledger'])
            if registry.preflight(KEY,WINDOW)!=provenance:raise ValueError('source/gate/policy changed')
            safe=not appended
        except Exception as check_exc:ledger_error=f'{type(check_exc).__name__}: {check_exc}'
        if safe:
            try:append_ledger_once(ledger,receipt,gate['financial_ledger']);appended=True
            except Exception as append_exc:ledger_error=f'{type(append_exc).__name__}: {append_exc}'
        write_json(output/'failure.json',dict(**provenance,status='unavailable',reason=reason,cells=failed,
            accepted_comparisons=False,prepared_rows=len(rows),central_ledger_appended=appended,
            recovery_required=not safe or ledger_error is not None,ledger_error=ledger_error,
            failed_utc=now()))
        raise


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true')
    args=parser.parse_args(argv)
    if not args.execute:
        print('Dry run: no inputs or state consumed. Use --execute only after committed-source authorization.')
        return 0
    execute();return 0


if __name__=='__main__':raise SystemExit(main())
