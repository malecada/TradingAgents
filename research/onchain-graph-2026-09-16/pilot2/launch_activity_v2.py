"""One separately committed schema-corrected independent review, no run replay."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]

def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);args=parser.parse_args()
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    assert head==args.source
    relative=HERE.relative_to(ROOT)/'activity-correction.json'
    raw=(ROOT/relative).read_bytes()
    assert subprocess.check_output(['git','show',f'{head}:{relative}'],cwd=ROOT)==raw
    contract=json.loads(raw);execution=Path(contract['execution_root'])
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=execution,text=True).strip()==contract['execution_source']
    for relative,digest in contract['committed_files'].items():
        assert sha(ROOT/relative)==digest
        assert hashlib.sha256(subprocess.check_output(['git','show',f'{head}:{relative}'],cwd=ROOT)).hexdigest()==digest
    for relative,digest in contract['execution_files'].items():assert sha(execution/relative)==digest
    destination=execution/HERE.relative_to(ROOT)
    report=destination/'independent-report-v2.json';receipt=destination/'independent-resource-v2.json'
    assert not report.exists() and not receipt.exists()
    guard=module('activity_v2_cpu_guard',execution/'research/strategy-search-2026-09-11/resource_guard_v2.py')
    memory=module('activity_v2_memory_guard',execution/'research/onchain-graph-2026-09-16/motifs8gib/launch.py')
    os.environ['TMPDIR']=str(destination/'scratch')
    command=[sys.executable,'-B',str(HERE/'check_activity_v2.py'),'--root',str(execution),'--source',contract['execution_source'],'--report',str(report)]
    with receipt.open('x') as stream:
        result=memory.run_with_limit(command,guard,execution)
        result.update(source=contract['execution_source'],correction_source=head,correction_contract_sha256=hashlib.sha256(raw).hexdigest())
        json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps(result),flush=True)
    return int(result['child_exit_code']!=0 or result['limit_reason'] is not None)

if __name__=='__main__':raise SystemExit(main())
