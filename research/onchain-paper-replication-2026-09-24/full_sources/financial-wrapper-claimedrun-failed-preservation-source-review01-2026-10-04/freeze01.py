from pathlib import Path
import hashlib,json,stat,os
D=Path(__file__).resolve().parent;F=D.parent;T=F/'financial-wrapper-claimedrun-failed-remote01-2026-10-04';C=F/'financial-wrapper-claimedrun-failed-capture01-2026-10-04';P=F/'financial-batch-output-genuine-byte-bridge-preparation03-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();enc=lambda x:(json.dumps(x,sort_keys=True,indent=2)+'\n').encode()
r1=json.loads((D/'READBACK01.json').read_bytes());r2=json.loads((D/'READBACK02.json').read_bytes());r3=json.loads((D/'READBACK03.json').read_bytes());total=r1['checks']+r2['checks']+r3['checks']
evidence=D/'source-evidence';evidence.mkdir()
for name in ('recover01.py','restore01.py','SOURCE_INVERSE01.json'):(evidence/name).write_bytes((T/name).read_bytes())
for name in ('recovery04.py','owned_io.py','bounded_git01.py'):(evidence/name).write_bytes((P/name).read_bytes())
for name in ('CAPTURE01.json','INTENT01.json','CAPSULE_MANIFEST01.json','PARENT_MANIFEST01.json','ROOT_MANIFEST01.json'):(evidence/name).write_bytes((C/name).read_bytes())
machine={'schema_version':1,'decision':'ACCEPTED_LOCAL_FAILED_BYTE_CAPTURE_AND_BOUNDED_TRANSPORT_FLAT_SOURCE_ONLY','capture_sha256':r1['capture_sha256'],'transport_source_sha256':r1['source_sha256'],'restore_source_sha256':r3['restore_source_sha256'],'checks':total,'captured_members':483,'regular_bodies':402,'logical_body_bytes':8768628,'required_selection_count':8,'required_selection_bytes':2594804,'future_exact_git_calls':27,'remote_commit':None,'actual_remote_recovery':False,'actual_root_flat_recovery':False,'actual_full_flat_acceptance':False,'source':'0a2e7639b42b9423b90743feadcda4078aa21816','source339_git_body_joins':339,'original_parent_exit':None,'actual_root_exit':1,'spent_claims':2,'highest_actual_allowance':19,'native_tensor_checkpoint_validation':False,'paper_fit_credit':0,'installed_runtime_body_backup':False,'posix_tree_restoration':False,'native_capacity_release':False,'replay_authority':False,'requirements_before_remote':'Root must freeze canonical selection against actual committed+confirmed remote HEAD and independently verify exact eight required rows; this source review contains no invented commit/origin receipt.','requirements_before_flat':'Only actual original remote receipt hash, all eight exact saved blob/mode/OID/body joins, and independent actual remote acceptance authorize the one fresh caller.'}
assert sum(x['members']for x in r1['roles'])==machine['captured_members']
assert sum(x['bytes']for x in r1['roles'])==machine['logical_body_bytes']
(D/'MACHINE01.json').write_bytes(enc(machine))
(D/'REPORT01.md').write_text('''# Failed claimedrun preservation and recovery source review

**Accepted for the exact local byte capture and bounded source-only remote/flat preparation.** No external recovery, actual Root flat restoration or numerical release is claimed. The concrete actual commit and its canonical eight-row selection remain pending.

The entire non-Git capsule has 443 typed members, 367 regular files and 8,160,486 bytes. Parent has 34 members, 29 files and 603,892 bytes. The Root scope is exactly six named outcome files and 4,250 bytes, not the whole heartbeat directory. Total: 483 typed members, 402 files and 8,768,628 bytes. Every original/snapshot/archive name, type, literal mode, extent and opaque body hash was joined twice against current originals. Each complete archive passed unchanged R4 raw gzip/TAR framing and exact canonical compressed reencoding; maximum compressed size is 2,278,895 bytes. Source and Parent root modes agree with their originals. Capsule .git is explicitly excluded from this new capture; its previous full Source339 recovery is a separate historical chain.

Two bounded local read-only Git operations verify unchanged HEAD0a2 and all 339 immutable commit-tree/blob body joins. Actual claim, failed marker, checkpoint manifest and checkpoint state hashes from the separate genuine outcome review occur in the captured capsule. Checkpoint bytes were hashed only, never deserialized. Original Parent actual_parent_exit remains null; independent observed outer exit1 and child exit1 stay separate. Recorded original PIDs/groups and the recorded cgroup are currently absent. This is not a claim that an unrecorded complete native PID history exists. Spent2/highest19 and zero paper-fit credit remain unchanged.

## Exact source review

The new remote source b1b66189 is the accepted0b397 predecessor with exactly four literal substitutions: required-eight body map, fresh bare path, status label and truthful scope qualification. Whole source inverse is exact. Process creation, streamed reads, 60-second operation deadline, 600-second entry budget, 1024-call maximum, group kill/reap, independent pipe/selector cleanup, first fatal precedence, current10GiB floor,4MiB body/64MiB selected logical limits and effective506-row ceiling are unchanged. The exact eight fixed files total2,594,804 bytes and imply27 Git operations. Pure local malformed/missing/duplicate/typed selection controls, O_EXCL collision, and nine real write/close fatal pairs passed. No Git remote call or entry/main execution occurred. The generic validator permits supplemental rows, but this reviewed contract and new flat caller require the exact eight; later actual selection/receipt review must enforce that set.

The new flat caller1cdfe7bf authenticates all three actual Parent helper hashes before import, requires the actual future receipt digest, eight unique saved body/GitOID/mode joins, pinned capture08f69 and three pinned canonical manifests/archives, fresh one-use target names and intent, sampled120-second/10GiB checks. Source preserves the null Parent outcome and refuses a changed FAILED/source/identity chain. All R4/owned_io/boundedGit bytes are unchanged. Three fresh tiny ordinary opaque role roundtrips, reused output refusals and wrong archive pin refusals passed. No fake receipt was constructed, and the actual Root restore was not invoked. Every original target is still absent at source review.

There are 2,577 checks across three retained harnesses. No numerical import, value/label decode, new claim, replay, deletion, network, source/gate mutation or native dispatch occurred. Actual source release is limited to these fixed helpers. Root must bind a genuine committed/remote-confirmed selection, execute its one fresh transfer, obtain independent actual outcome acceptance, then supply only the genuine receipt to the one fresh flat caller. External scope closure and complete actual flat acceptance remain separate. Local archives do not establish those outcomes, installed runtime backup, POSIX reproduction, whole-fit capacity or scientific success.
''')
rows=[]
for p in [D]+sorted(D.rglob('*')):
 if p.name=='MANIFEST01.json':continue
 s=p.lstat();r={'path':'.'if p==D else p.relative_to(D).as_posix(),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISDIR(s.st_mode):r['kind']='directory'
 elif stat.S_ISREG(s.st_mode):r.update(kind='file',bytes=s.st_size,sha256=sha(p.read_bytes()))
 elif stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(p))
 else:raise ValueError('unexpected type')
 rows.append(r)
(D/'MANIFEST01.json').write_bytes(enc({'schema_version':1,'self_excluded':True,'members':rows}))
print(json.dumps({'checks':total,'machine_sha256':sha((D/'MACHINE01.json').read_bytes()),'manifest_sha256':sha((D/'MANIFEST01.json').read_bytes()),'members':len(rows)}))
