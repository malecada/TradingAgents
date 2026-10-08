import hashlib,json
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';N=F/'real-data-pilot-final20-2026-10-08';H=Path(__file__).resolve().parent
p=H/'BINDING_REVIEW02.json';raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()=='6dd45218eaa97768ed0013230db9e2022eedff49e81e44141d9aadad4e5b2ae2';review=json.loads(raw);evidence=dict(review['evidence'])
a=json.loads((N/'BINDING_DRAFT03.json').read_bytes());body=(N/'BINDING02.json').read_bytes();b=json.loads(body)
assert {k for k in a.keys()|b.keys() if a.get(k)!=b.get(k)}=={'status','binding_review'}
assert b['status']=='BOUND_FINAL_PENDING_RELEASE' and b['binding_review']=={'path':str(p.relative_to(R)),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
assert b['identity']==review['identity'] and review['decision']=='accepted'
evidence[str(p.relative_to(R))]=hashlib.sha256(raw).hexdigest();evidence[str((N/'BINDING02.json').relative_to(R))]=hashlib.sha256(body).hexdigest()
for v in b.values():
 if isinstance(v,dict) and {'path','sha256'}<=v.keys():assert evidence[v['path']]==v['sha256']
g=json.loads((N/'gate03.json').read_bytes())['experiments'][b['identity']]
assert len(g['source_files'])==320 and len(g['inputs'])==59
for name,h in g['source_files'].items():assert evidence[name]==h
for v in g['inputs'].values():assert evidence[v['path']]==v['sha256']
for name in ('gate03.json','preflight03.py','root_io03.py'):
 p=N/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==evidence[str(p.relative_to(R))]
private=b['transport']['path'];assert [name for name in evidence if name.startswith('research_artifacts/real_pilot_runtime/pilot-transport-')]==[private]
for name in evidence:
 p=R/name;assert not Path(name).is_absolute() and '..' not in Path(name).parts and p.resolve(strict=True)==p and p.is_file() and p.stat().st_nlink==1 and p.stat().st_size<=4*1024**2
 if name!=private:assert p.suffix not in ('.npy','.npz','.bin','.body') and not any(k in Path(name).parts for k in ('keys','apis','.env'))
result={'schema_version':1,'decision':'accepted','identity':b['identity'],'evidence':evidence,'final_binding_sha256':hashlib.sha256(body).hexdigest(),'source_count':320,'input_count':59,'opaque_evidence_count':1,'scope':'Focused final two-field seal only, reusing accepted corrected helper/policy/entry review. Current gate03/preflight03/root_io03 and all binding/source/input joins exact; sole new opaque private dispatch hash-only. Public commit/recovery and fresh preflight remain Root responsibilities. No suite, numerical work, admission, native launch or allowance adoption repeated. Prior releases/refusals remain preserved; full MCM/update/fit incomplete.'}
(H/'RELEASE_REVIEW02.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'decision':'accepted','release_sha256':hashlib.sha256((H/'RELEASE_REVIEW02.json').read_bytes()).hexdigest(),'evidence_count':len(evidence),'binding_sha256':result['final_binding_sha256']}))
