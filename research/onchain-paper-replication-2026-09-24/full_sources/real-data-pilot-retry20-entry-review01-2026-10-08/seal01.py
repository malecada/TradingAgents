import copy,hashlib,json
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';N=F/'real-data-pilot-final20-2026-10-08';H=Path(__file__).resolve().parent
reviewpath=H/'BINDING_REVIEW01.json';reviewraw=reviewpath.read_bytes();assert hashlib.sha256(reviewraw).hexdigest()=='7ef145a877d1a2dfe9f40d743ac13e87d3f7c28b370abfef3b55222bd053c3cd'
review=json.loads(reviewraw);evidence=dict(review['evidence'])
a=json.loads((N/'BINDING_DRAFT02.json').read_bytes());bindingraw=(N/'BINDING01.json').read_bytes();b=json.loads(bindingraw)
assert {k for k in a.keys()|b.keys() if a.get(k)!=b.get(k)}=={'binding_review','status'}
assert b['status']=='BOUND_FINAL_PENDING_RELEASE'
assert b['binding_review']=={'path':str(reviewpath.relative_to(R)),'bytes':len(reviewraw),'sha256':hashlib.sha256(reviewraw).hexdigest()}
assert review['identity']==b['identity'] and review['decision']=='accepted'
evidence[str(reviewpath.relative_to(R))]=hashlib.sha256(reviewraw).hexdigest();evidence[str((N/'BINDING01.json').relative_to(R))]=hashlib.sha256(bindingraw).hexdigest()
for v in b.values():
 if isinstance(v,dict) and {'path','sha256'}<=v.keys():assert evidence[v['path']]==v['sha256']
gate=json.loads((N/'gate02.json').read_bytes());experiment=gate['experiments'][b['identity']]
for p,h in experiment['source_files'].items():assert evidence[p]==h
for v in experiment['inputs'].values():assert evidence[v['path']]==v['sha256']
private=b['transport']['path'];assert private in evidence
public=[]
for name in evidence:
 p=R/name
 assert not Path(name).is_absolute() and '..' not in Path(name).parts and p.resolve(strict=True)==p and p.is_file() and p.stat().st_nlink==1 and p.stat().st_size<=4*1024**2,name
 if name==private:continue
 assert not any(x in Path(name).parts for x in ('keys','apis','.env')) and p.suffix not in ('.npy','.npz','.body','.bin'),name
 public.append(name)
assert len(public)==len(evidence)-1
for file in ('preflight02.py','root_io02.py','gate02.json'):
 p=N/file;assert hashlib.sha256(p.read_bytes()).hexdigest()==evidence[str(p.relative_to(R))]
result={'schema_version':1,'decision':'accepted','identity':b['identity'],'evidence':evidence,'scope':'Focused final seal: exact BINDING_DRAFT02 plus binding_review and final status only. Reuses accepted corrected gate02 source318/input59 closure and prior semantic entry review. No repeated suites, admission or native work. Public bodies require Root commit and actual recovery before unchanged preflight verifies Git and fresh eligibility. Sole private dispatch remains hash-only. Full MCM/update/fit incomplete.','final_binding_sha256':hashlib.sha256(bindingraw).hexdigest(),'public_evidence_count':len(public),'opaque_evidence_count':1}
(H/'RELEASE_REVIEW01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'decision':'accepted','evidence_count':len(evidence),'public_evidence_count':len(public),'release_sha256':hashlib.sha256((H/'RELEASE_REVIEW01.json').read_bytes()).hexdigest(),'binding_sha256':result['final_binding_sha256']}))
