import pathlib,json,hashlib,copy,stat,resource,signal,os
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(30);os.nice(10)
R=pathlib.Path(__file__).resolve().parent;F=R.parent;ROOT=pathlib.Path.cwd();E=F/'real-data-pilot-full24-entry01-2026-10-09';T=F/'real-data-pilot-full24-transport-binding01-2026-10-09'
j=lambda p:json.loads(pathlib.Path(p).read_bytes());h=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
oldreview=j(R/'BINDING_REVIEW01.json');oldb=j(E/'BINDING_DRAFT04.json');b=j(E/'BINDING_DRAFT05.json');gate=j(E/'gate01.json');oldgate=j(E/'gate-PREDECESSOR02.json');name=b['identity'];entry=gate['experiments'][name];oldentry=oldgate['experiments'][name];norm=lambda d:{k:{q:v[q] for q in ('path','sha256')} for k,v in d.items()};refs=norm(entry['inputs'])
assert len(refs)==64 and refs==b['input_refs'] and len(entry['source_files'])==378 and entry['source_files']==oldentry['source_files']
x=copy.deepcopy(entry);x['inputs']=oldentry['inputs'];assert x==oldentry
parent=entry['parent'];claimpath=ROOT/'research_runs'/parent/'claim.json';terminalpath=claimpath.parent/'failed.json';claim=j(claimpath);terminal=j(terminalpath)
assert gate['experiments'][parent]==claim['experiment'];assert terminal['claim_sha256']==h(claimpath) and terminal['status']=='failed'
y=copy.deepcopy(gate);del y['experiments'][parent];y['experiments'][name]=oldentry;assert y==oldgate
p1=j(T/'PREPARED01.json');p2=j(T/'PREPARED02.json');bo1=j(T/'BOUND01.json');bo2=j(T/'BOUND02.json')
assert h(ROOT/b['preparation']['path'])==b['preparation']['sha256'] and bo2['source_request']['prepared']==b['preparation'] and bo2['source_request']['archive_policy']==b['unbound_archive']
assert p2['preparation_origin']['public_manifest']==b['public_manifest']
# Invert only the two descriptive policy digests; all public decoded bodies remain.
a=copy.deepcopy(bo2['inputs']);original=bo1['inputs']
for value,ov in ((a['execution_job']['payload']['representation_jobs']['original32'],original['execution_job']['payload']['representation_jobs']['original32']),(a['producer_plan']['producers']['original32'],original['producer_plan']['producers']['original32'])):
 d=value['descriptor'];assert d['configs']['dictionary']['sample_count']==512 and d['configs']['dictionary']['size']==32 and len(d['required_graphs'])==7
 for key,role in (('compact_execution','compact_policy'),('pair_execution','pair_policy'),('compact_archive_execution','archive_policy')):assert d[key]['policy_sha256']==refs[role]['sha256']
 for key in ('compact_execution','pair_execution'):d[key]['policy_sha256']=ov['descriptor'][key]['policy_sha256']
assert a==original
for role in refs:
 if role not in bo2['inputs'] and role!='archive_transport':assert refs[role]==oldreview['input_refs'][role]
for role,doc in bo2['inputs'].items():assert j(ROOT/refs[role]['path'])==doc and h(ROOT/refs[role]['path'])==refs[role]['sha256']
assert bo2['private_input']=={'archive_transport':b['transport']};opaque=ROOT/b['transport']['path'];s=opaque.lstat();assert s.st_size==b['transport']['bytes'] and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600 and stat.S_IMODE(opaque.parent.stat().st_mode)==0o700
assert h(opaque)==b['transport']['sha256'] and b['transport']['path']!=oldb['transport']['path']
# Source caller is unchanged; inverse binder retains expected exact source-request references.
assert p2['builder03_spec']['references']['archive_policy']==b['unbound_archive'];assert entry['cumulative_budget_extension']['review']==b['budget_review']
assert bo2['binding']==bo1['binding']
source=(T/'bind_actual02.py').read_text();assert "policy_digest = module.sha(module.raw(docs[expected_role]))" in source
assert h(F/'real-data-pilot-transport-binding-preparation01-2026-10-06/bind01.py')=='bcca66a6c7daba762a629dff84b9f16e48e7b9c2ffe51f77511942816ee444cb'
evidence=dict(oldreview['evidence']);del evidence[oldb['transport']['path']]
def add(ref):
 p=ROOT/ref['path'];assert h(p)==ref['sha256'];evidence[ref['path']]=ref['sha256']
for ref in refs.values():add(ref)
for v in b.values():
 if isinstance(v,dict) and {'path','sha256'}<=v.keys():add(v)
for p in [E/'BINDING_DRAFT05.json',E/'REGISTRATION_BINDING_CORRECTION01.json',T/'bind_actual02.py',T/'REQUEST02.json',T/'BINDING_CHECK02.json',T/'ALL_INPUT_REFS02.json',R/'BINDING_REVIEW01.json',claimpath,terminalpath]:add({'path':str(p.relative_to(ROOT)),'sha256':h(p)})
assert [p for p in evidence if p.startswith('research_artifacts/real_pilot_runtime/')]==[b['transport']['path']]
r={'decision':'accepted','identity':name,'input_refs':refs,'evidence':evidence,'scope':'Supplement to accepted source03/core/public review: literal actual terminal23 parent registration and two descriptive policy hashes corrected before unchanged binder; exact new dispatch hash-only. No runtime eligibility, final release, recovery or execution approval.'}
(R/'BINDING_REVIEW02.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
sr={'decision':'accepted_changed_parent_descriptor_binding_only','binding_review_sha256':h(R/'BINDING_REVIEW02.json'),'previous_review_sha256':h(R/'BINDING_REVIEW01.json'),'source_pins_unchanged':378,'inputs':64,'evidence_count':len(evidence),'parent_claim_sha256':h(claimpath),'parent_failed_sha256':h(terminalpath),'checks':['Exact terminal parent definition equals original claim experiment; all other gate fields unchanged except selected input refs.','Both selected and producer descriptors join actual compact/pair/archive policy byte digests; literal inverse restores only compact/pair descriptive digests.','All actual policy/science/resource decoded bodies equal accepted bound01;512samples32motifs7graphs retained.','Accepted binder source unchanged, actual pre-bind canonical digest derivation inspected; new private dispatch hash/stat only.','Old opaque ref excluded from new release evidence; old public histories retained. Current evidence authenticates exactly one opaque body.'],'limitations':['No actual admission/preflight/transport/native run; Root read-only admission separate.','Actual corrected public increment external return and final BINDING/release still pending.']}
(R/'SOURCE_REVIEW02.json').write_text(json.dumps(sr,indent=2)+'\n');print(json.dumps({'binding_review_sha256':h(R/'BINDING_REVIEW02.json'),'source_review_sha256':h(R/'SOURCE_REVIEW02.json'),'evidence_count':len(evidence)}))
