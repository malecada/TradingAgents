import hashlib,json,os,stat,subprocess
from pathlib import Path
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'held-consumer-root-checkpoint07-2026-10-03';staged=[];skipped=[]
names=['batch-output-full-source-helper-preparation01','batch-output-full-source-helper-review01','batch-output-full-source-helper-preparation02','batch-output-full-source-helper-review02','batch-output-combined-worker-preparation01','batch-output-combined-worker-review01','held-consumer-final-recovery-preparation01','held-consumer-final-recovery-preparation02','held-consumer-final-recovery-preparation03','held-consumer-final-recovery-review01','held-consumer-final-recovery-review02','held-consumer-final-recovery-review03','held-consumer-flat-git-recovery-preparation01','held-consumer-flat-git-recovery-review01','held-consumer-one-use-parent-preparation01','held-consumer-one-use-parent-preparation02','held-consumer-one-use-parent-preparation03','held-consumer-one-use-parent-review01','held-consumer-one-use-parent-review02','held-consumer-one-use-parent-review03','held-consumer-final-composition-root-preparation01','held-consumer-final-composition-review01','held-consumer-final-baseline-root-capture01','held-consumer-final-baseline-capture-review01']
for prefix in names:
 folder=F/(prefix+'-2026-10-03');assert folder.is_dir();manifests=[p for p in folder.iterdir() if p.name.startswith('MANIFEST') and p.suffix=='.json'];assert len(manifests)==1,(prefix,manifests)
 manifest=manifests[0];v=json.loads(manifest.read_bytes());rows=v.get('files',v.get('members'));assert isinstance(rows,list)
 paths=[manifest]
 for row in rows:
  p=folder/row['path'];assert p.is_relative_to(folder) and '..' not in p.relative_to(folder).parts;s=p.lstat();kind=row.get('type',row.get('kind'));protected={'keys','apis','.env','.ssh','hf_token.txt'};assert not any(x.lower() in protected or x.lower().endswith(('.pem','.key')) for x in p.relative_to(folder).parts)
  if stat.S_ISDIR(s.st_mode):continue
  if stat.S_ISREG(s.st_mode):
   assert s.st_size==row['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'];assert 'mode' not in row or stat.S_IMODE(s.st_mode)==(int(row['mode'],0) if type(row['mode']) is str else row['mode'])
  elif stat.S_ISLNK(s.st_mode):assert os.readlink(p)==row.get('target',row.get('link_target'))
  else:skipped.append({'path':str(p.relative_to(R)),'actual_mode':s.st_mode,'reason':'special adversarial fixture recorded by exact typed manifest; not a Git regular body or production baseline'});continue
  if '.git' in p.relative_to(folder).parts:skipped.append({'path':str(p.relative_to(R)),'reason':'nested Git internal namespace remains original local; exact manifest retained, no complete prototype recovery claim'});continue
  paths.append(p)
 for p in paths:staged.append(str(p.relative_to(R)))
staged += ['research/onchain-paper-replication-2026-09-24/STATE.md','research/onchain-paper-replication-2026-09-24/full_sources/parallel-execution-2026-10-02/COORDINATION.md','research/onchain-paper-replication-2026-09-24/full_sources/held-consumer-root-checkpoint06-2026-10-03/REMOTE_CONFIRMATION01.json']
for p in D.iterdir():
 if p.is_file():staged.append(str(p.relative_to(R)))
assert len(staged)==len(set(staged))
report={'schema_version':1,'selected_body_count':len(staged),'skipped_special_or_nested_fixture_namespaces':skipped,'source_and_manifest_body_staging_only':True,'local_prototype_original_trees_preserved':True,'complete_actual_capsule_and_parent_archive_members':937,'whole_prototype_or_runtime_or_outside_stores_recovery_claim':False}
(D/'STAGING_SCOPE01.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');staged.append(str((D/'STAGING_SCOPE01.json').relative_to(R)))
for i in range(0,len(staged),80):
 run=subprocess.run(['git','add','-f','--',*staged[i:i+80]],cwd=R,capture_output=True);assert run.returncode==0,run.stderr[:300]
print('staged',len(staged),'skipped metadata-only fixture paths',len(skipped))
