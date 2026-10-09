from pathlib import Path
import json,hashlib,copy
R=Path(__file__).resolve().parent;ROOT=Path.cwd();E=R.parent/'real-data-pilot-full26-entry01-2026-10-09';name='eth-paper-real-data-end-to-end-resource-20261009-26';j=lambda p:json.loads(p.read_bytes());h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=j(E/'gate01-PREDECESSOR02.json');g=j(E/'gate01.json');b=j(E/'BINDING_DRAFT05.json');d=j(E/'BINDING_DRAFT04.json');pr=j(R/'BINDING_REVIEW02.json');ev=dict(pr['evidence']);gatepath=str((E/'gate01.json').relative_to(ROOT));assert h(E/'gate01-PREDECESSOR02.json')==ev[gatepath]
aentry=a['experiments'][name];entry=g['experiments'][name];old=aentry['runtime_hashes'];new=entry['runtime_hashes'];assert len(old)==len(new)==7 and set(old)==set(new);assert {k for k in new if new[k]!=old[k]}=={'admission.py'}
p=ROOT/'tradingagents/research/admission.py';assert new['admission.py']==h(p)==entry['source_files']['tradingagents/research/admission.py']=='90bb459bcc7d9f73dda6965c59bf3d6f3bf75f3cbb8bd0ff3b869f7f8b76c930'
z=copy.deepcopy(g);z['experiments'][name]['runtime_hashes']=old;assert z==a
assert {k for k in b if b[k]!=d[k]}=={'gate'} and b['input_refs']==pr['input_refs']
def pin(ref):
 p=ROOT/ref['path'];assert p.resolve()==p and p.is_file() and p.stat().st_nlink==1 and h(p)==ref['sha256']
 if 'bytes' in ref:assert p.stat().st_size==ref['bytes']
 ev[ref['path']]=ref['sha256']
def add(p):pin({'path':str(p.relative_to(ROOT)),'sha256':h(p)})
for k,v in b.items():
 if isinstance(v,dict) and {'path','sha256'}<=v.keys():
  if k!='gate':assert ev[v['path']]==v['sha256']
  pin(v)
for p in (E/'gate01-PREDECESSOR02.json',E/'BINDING_DRAFT05.json',E/'RUNTIME_CORRECTION01.json',E/'ADMISSION_CHECK01.json',R/'BINDING_REVIEW02.json',R/'SOURCE_REVIEW02.json'):add(p)
assert len(entry['source_files'])==395 and len(entry['inputs'])==64
assert all(ev[p]==v for p,v in entry['source_files'].items())
r={'decision':'accepted','identity':name,'input_refs':pr['input_refs'],'evidence':ev,'scope':'Single actual runtime declaration correction: admission.py joins accepted installed90bb dedup source. The former runtime-hashes-unchanged statement was incorrect for this field and is superseded; all six other runtime values,395 sources,64 inputs, scientific/native/storage limits unchanged. No genuine admission, current capacity, recovery or launch granted.'};out=R/'BINDING_REVIEW03.json';assert not out.exists();out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
s={'decision':'accepted_single_runtime_pin_correction','binding_review_sha256':h(out),'old_runtime_hash':old['admission.py'],'current_runtime_hash':new['admission.py'],'checks':['Entire gate inverse changes only selected runtime_hashes.admission.py.','Current declaration equals installed source SHA and already admitted source pin; six other runtime hashes and seven fieldnames unchanged.','DRAFT05 inverse changes only gate ref;395 sources64 inputs and all other binding references retained.'],'qualification':'Previous acceptance omitted this runtime declaration drift; actual preclaim refusal preserved. Corrected source metadata only, no rerun/admission/claim or numerical execution.'};(R/'SOURCE_REVIEW03.json').write_text(json.dumps(s,indent=2)+'\n');print(json.dumps({'binding_sha256':h(out),'source_sha256':h(R/'SOURCE_REVIEW03.json'),'evidence_count':len(ev)}))
