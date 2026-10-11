"""Read-only exact frozen source/evidence authentication; writes this review only."""
import hashlib,json,subprocess
from pathlib import Path
root=Path.cwd();dest=Path(__file__).parent
names=('compact_mcm_batched','real_pilot_import_caller','phase_timing','imported_authority_lease','matching_annealing','matching_immutable_session','matching_numeric_policy','matching_numeric_kernel','batched_continuation','batched_driver','batched_journal','batched_numeric_execution','batched_numeric_reuse','batched_pair_executor')
paths=[Path('tradingagents/research/onchain_replication')/(n+'.py') for n in names]
paths += [Path('tests/research/onchain_replication')/n for n in ('test_phase_timing.py','test_pilot_efficiency_selection.py','test_batched_continuation.py','test_matching_numeric_policy.py')]
def ref(p):
    raw=p.read_bytes();return dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
checks=[]
for name in ('pilot-efficiency-solver-qualification-2026-10-11','pilot-efficiency-continuation-2026-10-11'):
    p=dest.parent/name/'SOURCE_SNAPSHOT02.json';value=json.loads(p.read_bytes())
    entries=value['files'] if 'files' in value else [dict(path=k,**v) for k,v in value.items()]
    for item in entries:
        actual=ref(Path(item['path']))
        assert actual['sha256']==item['sha256'] and actual['bytes']==item['bytes'],actual['path']
    checks.append(dict(snapshot=ref(p),matched_entries=len(entries)))
value=dict(format='independent-source-review-snapshot-v1',git_head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip(),source_frozen_by_owners=True,files=[ref(p) for p in paths],owner_snapshot_checks=checks,empirical_authority=False)
(dest/'SOURCE_SNAPSHOT01.json').write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
print(json.dumps(dict(source_bodies=len(paths),owner_snapshot_checks=checks)))
