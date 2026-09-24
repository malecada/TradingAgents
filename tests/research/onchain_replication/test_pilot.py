"""New pilot tests use synthetic files only; no retained transaction bodies."""
import importlib.util
import json
from pathlib import Path
import pytest
import pyarrow as pa
import pyarrow.parquet as pq
from tradingagents.research.onchain_replication.provenance import file_hash

HERE=Path(__file__).resolve().parents[3]/'research/onchain-paper-replication-2026-09-24/pilot'

def module(name):
    spec=importlib.util.spec_from_file_location('pilot_'+name,HERE/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def test_inventory_and_unavailable_forecast_account_all_nine_weeks():
    m=module('run');index=json.loads((HERE/'source-index.json').read_bytes())
    phases=m.phase_inventory(index)
    assert len(phases)==46 and sum(p=='dictionary' for w,p in phases)==1
    cells=[{'id':p+'-'+w,'phase':p,'week':w,'status':'unavailable'} for w,p in phases]
    forecast=m.forecast(cells,index)
    assert forecast['completed_whole_weeks']==0 and forecast['required_pilot_weeks']==9
    assert forecast['conservative_multigraph_rss_forecast_bytes'] is None
    assert not forecast['financial_run_admitted']
    assert len(set(p+'-'+w for w,p in phases))+sum(len(w['members']) for w in index['weeks'].values())==109


def test_phase_exact_input_hash_refuses_drift(tmp_path):
    m=module('phase');path=tmp_path/'input.json';path.write_text('{}');m.BINDINGS={str(path):file_hash(path)}
    assert m.load(path)=={}
    path.write_text('{"drift":true}')
    with pytest.raises(ValueError,match='changed parsed bytes'):m.load(path)


def test_whole_week_phase_conserves_synthetic_source(tmp_path):
    m=module('phase');week='2024-01-01';directory=tmp_path/'phase';directory.mkdir()
    table=pa.table({'hash':['0x'+'1'*64,'0x'+'2'*64],'block_timestamp':pa.array([1704153600000000000]*2,type=pa.timestamp('ns')),'from_address':['0x'+'a'*40]*2,'to_address':['0x'+'b'*40]*2,'value':[1e18,2e18],'receipt_status':pa.array([1,1],type=pa.int64())})
    source=tmp_path/'source.parquet';pq.write_table(table,source)
    index={'expected_schema':{f.name:str(f.type) for f in table.schema},'weeks':{week:{'start_utc':week+'T00:00:00Z','end_utc':'2024-01-08T00:00:00Z','status':'complete','expected_members':1,'expected_rows':2,'members':[{'path':str(source),'sha256':file_hash(source),'format':'parquet','expected_rows':2}]}}}
    result=m.perform('decode_graph',week,directory,tmp_path,index,{})
    assert result['status']=='complete'
    assert result['details']['raw_count']==result['details']['admitted_count']==2
    assert result['details']['edges']==1 and result['details']['nodes']==2


@pytest.mark.parametrize('partial_observer',[False,True])
def test_dead_worker_observer_closes_all_cells_without_rerun(tmp_path,monkeypatch,partial_observer):
    m=module('reconcile');monkeypatch.setattr(m,'ROOT',tmp_path)
    receipt=tmp_path/'receipt';receipt.mkdir();cgroup=tmp_path/'synthetic-cgroup';cgroup.mkdir();(cgroup/'cgroup.events').write_text('populated 0\n');(receipt/'live.json').write_text(json.dumps({'cgroup':str(cgroup),'owner_identity':{'monitor_pid':123},'monitor_pid':123}))
    artifacts=tmp_path/'artifacts';artifacts.mkdir()
    if partial_observer:(artifacts/'postmortem').mkdir()
    run=tmp_path/'research_runs'/m.EXPERIMENT;run.mkdir(parents=True);(run/'outputs').mkdir()
    (run/'claim.json').write_text(json.dumps({'source':'a'*40,'experiment':{'cells':['decode_graph-2024-01-01','source-2024-01-01']}}))
    result=m.reconcile(receipt,artifacts,'a'*40,{'monitor_pid':123})
    assert result['status']=='failed' and (run/'failed.json').exists()
    cells=json.loads((artifacts/'postmortem/cell-ledger.json').read_bytes())
    assert len(cells)==2 and all(c['status']=='unavailable' for c in cells)


@pytest.mark.parametrize('guard_status',['failed','missing'])
def test_lifecycle_completion_cannot_override_bad_guard(tmp_path,monkeypatch,guard_status):
    m=module('reconcile');monkeypatch.setattr(m,'ROOT',tmp_path)
    receipt=tmp_path/'receipt';receipt.mkdir();cgroup=tmp_path/'cg';cgroup.mkdir();(cgroup/'cgroup.events').write_text('populated 0\n')
    owner={'monitor_pid':123};(receipt/'live.json').write_text(json.dumps({'cgroup':str(cgroup),'owner_identity':owner,'monitor_pid':123}))
    if guard_status=='failed':(receipt/'final.json').write_text(json.dumps({'phase':'failed','memory_events':{'oom':1}}))
    run=tmp_path/'research_runs'/m.EXPERIMENT;run.mkdir(parents=True)
    (run/'claim.json').write_text(json.dumps({'source':'a'*40}));(run/'complete.json').write_text('{}')
    result=m.reconcile(receipt,tmp_path/'artifacts','a'*40,owner)
    assert result['status']=='resource_verification_failed' and result['lifecycle_status']=='complete'
    assert not (run/'failed.json').exists()


def test_observer_missing_cgroup_and_wrong_owner_fail_closed(tmp_path,monkeypatch):
    m=module('reconcile');monkeypatch.setattr(m,'ROOT',tmp_path)
    receipt=tmp_path/'receipt';receipt.mkdir();owner={'monitor_pid':123}
    (receipt/'live.json').write_text(json.dumps({'cgroup':None,'owner_identity':owner,'monitor_pid':123}))
    run=tmp_path/'research_runs'/m.EXPERIMENT;run.mkdir(parents=True);(run/'claim.json').write_text('{}')
    with pytest.raises(ValueError,match='ownership'):m.reconcile(receipt,tmp_path/'artifacts','a'*40,{'monitor_pid':124})
    with pytest.raises(RuntimeError,match='cgroup-death'):m.reconcile(receipt,tmp_path/'artifacts','a'*40,owner)
    assert not (run/'failed.json').exists()
