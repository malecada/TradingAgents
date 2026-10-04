import hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parent/'financial-genuine-wrapper-root-claimedrun-sharded-witness-capture02-2026-10-04'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,b):
 with (H/n).open('xb') as f:f.write(b)
def enc(q):return (json.dumps(q,sort_keys=True,indent=2)+'\n').encode()
for n in ['ACTUAL_TOOL_TERMINAL02.json','INTENT01.json','ROOT_ADOPTION01.json','LAUNCH01.py','ACTUAL_CAPTURE01.out','ACTUAL_CAPTURE01.err','UNION_AUTHENTICATION01.json']:put('ORIGINAL_'+n,(R/n).read_bytes())
r=json.loads((H/'READBACK01.json').read_bytes())
verdict={'schema_version':1,'decision':'LOCAL_CANONICAL_WITNESS_BYTES_VERIFIED_RECOVERY_COMPATIBILITY_WITHHELD','authentication_sha256':r['authentication_sha256'],'source_sha256':r['source_sha256'],'readback_sha256':sha((H/'READBACK01.json').read_bytes()),'refusal_sha256':sha((H/'REFUSAL03.json').read_bytes()),'local_complete_bytes':True,'requires_exact_direct_body':True,'shards_alone_complete':False,'unchanged_recovery04_compatible':False,'actual_external_or_flat_recovery':False,'native_or_numerical_release':False,'blocker':'Canonical PAX regular names truncated at slash are rejected by unchanged recovery04.framed_members. Actual shards 0035 and 0049 refuse; original bytes must remain unchanged. A separately reviewed PAX-aware decoder successor is required before actual recovery.'}
put('VERDICT01.json',enc(verdict))
put('REPORT01.md',('''# Actual five-tree witness capture review

Complete local canonical bytes are verified. Compatibility with unchanged recovery04 is withheld; actual recovery and numerical release are not accepted.

All 57 compressed archives (20,123,201 bytes) were independently framed under bounded gzip/TAR/PAX parsing and exactly recompressed. The full virtual cover contains 2,302 regular bodies: 2,301 archived original bodies and the mapping. The exact additional original raw READBACK01.json remains outside the archives and is required: 2,532,973 bytes, SHA c47fcb6875375ecb8ea5c60926bae307955007751cdf52bec2473c44964e17e3, mode 0600. Shards alone are incomplete.

All five original trees still match the source-review census and genuine seals: 2,762 typed nodes, 2,302 original regular bodies and 59 literal links. Every path, literal mode, link target, body extent and hash was checked against actual canonical archive bodies or the sole direct body. Source339's full captured tree and the final Parent request/proof remain unchanged. Parent attempt is absent. Whole original bytes plus mapping are 62,816,678 bytes, below 64 MiB. Every shard obeys 2 MiB logical, 256 typed-member and 4 MiB archive limits. The original actual exit-zero terminal, streams, intent, before/final disk observations and source pins join; the original PID and process group are currently absent. Continuous historical process/disk monitoring is not inferred.

## R4-PAX-REG-01: actual recovery blocker

The unchanged decoder rejects nine canonical regular headers across shard-0035 and shard-0049. Their short raw-name fields are truncated at a slash while their bounded local PAX path gives the complete regular filename. recovery04.py's raw-name slash check runs before resolving that PAX path and raises ValueError('noncanonical raw member slash/type'). Actual R4.framed_members reproduces the refusal on both original archives. A one-byte owned canonical PAX archive independently reproduces the same failure. No actual restore was run.

The first review decoder inherited that same overly restrictive test and its original failure is retained. A separately named second independent reader validates the complete PAX path and then demands exact complete canonical compressed reencoding; all original archive bytes pass. That reader is review-only and does not modify or release any runtime recovery helper. The narrow required correction is PAX-aware handling of the truncated raw name while retaining raw type agreement, complete semantic path/type restrictions, finite bounds, and canonical reencoding. A successor must be reviewed before actual restoration; originals must not be recaptured or changed to hide this case.

No installed runtime-body recovery, empirical store, POSIX directory-tree restoration, numerical capacity or execution authority follows. Original Source339 recovery and the twenty-tree final caller union remain separate required scopes.
''').encode())
rows=[]
def walk(p,n):
 s=p.lstat();r={'path':n,'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISLNK(s.st_mode):r.update(kind='lexical-symlink',target=os.readlink(p))
 elif stat.S_ISDIR(s.st_mode):
  r['kind']='directory';rows.append(r)
  for c in sorted(p.iterdir()):walk(c,n+'/'+c.name)
  return
 else:
  assert stat.S_ISREG(s.st_mode) and s.st_nlink==1;b=p.read_bytes();r.update(kind='file',bytes=len(b),sha256=sha(b))
 rows.append(r)
for p in sorted(H.iterdir()):walk(p,p.name)
put('MANIFEST01.json',enc({'schema_version':1,'members':sorted(rows,key=lambda r:r['path'])}))
for n in ['VERDICT01.json','READBACK01.json','REFUSAL03.json','REPORT01.md','MANIFEST01.json']:print(n,sha((H/n).read_bytes()))
print('members',len(rows),'checks',r['checks'])
