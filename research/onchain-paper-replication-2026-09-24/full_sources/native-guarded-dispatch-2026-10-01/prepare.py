"""Prepare one durable synthetic checkout; does not launch a worker or claim."""
import argparse
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch
from tests.research.onchain_replication import test_matching_owner as first
from tests.research.test_lifecycle import commit
from tradingagents.research.lifecycle import ResearchRun
from tradingagents.research.onchain_replication.provenance import file_hash,canonical_bytes
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('guarded_native_fixture',HERE.parent/'native-job-dispatch-2026-10-01/test_dispatch.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
class Prepared(Exception):
    def __init__(self,arguments):self.arguments=arguments

def prepare(destination):
    destination=Path(destination).absolute()
    class RetainedDirectory:
        def __init__(self,*args,**kwargs):
            destination.mkdir(parents=True,exist_ok=False);self.name=str(destination)
        def cleanup(self):pass
    def stop_before_claim(**kwargs):raise Prepared(kwargs)
    fixture=base.Tests('test_actual_job_creates_first_owner_and_completes_both_cells')
    try:
        with patch.object(first.tempfile,'TemporaryDirectory',RetainedDirectory),patch.object(ResearchRun,'start',side_effect=stop_before_claim):
            try:fixture.fixture()
            except Prepared as ready:arguments=ready.arguments
            else:raise AssertionError('fixture passed claim boundary')
    finally:fixture.doCleanups()
    root=arguments['root'];registration=json.loads((root/'registration.json').read_bytes())
    exp=registration['experiments']['example-a'];registration['families']['family-a']['attempt_budget']=1
    exp['outputs'].remove('summary.json')
    exp['question']='Tiny synthetic native full-chain dispatch under the actual OS guard; no financial inference.'
    (root/'charter.md').write_text('One synthetic guarded dispatch with direction and regression cells. One epoch, batch size one, inherited tiny topology and two-day lookback. No financial data, resource-coverage credit or automatic retry. Preserve all partial work and terminal evidence.\n')
    exp['charter']['sha256']=file_hash(root/'charter.md')
    execution=json.loads((root/'execution_job.json').read_bytes());execution['resources']['wall_seconds']=900
    (root/'execution_job.json').write_bytes(canonical_bytes(execution));exp['inputs']['execution_job']['sha256']=file_hash(root/'execution_job.json')
    source=commit(root,registration)
    record={'schema_version':1,'root':str(root),'registration':'registration.json','experiment':'example-a','source':source,
            'registration_sha256':file_hash(root/'registration.json'),'execution_job_sha256':file_hash(root/'execution_job.json'),
            'scope':'tiny synthetic actual-guard integration; no empirical study admission',
            'financial_fits':0,'synthetic_fits':2,'automatic_retry':False,'resources':execution['resources']}
    (root.parent/(root.name+'-prepared.json')).write_bytes(canonical_bytes(record)+b'\n')
    print(json.dumps(record,sort_keys=True),flush=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('destination',type=Path);prepare(parser.parse_args().destination)
