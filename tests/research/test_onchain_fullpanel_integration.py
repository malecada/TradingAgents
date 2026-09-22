"""Actual producer-to-independent-check integration on invented retained Parquet."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import pytest
ROOT=Path(__file__).resolve().parents[2]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
f=load('fullpanel_integration_fixture',ROOT/'tests/research/test_onchain_fullpanel_check_day.py')
d=load('fullpanel_integration_day',ROOT/'research/onchain-graph-2026-09-16/fullpanel/day.py')

@pytest.mark.parametrize('reused_blocks',[False,True])
def test_producer_independent_transport_and_count_roundtrip(tmp_path,reused_blocks):
 plan,old=f.fixture(tmp_path,reused_blocks);day=old['date'];base=Path(f.c.PREFIX)
 # These are only invented fixture arrays, replaced by actual producer outputs.
 shutil.rmtree(tmp_path/base/'artifacts/scratch'/day)
 plan['reuse']={};plan_raw=json.dumps(plan).encode();(tmp_path/'plan.json').write_bytes(plan_raw)
 prior=old['previous'];report=json.loads((tmp_path/prior['audit']['path']).read_bytes())
 previous=dict(date=prior['date'],source=dict(prior,status='complete'),audit=prior['audit'],independent=report)
 raw=json.dumps(previous).encode();(tmp_path/'previous.json').write_bytes(raw)
 args=argparse.Namespace(root=str(tmp_path),plan='plan.json',date=day,phase=str(base/'artifacts/scratch'/day/'phase.json'),previous='previous.json',previous_sha256=hashlib.sha256(raw).hexdigest())
 actual=d.execute(args)
 assert actual['source']['status']==actual['count']['status']=='complete',actual
 wire=json.loads((tmp_path/args.phase).read_bytes())
 checked=f.c.check(tmp_path,plan,wire)
 assert checked['passed'] and checked['count_verified'] and checked['source_rows']==7
 assert checked['boundary_status']=='passed'
 # Retained representation matches the verifier too, not just live tuples.
 reread=json.loads((tmp_path/args.phase).read_bytes())
 assert f.c.check(tmp_path,plan,reread)==checked
