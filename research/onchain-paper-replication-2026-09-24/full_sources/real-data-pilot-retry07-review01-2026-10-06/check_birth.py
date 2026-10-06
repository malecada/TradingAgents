"""Independent nonempty-tree birth reconstruction; synthetic bytes only."""
from pathlib import Path
import hashlib,importlib.util,json,tempfile
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;W=HERE.parent/'real-data-pilot-storage-birth-fix01-2026-10-06';ROOT=HERE.parents[3]
p=W/'candidate/real_pilot_storage.py';spec=importlib.util.spec_from_file_location('tradingagents.research.onchain_replication.review_birth_candidate',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with tempfile.TemporaryDirectory(dir=HERE) as t:
 root=Path(t);art=root/'research_artifacts';art.mkdir();(art/'old').write_bytes(b'o'*19);parent=root/'research_runs';parent.mkdir();(parent/'.lock').write_bytes(b'l'*5);target=parent/m.EXPERIMENT
 limits=dict(max_allocated_bytes=2**20,max_logical_bytes=100,max_entries=100,max_depth=8,max_scan_seconds=5)
 budget=dict(schema_version=2,kind=m.KIND,authority_root=str(root),experiment=m.EXPERIMENT,roots=[str(art),str(target)],shared_files=[str(parent/'.lock')],limits=limits)
 watch=m.WritableUnion(budget,root);original=m.StorageWatch._check;events=[]
 def inject(w,begin,history):
  result=original(w,begin,history)
  if w.root==art:
   events.append(begin)
   if len(events)==1:
    target.mkdir();(target/'nested').mkdir();(target/'nested'/'new').write_bytes(b'n'*31)
  return result
 with patch.object(m.StorageWatch,'_check',inject):raced=watch.check()
 stable=m.WritableUnion(budget,root).check()
 keys=['logical_file_bytes','allocated_bytes','entries','regular_files','directories']
 assert {k:raced[k] for k in keys}=={k:stable[k] for k in keys}
 assert raced['logical_file_bytes']==19+5+31==55
 assert raced['residual_domains']['training_and_lifecycle']['logical_file_bytes']==31
 assert len(events)==2 and len(set(events))==1
 assert watch.target_identity==(target.stat().st_dev,target.stat().st_ino)
 report={'decision':'passed','candidate_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'same_begin':True,'artifact_passes':2,'raced_counts':{k:raced[k] for k in keys},'stable_counts':{k:stable[k] for k in keys},'late_born_residual_logical_bytes':31,'scope':'Independent exact count comparison for nonempty artifact/shared lock and nested late-born subtree; tiny local synthetic metadata only.'}
 (HERE/'BIRTH_RECONSTRUCTION01.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2))
