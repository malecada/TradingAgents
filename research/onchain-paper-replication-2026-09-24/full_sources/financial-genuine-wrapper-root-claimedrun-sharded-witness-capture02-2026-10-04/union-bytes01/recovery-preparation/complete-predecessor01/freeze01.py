import hashlib,json,os,shutil,stat,time
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent
import sys
sys.path.insert(0,str(H));import recovery04 as R
sha=R.digest
sources={'complete-original-preparation01':'financial-genuine-wrapper-recordfix-final-union-recovery-preparation01-2026-10-04','complete-original-review01':'financial-genuine-wrapper-recordfix-final-union-recovery-review01-2026-10-04','complete-capture-preparation01':'financial-genuine-wrapper-claimedrun-final-capture-preparation01-2026-10-04'}
for n,p in sources.items():shutil.copytree(B/p,H/n,symlinks=True)
expected=json.loads(R.read(H,'EXPECTED_ORIGINALS01.json'));start=time.monotonic();checks=0
for t in expected['scope_trees']:
 root=Path(t['original_root']);rows=[]
 def scan(p,n):
  global checks
  R.require(time.monotonic()-start<120,'bounded current census');s=p.lstat();before=R.sig(s);r={'path':n,'mode':stat.S_IMODE(s.st_mode)}
  if stat.S_ISDIR(s.st_mode):
   r['kind']='directory';rows.append(r)
   for c in sorted(p.iterdir()):scan(c,c.name if n=='.' else n+'/'+c.name)
   R.require(before==R.sig(p.lstat()),'dir changed');checks+=1;return
  if stat.S_ISLNK(s.st_mode):r.update(kind='lexical-symlink',target=os.readlink(p))
  else:
   R.require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=R.FILE,'original regular bounded');body=R.read(root,n);r.update(kind='file',bytes=len(body),sha256=sha(body),union_path=t['scope']+'/'+n)
  R.require(before==R.sig(p.lstat()),'member changed');rows.append(r);checks+=1
 scan(root,'.');R.require(sorted(rows,key=lambda r:r['path'])==t['members'],'late original membership differs');checks+=1
R.put(H/'FINAL_CENSUS_READBACK01.json',{'checks':checks,'exact_twenty_originals_unchanged':True,'expected_originals_sha256':sha(R.read(H,'EXPECTED_ORIGINALS01.json')),'actual_capture':None,'actual_recovery':None,'links_followed':False})
R.put(H/'PREPARATION_FAILURE01.json',{'status':'preserved author prepare01 failure','cause':'Text inverse construction asserted uniqueness for a substring appearing twice in the original helper. prepare02 uses distinct full loop/return anchors; no candidate or actual recovery executed by failed preparation.','actual_root_or_capture_mutation':False,'originals_changed':False})
protocol='''This is an uninstalled source candidate for one future complete claimedrun final-caller ordinary-byte flat recovery. It does not execute a financial job, generate a claim, admit a Run or authorize native execution. The original recordfix helper2bda, complete original source/review trees and all failures remain preserved.

Root must install restore_union01.py, EXPECTED_ORIGINALS01.json and the three exact pinned primitive helpers together in a fresh preparation namespace. A separate Root REQUEST_CLAIMEDRUN_FINAL_UNION01.json must bind a genuinely completed external remote receipt/commit and exact selected archive, manifest and UNION_AUTHENTICATION01 bytes. Its expected member/file/logical counts must come from that actual pinned manifest, not old276 counts or anticipated counts. review and release remain null until a different author approves the exact actual contract and helper hash through the unchanged five-field release API. The checked-in NULL template refuses. Output is fixed to full_sources/financial-genuine-wrapper-claimedrun-final-union-flat-20261004-01 and must be absent.

Capture interface is exact source1c74338bb78018c8816933c23b850090ef29ebce503ef7420d716e1f2a374749: union.tar.gz, union-manifest.json, UNION_AUTHENTICATION01.json and union-bytes01/ORIGINAL_TREES01.json. Mapping/auth field schemas remain unchanged. The expected census40b4002ee1b0edf1d2d4e4202cf3d5c98834eb9656b02558caedf40d7261dc30 freezes all20 exact original roots and all1,525 typed rows,1,185 regular bodies,50 literal links and18,864,635 original regular bytes. Those are current source census facts, not an actual archive/restore receipt. Every scope tree must match the full census exactly before successful recovery publication. Any late original addition, omission, body/mode/root/link change needs a new separately reviewed preparation; the original is never amended silently. Root confirmed these20 source trees are closed.

Source0a2/339tracked338pins/eight inputs is bound through mappingb5b6/fdf7/468d and exact actual Parent/request/proof/verifier body anchors. Caller5d5/Q529c/finalrelease95dadb/3268+0592+468d and verifier1408/BINDING57e3/actualreview0c399882 are immutable. Final union bytes supplement the separately genuine full Source339 recovery; they do not claim to include original runtime package bodies, empirical stores or instantiate the POSIX origin tree. All lexical links remain literal metadata and are not followed or extracted.

R4, owned_io and boundedGit bytes are unchanged. Exact hashed/reference/contract/selected/manifest_join/reserve/restore_ordinary function bodies are unchanged. run changes only the final explanatory scope label; its reservation, floors, failure receipt and first-fatal cleanup are identical. request changes only the exact absent target name. authenticate_union changes Source binding and enforces exact20 census instead of11 named scopes; actual count reconciliation remains dynamic against the actual manifest/auth. The historical remote status text source325 is deliberately retained because the accepted transport still emits it; current Source semantics come from the new immutable mapping and body pins, never that historical label.

Bounds remain4MiB per file/archive,64MiB ordinary logical scope,10GiB observed free floor and original finite parser/flat limits. The unchanged transport selection ceiling506 and Git limits remain prerequisites. No saving, numerical capacity or100epoch feasibility follows. No actual capture, external recovery or real final union restore exists at preparation freeze. Only a tiny opaque utility archive was restored locally by controls. Root alone may perform later genuine operations following independent source and exact release reviews.
'''
(H/'PROTOCOL01.md').write_text(protocol)
report='''Implemented a concrete source successor with full inverse, unchanged accepted I/O/cleanup primitives, exact fresh target and complete anti-truncation census.165 controls passed: NULL release refusal;20 scopes each missing/extra/root/mode mutations; hash/link/order changes; tiny complete opaque flat restoration; corrupted manifest/archive, repeat output, late-extra and real redirected-parent refusals; nine first-fatal/ordinary cleanup pairs with all callbacks attempted. The final second read-only census matched all20 actual originals. No scientific dependency import, actual full Source restore, network or native execution occurred.

The initial prepare01 text-anchor assertion is preserved, and prepare02 corrects only that authoring harness. No candidate failed runtime or actual recovery is disguised as completion. This is authored preparation requiring different-author independent review, not self-approval. The full original accepted preparation/review and complete capture source preparation are retained. Original released recordfix and permanently failed numerical scopes remain unchanged.
'''
(H/'REPORT01.md').write_text(report)
R.put(H/'MACHINE01.json',{'schema_version':1,'status':'SOURCE_PREPARATION_REQUIRES_INDEPENDENT_REVIEW','source_sha256':sha(R.read(H,'restore_union01.py')),'original_source_sha256':sha(R.read(H,'original-restore_union01.py')),'expected_originals_sha256':sha(R.read(H,'EXPECTED_ORIGINALS01.json')),'capture_source_sha256':sha(R.read(H,'CAPTURE_SCHEMA_SOURCE01.py')),'checks':165,'final_actual_census_checks':checks,'original_trees':20,'original_typed_members':1525,'original_regular_members':1185,'original_lexical_links':50,'original_regular_bytes':18864635,'actual_capture_archive':None,'actual_capture_manifest':None,'actual_capture_auth':None,'actual_remote':None,'actual_root_request':None,'independent_review':None,'release':None,'actual_recovery':None,'numerical_authority':False})
rows=[]
def seal(p):
 for q in sorted(p.iterdir()):
  s=q.lstat();r={'path':q.relative_to(H).as_posix(),'mode':stat.S_IMODE(s.st_mode)}
  if stat.S_ISDIR(s.st_mode):r['kind']='directory'
  elif stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(q))
  else:
   R.require(stat.S_ISREG(s.st_mode),'file type');body=q.read_bytes();r.update(kind='file',bytes=len(body),sha256=sha(body))
  rows.append(r)
  if r['kind']=='directory':seal(q)
seal(H);rows.sort(key=lambda r:r['path']);R.put(H/'MANIFEST01.json',{'schema_version':1,'scope':'complete preparation excluding this manifest','members':rows,'member_count':len(rows),'counts':{kind:sum(r['kind']==kind for r in rows) for kind in ('file','directory','symlink')}})
for n in ('restore_union01.py','EXPECTED_ORIGINALS01.json','MACHINE01.json','MANIFEST01.json'):print(n,sha(R.read(H,n)))
print('members',len(rows))
