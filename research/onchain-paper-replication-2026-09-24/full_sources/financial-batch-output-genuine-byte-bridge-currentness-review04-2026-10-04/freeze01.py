from pathlib import Path
import hashlib,json,os,stat,ast
D=Path(__file__).resolve().parent;F=D.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
canon=lambda x:json.dumps(x,sort_keys=True,separators=(',',':')).encode()
scopes=[('financial-batch-output-genuine-byte-bridge-preparation03-2026-10-04','335c925e5be70efa624d0f6757690be81e97677c61bd565075a5d1167fbb69f2'),('financial-batch-output-genuine-byte-bridge-source-review03-2026-10-04','da12d8ed42baf4723204c218360f75acc57af2c4090dd5ded96fdb04a4c7d356'),('financial-graph-feature-npy-byte-source-review01-2026-10-04','10c52643f4431a3ecc791ade86773b2fee18128b9982682110dff8b205ef6cd7')]
verified=[]
for name,pin in scopes:
 root=F/name;mp=root/'MANIFEST01.json';assert sha(mp.read_bytes())==pin
 m=json.loads(mp.read_bytes());paths=set()
 for row in m['members']:
  p=root if row['path']=='.'else root/row['path'];s=p.lstat();mode=int(row['mode'],8)if isinstance(row['mode'],str)else row['mode'];assert stat.S_IMODE(s.st_mode)==mode,(name,row['path'],'mode')
  if row['kind']=='file':assert stat.S_ISREG(s.st_mode)and len(p.read_bytes())==row['bytes']and sha(p.read_bytes())==row['sha256']
  elif row['kind'] in ('directory','dir'):assert stat.S_ISDIR(s.st_mode)
  elif row['kind']=='symlink':assert stat.S_ISLNK(s.st_mode)and os.readlink(p)==row.get('target',row.get('link_target'))
  else:raise AssertionError(row['kind'])
  if row['path']!='.':paths.add(row['path'])
 actual={p.relative_to(root).as_posix()for p in root.rglob('*')if p!=mp};assert actual==paths,(name,actual-paths,paths-actual)
 verified.append({'root':str(root),'manifest_sha256':pin,'typed_members':len(m['members']),'complete_current_membership':True})
(D/'SOURCE_READBACK01.json').write_bytes(canon({'verified_scopes':verified}))
rows=[]
for i in (2,3,4):rows+=json.loads((D/('WITNESSES%02d.json'%i)).read_bytes())['cases']
assert len(rows)==192 and all(not r['tail_accepted']and not r['all_population_equal']and r['original_first_frame_sha256']!=r['current_first_frame_sha256']and r['independent_verify_refusal']for r in rows)
for r in rows:
 prefix='fresh'if r in json.loads((D/'WITNESSES02.json').read_bytes())['cases']else None
# Authenticate retained physical bodies independently by each named population.
for i,prefix in ((2,'fresh'),(3,'small'),(4,'late-sample'),(5,'intact')):
 for r in json.loads((D/('WITNESSES%02d.json'%i)).read_bytes())['cases']:
  root=D/('%s-%03d'%(prefix,r['case']))/'codec'
  assert sha((root/'chunk-00000.bin').read_bytes())==r['current_first_frame_sha256']
  for name,sig,blocks,blksize in r['actual_after_population'][3]:
   s=(root/name).lstat();actual=[s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
   assert actual==sig and s.st_blocks==blocks and s.st_blksize==blksize
machine={'schema_version':1,'decision':'NO_DIRECT_BRIDGE03_FAILURE_REPRODUCED_IN_BOUNDED_DOMAIN','source_sha256':'ca5f4768789ec0fd632c4667439c7560d6318d288cd22c8b3f543361eb2c39b1','prior_source_acceptance_preserved':True,'recorded_corruption_cases':192,'corrupted_tail_acceptances':0,'all_corrupted_cases_refused_population_change':True,'fresh_intact_passes':4,'initial_logging_failure_cases_not_counted':96,'genuine_encode_executed':False,'genuine_authority_boundary_executed':False,'continuous_currentness_proved':False,'timestamp_collision_impossible_proved':False,'writer_exclusion_established':False,'native_release':False,'NPY_failure_does_not_by_itself_establish_bridge_failure':True}
(D/'MACHINE01.json').write_bytes(canon(machine))
(D/'REPORT01.md').write_text('''# Bridge03 currentness — bounded negative result

No direct bridge03 failure was reproduced. The earlier narrow source acceptance remains unchanged. This result does not prove timestamp uniqueness, continuous filesystem immunity, or native production readiness.

The complete original bridge03 preparation (354 typed members), prior independent review (272), and independent NPY review (106) were authenticated by exact seal, current membership, type, mode and every file hash. All are unchanged. NPY's five actual timestamp-collision acceptances remain valid within that separately reviewed NPY utility domain.

## Exact tested domain

The source AST for the final five utility statements of bridge03 `_encode` is extracted literally: full codec population snapshot, real LocalStore final byte verification, full proof/raw cursor join, final boundary, and population equality check. The genuine `_encode` function, Owner/Target handles and scientific imports are not executed or simulated. The substituted boundary performs only real opaque summary readback and store metadata checks; it cannot establish the genuine ancestry, registration or shared writer-exclusion conditions.

There are 192 recorded fresh opaque corruptions: 96 two-chunk, 64 one-chunk, and 32 late-sample cases. Half each inject one actual same-extent first-frame byte mutation after a real final-verifier descriptor close; half inject it after actual summary readback close in the final opaque boundary. Hooks qualify descriptors by actual inode/device and fire once. Descriptor integers are not replayed. Several cases rewrite the exact original bytes before the population sample. The final 32 do that immediately before the original population's actual frame stat; the stat result itself is never changed. All original and new bytes, before/after signatures, complete populations, close ordering and independent codec refusals are retained. No timestamp is reset.

All 192 reject with `post-verification codec population changed`; zero retained changed-byte cases have equal populations or return acceptance. The actual timestamps advanced in every tested bridge case. Four fresh intact cases pass both the exact tail and independent full codec verification. This includes actual verification and cleanup paths, not a fabricated expected answer.

The first 96-case attempt finished fixture operations but failed serializing its full review log through the bridge's bounded metadata encoder. Its original script, traceback and every partial fixture remain unchanged. Those results are not counted because the detailed in-memory witness rows were not retained. The corrected harness uses ordinary JSON for the review log; the codec and bridge formats are unchanged.

## Limit of the conclusion

The NPY witness establishes that this filesystem can produce equal metadata fingerprints for changed bytes within an effective timestamp tick. Bridge03 also relies on such fingerprints around its byte proof. The longer actual bridge path rejected every attempt here, but elapsed IO or a finite negative test is not a guarantee that equal-fingerprint corruption cannot occur. A universal currentness or production claim still needs an admitted immutable-file/writer-exclusion contract or an explicitly scoped proof/resource lifetime. Merely adding another identical scan does not supply that authority. No new bridge defect is declared solely by analogy, and no accepted artifact is rewritten or silently revoked.

Current Source339 integration, full genuine population, shared storage lease, typed external recovery, retirement and native capacity remain separate. Root's original active engineering attempt is unaffected by this read-only/source-utility investigation. No network, numerical import, original mutation, claim or launcher action occurred.
''')
manifest=[]
for p in [D]+sorted(D.rglob('*')):
 if p.name=='MANIFEST01.json':continue
 s=p.lstat();r={'path':'.'if p==D else p.relative_to(D).as_posix(),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISDIR(s.st_mode):r['kind']='directory'
 elif stat.S_ISREG(s.st_mode):r.update(kind='file',bytes=s.st_size,sha256=sha(p.read_bytes()))
 elif stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(p))
 else:raise AssertionError('unexpected kind')
 manifest.append(r)
(D/'MANIFEST01.json').write_bytes(canon({'schema_version':1,'self_excluded':True,'members':manifest}))
print(json.dumps({'manifest_sha256':sha((D/'MANIFEST01.json').read_bytes()),'machine_sha256':sha((D/'MACHINE01.json').read_bytes()),'typed_members':len(manifest),'body_bytes':sum(r.get('bytes',0)for r in manifest)}))
