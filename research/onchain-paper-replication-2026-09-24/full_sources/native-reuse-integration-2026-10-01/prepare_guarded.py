"""Prepare a distinct durable synthetic consumer; never claims or launches."""
import argparse
import importlib.util
import json
from pathlib import Path
from tests.research.test_lifecycle import commit
from tradingagents.research.onchain_replication.provenance import canonical_bytes,file_hash
HERE=Path(__file__).resolve().parent

def prepare(destination):
    destination=Path(destination).absolute();destination.mkdir(parents=True,exist_ok=False)
    spec=importlib.util.spec_from_file_location('native_reuse_fixture',HERE/'test_reuse.py')
    fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
    root,registration,_,execution=fixture.prepare(destination)
    registration['families']['family-a']['attempt_budget']=1
    exp=registration['experiments']['example-a']
    (root/'charter.md').write_text('One synthetic guarded consumer of the closed native producer at its original canonical root. Two tiny neural fits, one epoch and batch size one, with unchanged synthetic scientific settings. No producer replay, financial data, resource-coverage credit or automatic retry. Preserve all terminal and partial evidence.\n')
    exp['charter']['sha256']=file_hash(root/'charter.md');source=commit(root,registration)
    record={'schema_version':1,'root':str(root),'registration':'registration.json','experiment':'example-a','source':source,
        'registration_sha256':file_hash(root/'registration.json'),'execution_job_sha256':file_hash(root/'execution_job.json'),
        'source_transition_sha256':file_hash(root/'source_transition.json'),'reuse_reference_sha256':file_hash(root/'reuse_reference.json'),
        'scope':'tiny synthetic actual-guard native reuse; no empirical study admission','financial_fits':0,
        'synthetic_fits':2,'automatic_retry':False,'resources':execution['resources']}
    with (HERE/'guarded-prepared01.json').open('xb') as stream:stream.write(canonical_bytes(record)+b'\n')
    print(json.dumps(record,sort_keys=True))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('destination',type=Path);prepare(p.parse_args().destination)
