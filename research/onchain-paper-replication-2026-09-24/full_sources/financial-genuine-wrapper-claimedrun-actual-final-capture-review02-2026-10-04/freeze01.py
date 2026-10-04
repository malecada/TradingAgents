import hashlib,json,os,shutil,stat
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;N=B/'financial-genuine-wrapper-root-claimedrun-final-capture02-2026-10-04';O=B/'financial-genuine-wrapper-root-claimedrun-final-capture01-2026-10-04'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,o):
 with (H/n).open('x') as f:f.write(json.dumps(o,sort_keys=True,indent=2)+'\n')
for dest,root in [('actual-new-root-metadata',N),('actual-old-failed-root-metadata',O)]:
 d=H/dest;d.mkdir()
 for p in sorted(root.iterdir()):
  if p.is_file() and p.name!='union.tar.gz':shutil.copy2(p,d/p.name)
 if root==N:
  (d/'shard-manifests').mkdir()
  for p in sorted((root/'shards').glob('*-manifest.json')):shutil.copy2(p,d/'shard-manifests'/p.name)
report='''Accepted complete actual sharded byte capture after17,006 independent checks. Root actualcapture02 source31f8/planner9c38 and prior independent source reviewe2c313 are authenticated. Actual session73084/startca4a83/completion00f491exit0 joins original intentPID498623/startticks16294313/group-session498620 and exact raw stdout/empty stderr. Current bounded /proc stat census observed the original PID and group/session absent, with observation races/visibility listed separately; historical complete descendant lineage and native capacity are not inferred.

All11 actual archives passed exact size/hash joins, complete original R4 bounded raw framing, every header/type/mode/path/body hash and ordering, and full deterministic canonical recompression hash equality. Maximum archive577,966B stays below original4MiB cap. Exact deterministic sorted cover has1186 unique regular bodies across virtual1476members. Full physical shard trees and both new and old virtual union trees were reread. All20 current original trees match frozen40b4002e census:1525typed/1185regular/50literal links/18,864,635B. The50 links remain only literal mapping entries and were never followed or extracted. Original directory/file modes remain explicit metadata; no POSIX-origin restoration is claimed.

Actual auth77c739cd/indexda1aa342/virtualmanifestc72030b4/mapping6f78f76b join all denominators and flags. Source339 current=design0a2 remains whole1029typed747body unchanged against original fdf7 source capture, with all338 source pins/eight inputs/251 runtime RECORD metadata authentic. Pinned actualParent529c/95release/5d5/proofs3268+0592+468d/generatedverifier1408/BINDING57e3/independentbinding0c399 are covered by the exact original census and semantic footer. Fresh claimedrun claim and Parent attempt remain absent. No API admission, outcome verifier, job or native operation was invoked.

Original failed capture01 stays permanentlyFAILED. Frozen failedmanifestfdda7c05 covers1484members; current1485 is exactly that tree plus its own frozen manifest. Failed terminalef8e9f17/raw stderr retain both original4MiB cap failure and gzip cleanup CleanupFailure, with original OS historyNULL. Partialfc7d4f78 is exactly4,190,463B of failed opaque bytes; it was hashed and never parsed/extracted or credited as valid gzip. New virtual manifest and ORIGINAL_TREES01 are byte-identical to old prepack, and all old virtual files/modes match the new union. This equivalence does not turn the old attempt into a success.

FAILED_SCOPE_RECOVERY_REQUIREMENTS01 lists eight exact old non-union files including failed terminal, raw outputs, source/adoption, prepack manifest, frozen failure manifest and partial gzip. They must be genuinely selected externally with their exact hashes/modes. The old union-bytes01 root and1476 virtual members/1186 bodies can then be represented by the identical fully recovered new canonical shard set with the declared old-prefix mapping. Until that actual recovery is performed and independently accepted, neither failed-scope nor new final-caller external recoverability is credited. The4,190,463B partial must be selected directly as an opaque bounded file; it is not put through the2MiB logical-shard planner and is not copied into this review witness tree.

The raw detailed17,006-check readback was initially2,532,973B, too large for a2MiB witness-shard body. Its exact unsealed bytes are retained losslessly in RAW_DETAILED_READBACK01.json.gz with uncompressed hash/length and compressed reference in compact READBACK01. This is metadata evidence encoding, not deletion or alteration of any prior seal. The copied actual Root metadata and all shard manifests preserve original bytes; canonical archive bodies remain in their audited actualRoot paths and must be selected directly by Root. Complete review census excludes only its own manifest.

No actual flat restore, network recovery or numerical run occurred in this review. Actual external selection/recovery, fresh private flat union recovery, complete five-tree witness preservation, final native eligibility and Root release remain separate. Installed runtime bodies, empirical stores, scientific representations,100epoch resource capacity, return/cashflow or fee/funding results and all1420paper fits were not tested or validated. Source-only byte capture supplies no numerical authority.
'''
with (H/'REPORT01.md').open('x') as f:f.write(report)
r=json.loads((H/'READBACK01.json').read_bytes());put('VERDICT01.json',{'schema_version':1,'reviewer':'combined_worker_review','author_reviewed':'Root actual capture of outcome_archive source','decision':'ACCEPTED_COMPLETE_ACTUAL_SHARDED_BYTE_CAPTURE','checks':17006,'readback_sha256':sha((H/'READBACK01.json').read_bytes()),'actual_auth_sha256':r['auth_sha256'],'actual_index_sha256':r['index_sha256'],'virtual_manifest_sha256':r['virtual_manifest_sha256'],'mapping_sha256':r['mapping_sha256'],'old_scope_status':'PERMANENT_FAILED','old_partial_valid_archive':False,'actual_flat_recovery':None,'actual_external_recovery':None,'numerical_authority':False,'requirements_sha256':sha((H/'FAILED_SCOPE_RECOVERY_REQUIREMENTS01.json').read_bytes())})
rows=[]
def scan(p):
 for q in sorted(p.iterdir()):
  s=q.lstat();r={'path':q.relative_to(H).as_posix(),'mode':stat.S_IMODE(s.st_mode)}
  if stat.S_ISDIR(s.st_mode):r['kind']='directory'
  elif stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(q))
  else:
   assert stat.S_ISREG(s.st_mode);body=q.read_bytes();assert len(body)<=2*1024**2;r.update(kind='file',bytes=len(body),sha256=sha(body))
  rows.append(r)
  if r['kind']=='directory':scan(q)
scan(H);rows.sort(key=lambda r:r['path']);put('MANIFEST01.json',{'schema_version':1,'scope':'complete independent actual capture review excluding this manifest','members':rows,'member_count':len(rows),'counts':{k:sum(r['kind']==k for r in rows) for k in ('file','directory','symlink')}})
for n in ('MANIFEST01.json','VERDICT01.json','READBACK01.json','FAILED_SCOPE_RECOVERY_REQUIREMENTS01.json','REPORT01.md'):print(n,sha((H/n).read_bytes()))
print('members',len(rows))
