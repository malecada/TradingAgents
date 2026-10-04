import json,os,shutil,stat,time
from pathlib import Path
import recovery04 as R
H=Path(__file__).resolve().parent;B=H.parent
for dest,source in [('complete-predecessor01','financial-genuine-wrapper-claimedrun-final-union-recovery-preparation01-2026-10-04'),('complete-capture-preparation02','financial-genuine-wrapper-claimedrun-final-capture-preparation02-2026-10-04')]:shutil.copytree(B/source,H/dest,symlinks=True)
expected=json.loads(R.read(H,'EXPECTED_ORIGINALS01.json'));start=time.monotonic();count=0
for tree in expected['scope_trees']:
 root=Path(tree['original_root']);rows=[]
 def scan(p,n):
  global count
  R.require(time.monotonic()-start<120,'bounded final census');s=p.lstat();sig=R.sig(s);r={'path':n,'mode':stat.S_IMODE(s.st_mode)}
  if stat.S_ISDIR(s.st_mode):
   r['kind']='directory';rows.append(r)
   for c in sorted(p.iterdir()):scan(c,c.name if n=='.' else n+'/'+c.name)
   R.require(sig==R.sig(p.lstat()),'directory stable');count+=1;return
  if stat.S_ISLNK(s.st_mode):r.update(kind='lexical-symlink',target=os.readlink(p))
  else:
   R.require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=R.FILE,'bounded original file');body=R.read(root,n);r.update(kind='file',bytes=len(body),sha256=R.digest(body),union_path=tree['scope']+'/'+n)
  R.require(sig==R.sig(p.lstat()),'original stable');rows.append(r);count+=1
 scan(root,'.');R.require(sorted(rows,key=lambda r:r['path'])==tree['members'],'complete exact original membership');count+=1
R.put(H/'FINAL_CENSUS01.json',{'checks':count,'original_trees':20,'original_typed_members':1525,'original_regular_members':1185,'original_lexical_links':50,'original_regular_logical_bytes':18864635,'complete_originals_unchanged':True,'links_followed':False,'actual_capture_or_recovery':None})
protocol='''This separately authored source successor requires independent review. It does not supersede original evidence or increase any file/archive limit. The original single-archive adapter01 and actual failed aggregate Root capture remain preserved; neither may be represented as a complete recovery. No actualRoot capture or recovery is executed by this preparation.

Install restore_sharded01.py, exact shards01.py9c38c089, EXPECTED_ORIGINALS01.json40b4002e and byte-identical recovery04/owned_io/boundedGit together in a fresh Root namespace. Actual request must be separately named (suggested REQUEST_CLAIMEDRUN_SHARDED_UNION01.json), hash-pinned on CLI and approved by an independent exact five-field release whose decision is accepted-exact-one-use-final-union-sharded-flat. The old single-archive release cannot satisfy this schema. Target is fixed fresh full_sources/financial-genuine-wrapper-claimedrun-final-union-sharded-flat-20261004-01. request/review/release/actual remote/capture pins remain null in the template and refuse.

The real request binds three selected objects: union-manifest.json, SHARD_INDEX01.json and UNION_AUTHENTICATION01.json, including actual remote receipt/commit, bytes/hashes and actual member/file/logical/shard counts. There is no aggregate archive hash. Index schema is the exact capture02 protocol: kind complete-final-union-shards-v1, virtual_manifest reference, limits logical2097152/typed256/archive4194304, regular_bodies and ordered shards. Each shard binds its exact id, sorted regular_paths, manifest and archive references, members/regular_bodies/logical_bytes/tar_bytes_bound. The actual index must match the deterministic greedy sorted partition reconstructed from the complete virtual manifest. Repeated parent directories across shards are permitted and match the same virtual rows; regular files are disjoint and covered once. Empty directories remain in virtual metadata. Shard manifest/archive paths are fixed relative to the real selected index. All selected bodies retain exact Git blob/hash/extent/mode joins under the existing transport receipt and finite506-path selection ceiling. Historical source325 transport status text remains unchanged and supplies no Source339 authority.

Each shard has at most2MiB logical regular bytes and256 typed members including parent directories. Exact PAX/TAR header/padding/terminal-record bound and conservative gzip bound are recomputed by the pinned pure planner; actual original R4Sink still caps every archive at4MiB. Every file/reference/receipt remains at most4MiB, virtual logical and selected aggregate at most64MiB, original10GiB observed free floor remains. The output is separate private flat directories, one per original R4.restore call. No cap ladder, compression-size guarantee for arbitrary data or numerical capacity claim is made. Existing R4/owned_io/boundedGit and descriptor reserve/restore_ordinary functions remain byte-identical. Full ordered byte/AST inverse declares the new orchestration rather than claiming it equals the old single-archive algorithm.

The adapter joins every actual shard manifest with the planned virtual subset, restores and reads every body, merges exact global regular membership, and obtains ORIGINAL_TREES01.json from its unique recovered shard. Actual sharded auth binds index+virtualmanifest+mapping hashes and shard count. The complete20-tree census exactly fixes all1525 original typed members/1185 regular/50 literal links/18,864,635 bytes. Missing or extra roots/members, body hashes, paths, modes or link targets refuse. Mapping pins Source0a2/b5b6/fdf7/468d and mandatory caller5d5/request529c/release95dadb/proofs3268+0592+468d/verifier1408/BINDING57e3/review0c399882. Final whole remote shard bytes are reread before successful publication. Original R4 per-shard receipts and their false authority/POSIX/runtime flags remain intact; VIRTUAL_RECOVERY01 retains complete virtual directory/mode metadata and global flat map. RECOVERY01 has single_archive_identity:null and no numerical authority.

Failures retain all private shard outputs and completed shard results. The outer first-fatal cleanup attempts a FAILED receipt without substituting later cleanup failures for an earlier fatal exception. This does not claim that every inherited low-level allocation/callback failure is equivalent; unchanged R4 behavior is explicitly preserved. No real financial/native result, tensor/checkpoint validation, runtime package recovery, empirical store recovery or reconstructed POSIX origin follows.

Actual capture02 source31f8c7df/planner9c38c089/MANIFESTa2b07ace is frozen; interface interoperability was checked against its existing three owned opaque shards without rerunning capture or restoration. All real archive/index/auth hashes remain future actual evidence. Different-author source review, genuine Root capture+external recovery, exact request/release review and actual bounded flat recovery acceptance remain separate required steps. Root alone performs them.
'''
(H/'PROTOCOL01.md').write_text(protocol)
(H/'REPORT01.md').write_text('''Implemented separately bounded sharded recovery with exact disjoint cover, fixed full source census and unchanged primitive helpers.367 controls passed using an actual two-shard tiny opaque fixture with261 regular bodies; tests cover omission/duplication/order/mode/link/hash/limit/tamper, repeated/redirected outputs, late extras and nine first-fatal pairs. A corrupted second shard refuses while the first completed result and partial directory remain. Five additional checks authenticate full byte/AST inverse and planner origin. Nine interface checks accept the capture author’s frozen three-shard opaque index and actual archive hashes without executing its capture or any real Root recovery. Total381 checks, plus1545 final read-only census checks. All actual20 roots remain unchanged.

No harness failed in this successor. Source-only author checks do not constitute independent review or actual recovery. Full predecessor preparation and complete frozen capture02 preparation/witness trees are retained. All future authority fields remain null. No array/numerical imports, claims, native processes, network operations or live mutations occurred.
''')
R.put(H/'MACHINE01.json',{'schema_version':1,'status':'SHARDED_SOURCE_PREPARATION_REQUIRES_DIFFERENT_AUTHOR_REVIEW','source_sha256':R.digest(R.read(H,'restore_sharded01.py')),'planner_sha256':R.digest(R.read(H,'shards01.py')),'census_sha256':R.digest(R.read(H,'EXPECTED_ORIGINALS01.json')),'original_source_sha256':R.digest(R.read(H,'original-restore_union01.py')),'checks':381,'census_checks':count,'file_archive_cap':4194304,'shard_logical_cap':2097152,'shard_typed_cap':256,'whole_logical_cap':67108864,'actual_capture':None,'actual_remote':None,'actual_root_request':None,'independent_review':None,'release':None,'actual_recovery':None,'numerical_authority':False,'single_archive_identity':None})
rows=[]
def seal(p):
 for q in sorted(p.iterdir()):
  s=q.lstat();r={'path':q.relative_to(H).as_posix(),'mode':stat.S_IMODE(s.st_mode)}
  if stat.S_ISDIR(s.st_mode):r['kind']='directory'
  elif stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(q))
  else:
   R.require(stat.S_ISREG(s.st_mode),'typed seal');body=q.read_bytes();r.update(kind='file',bytes=len(body),sha256=R.digest(body))
  rows.append(r)
  if r['kind']=='directory':seal(q)
seal(H);rows.sort(key=lambda r:r['path']);R.put(H/'MANIFEST01.json',{'schema_version':1,'scope':'complete source preparation excluding this manifest','members':rows,'member_count':len(rows),'counts':{k:sum(r['kind']==k for r in rows) for k in ('file','directory','symlink')}})
for n in ('restore_sharded01.py','shards01.py','MACHINE01.json','MANIFEST01.json'):print(n,R.digest(R.read(H,n)))
print('members',len(rows))
