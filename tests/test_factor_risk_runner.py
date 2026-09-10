"""Runner fences exercised with synthetic artifacts in temporary directories."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

from test_factor_risk_diagnostics import synthetic_book


ROOT = Path(__file__).resolve().parents[1]


def module():
    path = ROOT/'scripts/audit_factor_risk_2026_09_10.py'
    assert path.exists(), 'guarded factor-risk runner has not been implemented'
    spec = importlib.util.spec_from_file_location('factor_risk_runner_test', path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(tmp_path):
    m = module()
    t, r = synthetic_book()
    base = tmp_path/'data/factor-correction/2026-09-10/results'; base.mkdir(parents=True)
    cells, priorcells, pins = [], [], {}
    for name in ('one', 'two'):
        spec = {'name': name, 'family': 'synthetic'}
        sleeves = {}
        for coin in ('bitcoin', 'ethereum'):
            target = base/f'{name}-{coin}-targets.parquet'
            trace = base/f'{name}-primary-{coin}-trace.parquet'
            t.to_parquet(target); r.to_parquet(trace)
            cells.append(dict(id=name+'|'+coin, configuration=spec, coin=coin,
                target_path=str(target.relative_to(tmp_path)), trace_path=str(trace.relative_to(tmp_path))))
            pins.update({str(p.relative_to(tmp_path)):digest(p) for p in (target, trace)})
            sleeves[coin] = dict(halted=False, halt_date=None, price_stops=0,
                stop_fills_outside_envelope=0, **{k:float(r[k].sum()) for k in
                    ('gross_dollars','funding_dollars','fee_dollars','impact_dollars','turnover_dollars')},
                metrics=dict(n_bars=len(r)))
        priorcells.append(dict(id=name, config=spec, variants={'primary': {'status':'complete', 'sleeves':sleeves}}))
    result=base/'result.json'
    result.write_text(json.dumps(dict(git_commit='old-source', cells=priorcells,
        output_sha256={Path(k).name:v for k,v in pins.items()})))
    pins[str(result.relative_to(tmp_path))]=digest(result)
    ledger=tmp_path/'financial.jsonl'; ledger.write_bytes(b'original financial ledger\n')
    gate=dict(cells=cells, configurations=[{'name':n,'family':'synthetic'} for n in ('one','two')],
        expected_configurations=2, expected_sleeves=4, forensic_ledger_rows=4,
        expected_target_dates=len(t), expected_trace_dates=len(r),
        development_window=[str(t.Date.iloc[0].date()),str(t.Date.iloc[-1].date())],
        source_result=str(result.relative_to(tmp_path)), source_execution_commit='old-source',
        pinned_files=pins, output_dir='data/diagnostics/test/risk', policy={})
    return m, gate, ledger


def test_default_and_help_do_not_read_inputs_or_preflight(monkeypatch, capsys):
    m=module()
    def forbidden(*a, **kw): pytest.fail('dry invocation consumed execution state')
    monkeypatch.setattr(m, 'execute', forbidden)
    assert m.main([]) == 0
    assert '--execute' in capsys.readouterr().out
    with pytest.raises(SystemExit) as exc: m.main(['--help'])
    assert exc.value.code == 0


def test_runner_retains_all_records_and_never_changes_financial_ledger(tmp_path):
    m,g,ledger=fixture(tmp_path); before=ledger.read_bytes()
    out=m.run_registered(g, {'git_commit':'synthetic'}, root=tmp_path, financial_ledgers=[ledger])
    assert out['status'] == 'complete_qualified'
    assert len(out['cells']) == 4
    assert out['counts'] == dict(expected_sleeves=4, complete_sleeves=4, unavailable_sleeves=0)
    output=tmp_path/g['output_dir']
    rows=[json.loads(x) for x in (output/'forensic-ledger.jsonl').read_text().splitlines()]
    assert [x['cell'] for x in rows] == [x['id'] for x in g['cells']]
    assert all(x['financial_hypothesis_evaluated'] is False for x in rows)
    assert ledger.read_bytes() == before
    for relative, expected in out['output_sha256'].items(): assert digest(output/relative)==expected
    with pytest.raises(FileExistsError):
        m.run_registered(g, {}, root=tmp_path, financial_ledgers=[ledger])


@pytest.mark.parametrize('defect', ['missing', 'changed', 'inconsistent'])
def test_unavailable_sleeve_stays_in_denominator_and_invalid_bytes_not_parsed(tmp_path, monkeypatch, defect):
    m,g,ledger=fixture(tmp_path)
    bad=tmp_path/g['cells'][0]['trace_path']
    if defect=='missing': bad.unlink()
    elif defect=='changed': bad.write_bytes(b'not parquet')
    else:
        r=pd.read_parquet(bad); r.loc[3,'gross_dollars']=123.; r.to_parquet(bad)
        g['pinned_files'][str(bad.relative_to(tmp_path))]=digest(bad)
        prior=tmp_path/g['source_result']; x=json.loads(prior.read_text())
        x['output_sha256'][bad.name]=digest(bad); prior.write_text(json.dumps(x))
        g['pinned_files'][g['source_result']]=digest(prior)
    read=m.pd.read_parquet
    def checked(path,*a,**kw):
        if defect!='inconsistent': assert Path(path)!=bad, 'invalid hash was parsed'
        return read(path,*a,**kw)
    monkeypatch.setattr(m.pd,'read_parquet',checked)
    out=m.run_registered(g, {}, root=tmp_path, financial_ledgers=[ledger])
    assert len(out['cells'])==4
    assert out['counts']['unavailable_sleeves']==1
    assert out['cells'][0]['summary']['status']=='unavailable'


def test_input_change_during_analysis_never_gets_completion_artifact(tmp_path, monkeypatch):
    m,g,ledger=fixture(tmp_path); analyze=m.analyze_sleeve
    def changed(*a,**kw):
        out=analyze(*a,**kw)
        (tmp_path/g['cells'][0]['target_path']).write_bytes(b'changed during inspection')
        return out
    monkeypatch.setattr(m,'analyze_sleeve',changed)
    with pytest.raises(RuntimeError,match='changed during'):
        m.run_registered(g, {}, root=tmp_path, financial_ledgers=[ledger])
    output=tmp_path/g['output_dir']
    assert (output/'started.json').exists()
    assert (output/'failed.json').exists()
    assert not (output/'result.json').exists()


def test_prior_result_reconciliation_failure_is_unavailable(tmp_path):
    m,g,ledger=fixture(tmp_path)
    prior=tmp_path/g['source_result']; x=json.loads(prior.read_text())
    x['cells'][0]['variants']['primary']['sleeves']['bitcoin']['gross_dollars']+=2
    prior.write_text(json.dumps(x)); g['pinned_files'][g['source_result']]=digest(prior)
    out=m.run_registered(g, {}, root=tmp_path, financial_ledgers=[ledger])
    assert out['cells'][0]['summary']['status']=='unavailable'
    assert 'prior result' in out['cells'][0]['summary']['reason']


def test_unregistered_or_escaping_input_paths_rejected_before_read(tmp_path):
    m,g,ledger=fixture(tmp_path)
    g['cells'][0]['trace_path']='../outside.parquet'
    with pytest.raises(ValueError,match='path|pin'):
        m.run_registered(g, {}, root=tmp_path, financial_ledgers=[ledger])
    assert not (tmp_path/g['output_dir']).exists()


def test_financial_ledger_mutation_prevents_completion(tmp_path,monkeypatch):
    m,g,ledger=fixture(tmp_path); analyze=m.analyze_sleeve
    def changed(*a,**kw):
        out=analyze(*a,**kw); ledger.write_text('changed'); return out
    monkeypatch.setattr(m,'analyze_sleeve',changed)
    with pytest.raises(RuntimeError,match='financial ledger'):
        m.run_registered(g, {}, root=tmp_path, financial_ledgers=[ledger])
    assert not (tmp_path/g['output_dir']/'result.json').exists()


def test_hashing_failure_preserves_started_failed_and_all_unavailable_identities(tmp_path,monkeypatch):
    m,g,ledger=fixture(tmp_path); original=m.fingerprint
    def failure(path):
        if Path(path)==tmp_path/g['cells'][0]['trace_path']: raise OSError('synthetic inaccessible input')
        return original(path)
    monkeypatch.setattr(m,'fingerprint',failure)
    with pytest.raises(OSError,match='inaccessible'):
        m.run_registered(g,{},root=tmp_path,financial_ledgers=[ledger])
    output=tmp_path/g['output_dir']
    assert (output/'started.json').exists() and (output/'failed.json').exists()
    rows=[json.loads(x) for x in (output/'forensic-ledger.jsonl').read_text().splitlines()]
    assert [x['cell'] for x in rows]==[x['id'] for x in g['cells']]
    assert all(x['status']=='unavailable' for x in rows)
    assert not (output/'result.json').exists()


def test_full_admission_identity_is_checked_before_parse_and_again_before_completion(tmp_path,monkeypatch):
    m,g,ledger=fixture(tmp_path)
    seen=[]
    def check():
        seen.append('check')
        return {'gate':'same','policy':'first' if len(seen)==1 else 'changed'}
    read=m.pd.read_parquet
    def guarded_read(*a,**kw):
        assert seen==['check']
        return read(*a,**kw)
    monkeypatch.setattr(m.pd,'read_parquet',guarded_read)
    with pytest.raises(RuntimeError,match='admission provenance'):
        m.run_registered(g,{},root=tmp_path,financial_ledgers=[ledger],admission_check=check)
    assert seen==['check','check']
    assert not (tmp_path/g['output_dir']/'result.json').exists()


def test_baseline_ledger_must_match_exact_bytes_and_registered_748_rows():
    m=module(); original=b'{}\n'*748
    assert m.verify_baseline_ledger(original,original)==hashlib.sha256(original).hexdigest()
    with pytest.raises(ValueError,match='baseline'):
        m.verify_baseline_ledger(original+b'{}\n',original)
    with pytest.raises(ValueError,match='748'):
        m.verify_baseline_ledger(b'{}\n',b'{}\n')
