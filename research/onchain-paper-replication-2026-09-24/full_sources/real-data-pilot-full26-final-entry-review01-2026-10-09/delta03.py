from pathlib import Path
import json,hashlib,copy
R=Path(__file__).resolve().parent;ROOT=Path.cwd();E=R.parent/'real-data-pilot-full26-entry01-2026-10-09';name='eth-paper-real-data-end-to-end-resource-20261009-26'
j=lambda p:json.loads(p.read_bytes());h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=j(E/'gate01-PREDECESSOR01.json');g=j(E/'gate01.json');old=a['experiments'][name];new=g['experiments'][name];prior=j(R/'BINDING_REVIEW01.json');ev=dict(prior['evidence'])
assert h(E/'gate01-PREDECESSOR01.json')==ev[str((E/'gate01.json').relative_to(ROOT))]
assert len(old['source_files'])==393 and len(new['source_files'])==395
assert all(new['source_files'][p]==v for p,v in old['source_files'].items())
added={p:v for p,v in new['source_files'].items() if p not in old['source_files']};ce=new['cumulative_budget_extension'];assert added=={v['path']:v['sha256'] for v in ce.values()}
restored=copy.deepcopy(g);restored['experiments'][name]['source_files']=old['source_files'];restored['experiments'][name]['cumulative_budget_extension']=old['cumulative_budget_extension'];assert restored==a
b=j(E/'BINDING_DRAFT04.json');oldb=j(E/'BINDING01-PREDECESSOR01.json');assert h(E/'BINDING01-PREDECESSOR01.json')==j(R/'RELEASE_REVIEW01.json')['actual_final_binding_sha256']
assert {k for k in b if b[k]!=oldb.get(k)}=={'gate','budget_review','binding_review','status'};assert b['binding_review'] is None and b['budget_review']==ce['review']
def pin(ref):
 p=ROOT/ref['path'];assert p.resolve()==p and p.is_file() and p.stat().st_nlink==1 and h(p)==ref['sha256']
 if 'bytes' in ref:assert p.stat().st_size==ref['bytes']
 ev[ref['path']]=ref['sha256']
def add(p):pin({'path':str(p.relative_to(ROOT)),'sha256':h(p)})
for ref in ce.values():pin(ref)
ext=j(ROOT/ce['extension']['path']);prev=j(ROOT/old['cumulative_budget_extension']['extension']['path']);assert {k for k in ext if ext[k]!=prev[k]}=={'allocation'}
assert ext['allocation']['path']==str((E/'CUMULATIVE_ALLOCATION_PROPOSED97_01.json').relative_to(ROOT));pin(ext['allocation']);assert new['source_files'][ext['allocation']['path']]==ext['allocation']['sha256']
br=j(ROOT/ce['review']['path']);assert br['decision']=='accepted' and br['extension_sha256']==ce['extension']['sha256'];assert ext['cumulative_ceiling']==97 and ext['consumed_before']==65 and ext['initial_experiment']==name
for k,v in b.items():
 if isinstance(v,dict) and {'path','sha256'}<=v.keys():
  if k not in ('gate','budget_review'):assert ev[v['path']]==v['sha256']
  pin(v)
assert b['input_refs']==prior['input_refs'] and all(ev[p]==v for p,v in new['source_files'].items())
for p in (E/'gate01-PREDECESSOR01.json',E/'BINDING01-PREDECESSOR01.json',E/'BINDING_DRAFT04.json',R/'BINDING_REVIEW01.json',R/'SOURCE_REVIEW01.json'):add(p)
r={'decision':'accepted','identity':name,'input_refs':prior['input_refs'],'evidence':ev,'scope':'Narrow correction of extension97 allocation reference and associated gate/budget binding only; previous393-source/64-input proof reused. Prior01 extension review missed wrong96 allocation reference and is superseded for authority by accepted02. No science/native/input/private body changes. Conditional source entry only, no actual admission/recovery/current capacity/launch.'}
p=R/'BINDING_REVIEW02.json';assert not p.exists();p.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
s={'decision':'accepted_changed_reference_seam_only','binding_review_sha256':h(p),'source_count':395,'input_count':64,'added_source_pins':added,'checks':['Entire gate inverse restores only cumulative extension references and removes exactly two new pins.','Exact extension inverse differs only genuine97 allocation path/hash;97 allocation source membership and independent02 review join.','DRAFT04 inverse differs final01 only gate,budget_review,review placeholder,status.','Original64 inputs and393 source hashes unchanged; prior source/science/capacity proof reused.'],'qualification':'01 false allocation join is preserved, not retroactively repaired;02 replaces its authority. No launch or current resource eligibility, no repeated numerical/source suites.'};(R/'SOURCE_REVIEW02.json').write_text(json.dumps(s,indent=2)+'\n');print(json.dumps({'binding_sha256':h(p),'source_sha256':h(R/'SOURCE_REVIEW02.json'),'evidence_count':len(ev)}))
