"""One compact/stat graph05 closure; refuses incomplete/active producers."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess
from tradingagents.research.verify import verify_run
ROOT=Path.cwd()
HERE=Path(__file__).resolve().parent
NAME='eth-paper-graph-resource-20260930-05'
HEAD='9f7401158b3544deefbc4c1b9e995d565880ce50'
RUN=ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/NAME
LEDGER=ROOT/'research_runs'/NAME
PREP=HERE.with_name('graph-successor-05-2026-09-30')


def sha(path):
    if path.is_symlink() or path.stat().st_size>=2_000_000:
        raise ValueError('compact regular file required')
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    sha(path)
    return json.loads(path.read_bytes())

def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==HEAD
    guard=read(RUN/'guard/final.json');owner=read(RUN/'owner.json')
    assert guard['phase']=='complete' and guard['child_exit_code']==0 and guard['cleanup_verified']
    assert guard['owner_identity']==owner and owner['source_commit']==HEAD
    assert owner['monitor_pid']==682090 and owner['monitor_start_ticks']=='6752378'
    assert guard['unit']=='onchain-replication-77a2be0d275d41258a74ee65f00676f3.service'
    assert not Path(guard['cgroup']).exists() and not Path('/proc',str(owner['monitor_pid'])).exists()
    claim=read(LEDGER/'claim.json');terminal=read(LEDGER/'complete.json');observer=read(RUN/'observer.json')
    assert observer['terminal_sha256']==sha(LEDGER/'complete.json') and observer['owner_sha256']==sha(RUN/'owner.json')
    assert observer['all_cells_complete'] and observer['cgroup_empty']
    for name,h in observer['evidence_sha256'].items():assert sha(RUN/name)==h,name
    for name,h in claim['experiment']['source_files'].items():assert sha(ROOT/name)==h,name
    for info in claim['experiment']['inputs'].values():assert sha(ROOT/info['path'])==info['sha256'],info['path']
    verification=verify_run(LEDGER)
    assert terminal['cell_count']==8 and all(c['status']=='complete' for c in terminal['cells'])
    cell,=[c for c in terminal['cells'] if c['id']=='graph-2023-06-05']
    assert cell['raw_count']==7684076 and cell['admitted_count']+sum(cell['exclusion_counts'].values())==cell['raw_count']
    small={};large={}
    for name,info in read(LEDGER/'outputs/artifact-index.json').items():
        p=ROOT/name;assert p.is_file() and not p.is_symlink() and p.stat().st_size==info['bytes'],name
        if p.suffix=='.json':assert sha(p)==info['sha256'];small[name]=info
        else:large[name]=info
    assert len(large)==6 and sum(Path(n).suffix=='.npy' for n in large)==5
    evidence={str(p.relative_to(ROOT)):sha(p) for p in (LEDGER/'claim.json',LEDGER/'complete.json',RUN/'observer.json',RUN/'owner.json',RUN/'guard/final.json')}
    result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'compact_closure_complete_array_verification_pending','source':HEAD,'source_pins_verified':len(claim['experiment']['source_files']),'compact_input_pins_verified':len(claim['experiment']['inputs']),'owner_cgroup_absent':True,'effective_attempt_budget':56,'consumed_claims':29,'lifecycle_verification':verification,'graph':cell,'guard':{k:guard[k] for k in ('phase','elapsed_seconds','peak_sampled_memory_current_bytes','memory_events','child_exit_code','cleanup_verified')},'compact_artifacts_verified':small,'large_artifacts_stat_only_hashes_attributed_to_producer':large,'evidence':evidence,'qualification':'Compact hashes and file stats only. No raw/SQLite/array body read or graph rebuild. Separate bounded array verification is required; raw semantics remain producer evidence.'}
    with (PREP/'empirical-closure01.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({'status':result['status'],'compact_artifacts':len(small),'large_artifacts_stat_only':len(large),'raw_count':cell['raw_count'],'admitted_count':cell['admitted_count'],'guard':result['guard']},indent=2))

if __name__=='__main__':main()
