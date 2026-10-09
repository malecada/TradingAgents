import pathlib,json,hashlib
ROOT=pathlib.Path.cwd();R=pathlib.Path(__file__).resolve().parent;E=R.parent/'real-data-pilot-full29-entry01-2026-10-09';j=lambda p:json.loads(p.read_bytes());h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=j(E/'BINDING01.json');d=j(E/'BINDING_DRAFT03.json');review=j(R/'BINDING_REVIEW01.json');ev=dict(review['evidence'])
assert len(ev)==543 and review['decision']=='accepted'
assert {k for k in b.keys()|d.keys() if b.get(k)!=d.get(k)}=={'binding_review'}
assert d['binding_review'] is None and b['status']=='BOUND_FINAL_PENDING_RELEASE'
ref=b['binding_review'];assert ref=={'path':str((R/'BINDING_REVIEW01.json').relative_to(ROOT)),'sha256':h(R/'BINDING_REVIEW01.json'),'bytes':(R/'BINDING_REVIEW01.json').stat().st_size}
assert ref['sha256']=='a3b49e629a33f0375358c49396e59470cb3b6c06873b0370742e6091d6544f51'
for k,v in b.items():
 if isinstance(v,dict) and {'path','sha256'}<=v.keys() and k!='binding_review':assert ev[v['path']]==v['sha256']
def add(p):ev[str(p.relative_to(ROOT))]=h(p)
for p in [E/'gate03.json',E/'preflight29_01.py',E/'root_io29_01.py']:
 assert ev[str(p.relative_to(ROOT))]==h(p)
g=j(E/'gate03.json');x=g['experiments'][b['identity']];assert len(x['source_files'])==455 and len(x['inputs'])==64
assert all(ev[p]==sha for p,sha in x['source_files'].items())
assert all(ev[v['path']]==v['sha256'] for v in x['inputs'].values())
assert x['cumulative_budget_extension']['review']==b['budget_review']
assert [p for p in ev if p.startswith('research_artifacts/real_pilot_runtime/')]==[b['transport']['path']]
ad=j(E/'ADMISSION_CHECK02.stdout');assert ad=={'experiment':b['identity'],'stage':'development','ready':True,'status':'metadata_admitted','empirical_inputs_opened':False,'run_started':False};assert not (E/'ADMISSION_CHECK02.stderr').read_bytes()
for p in (E/'BINDING01.json',R/'BINDING_REVIEW01.json',R/'SOURCE_REVIEW01.json',E/'ADMISSION_CHECK02.stdout',E/'ADMISSION_CHECK02.stderr',E/'ADMISSION_REFUSAL01.json',R/'seal01.py'):add(p)
release={'decision':'accepted','identity':b['identity'],'actual_final_binding_sha256':h(E/'BINDING01.json'),'reused_binding_review_sha256':ref['sha256'],'evidence':ev,'scope':'Exact final full29 source/input/binding release candidate, reusing accepted455-source/64-input/100-allowance review. Actual final binding changes only binding_review; status was already BOUND_FINAL_PENDING_RELEASE in draft03. No evidence self-reference.','conditions':['Actual final declared full29 public increment14 external return and independent exact typed-member/body verification.','Fresh original preflight committed admission/source/runtime/resource/process/namespace eligibility and authenticated committed release before at most one unused29 attempt.'],'admission_qualification':'Actual saved ADMISSION_CHECK02 stdout says ready/metadata_admitted and no empirical inputs or run start; stderr is empty. Root separately reports original tool exit0/a020e0 at source714715; these fields are not present in stdout and no raw tool export is invented.','qualification':'Original before-claim admission refusal and both binder wrapper failures remain preserved. Saved BOUND02/public outputs are independently hash-joined, not a coerced successful wrapper exit. No new increment14 recovery or current capacity eligibility asserted; inherited failed28 outcome13 recovery is distinct. No numerical input/import, Run/Owner/claim/network/launch, complete MCM/training, whole future capacity or speedup credit. Sole current29 opaque dispatch remains hash/stat evidence only.'}
(R/'RELEASE_REVIEW01.json').write_text(json.dumps(release,indent=2,sort_keys=True)+'\n')
proof={'decision':'accepted_final_binding_delta_only','binding_sha256':h(E/'BINDING01.json'),'release_sha256':h(R/'RELEASE_REVIEW01.json'),'changed_binding_fields':['binding_review'],'inherited_evidence_count':543,'release_evidence_count':len(ev),'no_self_reference':str((R/'RELEASE_REVIEW01.json').relative_to(ROOT)) not in ev}
(R/'SEAL01.json').write_text(json.dumps(proof,indent=2,sort_keys=True)+'\n');print(json.dumps(proof))
