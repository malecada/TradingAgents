"""Synthetic manifest integrity, missing boundary and duplicate transaction checks."""
import importlib.util
import json
from pathlib import Path
import sys
import pytest
ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'research/onchain-graph-2026-09-16/pilot'
spec=importlib.util.spec_from_file_location('storage',HERE/'storage.py');storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage)
sys.modules['storage']=storage
spec=importlib.util.spec_from_file_location('pilot_run_test',HERE/'run.py');run=importlib.util.module_from_spec(spec);spec.loader.exec_module(run)


def test_manifest_requires_binding_intent_completion_and_roundtrip(tmp_path):
    artifacts=tmp_path/'artifacts';artifacts.mkdir()
    meta=storage.write_blob(artifacts/'body.zst',b'raw')
    with pytest.raises(ValueError,match='orphan'):run.validate_artifacts(tmp_path,artifacts)
    storage.atomic_json(artifacts/'request-0001.json',{'blob':meta})
    storage.atomic_json(artifacts/'request-0001-intent.json',{'status':'intent'})
    assert len(run.validate_artifacts(tmp_path,artifacts))==3
    storage.atomic_json(artifacts/'request-0002-intent.json',{'status':'intent'})
    with pytest.raises(ValueError,match='unresolved'):run.validate_artifacts(tmp_path,artifacts)
    (artifacts/'request-0002-intent.json').unlink()
    (artifacts/'body.zst').write_bytes(b'changed')
    with pytest.raises(ValueError,match='mismatch'):run.validate_artifacts(tmp_path,artifacts)


def test_exact_cross_day_hash_duplicates(tmp_path):
    rows=[]
    for i,ids in enumerate([[b'a'*32,b'b'*32],[b'c'*32,b'a'*32]]):
        path=tmp_path/f'{i}.zst';meta=storage.write_blob(path,b''.join(ids));meta['hashes']=2
        rows.append({'date':str(i),'status':'complete','transaction_hashes':[meta],'integrity':{'rows':2}})
    report=run.unique_transactions(tmp_path,rows)
    assert report['status']=='unavailable' and report['unique_hashes']==3 and report['duplicate_days']==['1']


def test_both_adjacent_links_are_required():
    def row(height,hash,parent,clock):return {'status':'complete','integrity':{'first_block':[height,hash,parent,clock],'last_block':[height,hash,parent,clock]}}
    a,b,c=row(1,'a','z',1),row(2,'b','a',2),row(3,'c','b',3)
    assert run.linkage(a,b,c)['prior_and_next_block_links']=='passed'
    c['integrity']['first_block'][2]='wrong'
    with pytest.raises(ValueError,match='discontinuity'):run.linkage(a,b,c)
    with pytest.raises(ValueError,match='unavailable'):run.linkage(a,b,{'status':'unavailable'})
