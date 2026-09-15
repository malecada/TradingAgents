"""Disposable staged-return sources; no network, production or financial calls."""
import base64
from datetime import datetime,timezone
import json
from pathlib import Path
import pytest
from tradingagents.research_options_timing import returned as r
from tradingagents.research_options_timing import worker,adapter
from tradingagents.research_options_timing.journal import Journal,encode,digest
from tradingagents.research_options_timing.schedule import calendar,DAY,ASSETS,groups
from tests.research.test_options_timing_adapter import T,initial,metadata,receipt,selected


def stamp(ms):return datetime.fromtimestamp(ms/1000,timezone.utc).isoformat()


def package(root):
    p=root/'package';p.mkdir();actual=Path(__file__).resolve().parents[2]
    files={}
    for name in worker.PACKAGE_FILES:
        path=p/name;path.parent.mkdir(parents=True,exist_ok=True)
        raw=b'# invented bootstrap, never executed\n' if name=='release_bootstrap.py' else (actual/name).read_bytes()
        path.write_bytes(raw);files[name]=digest(raw)
    claim={'source':'a'*40,'episode_protocol':{'schema_version':3,'hourly_acquisition_delay_ms':2000,'worker_lease':{'not_before':stamp(T-120000),'expires_at':stamp(T+45*DAY+60000)},'observation_window':{'start':stamp(T),'end':stamp(T+44*DAY+5000)}}}
    (p/'claim.json').write_bytes(encode(claim))
    value={'schema_version':1,'entry_ms':T,'lease_not_before_ms':T-120000,'lease_expires_ms':T+45*DAY+60000,
           'claim_path':'claim.json','claim_sha256':digest(encode(claim)),'package_files':files,'journal_caps':worker.CAPS,'terminal_reserves':worker.RESERVES,
           'authority':'raw-worker-only','target':'options-timing-20260915','source_commit':'a'*40,'data_root':'/invented/vps/research-data','host_identity':'invented-vps-host'}
    (p/'assignment.json').write_bytes(encode(value))
    data=root/'staged';data.mkdir()
    return p,data,digest(encode(value)),value


def populate(p,data,anchor,spec,*,successful_selection=False,sealed=True):
    original,known,futures=initial();sel=selected() if successful_selection else None
    chosen={a:sel[a]['selected'] for a in ASSETS} if sel else None
    full=calendar(T,chosen);seals={}
    names=[name for name in full if name!='selected' or chosen]
    for name in names:
        with Journal(data/name,claim_path=p/'claim.json',claim_sha256=spec['claim_sha256'],slots=full[name],total_cap=worker.CAPS[name],terminal_reserve=worker.RESERVES[name],check_source=lambda:None) as j:
            if successful_selection and name in ('bootstrap','known'):
                ids=groups(full[name])[0][1];at=full[name][0]['scheduled_ms'];j.begin_group(ids,now_ms=at)
                for n in ids:
                    if n=='initial-options-rules':value=original
                    elif n=='initial-futures-rules':value=receipt(full[name][ids.index(n)]['request'],futures,at)
                    elif n=='initial-funding-rules':value=receipt(full[name][ids.index(n)]['request'],[],at)
                    else:value=known[n.removeprefix('h0000-')]
                    j.record(n,base64.b64decode(value['body_base64']),metadata=value['metadata'])
            if sealed:seals[name]=j.seal('failed')
    if successful_selection:
        first=json.loads((data/'bootstrap/receipt-initial-options-rules.json').read_bytes())
        known_saved={n:json.loads((data/'known'/('receipt-'+n+'.json')).read_bytes()) for n in groups(full['known'])[0][1]}
        (data/'selection.json').write_bytes(encode({'assignment_sha256':anchor,'result':adapter.select_initial(first,{n.removeprefix('h0000-'):v for n,v in known_saved.items()},entry_ms=T),'input_sha256':{'initial':digest(encode(first)),**{n:digest(encode(v)) for n,v in known_saved.items()}}}))
    if sealed:
        unresolved=[f'h{h:04d}-{a.lower()}-{side}-{role}' for h in range(1057) for a in ASSETS for side in ('call','put') for role in ('depth','mark')]
        value={'assignment_sha256':anchor,'status':'failed','reason':'invented stop','journal_seals':seals,'intended_slot_count':17144,
               'unresolved_selected_slots':0 if chosen else 8456,'unresolved_selected_ids_sha256':None if chosen else digest(encode(unresolved)),
               'failure_scope':'Source operability only; no economic rejection of either asset or strategy family.',
               'selection_sha256':r._hash(data/'selection.json') if chosen else None,'quiescent_ms':T+6000,
               'scope':'raw source seal only; no financial or outer terminal authority'}
        (data/'source-seal.json').write_bytes(encode(value))


def test_staging_location_differs_and_unsealed_all_unavailable(tmp_path):
    p,data,anchor,spec=package(tmp_path);populate(p,data,anchor,spec,sealed=False)
    result=r.prepare(package=p,data=data,expected_assignment_sha256=anchor)
    assert result['evaluate_kwargs'] is None and len(result['unavailable_cells'])==8
    assert result['source_report']['source_status']=='incomplete'
    assert result['source_report']['original_host']=='invented-vps-host'
    assert result['source_report']['original_data_root']!=str(data)
    assert not (data/'source-seal.json').exists()


def test_failed_selection_whole_denominator_no_symbols_no_evaluation(tmp_path,monkeypatch):
    p,data,anchor,spec=package(tmp_path);populate(p,data,anchor,spec)
    result=r.prepare(package=p,data=data,expected_assignment_sha256=anchor)
    assert result['evaluate_kwargs'] is None and len(result['unavailable_cells'])==8
    assert result['source_report']['intended_slot_count']==17144
    assert 'independent external' in result['source_report']['quiescence']
    assert result['source_report']['journal_reports']['known']['states']=={'suppressed':8456}


@pytest.mark.parametrize('fault',['anchor','source','extra-package','symlink','fifo','fragmentation','seal'])
def test_unsafe_or_changed_return_refused(tmp_path,fault):
    import os
    p,data,anchor,spec=package(tmp_path);populate(p,data,anchor,spec)
    if fault=='anchor':anchor='0'*64
    elif fault=='source':(p/'tradingagents/research_options_timing/adapter.py').write_bytes(b'changed')
    elif fault=='extra-package':(p/'unexpected').write_bytes(b'unknown')
    elif fault=='symlink':(data/'known/receipt-h0000-futures-time.json').symlink_to(p/'claim.json')
    elif fault=='fifo':os.mkfifo(data/'known/receipt-h0000-futures-time.json')
    elif fault=='fragmentation':
        for i in range(2):(data/f'known/partial-h0000-futures-time-{i:06d}.bin').write_bytes(b'x')
    else:
        value=json.loads((data/'source-seal.json').read_bytes());value['intended_slot_count']=17143
        (data/'source-seal.json').write_bytes(encode(value))
    with pytest.raises((ValueError,RuntimeError)):r.prepare(package=p,data=data,expected_assignment_sha256=anchor)


def test_actual_selection_reconstruction_then_missing_hour_placeholders(tmp_path):
    p,data,anchor,spec=package(tmp_path);populate(p,data,anchor,spec,successful_selection=True)
    result=r.prepare(package=p,data=data,expected_assignment_sha256=anchor)
    values=result['evaluate_kwargs'];assert values is not None
    assert all(len(values['records'][a])==697 for a in ASSETS)
    assert all(values['records'][a][1]['time_ms']==T+3600000 and not values['records'][a][1]['hedge_available'] for a in ASSETS)
    assert all(values['benchmarks'][a][0]=='100' and values['benchmarks'][a][1] is None for a in ASSETS)
    assert all(values['funding'][a]['engine_inputs'] is None for a in ASSETS)
    saved=json.loads((data/'selection.json').read_bytes());saved['result']['BTC']['selected']['quantity']='1'
    (data/'selection.json').write_bytes(encode(saved))
    with pytest.raises(ValueError,match='selection'):r.prepare(package=p,data=data,expected_assignment_sha256=anchor)


def test_rule_projection_preserves_per_asset_duplicate_errors():
    options,futures=metadata();choices={a:selected()[a]['selected'] for a in ASSETS}
    options['optionSymbols'].append(dict(options['optionSymbols'][0]))
    compact=r._rules(options,futures,choices)
    with pytest.raises(ValueError):adapter.rule_snapshot(compact['options'],compact['futures'],'BTC',choices['BTC'])
    assert adapter.rule_snapshot(compact['options'],compact['futures'],'ETH',choices['ETH'])['perp']
