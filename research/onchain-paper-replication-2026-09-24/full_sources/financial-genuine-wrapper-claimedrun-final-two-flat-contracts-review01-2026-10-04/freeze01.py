import hashlib,json,stat
from pathlib import Path
H=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def enc(q):return (json.dumps(q,sort_keys=True,indent=2)+'\n').encode()
def put(n,b):
 with (H/n).open('xb') as f:f.write(b)
readbacks={r:json.loads((H/(r+'_READBACK01.json')).read_bytes()) for r in ['FINAL11','WITNESS57']};m={'schema_version':1,'decision':'accepted-exact-two-one-use-flat-contracts','releases':{r:{'path':str(H/(r+'_RELEASE01.json')),'sha256':sha((H/(r+'_RELEASE01.json')).read_bytes()),'contract_sha256':q['contract_sha256'],'original_request_sha256':q['original_request_sha256']} for r,q in readbacks.items()},'actual_remote_review_sha256':'236918fc76a2ce7119a4ac959b2398e849307528a9ede73566328571626c501f','checks':sum(q['checks'] for q in readbacks.values()),'actual_restore':False,'numerical_authority':False};put('MACHINE01.json',enc(m))
put('REPORT01.md',('''# Exact final11 and witness57 flat contracts

Both original Root drafts are accepted with separately authored genuine five-field releases. Final11 contract839a13bdfe6df92c4b0b641111f98bb3fb34526913c3c760783be186bee8befc binds exact f0fa caller and genuine source reviewf730. Witness57 contract8bbe2be217a75a13fcc971bf66f84a924bdeae11ca5779cae5517a34986fcc4f binds exact5352 caller, genuine source reviewfe47 and PAX review64bc. Each contract excludes only release. Root drafts and all prior evidence remain unchanged.

Both requests bind actual primary remoteec84 at immutablea9b219 and the independently accepted two-batch outcome236918. Every requested metadata/archive reference was checked through the actual selected reader, including genuine Git blob OID, mode, extent and hash. Complete deterministic indexes/manifests, all68canonical gzip archives, every framed original body and all current20+5original trees were authenticated. The exact expected-original census files match their source pins. No synthetic remote or proof was supplied.

The original failedc720union identity and eight retained outside bodies remain joined. The witness sole raw c47f2,532,973-byte direct body is actually present in selected bytes, disjoint from archived originals and mode0600 in original metadata. Source339's entire current captured tree and finalParent529 remain unchanged; no Parent attempt exists. Fixed output namespaces are absent and current free space exceeds10GiB. Existing2MiB/256typed/4MiB/archive/direct/64MiB/506row/120second checks remain as source semantics; no continuous future capacity is inferred.

After all predicates passed, each release was written only in this review directory and bound in memory to the actual caller's pure request validator. Both validated. Original null-release drafts and subsequent commit/count/output tampering refused. No recovery function, Root namespace reservation, network, admission, claim or numerical operation ran.

Root may copy only the genuine release references into separately named final requests, preserve the exact contract and execute each original fresh flat identity once. Actual complete restored bodies, metadata, canonical byte union and cleanup still require independent outcome review. These releases confer no scientific/native/runtime/POSIX/capacity authority.
''').encode())
rows=[]
for p in sorted(H.iterdir()):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1;b=p.read_bytes();rows.append({'path':p.name,'kind':'file','mode':stat.S_IMODE(s.st_mode),'bytes':len(b),'sha256':sha(b)})
put('MANIFEST01.json',enc({'schema_version':1,'members':rows}))
for n in ['FINAL11_RELEASE01.json','WITNESS57_RELEASE01.json','MACHINE01.json','MANIFEST01.json']:print(n,sha((H/n).read_bytes()))
print('members',len(rows),'checks',m['checks'])
