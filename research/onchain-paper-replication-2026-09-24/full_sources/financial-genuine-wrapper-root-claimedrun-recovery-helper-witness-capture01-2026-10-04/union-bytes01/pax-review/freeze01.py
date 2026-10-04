import hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;A=H.parent/'financial-genuine-wrapper-claimedrun-witness-pax-framer-correction-preparation01-2026-10-04'
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(q):return (json.dumps(q,sort_keys=True,indent=2)+'\n').encode()
def put(n,b):
 with (H/n).open('xb') as f:f.write(b)
for n in ['recovery_pax01.py','INVERSE01.json','MANIFEST01.json']:put('CANDIDATE_'+n,(A/n).read_bytes())
put('READBACK01.json',(H/'case05/READBACK01.json').read_bytes());r=json.loads((H/'READBACK01.json').read_bytes());m={'schema_version':1,'decision':'accepted-source-only-witness-pax-framer-correction','source_sha256':r['source_sha256'],'original_sha256':r['original_sha256'],'author_manifest_sha256':r['author_manifest_sha256'],'readback_sha256':sha((H/'READBACK01.json').read_bytes()),'independent_checks':893,'actual_Root_restore':False,'original_archives_unchanged':True,'scope':'Witness PAX framing only; no change to source/final caller recovery, no numerical authority. Actual adapter integration and exact release remain separate.'};put('MACHINE01.json',enc(m))
put('REPORT01.md',('''# Independent witness PAX framer correction

Accepted narrowly as witness recovery source. The exact candidate a054d5922899b53579f4220ff3b427dc050dff075cb5470b43ff55e621b97eb2 changes only the premature raw-name slash predicate and adds complete effective-name slash validation. The inverse exactly reproduces every original b40e source byte and AST. Original IO, Git, manifest, restore, canonical reencoding and cleanup code remain unchanged; all 59 author manifest members were checked.

Original actual witness shards 0035 and 0049 still fail with unchanged R4. The candidate parses every original member with exact order, type, mode, extent and opaque hash; full canonical compressed bytes match. No actual archive was restored or changed. A fresh owned canonical PAX regular member whose raw prefix ends at a slash restored correctly to private flat files; no POSIX-tree or research authority is reported.

893 independent checks cover the inverse, both original actual RED/new GREEN cases, real tiny restore, malformed effective and raw paths, link/device/sparse types, traversal and protected paths, PAX extra fields/oversized payload, 4 MiB member bound before payload, nonempty directories, missing/extra/duplicate/reordered members, original modes, footer/truncation/corruption and canonical gzip headers. Effective PAX NUL is refused. A raw NUL terminates the raw header name; hidden subsequent bytes are rejected by complete canonical reencoding. Canonical archive verification remains mandatory after framing.

Actual write-stage MemoryError, KeyboardInterrupt and SystemExit preserve the original exception identity when descriptor close also fails; owned descriptors close. Ordinary canonical-byte mismatch plus gzip/TAR close mismatch remains the original CleanupFailure with retained causes. It must stop the operation.

Four reviewer harness failures remain immutable: initial tree traversal ordering was not lexical manifest ordering; raw NUL was initially expected to fail at framing rather than canonical verification; CleanupFailure needed explicit classification because it derives from BaseException; initial close fault injection triggered during archive read before body writing. Separately named scripts and fresh fixtures correct only those test assumptions. Original failures and partial outputs are retained.

This does not release the historical b40e Source/final caller adapter, modify any original archive, or establish actual external/flat recovery, numerical capacity, runtime-body preservation or execution authority. The witness adapter must bind this exact successor with genuine source-review evidence, then receive separate exact-request and actual-outcome review.
''').encode())
rows=[]
def walk(p,n):
 st=p.lstat();r={'path':n,'mode':stat.S_IMODE(st.st_mode)}
 if stat.S_ISLNK(st.st_mode):r.update(kind='lexical-symlink',target=os.readlink(p))
 elif stat.S_ISDIR(st.st_mode):
  r['kind']='directory';rows.append(r)
  for c in sorted(p.iterdir()):walk(c,n+'/'+c.name)
  return
 else:
  assert stat.S_ISREG(st.st_mode) and st.st_nlink==1;b=p.read_bytes();r.update(kind='file',bytes=len(b),sha256=sha(b))
 rows.append(r)
for p in sorted(H.iterdir()):walk(p,p.name)
put('MANIFEST01.json',enc({'schema_version':1,'members':sorted(rows,key=lambda r:r['path'])}))
for n in ['MACHINE01.json','READBACK01.json','REPORT01.md','MANIFEST01.json']:print(n,sha((H/n).read_bytes()))
print('members',len(rows))
