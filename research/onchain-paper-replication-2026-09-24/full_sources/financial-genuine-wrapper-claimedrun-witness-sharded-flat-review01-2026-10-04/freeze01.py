import hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;A=H.parent/'financial-genuine-wrapper-claimedrun-witness-sharded-flat-preparation01-2026-10-04'
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(q):return (json.dumps(q,sort_keys=True,indent=2)+'\n').encode()
def put(n,b):
 with (H/n).open('xb') as f:f.write(b)
for n in ['restore_witness01.py','INVERSE01.json','MANIFEST01.json','REQUEST_TEMPLATE01.json']:put('CANDIDATE_'+n,(A/n).read_bytes())
r=json.loads((H/'READBACK01.json').read_bytes());m={'schema_version':1,'decision':'accepted-source-only-witness-sharded-plus-direct-flat','source_sha256':r['source_sha256'],'author_manifest_sha256':r['author_manifest_sha256'],'readback_sha256':sha((H/'READBACK01.json').read_bytes()),'framer_sha256':'a054d5922899b53579f4220ff3b427dc050dff075cb5470b43ff55e621b97eb2','framer_review_sha256':'64bc091e50fda054306df6ef7d966582b8a4580d5591049fe6cf409105503588','original_caller_sha256':'f0fa6231ed61dea322021e75578187c604633df21c3acee7eade4f0497e9cab7','checks':r['checks'],'actual_Root_restore':False,'actual_remote_or_exact_release':False,'shards_alone_complete':False,'native_or_numerical_authority':False,'scope':'Exact witness57 plus sole direct body caller source only. Genuine future selected remote and exact independent release plus complete actual outcome remain mandatory.'};put('MACHINE01.json',enc(m))
put('REPORT01.md',('''# Independent witness sharded-flat caller source review

Accepted narrowly for exact restore_witness01.py 5352c2e42d11d585e92187f2d51be9c42eaadcfc9b03f8e11e9a7097bf7c28ac. The complete author manifest (1,851 declared typed nodes), all actual file bytes/modes and the full byte/AST inverse to f0fa6231ed61dea322021e75578187c604633df21c3acee7eade4f0497e9cab7 were checked. The concrete standalone imports bind exact a054 PAX source, unchanged IO/Git/planner, full expected-original census and genuine independent framer review 64bc. The unresolved future request is refused; no synthetic remote receipt, release or ResearchRun object was constructed.

7,270 independent checks include all 57 actual immutable witness archives through the pinned PAX module: every effective path, mode, type, extent and opaque hash joins, and complete canonical compressed bytes match. The fixed virtual manifest/index/authentication and full expected five-tree census match 2,302 original files and 59 literal links. The exact raw direct c47f body is disjoint from archived originals. Its size, mode and name remain mandatory. Source339 archive/manifest/full-source-proof pins are separately bound; they do not substitute for caller or runtime recovery.

The deterministic partition includes all required parent directories, enforces sorted disjoint coverage, and retains 2 MiB logical / 256 typed / 4 MiB archive bounds. The selected references including direct bytes fit the existing 64 MiB bound; the entire original logical denominator also includes the direct body and mapping. Genuine selected bytes must match actual receipt SHA, commit, unique finite rows, blob OID, mode, size and SHA. These are source checks, not a future-origin observation. No actual remote was fabricated or fetched during this review.

A real owned three-shard, 513-body pipeline restored every opaque original byte. The genuine raw direct body was copied only into the owned utility fixture and checked against its exact descriptor and private 0600 single-use output. Missing/duplicate/hash/mode/path direct metadata, shard ordering/omission/duplication/path/logical changes, consistent original-population mutations, truncation and namespace reuse refused. A corrupted second shard retained the completed first result. A real second-shard body MemoryError, with a later close SystemExit, retained the original fatal identity and closed owned descriptors; partial outputs remain retained. No test required changing expected Root receipts or original archive bodies.

The whole-operation 120-second checks, observed 10 GiB floor checks, at-most-506 selected rows, full canonical reencoding, final selected-byte reread, original metadata-only modes and original archival-only flags remain. These checks do not claim a continuous disk monitor, POSIX birth/restoration, runtime installation recovery, empirical result or numerical capacity.

No blocker remains in this exact bounded caller source. Actual Root remote selection/outcome, a genuine exact request/release and complete actual 57-shard-plus-direct recovered union must be independently checked before any use as recovery evidence. Original b40e source/final-caller recovery and all old receipts remain immutable. This review provides no native or numerical release.
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
