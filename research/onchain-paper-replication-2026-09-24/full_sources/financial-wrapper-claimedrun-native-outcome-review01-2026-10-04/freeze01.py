from pathlib import Path
import json,os,stat,hashlib
H=Path(__file__).resolve().parent;sha=lambda b:hashlib.sha256(b).hexdigest();r=json.loads((H/'READBACK01.json').read_text());j=json.loads((H/'JOINS01.json').read_text());census=json.loads((H/'ORIGINAL_OUTCOME_CENSUS01.json').read_text());count=0
for row in census:
 p=Path(row['root'])/row['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==row['mode'];count+=1
 if row['kind']=='file':assert sha(p.read_bytes())==row['sha256'] and sha((H/'evidence'/row['role']/row['path']).read_bytes())==row['sha256'];count+=1
for role in {x['role'] for x in census}:
 rows=[x for x in census if x['role']==role];root=Path(rows[0]['root']);assert sorted(['.']+[str(p.relative_to(root)) for p in root.rglob('*')])==sorted(x['path'] for x in rows);count+=1
(H/'REPORT01.md').write_text('''# Actual claimedrun engineering interruption review

Accepted actual FAILED/spent planned-interruption outcome at the metadata/opaque-checkpoint level. The unchanged Parent5d5 and final request529c launched Source/current-design0a2. The genuine ResearchRun claim d390980c records effective allowance19, eight authentic input roles and338 pinned source files; actual Git HEAD and339 tracked membership match. The registered full experiment, expanded windows, source/runtime251 RECORD pins and original interpreter hash match. The previously failed recordfix claim remains present at its original allowance18. Two genuine claims are now spent, both failed; no refund, replay or completed paper fit follows.

The actual training journal records epoch0 with16 examples/seed11. Original source order performs optimizer.step, writes the epoch record, saves the checkpoint, then invokes the registered interrupt callback requiring cursor epoch1/batch0. The actual diagnostic and failed-fit record agree on the checkpoint manifest and complete provenance; state.pt493424bytes matches223ced42edec29ec0afd4ea5265b2e0a557a98787e57be47e841e8491511a281. Checkpoint tensors/model/optimizer/RNG state were not decoded or loaded. Numerical continuation correctness is therefore unproved. This is the expected engineering interruption after one recorded update, while lifecycle and fit remain genuinely FAILED. No complete.json or published research output exists. Postmortem cell is unavailable; it is not silently upgraded from that original disposition.

Monitor Owner metadata, CPU-ready/worker receipts, guard and observer joins agree. Native memory.high=max3GiB, swap0, twoCPU masks, hard/soft4MiB file limits,1800second unit bound,3GiB host reserve/6GiB startup and10GiB disk floor are recorded. Native elapsed14.857321821997175seconds; sampled peak memory.current962785280bytes, not a kernel peak or full-population capacity measurement. No observed OOM/high/max event or elapsed kill is reported. Guard phase failed and non-null child-failure limit reason are correct for the planned nonzero exit. Supervisor/worker exited1. Recorded PIDs and cgroup are currently absent; available original start ticks are preserved. Original native_pid_start_records is empty and explicitly not complete history, so unrecorded native histories remain unknown.

Parent original actual_parent_exit remains null and outcome_semantics_accepted remains false. The separate Root receipt1863906b joins actual tool aab8fe/session33113/completion4f8f5d exit1, original terminal and exact empty Root stdout/stderr; no missing field was synthesized. The synthetic route has null scientific bindings: actual monitor Owner identity does not invent a compact scientific Owner/Binding. Genuine source control flow and stored ResearchRun admission are authenticated without constructing handles.

Complete opaque copies and original mode/path/hash census preserve both lifecycle run trees, this job/guard tree, wrapper diagnostics, fit/checkpoint tree and Parent attempt; Root launch intent/actual exit/stdout/stderr and control sources are retained separately. Final census/current-body rejoin passes. These local review copies are not external backup or fresh recovery of the whole capsule/runtime. Root's separate complete preservation and independent recovery are prerequisites to further execution.

Next phases must use only unused separately admitted identities, preserve the failed parent and its real checkpoint/claim/provenance, and satisfy the original continuation source/design lineage rules. A continuation also requires a genuine complete100 reference and the original accepted parent evidence/registration, plus native checkpoint-loader cursor/model/optimizer/RNG validation and final equality. Prediction requires genuine complete100 fit completion. Any gate/input/source revision needs exact source rebinding, cumulative allowance review and complete recovery; never relaunch this identity. All1420 paper fits, scientific full graph capacity and newly prepared uninstalled byte utilities remain separate and pending.

The initial review harness rejected the interpreter under the4MiB outcome-file bound. That failure is retained; review02 uses the previously qualified separate64MiB streaming runtime reader while keeping every outcome body under4MiB. No numerical imports, decoding, rerun, admission, new claim, network or original mutation occurred.
''')
m={'schema_version':1,'decision':'ACCEPTED_ACTUAL_FAILED_SPENT_PLANNED_INTERRUPT_OPAQUE_METADATA','checks':r['checks']+j['count']+count,'claim_sha256':r['claim_sha256'],'failed_sha256':r['failed_sha256'],'checkpoint_manifest_sha256':r['checkpoint_manifest_sha256'],'checkpoint_state_sha256':r['checkpoint_state_sha256'],'spent_claims':2,'highest_actual_allowance':19,'original_parent_exit':None,'separate_actual_outer_exit':1,'paper_fit_credit':0,'native_checkpoint_tensor_validation':False,'complete_external_recovery':False,'report_sha256':sha((H/'REPORT01.md').read_bytes())};(H/'MACHINE01.json').write_text(json.dumps(m,indent=2)+'\n');rows=[]
for p in sorted(H.rglob('*')):
 if p==H/'MANIFEST01.json':continue
 s=p.lstat();x={'path':str(p.relative_to(H)),'mode':oct(stat.S_IMODE(s.st_mode))}
 if stat.S_ISREG(s.st_mode):b=p.read_bytes();x.update(kind='file',bytes=len(b),sha256=sha(b))
 elif stat.S_ISDIR(s.st_mode):x.update(kind='directory')
 else:raise ValueError('unexpected review member')
 rows.append(x)
(H/'MANIFEST01.json').write_text(json.dumps({'schema_version':1,'members':rows},sort_keys=True,indent=2)+'\n');print(json.dumps({'manifest':sha((H/'MANIFEST01.json').read_bytes()),'machine':sha((H/'MACHINE01.json').read_bytes()),'report':sha((H/'REPORT01.md').read_bytes()),'members':len(rows),'checks':m['checks']}))
