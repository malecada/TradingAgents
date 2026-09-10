"""Guarded, saved-primary-trace diagnostics. Default invocation reads no data."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import pyarrow

from tradingagents.predlab import registry
from tradingagents.strategies.factor_risk_diagnostics import (
    DEFAULT_POLICY, QUALIFICATION, analyze_sleeve,
)

KEY = 'audit_factor_risk_2026_09_10'
WINDOW = ('2021-11-07', '2025-03-31')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stamp():
    return datetime.now(timezone.utc).isoformat()


def plain(value):
    if isinstance(value, dict): return {str(k):plain(v) for k,v in value.items()}
    if isinstance(value, (list, tuple)): return [plain(v) for v in value]
    if isinstance(value, np.generic): return plain(value.item())
    if isinstance(value, (pd.Timestamp, datetime)): return value.isoformat()
    if isinstance(value, float) and not np.isfinite(value): return None
    return value


def write_json(path, value):
    body=json.dumps(plain(value), indent=2, allow_nan=False)+'\n'
    with Path(path).open('x') as handle: handle.write(body)


def safe_path(root, name):
    path = (root/name).resolve()
    if Path(name).is_absolute() or not path.is_relative_to(root.resolve()):
        raise ValueError(f'path outside registered repository: {name}')
    return path


def fingerprint(path):
    return sha(path) if path.is_file() else None


def validate_registration(gate, root):
    cells, pins = gate['cells'], gate['pinned_files']
    if len(cells) != gate['expected_sleeves'] or len(cells) != gate['forensic_ledger_rows']:
        raise ValueError('registered sleeve denominator mismatch')
    ids = [c['id'] for c in cells]
    if len(set(ids)) != len(ids): raise ValueError('duplicate registered sleeve')
    configs = gate['configurations']
    if len(configs) != gate['expected_configurations'] or len({c['name'] for c in configs}) != len(configs):
        raise ValueError('configuration denominator mismatch')
    expected = [(c,coin) for c in configs for coin in ('bitcoin','ethereum')]
    if len(expected) != len(cells): raise ValueError('each configuration requires both sleeves')
    prefix = 'data/factor-correction/2026-09-10/results/'
    for cell,(configuration,coin) in zip(cells,expected):
        name=configuration['name']
        if cell['configuration']!=configuration or cell['coin']!=coin or cell['id']!=name+'|'+coin:
            raise ValueError('registered sleeve identity/order mismatch')
        expected_paths = dict(target_path=prefix+f'{name}-{coin}-targets.parquet',
                             trace_path=prefix+f'{name}-primary-{coin}-trace.parquet')
        for field,path in expected_paths.items():
            if cell[field]!=path or path not in pins:
                raise ValueError('unregistered primary input path or missing pin')
            safe_path(root,path)
    if gate['source_result'] not in pins:
        raise ValueError('source result is not pinned')
    for name,digest in pins.items():
        safe_path(root,name)
        if not isinstance(digest,str) or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError('invalid SHA256 pin')
    output = safe_path(root,gate['output_dir'])
    if not output.is_relative_to(root.resolve()/'data/diagnostics'):
        raise ValueError('output outside dedicated diagnostic namespace')
    if output.exists(): raise FileExistsError(f'output already reserved: {output}')
    start,end=gate['development_window']
    if end >= '2025-04-01': raise ValueError('diagnostic window reaches holdout')
    clock=pd.date_range(start,end,freq='D')
    if len(clock)!=gate['expected_target_dates'] or len(clock)-1!=gate['expected_trace_dates']:
        raise ValueError('registered target/trace clock count mismatch')
    return output,clock


def reconcile_prior(summary, previous, policy):
    if previous['metrics']['n_bars']!=summary['trace_rows']:
        raise ValueError('prior result trace denominator mismatch')
    for key in ('gross_dollars','funding_dollars','fee_dollars','impact_dollars'):
        if not np.isclose(previous[key], summary['components'][key],
            atol=policy['reconciliation_dollar_atol'], rtol=policy['reconciliation_rtol']):
            raise ValueError('prior result component mismatch: '+key)
    if not np.isclose(previous['turnover_dollars'],summary['turnover_dollars'],
        atol=policy['reconciliation_dollar_atol'],rtol=policy['reconciliation_rtol']):
        raise ValueError('prior result turnover mismatch')
    for key in ('price_stops','stop_fills_outside_envelope'):
        if previous[key]!=summary[key]: raise ValueError('prior result count mismatch: '+key)
    halt=summary['first_halt']
    if bool(previous['halted']) != (halt is not None):
        raise ValueError('prior result halt flag mismatch')
    if halt is not None and pd.Timestamp(previous['halt_date'])!=pd.Timestamp(halt['date']):
        raise ValueError('prior result halt date mismatch')
    if halt is None and previous.get('halt_date') is not None:
        raise ValueError('prior result unexpected halt date')


def forensic_rows(cells, provenance):
    return [dict(experiment=KEY,cell=c['id'],configuration=c['configuration'],coin=c['coin'],
        status=c['summary']['status'],summary=c['summary'],git_commit=provenance.get('git_commit'),
        financial_hypothesis_evaluated=False,strategy_replayed=False) for c in cells]


def write_forensic(path, rows):
    body=''.join(json.dumps(plain(row),sort_keys=True,allow_nan=False)+'\n' for row in rows)
    with path.open('x') as handle: handle.write(body)


def run_registered(gate, provenance, *, root=ROOT, financial_ledgers=(), admission_check=None):
    """Run only the declared saved-file inspection; caller supplies preflight."""
    root=Path(root).resolve()
    output,clock=validate_registration(gate,root)
    policy=DEFAULT_POLICY | gate['policy']
    metadata=dict(**provenance, experiment=KEY, started_utc=stamp(),
        source_execution_commit=gate['source_execution_commit'],
        expected_input_sha256=gate['pinned_files'],
        runtime=dict(python=platform.python_version(),numpy=np.__version__,
                     pandas=pd.__version__,pyarrow=pyarrow.__version__),
        policy=policy, holdout_evaluated=False, models_refit=False,
        financial_hypothesis_evaluated=False, strategy_replayed=False,
        qualification=QUALIFICATION)
    output.mkdir(parents=True,exist_ok=False)
    write_json(output/'started.json',metadata)
    try:
        # Reserve the attempt before hashing/admission: inaccessible inputs must
        # leave a refusal receipt rather than disappearing from run history.
        admission = admission_check() if admission_check is not None else None
        inputs={name:fingerprint(safe_path(root,name)) for name in gate['pinned_files']}
        input_errors={name:('missing' if inputs[name] is None else 'hash_mismatch')
                      for name,expected in gate['pinned_files'].items() if inputs[name]!=expected}
        ledgers={str(Path(p).resolve()):fingerprint(Path(p)) for p in financial_ledgers}
        source_paths=[Path(__file__),ROOT/'tradingagents/strategies/factor_risk_diagnostics.py',
                      Path(registry.__file__)]
        source={str(p.resolve()):sha(p) for p in source_paths}
        metadata.update(input_sha256=inputs,input_errors=input_errors,source_sha256=source,
                        financial_ledger_before=ledgers,admission=admission)
        write_json(output/'admitted.json',metadata)
        # Unavailable shared provenance makes every sleeve unavailable; bad
        # target/trace bytes only affect their own sleeve and are never parsed.
        market_paths={c[k] for c in gate['cells'] for k in ('target_path','trace_path')}
        shared_errors={k:v for k,v in input_errors.items() if k not in market_paths}
        prior, shared_reason = None,None
        if shared_errors:
            shared_reason='shared pinned input unavailable: '+json.dumps(shared_errors,sort_keys=True)
        else:
            try:
                prior=json.loads(safe_path(root,gate['source_result']).read_text())
                if prior['git_commit']!=gate['source_execution_commit']:
                    raise ValueError('prior execution source mismatch')
                names=[c['id'] for c in prior['cells']]
                if names != [c['name'] for c in gate['configurations']]:
                    raise ValueError('prior configuration identity/order mismatch')
                prior={c['id']:c for c in prior['cells']} | {'_outputs':prior['output_sha256']}
            except (KeyError,TypeError,ValueError) as exc:
                shared_reason='shared prior result unavailable: '+str(exc)
        cells=[]
        for cell in gate['cells']:
            errors={k:input_errors[cell[k]] for k in ('target_path','trace_path') if cell[k] in input_errors}
            unavailable=shared_reason or ('pinned sleeve input unavailable: '+json.dumps(errors) if errors else None)
            summary=None
            if unavailable is None:
                try:
                    for field in ('target_path','trace_path'):
                        name=Path(cell[field]).name
                        if prior['_outputs'][name]!=gate['pinned_files'][cell[field]]:
                            raise ValueError('prior result output hash disagrees with registration')
                    targets=pd.read_parquet(safe_path(root,cell['target_path']))
                    trace=pd.read_parquet(safe_path(root,cell['trace_path']))
                    analyzed=analyze_sleeve(targets,trace,policy=policy,expected_clock=clock)
                    summary=analyzed['summary']
                    if summary['status']=='complete_qualified':
                        previous=prior[cell['configuration']['name']]['variants']['primary']['sleeves'][cell['coin']]
                        reconcile_prior(summary,previous,policy)
                        stem=cell['id'].replace('|','__')
                        for field in ('daily','events'):
                            path=output/f'{stem}-{field}.parquet'
                            with path.open('xb') as handle:
                                analyzed[field].to_parquet(handle,index=False)
                        summary['prior_result_reconciled']=True
                except (OSError,ValueError,TypeError,KeyError) as exc:
                    unavailable=str(exc)
            if unavailable is not None:
                summary=dict(status='unavailable',reason=unavailable,
                    expected_target_rows=len(clock),expected_trace_rows=len(clock)-1,
                    qualification=QUALIFICATION)
            cells.append(dict(id=cell['id'],configuration=cell['configuration'],coin=cell['coin'],summary=summary))

        # This also detects disappearance or modification of initially invalid inputs.
        for name,original in inputs.items():
            if fingerprint(safe_path(root,name))!=original:
                raise RuntimeError('pinned input changed during inspection: '+name)
        for name,original in ledgers.items():
            if fingerprint(Path(name))!=original:
                raise RuntimeError('financial ledger changed during inspection: '+name)
        for name,original in source.items():
            if fingerprint(Path(name))!=original:
                raise RuntimeError('executable source changed during inspection: '+name)
        if admission_check is not None and admission_check()!=admission:
            raise RuntimeError('admission provenance changed during inspection')
        complete=sum(c['summary']['status']=='complete_qualified' for c in cells)
        write_forensic(output/'forensic-ledger.jsonl',forensic_rows(cells,provenance))
        result=dict(**metadata,completed_utc=stamp(),cells=cells,
            status='complete_qualified' if complete==len(cells) else 'incomplete',
            counts=dict(expected_sleeves=len(cells),complete_sleeves=complete,unavailable_sleeves=len(cells)-complete),
            financial_ledger_after={name:fingerprint(Path(name)) for name in ledgers},
            output_sha256={p.name:sha(p) for p in sorted(output.iterdir()) if p.is_file()})
        write_json(output/'result.json',result)
        return result
    except Exception as exc:
        reason=type(exc).__name__+': '+str(exc)
        failures=[dict(id=c['id'],configuration=c['configuration'],coin=c['coin'],
            summary=dict(status='unavailable',reason='run admission/integrity failure: '+reason,
                         qualification=QUALIFICATION)) for c in gate['cells']]
        if not (output/'forensic-ledger.jsonl').exists():
            write_forensic(output/'forensic-ledger.jsonl',forensic_rows(failures,provenance))
        write_json(output/'failed.json',dict(failed_utc=stamp(),error=reason,cells=failures,
            note='All diagnostic outputs from this failed attempt are unavailable; no result is admitted.'))
        raise


def verify_baseline_ledger(current, baseline):
    if len(baseline.splitlines())!=748:
        raise ValueError('baseline financial ledger does not contain the registered 748 rows')
    if current!=baseline:
        raise ValueError('financial ledger differs from registered baseline bytes')
    return hashlib.sha256(baseline).hexdigest()


def execute():
    provenance=registry.preflight(KEY,WINDOW)
    gate=registry.get_experiment(KEY)
    if (gate['development_window']!=list(WINDOW) or gate['expected_sleeves']!=36 or
        gate['expected_configurations']!=18 or len(gate['pinned_files'])!=78):
        raise ValueError('frozen factor risk registration denominator changed')
    def admission_check():
        current=registry.preflight(KEY,WINDOW)
        if current!=provenance:
            raise RuntimeError('admission provenance differs from initial registry preflight')
        ledger=registry.ledger_path().resolve()
        relative=ledger.relative_to(ROOT.resolve()).as_posix()
        baseline=subprocess.check_output(['git','show',f"{gate['baseline_commit']}:{relative}"],cwd=ROOT)
        ledger_sha=verify_baseline_ledger(ledger.read_bytes(),baseline)
        return dict(registry_provenance=current,baseline_ledger_sha256=ledger_sha,
                    baseline_commit=gate['baseline_commit'])
    return run_registered(gate,provenance,financial_ledgers=[registry.ledger_path(),ROOT/'data/rebuild/trial_ledger.jsonl'],
                          admission_check=admission_check)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true',help='inspect the committed fixed saved artifacts once')
    args=parser.parse_args(argv)
    if not args.execute:
        print('Dry invocation: no inputs read. Use --execute only after reviewed source is committed.')
        return 0
    result=execute()
    print(json.dumps(dict(experiment=KEY,status=result['status'],counts=result['counts']),sort_keys=True))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
