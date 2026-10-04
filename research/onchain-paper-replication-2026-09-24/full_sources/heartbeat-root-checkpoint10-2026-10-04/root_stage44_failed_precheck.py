from pathlib import Path
import os,json,hashlib,subprocess,datetime
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';C=F/'heartbeat-root-checkpoint10-2026-10-04'
assert subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip()=='research/onchain-paper-replication-2026-09-24';assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()=='c23c91562abe772c90f3db60e139a01750190589';assert subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R)==b''
roots=['financial-wrapper-complete100-failed-root-remote-release03-2026-10-04','financial-wrapper-complete100-failed-root-remote-outcome-review03-2026-10-04','financial-wrapper-complete100-failed-full-recovery-review03-2026-10-04','financial-wrapper-operational-provenance-compatibility-preparation01-2026-10-04','financial-wrapper-operational-provenance-compatibility-review01-2026-10-04','financial-wrapper-operational-provenance-compatibility-preparation02-2026-10-04','financial-wrapper-operational-provenance-compatibility-review02-2026-10-04','financial-wrapper-cumulative20-preparation01-2026-10-04','financial-wrapper-cumulative20-review01-2026-10-04','financial-wrapper-compatibility-root-integration01-2026-10-04','financial-wrapper-compatibility-root-source-adoption-review01-2026-10-04','financial-wrapper-compatibility-actual-source-adoption-review01-2026-10-04','financial-wrapper-compatibility-root-policy01-2026-10-04','financial-wrapper-compatibility-concrete-policy-review01-2026-10-04','financial-wrapper-compatibility-three-consumer-input-investigation01-2026-10-04','financial-wrapper-compatibility-registration-preparation01-2026-10-04','financial-wrapper-compatibility-operational-delta-tooling01-2026-10-04','financial-wrapper-compatibility-operational-delta-preservation-review02-2026-10-04']
files=[];excluded=[]
for name in roots:
 p=F/name;assert p.is_dir(),name
 for root,ds,fs in os.walk(p,followlinks=False):
  for n in list(ds):
   if n=='.git' or n.endswith('.git') or n=='__pycache__':ds.remove(n);excluded.append(str((Path(root)/n).relative_to(R)))
  for n in fs:
   p=Path(root)/n;assert not p.is_symlink();assert p.stat().st_size<4*1024**2;files.append(p)
# Completed actual remote receivers remain recoverable local raw stores. Stage receipts/source, not duplicate bare/flat/selected bytes.
T=F/'financial-wrapper-complete100-failed-root-remote03-2026-10-04'
files.extend(p for p in T.iterdir() if p.is_file());files.extend(p for p in (T/'utilities').iterdir() if p.is_file());excluded.extend(str(p.relative_to(R)) for p in T.iterdir() if p.is_dir() and p.name!='utilities')
# Canonical archive+manifest preserves complete retained snapshot membership/modes/bodies.
for name in ['financial-wrapper-compatibility-operational-delta-capture01-2026-10-04','financial-wrapper-compatibility-operational-delta-capture02-2026-10-04']:
 p=F/name;files.extend(x for x in p.iterdir() if x.is_file());excluded.append(str((p/'snapshot').relative_to(R)))
files.extend([R/'research/onchain-paper-replication-2026-09-24/STATE.md',F/'parallel-execution-2026-10-02/COORDINATION.md',C/'REMOTE_CONFIRMATION43.json',C/'TOP60_CHECKPOINT01.json',C/'root_top60.py'])
rows=[{'path':p.relative_to(R).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(set(files))]
manifest={'schema_version':1,'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stage':44,'paths':rows,'excluded_retained_local_duplicate_recovered_or_canonical_snapshot_trees':sorted(excluded),'qualification':'Closed exact source/reviews/receipts and canonical scoped archives. No installed-runtime-body recovery, prospective source/policy/gate/NUM authority or duplicate bare/flat archival claim follows.'}
p=C/'STAGE44_PREPARATION01.json';p.write_text(json.dumps(manifest,indent=2)+'\n');names=[x['path'] for x in rows]+[p.relative_to(R).as_posix()]
for start in range(0,len(names),100):subprocess.run(['git','add','--',*names[start:start+100]],cwd=R,check=True)
check=subprocess.run(['git','diff','--cached','--check'],cwd=R,capture_output=True);style=C/'STAGE44_STYLE01.json';style.write_text(json.dumps({'exit':check.returncode,'stdout':check.stdout.decode(),'stderr':check.stderr.decode(),'frozen_original_bytes_kept':True},indent=2)+'\n');subprocess.run(['git','add','--',style.relative_to(R).as_posix()],cwd=R,check=True)
print(len(names)+1,sum(x['bytes'] for x in rows),check.returncode)
