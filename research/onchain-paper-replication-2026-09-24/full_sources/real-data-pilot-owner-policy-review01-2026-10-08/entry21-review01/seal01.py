import hashlib,json
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';N=F/'real-data-pilot-final21-2026-10-08';H=Path(__file__).resolve().parent
p=H/'BINDING_REVIEW01.json';raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()=='5a795331d93748134cf484c86ff7bb2b2b1b0c15fd575b9d7db481855b506998';review=json.loads(raw);ev=dict(review['evidence']);a=json.loads((N/'BINDING_DRAFT01.json').read_bytes());body=(N/'BINDING01.json').read_bytes();b=json.loads(body)
assert {k for k in a.keys()|b.keys() if a.get(k)!=b.get(k)}=={'binding_review','status'} and b['status']=='BOUND_FINAL_PENDING_RELEASE'
assert b['binding_review']=={'path':str(p.relative_to(R)),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)} and review['decision']=='accepted' and b['identity']==review['identity']
ev[str(p.relative_to(R))]=hashlib.sha256(raw).hexdigest();ev[str((N/'BINDING01.json').relative_to(R))]=hashlib.sha256(body).hexdigest()
for v in b.values():
 if isinstance(v,dict) and {'path','sha256'}<=v.keys():assert ev[v['path']]==v['sha256']
g=json.loads((N/'gate01.json').read_bytes())['experiments'][b['identity']];assert len(g['source_files'])==331 and len(g['inputs'])==59
for name,h in g['source_files'].items():assert ev[name]==h
for v in g['inputs'].values():assert ev[v['path']]==v['sha256']
for name in ('preflight01.py','root_io.py','gate01.json'):
 p=N/name;assert ev[str(p.relative_to(R))]==hashlib.sha256(p.read_bytes()).hexdigest()
private=b['transport']['path'];assert [n for n in ev if n.startswith('research_artifacts/real_pilot_runtime/pilot-transport-')]==[private]
for n in ev:
 p=R/n;assert not Path(n).is_absolute() and '..' not in Path(n).parts and p.resolve(strict=True)==p and p.is_file() and p.stat().st_nlink==1 and p.stat().st_size<=4*1024**2
 if n!=private:assert p.suffix not in ('.npy','.npz','.bin','.body') and not any(k in Path(n).parts for k in ('keys','apis','.env'))
result={'schema_version':1,'decision':'accepted','identity':b['identity'],'evidence':ev,'final_binding_sha256':hashlib.sha256(body).hexdigest(),'source_count':331,'input_count':59,'opaque_evidence_count':1,'scope':'Focused final two-field binding seal, reusing accepted fresh21 changed-entry and source reviews. Exact source331/input59 and all final binding references joined. One opaque dispatch hash-only; public source commit, actual recovery and fresh eligibility remain separate Root obligations. No numerical tests/imports, admission, claim or native launch repeated. Full MCM/update/fit remain incomplete.'}
data=(json.dumps(result,indent=2,sort_keys=True)+'\n').encode()
for p in (H/'RELEASE_REVIEW01.json',N/'RELEASE_REVIEW01.json'):
 with p.open('xb') as f:f.write(data)
print(json.dumps({'decision':'accepted','release_sha256':hashlib.sha256(data).hexdigest(),'binding_sha256':result['final_binding_sha256'],'evidence_count':len(ev),'root_copy_identical':(H/'RELEASE_REVIEW01.json').read_bytes()==(N/'RELEASE_REVIEW01.json').read_bytes()}))
