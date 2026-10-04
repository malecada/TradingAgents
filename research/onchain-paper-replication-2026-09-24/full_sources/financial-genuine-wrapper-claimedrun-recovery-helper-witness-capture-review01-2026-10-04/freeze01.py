import hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;A=H.parent/'financial-genuine-wrapper-claimedrun-recovery-helper-witness-capture-preparation01-2026-10-04'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,b):
 with (H/n).open('xb') as f:f.write(b)
def enc(q):return (json.dumps(q,sort_keys=True,indent=2)+'\n').encode()
for n in ['capture_helpers01.py','INVERSE01.json','MANIFEST01.json']:put('CANDIDATE_'+n,(A/n).read_bytes())
r=json.loads((H/'READBACK01.json').read_bytes());m={'schema_version':1,'decision':'accepted-source-only-six-recovery-helper-witness-capture','source_sha256':r['source_sha256'],'author_manifest_sha256':r['author_manifest_sha256'],'readback_sha256':sha((H/'READBACK01.json').read_bytes()),'checks':r['checks'],'original_regular_bodies':4220,'original_regular_bytes':9187425,'literal_links':r['literal_links'],'whole_logical_with_metadata':11725363,'actual_Root_capture':False,'actual_external_recovery':False,'native_or_numerical_authority':False};put('MACHINE01.json',enc(m))
put('REPORT01.md',('''# Independent six-helper witness capture source review

Accepted source-only for exact capture_helpers01.py 06f1a923e4b1d77d019276117a55d34f5942990c7e19f631783a62116224d4da. All author frozen members and each of the six full original seals/current trees were authenticated. The complete byte/AST inverse returns the actual previous tooling capture source; R4 b40e, IO and bounded Git are unchanged.

17,695 checks verify 4,220 original regular files totaling 9,187,425 bytes, with original literal modes, paths, empty directories and link targets preserved as metadata. Full originals plus six metadata bodies and union mapping total 11,725,363 bytes, below the unchanged 64 MiB bound. Current Source339's entire captured tree, archive and manifest and final Parent request/full-source proof remain unchanged. No Parent attempt exists.

Independent read-only in-memory canonical encoding reproduces all six author archive hashes exactly. Sizes are: flat-preparation 242,759; flat-review 352,657; pax-preparation 26,372; pax-review 34,080; tooling-preparation 22,910; tooling-review 440,829 bytes. All are below 4 MiB. Every projected canonical header/member successfully parses through unchanged R4; these six current projections have no truncated-raw-name slash refusal. No actual original-tree capture or restore was performed in this review.

The exact main suffix was exercised only on six owned tiny roots. All six canonical archives restored original opaque bodies plus original metadata; empty directories and literal links joined without extraction. Late member additions, body changes, mode changes and literal-target changes were refused before success authentication. Reusing an owned output namespace refused. Real MemoryError, KeyboardInterrupt and SystemExit during put retained their first-fatal identity when close also failed; both body and held-parent descriptors closed.

The original 4 MiB body/archive limits, full before/after membership checks, 10 GiB observations and 120-second source checks remain. Actual capture, complete selected remote outcome and fresh recovery require separate review; no local projection is an external backup. Source339, original caller union, five-tree witness shards plus direct raw body and original tooling captures are separate mandatory scopes. The reviewed PAX correction remains required for the actual 57-shard witness recovery and does not change historical b40e source. No numerical, capacity, runtime-body, POSIX or empirical authority follows.
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
for n in ['MACHINE01.json','READBACK01.json','REPORT01.md','MANIFEST01.json']:print(n,sha((H/n).read_bytes()))
print('members',len(rows))
