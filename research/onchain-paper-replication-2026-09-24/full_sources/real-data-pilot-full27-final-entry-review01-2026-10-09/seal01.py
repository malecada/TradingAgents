from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parent;ROOT=Path.cwd();E=R.parent/'real-data-pilot-full27-entry01-2026-10-09';j=lambda p:json.loads(p.read_bytes());h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=j(E/'BINDING01.json');d=j(E/'BINDING_DRAFT02.json');r=j(R/'BINDING_REVIEW01.json');ev=dict(r['evidence'])
assert h(E/'BINDING01.json')=='d73bb08cee2828d72768cff3d5304c06c1cb065394005cb45c65f7d289d44ca0'
assert {k for k in set(b)|set(d) if b.get(k)!=d.get(k)}=={'binding_review','status'} and b['status']=='BOUND_FINAL_PENDING_RELEASE'
assert b['binding_review']['path']==str((R/'BINDING_REVIEW01.json').relative_to(ROOT)) and b['binding_review']['sha256']==h(R/'BINDING_REVIEW01.json')=='f0d811ce0a64d2183ae3a64629c42c58e895500291846547754d79fccc744005'
for k,v in b.items():
 if isinstance(v,dict) and {'path','sha256'}<=v.keys():
  p=ROOT/v['path'];assert h(p)==v['sha256']
  if 'bytes' in v:assert p.stat().st_size==v['bytes']
  if k!='binding_review':assert ev[v['path']]==v['sha256']
  ev[v['path']]=v['sha256']
g=j(E/'gate01.json')['experiments'][r['identity']];assert len(g['source_files'])==406 and len(g['inputs'])==64 and r['input_refs']==b['input_refs']
for p,v in g['source_files'].items():assert ev[p]==v
for v in g['inputs'].values():assert ev[v['path']]==v['sha256']
for n in ('preflight27_01.py','root_io27_01.py'):assert ev[str((E/n).relative_to(ROOT))]==h(E/n)
a=j(E/'ADMISSION_CHECK01.json');o=j(E/'ADMISSION_CHECK01.stdout');assert a['exit_code']==0 and a['source']=='8c213e6e2b3e303b459cb9be2d5d5628b4f168b9' and o['ready'] is True and o['status']=='metadata_admitted' and o['empirical_inputs_opened'] is False and o['run_started'] is False
for suffix in ('stdout','stderr'):assert h(E/('ADMISSION_CHECK01.'+suffix))==a[suffix+'_sha256']
assert [p for p in ev if p.startswith('research_artifacts/real_pilot_runtime/')]==[b['transport']['path']]
for p in (E/'BINDING01.json',R/'SOURCE_REVIEW01.json'):ev[str(p.relative_to(ROOT))]=h(p)
x={'decision':'accepted','identity':r['identity'],'actual_final_binding_sha256':h(E/'BINDING01.json'),'reused_binding_review_sha256':h(R/'BINDING_REVIEW01.json'),'evidence':ev,'scope':'Exact final full27 source/input/binding release candidate. Accepted406-source/64-input changed-entry proof reused; final binding changes only genuine review reference and status. Actual committed read-only admission01 joined without inventing missing effective-budget output fields.','qualification':'Conditional on actual new27 public-increment external recovery with independent returned-artifact acceptance, committed source/release authentication, and fresh resource/native/runtime/namespace preflight before the single unused27 launch. New27 recovery is not completed or implied by inherited failed26 recovery. No current capacity, whole-job success, speedup, hard quota, writer exclusion or financial credit promised. Sole current27 opaque transport is hash/stat evidence only. No numerical input reads/imports, Run/Owner/claim, network or launch performed by reviewer.'}
p=R/'RELEASE_REVIEW01.json';assert not p.exists();p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n');print(json.dumps({'sha256':h(p),'evidence_count':len(ev)}))
