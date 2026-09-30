"""Exclusive prospective resource amendment; no claim, temp check or graph run."""
from pathlib import Path
import copy
import hashlib
import json
from tradingagents.research.onchain_replication.job import required_sources,resource_policy
ROOT=Path.cwd();HERE=Path(__file__).resolve().parent;NAME='eth-paper-graph-resource-20260930-10'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def ref(path):return {'path':str(path.relative_to(ROOT)),'sha256':sha(path)}
def write(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
if __name__=='__main__':
    for p in (HERE/'gate-v4.json',HERE/'gate-v4-derivation.json',ROOT/'research_runs'/NAME,
              ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/NAME,
              ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/NAME):
        assert not p.exists() and not p.is_symlink(),p
    original=json.loads((HERE/'gate-v3.json').read_bytes());gate=copy.deepcopy(original)
    old=original['experiments'][NAME];item=gate['experiments'][NAME]
    for p,h in old['source_files'].items():assert sha(ROOT/p)==h,p
    for v in old['inputs'].values():assert sha(ROOT/v['path'])==v['sha256'],v['path']
    assert sha(ROOT/old['charter']['path'])==old['charter']['sha256']
    before=json.loads((HERE/'execution-job.json').read_bytes());after=json.loads((HERE/'execution-job-v4.json').read_bytes())
    expected=copy.deepcopy(before);expected['resources'].update(memory_max_bytes=5905580032,start_reserve_bytes=9126805504)
    assert after==expected
    resource_policy(after['resources'],ROOT)
    item['charter']=ref(HERE/'CHARTER_V4.md')
    item['inputs']['execution_job']={**ref(HERE/'execution-job-v4.json'),'dataset':'eth'}
    for name in ('run_temp_check03.py','preflight04.py','prepare_registration_v4.py','PRELAUNCH_ROUTE_V4.md'):
        item['source_files'][str((HERE/name).relative_to(ROOT))]=sha(HERE/name)
    refs={'resource_v4_prior_gate':HERE/'gate-v3.json','resource_v4_prior_charter':HERE/'CHARTER.md',
          'resource_v4_prior_job':HERE/'execution-job.json','resource_v4_amendment':HERE/'PRELAUNCH_ROUTE_V4.md',
          'resource_v4_memory_evidence':HERE/'memory-amendment-v4-evidence.json',
          'resource_v4_preflight_refusal':HERE/'dispatch-attempt03-refusal.json',
          'resource_v4_closed_temp':HERE/'temp-check02/final.json'}
    evidence=json.loads((HERE/'memory-amendment-v4-evidence.json').read_bytes())
    for n,record in enumerate(evidence['completed_graphs']):
        p=ROOT/record['receipt']['path'];assert sha(p)==record['receipt']['sha256']
        refs[f'resource_v4_prior_graph_guard_{n:02}']=p
    for name,p in refs.items():
        assert name not in item['inputs'];item['inputs'][name]={**ref(p),'dataset':'eth'}
    assert required_sources()<=set(item['source_files'])
    assert {k:v for k,v in gate.items() if k!='experiments'}=={k:v for k,v in original.items() if k!='experiments'}
    for name,v in original['experiments'].items():
        if name!=NAME:assert gate['experiments'][name]==v
    allowed={'charter','inputs','source_files'}
    assert {k:v for k,v in item.items() if k not in allowed}=={k:v for k,v in old.items() if k not in allowed}
    assert all(item['inputs'][k]==v for k,v in old['inputs'].items() if k!='execution_job')
    assert all(item['source_files'][k]==v for k,v in old['source_files'].items())
    write(HERE/'gate-v4.json',gate)
    write(HERE/'gate-v4-derivation.json',{'prior_gate':ref(HERE/'gate-v3.json'),'new_gate':ref(HERE/'gate-v4.json'),
        'inherited_experiments_unchanged':len(gate['experiments'])-1,'source_pins':len(item['source_files']),
        'input_pins':len(item['inputs']),'changed_existing_inputs':['execution_job'],
        'changed_other_experiment_fields':['charter'],'added_sources':sorted(set(item['source_files'])-set(old['source_files'])),
        'added_inputs':sorted(refs),'worker_max_before':6442450944,'worker_max_after':5905580032,
        'startup_before':9663676416,'startup_after':9126805504,'strict_dispatch_bytes':9261023232,
        'qualification':'Prospective resource amendment only; no run admission, budget adoption, body read or launch.'})
    print(json.dumps({'source_pins':len(item['source_files']),'input_pins':len(item['inputs']),'gate_sha256':sha(HERE/'gate-v4.json')}))
