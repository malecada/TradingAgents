from pathlib import Path
import hashlib,json,os,stat
D=Path(__file__).resolve().parent;M=D.parents[3];E=M/'research/onchain-paper-replication-2026-09-24/storage/closed-array-pilot-offload-2026-10-05-01';c=json.loads((E/'manifest.json').read_text());draft=json.loads((M/c['draft']['path']).read_text())
def h(p):
 assert p.suffix not in ('.npy','.npz','.pt','.sqlite') and p.stat().st_size<=4*1024**2
 return hashlib.sha256(p.read_bytes()).hexdigest()
for p,r in draft['metadata_pins'].items():assert h(M/p)==r['sha256']
for r in c['protected_metadata']:assert h(M/r['path'])==r['sha256']
protected=[(M/p).resolve() for p in c['protected_roots']];selected=[]
for row in draft['files']:
 p=M/row['path'];s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and not p.is_symlink();assert [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]==row['stat_identity'];assert s.st_size==row['bytes'];assert not p.with_name(p.name+'.remote.json').exists()
 manifest=p.parent/'manifest.json';assert h(manifest)==row['graph_manifest_sha256'];v=json.loads(manifest.read_text());a=v['arrays'][p.stem];assert a['path']==p.name and a['bytes']==row['bytes'] and a['sha256']==row['sha256'];assert not any(p.resolve()==q or p.resolve().is_relative_to(q) for q in protected);selected.append(p.resolve())
closure_summary=[]
for row in draft['closures']:
 name=row['experiment'];run=M/'research_runs'/name;assert h(run/'claim.json')==row['claim_sha256'];assert h(run/'complete.json')==row['terminal_sha256'];assert h(run/'outputs/artifact-index.json')==row['artifact_index_sha256'];assert not (run/'failed.json').exists();t=json.loads((run/'complete.json').read_text());assert t['status']=='complete' and t['claim_sha256']==row['claim_sha256'];g=json.loads((M/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/name/'guard/final.json').read_text());assert g['phase']=='complete' and g['child_exit_code']==0 and g['cleanup_verified'] is True;assert not Path(g['cgroup']).exists() and not Path('/proc',str(g['monitor_pid'])).exists();closure_summary.append(name)
active=[]
C=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-canonical-native-20261005-01/source')
for root in [M,C]:
 for p in (root/'research_runs').glob('*/claim.json'):
  if (p.parent/'complete.json').exists() or (p.parent/'failed.json').exists():continue
  claim=json.loads(p.read_text());active.append({'root':str(root),'identity':p.parent.name})
  for info in claim['experiment']['inputs'].values():
   q=(root/info['path']).resolve();assert not any(q==r or q.parent==r.parent or r.is_relative_to(q) for r in selected)
# The actual original import control names its protected graph, not a guessed week.
control=C/'fixture_inputs/held/success01/original_import.json';v=json.loads(control.read_text());assert v['week']=='2022-01-03' and v['sample_count']==512 and v['motif_count']==32
original=Path(v['refs']['graph_manifest']['original_path']);assert original.is_relative_to(protected[0]);assert h(original)==v['refs']['graph_manifest']['sha256']==h(C/'fixture_inputs/original/03-manifest.json');g=json.loads(original.read_text());assert g['graph_hash']=='67ffff78a83d67b77d3fefce1bc7f6dc3a7cab0c80ac68d8c72e0c99a30022b8'
assert protected[3]==C/'fixture_inputs/original'
for n in ('preflight01.json','launch-attempt01.json','guard01','intent.json','complete.json','failed.json','outer-exit01.json'):assert not (E/n).exists() and not (E/n).is_symlink()
assert not list(E.glob('*-attempted.json')) and not list(E.glob('*-verified.json'))
print(json.dumps({'decision':'pass','selected_arrays':len(selected),'logical_bytes':sum(r['bytes'] for r in draft['files']),'max_body_bytes':max(r['bytes'] for r in draft['files']),'metadata_pins_verified':len(draft['metadata_pins']),'protected_metadata_verified':len(c['protected_metadata']),'closed_complete_producers':closure_summary,'active_claims_checked':active,'canonical_original_graph':g['graph_hash'],'canonical_original_control_sha256':h(control),'protected_roots':c['protected_roots'],'fixed_namespace_absent':True,'large_body_read_or_hash':False,'credentials_read':False,'native_or_network':False},sort_keys=True,indent=2))
