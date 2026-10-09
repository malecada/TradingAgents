from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parent;ROOT=Path.cwd();F=R.parent;E=F/'real-data-pilot-full26-entry01-2026-10-09'
j=lambda p:json.loads(p.read_bytes());h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=j(E/'BINDING01.json');d=j(E/'BINDING_DRAFT05.json');review=j(R/'BINDING_REVIEW03.json');evidence=dict(review['evidence'])
assert b['status']=='BOUND_FINAL_PENDING_RELEASE'
assert b['binding_review']['path']==str((R/'BINDING_REVIEW03.json').relative_to(ROOT)) and b['binding_review']['sha256']==h(R/'BINDING_REVIEW03.json')
if 'bytes' in b['binding_review']:assert b['binding_review']['bytes']==(R/'BINDING_REVIEW03.json').stat().st_size
changed={k for k in set(d)|set(b) if d.get(k)!=b.get(k)};assert changed=={'status','binding_review'}
for k,v in b.items():
 if isinstance(v,dict) and {'path','sha256'}<=v.keys():
  assert h(ROOT/v['path'])==v['sha256']
  if k!='binding_review':assert evidence[v['path']]==v['sha256']
  evidence[v['path']]=v['sha256']
for p in (E/'BINDING01.json',R/'SOURCE_REVIEW03.json',R/'CHECK_PRE01.json',R/'CHECK04.log'):
 evidence[str(p.relative_to(ROOT))]=h(p)
g=j(E/'gate01.json')['experiments'][review['identity']];assert len(g['source_files'])==395 and len(g['inputs'])==64
for p,v in g['source_files'].items():assert evidence[p]==v
for v in g['inputs'].values():assert evidence[v['path']]==v['sha256']
assert [p for p in evidence if p.startswith('research_artifacts/real_pilot_runtime/')]==[b['transport']['path']]
admission=j(E/'ADMISSION_CHECK02.json')
assert admission['exit_code']==0 and admission['claim'] is False
for suffix in ('stdout','stderr'):
 p=E/('ADMISSION_CHECK02.'+suffix);assert h(p)==admission[suffix+'_sha256'];evidence[str(p.relative_to(ROOT))]=h(p)
stdout=j(E/'ADMISSION_CHECK02.stdout');assert stdout['experiment']==review['identity'] and stdout['ready'] is True and stdout['status']=='metadata_admitted' and stdout['empirical_inputs_opened'] is False and stdout['run_started'] is False
evidence[str((E/'ADMISSION_CHECK02.json').relative_to(ROOT))]=h(E/'ADMISSION_CHECK02.json')
r={'decision':'accepted','identity':review['identity'],'actual_final_binding_sha256':h(E/'BINDING01.json'),'reused_binding_review_sha256':h(R/'BINDING_REVIEW03.json'),'evidence':evidence,'scope':'Exact final source/input/binding release candidate for fixed full26 guarded resource measurement; accepted395-source/64-input review reused. Final binding differs from reviewed draft05 only genuine review reference and status.','qualification':'Earlier release01 is superseded for the corrected97 allocation reference and runtime admission pin. Genuine read-only admission02 is joined; conditional on newest public-delta external recovery, committed source/release authentication and fresh resource/native/runtime/namespace checks before launcher. No pending recovery or current capacity is implied. No successful full pilot, speedup, hard quota, writer exclusion or financial credit. Sole current26 opaque transport retained as hash/stat evidence only. No numerical imports/arrays, Run, Owner, claim or network operation performed.'}
out=R/'RELEASE_REVIEW03.json';assert not out.exists();out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps({'path':str(out.relative_to(ROOT)),'sha256':h(out),'evidence_count':len(evidence)}))
