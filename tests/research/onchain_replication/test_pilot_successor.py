"""Exercise the exact serialized input-binding route without historical data."""
import importlib.util,json,os,sys
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from tradingagents.research.onchain_replication.provenance import file_hash

ROOT=Path(__file__).resolve().parents[3]
STUDY=ROOT/'research/onchain-paper-replication-2026-09-24'

def module(directory):
    spec=importlib.util.spec_from_file_location('synthetic_pilot_'+directory,STUDY/directory/'phase.py')
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def test_old_string_binding_error_reproduces_on_synthetic_bytes(tmp_path):
    old=module('pilot');p=tmp_path/'only_synthetic.json';p.write_text('{}')
    with pytest.raises(AttributeError,match='open'):
        old.perform('decode_graph','2024-01-01',tmp_path,tmp_path,{}, {str(p):file_hash(p)})


def test_successor_cli_worker_consumes_bound_synthetic_source_and_checks_drift(tmp_path,monkeypatch):
    m=module('pilot_successor_02');monkeypatch.setattr(m,'STUDY',tmp_path);monkeypatch.setattr(m,'ROOT',tmp_path)
    config=tmp_path/'config';config.mkdir();pilot=tmp_path/'pilot_successor_02';pilot.mkdir()
    for name in ('dictionary.json','matching-stable.json','graph.json'):(config/name).write_bytes((STUDY/'config'/name).read_bytes())
    (pilot/'resource-contract-v4.json').write_bytes((STUDY/'pilot/resource-contract-v4.json').read_bytes())
    source=tmp_path/'synthetic.parquet'
    table=pa.table({'hash':['0x'+'1'*64,'0x'+'2'*64],'block_timestamp':pa.array([1704153600000000000]*2,type=pa.timestamp('ns')),'from_address':['0x'+'a'*40]*2,'to_address':['0x'+'b'*40]*2,'value':[1e18,2e18],'receipt_status':pa.array([1,1],type=pa.int64())})
    pq.write_table(table,source);week='2024-01-01'
    index={'expected_schema':{f.name:str(f.type) for f in table.schema},'weeks':{week:{'start_utc':week+'T00:00:00Z','end_utc':'2024-01-08T00:00:00Z','status':'complete','expected_members':1,'expected_rows':2,'members':[{'path':str(source),'sha256':file_hash(source),'format':'parquet','expected_rows':2}]}}}
    (pilot/'source-index.json').write_text(json.dumps(index))
    bindings={str(p):file_hash(p) for p in [source,*config.iterdir(),*pilot.iterdir()]}
    directory=tmp_path/'decode';directory.mkdir();intent=directory/'intent.json'
    worker=[sys.executable,'-B',str(Path(m.__file__).resolve()),'--intent',str(intent)]
    intent.write_text(json.dumps({'bindings':bindings,'guard_command':['synthetic-guard'],'guard_receipt':str(tmp_path/'guard'),'worker_command':worker,'owner_pid':os.getppid(),'phase':'decode_graph','week':week,'artifacts':str(tmp_path/'artifacts')}))
    checked=[];monkeypatch.setattr(m,'assert_guarded_worker',lambda *a,**kw:checked.append(kw))
    monkeypatch.setattr(m.signal,'signal',lambda *a:None);monkeypatch.setattr(sys,'argv',[m.__file__,'--intent',str(intent)])
    assert m.main()==0
    result=json.loads((directory/'result.json').read_bytes())
    assert result['status']=='complete' and result['details']['raw_count']==2
    assert checked[0]['memory_max_bytes']==3*1024**3
    source.write_bytes(b'changed synthetic source')
    with pytest.raises(ValueError,match='upstream artifact bytes differ'):
        m.perform('decode_graph',week,tmp_path,tmp_path,index,bindings)
