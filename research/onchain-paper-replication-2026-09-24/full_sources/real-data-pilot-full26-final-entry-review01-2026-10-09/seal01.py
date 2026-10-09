from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parent;ROOT=Path.cwd();F=R.parent;E=F/'real-data-pilot-full26-entry01-2026-10-09'
j=lambda p:json.loads(p.read_bytes());h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=j(E/'BINDING01.json');d=j(E/'BINDING_DRAFT03.json');review=j(R/'BINDING_REVIEW01.json');evidence=dict(review['evidence'])
assert b['status']=='BOUND_FINAL_PENDING_RELEASE'
assert b['binding_review']['path']==str((R/'BINDING_REVIEW01.json').relative_to(ROOT)) and b['binding_review']['sha256']==h(R/'BINDING_REVIEW01.json')
if 'bytes' in b['binding_review']:assert b['binding_review']['bytes']==(R/'BINDING_REVIEW01.json').stat().st_size
changed={k for k in set(d)|set(b) if d.get(k)!=b.get(k)};assert changed=={'status','binding_review'}
for k,v in b.items():
 if isinstance(v,dict) and {'path','sha256'}<=v.keys():
  assert h(ROOT/v['path'])==v['sha256']
  if k!='binding_review':assert evidence[v['path']]==v['sha256']
  evidence[v['path']]=v['sha256']
for p in (E/'BINDING01.json',R/'SOURCE_REVIEW01.json',R/'CHECK_PRE01.json',R/'CHECK02.log'):
 evidence[str(p.relative_to(ROOT))]=h(p)
g=j(E/'gate01.json')['experiments'][review['identity']];assert len(g['source_files'])==393 and len(g['inputs'])==64
for p,v in g['source_files'].items():assert evidence[p]==v
for v in g['inputs'].values():assert evidence[v['path']]==v['sha256']
assert [p for p in evidence if p.startswith('research_artifacts/real_pilot_runtime/')]==[b['transport']['path']]
r={'decision':'accepted','identity':review['identity'],'actual_final_binding_sha256':h(E/'BINDING01.json'),'reused_binding_review_sha256':h(R/'BINDING_REVIEW01.json'),'evidence':evidence,'scope':'Exact final source/input/binding release candidate for fixed full26 guarded resource measurement; accepted393-source/64-input review reused. Final binding differs from reviewed draft03 only genuine review reference and status.','qualification':'Conditional on actual genuine read-only admission, newest public-delta external recovery, committed source/release authentication and fresh resource/native/runtime/namespace checks before launcher. No pending recovery or current capacity is implied. No successful full pilot, speedup, hard quota, writer exclusion or financial credit. Sole current26 opaque transport retained as hash/stat evidence only. No numerical imports/arrays, Run, Owner, claim or network operation performed.'}
out=R/'RELEASE_REVIEW01.json';assert not out.exists();out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps({'path':str(out.relative_to(ROOT)),'sha256':h(out),'evidence_count':len(evidence)}))
