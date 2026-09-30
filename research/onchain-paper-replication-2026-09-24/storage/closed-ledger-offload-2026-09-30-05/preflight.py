"""Fresh exact conditional preservation release check; no body/remote read."""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from tradingagents.research.onchain_replication.resources import mem_available,GIB
ROOT=Path.cwd();HERE=Path(__file__).resolve().parent
PREP=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/graph-successor-08-2026-09-30'

def sha(p):
    assert p.is_file() and not p.is_symlink() and p.stat().st_size<2_000_000
    return hashlib.sha256(p.read_bytes()).hexdigest()

def module(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
    source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip()
    assert branch=='research/onchain-paper-replication-2026-09-24'
    pushed=subprocess.check_output(['git','ls-remote','origin','refs/heads/'+branch],text=True).split()[0];assert pushed==source
    original=json.loads((HERE/'bindings.json').read_bytes());context=json.loads((HERE/'release-bindings01.json').read_bytes())
    manifest=json.loads((HERE/'manifest.json').read_bytes());local=manifest['connection_path']
    assert original[local]==manifest['connection_sha256']
    paths=dict(original)
    for p,h in context.items():
        if p in paths:assert paths[p]==h
        paths[p]=h
    count=0
    for p,h in paths.items():
        assert sha(ROOT/p)==h,p
        if p==local:
            assert not subprocess.check_output(['git','ls-files','--',p],text=True)
        else:
            committed=subprocess.check_output(['git','show',source+':'+p]);assert hashlib.sha256(committed).hexdigest()==h,p;count+=1
    review=HERE/'RELEASE_REVIEW.md';review_sha=sha(review)
    assert hashlib.sha256(subprocess.check_output(['git','show',source+':'+str(review.relative_to(ROOT))])).hexdigest()==review_sha
    for n in ('intent.json','complete.json','failed.json','guard01','preflight01.json'):
        assert not (HERE/n).exists() and not (HERE/n).is_symlink(),n
    units=subprocess.check_output(['systemctl','--user','list-units','--state=active','--no-legend','onchain-replication-*.service'],text=True);assert not units.strip()
    preservation=module('prior_preservation',PREP/'preservation_requirement.py')
    prior=preservation.verify(ROOT,storage=Path('research/onchain-paper-replication-2026-09-24/storage/closed-ledger-offload-2026-09-30-04'))
    graph=module('prior_graph',HERE/'previous_graph_requirement.py').verify(ROOT)
    row=module('ledger_eligibility',HERE/'offload.py').eligibility(ROOT,manifest)
    free=shutil.disk_usage(ROOT).free;available=mem_available()
    requirement=json.loads((ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/remaining-graph-metadata-2026-09-30/2024-12-23/storage-projection.json').read_bytes())['required_free_at_launch_bytes']
    scratch=10*GIB+row['bytes']+16*1024**2
    assert free<requirement,'storage operation unnecessary; skip and reconcile graph prerequisites'
    assert free>=scratch and available>=int(3.5*GIB)
    r={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head':source,'pushed_head_matches':True,
       'bindings_verified':len(original),'contextual_bindings_verified':len(context),'unique_bindings_verified':len(paths),'committed_bindings_verified':count,
       'exact_local_connection_hash_verified':True,'release_review_sha256':review_sha,
       'previous_preservation':prior,'previous_graph':graph,'workspace_free_bytes':free,'graph_required_free_bytes':requirement,
       'graph_shortfall_bytes':requirement-free,'roundtrip_scratch_required_bytes':scratch,'mem_available_bytes':available,
       'no_active_unit':True,'exclusive_identity_absent':True,
       'qualification':'Metadata/stat check; no source ledger, array or remote body read. Exact bound local connection metadata hashed only; no contents printed or committed.'}
    with (HERE/'preflight01.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
    print(json.dumps(r,indent=2))
if __name__=='__main__':main()
