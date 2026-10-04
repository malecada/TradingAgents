from pathlib import Path
import hashlib,json,os,shutil,stat,sys
H=Path(__file__).resolve().parent;P=H.parent/'financial-wrapper-operational-provenance-compatibility-preparation02-2026-10-04';R=H.parent/'financial-wrapper-operational-provenance-compatibility-review01-2026-10-04'
sha=lambda b:hashlib.sha256(b).hexdigest()
def save(n,v):(H/n).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
assert not (H/'MANIFEST01.json').exists()
readback=[]
for base,pin in ((P,'adf054ca1d9c9d04cb83c8a0cf5ee736c74c5b4be20d9715f9d6a4d78bc7b391'),(R,'6f80852042dbf029c24dd88b3d0243c6f486283fd7fe89715da36fe680f41e7a')):
 assert sha((base/'MANIFEST01.json').read_bytes())==pin
 for row in json.loads((base/'MANIFEST01.json').read_bytes())['members']:
  p=base/row['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==row['mode']
  if row['kind']=='file':assert stat.S_ISREG(s.st_mode) and s.st_size==row['bytes'] and sha(p.read_bytes())==row['sha256']
  elif row['kind']=='directory':assert stat.S_ISDIR(s.st_mode)
  else:assert stat.S_ISLNK(s.st_mode) and os.readlink(p)==row['target']
  readback.append({'scope':base.name,'path':row['path'],'passed':True})
shutil.copytree(P,H/'author02',symlinks=True)
checks=json.loads((H/'INDEPENDENT_PROGRESS01.json').read_bytes());history=json.loads((H/'HISTORICAL_CHECKS01.json').read_bytes());replay=json.loads((H/'replay/CHECKS01.json').read_bytes())
assert all(r['passed'] for r in checks+history['rows']) and len(checks)==540 and len(history['rows'])==52
assert replay['new_controls']==231 and replay['inherited_final_controls']==508
for n in ('SETUP01.err','REPLAY01.err','INDEPENDENT01.err','HISTORICAL01.err'):assert (H/n).read_bytes()==b''
assert sys.version_info[:3]==(3,13,13)
sources={n:sha((H/n).read_bytes()) for n in ('financial_wrapper_fixture.py','operational_source_compatibility.py','training.py','workflow_storage.py')}
report='''# Independent compatibility successor02 source review

ACCEPTED_SOURCE_ONLY_OPERATIONAL_PROVENANCE_COMPATIBILITY02. No material source defect was found within this bounded review. The predecessor remains WITHHELD_OPC_PREDICT_POLICY_01; its original report, witness, author controls and raw failures are retained. This acceptance applies to helper d0d770b45def89e8e00e81fa1bbb35416034eaace5ecab0f15193fd43b7a32d8, wrapper5f478bc3, training6f278f5b and watcher91e21c52. It creates no registered policy or execution authority.

The original policy-propagation finding is corrected at financial_wrapper_fixture.py:285–287 and operational_source_compatibility.py:246–266. The new guard is after original genuine claim verification, actual COMPLETE lifecycle checks and the unchanged strict prediction provenance comparison, before original checkpoint/member access. The predicate joins the registered policy hash, complete closure hash, fixed continuation identity and cell, and every195 exact target implementation path. The exact production comparison reproduced the previous policy-change RED; the new pure metadata predicate refused it. Independently valid policy mutations to consumer, historical alias and closure alias also refused against the old parent policy; a consistent same-policy opaque structure passed. All195 missing parent paths and a same-hash-set path substitution refused. These are pure component/source tests, not a genuine COMPLETE parent execution.

The optional-role boundary remains deliberate. With no operational_source_compatibility role, legacy strict equality is unchanged and supplementary policy checks do not run. That path confers no admission of the historical source edge. Root must bind the same explicit policy role on all three fixed prospective consumers in the separately reviewed preclaim contract. This source review does not substitute for that registration/release invariant.

All163 author manifest members and60 predecessor independent-review members authenticated before and after testing. The full author evidence tree is preserved under author02, including CHECK01's stale506-row expectation failure. Fresh replay passed231 focused controls and508 inherited rows (the original506 plus two successor inverse rows). Independently authored checks passed540 source, metadata and real filesystem assertions, followed by52 actual historical metadata/API assertions. No failed independent harness run occurred. Original source/helper findings and retained author harness failures remain distinguishable from the current passing controls.

The actual CAP installed closure was independently rehashed path by path:194 original paths/193 distinct hashes,195 target paths/194 distinct hashes, and191 original bodies byte-identical. Exact literal inverses reconstruct the actual original wrapper and training bytes. The successor inverse also reconstructs candidate01. Every unaffected AST, including numerical fit/prediction and wrapper execute functions, is identical; generic checkpoint/cache/evaluation/financial-execution bodies retain their original hashes. No scientific source exemption or hash-set-only compatibility was added.

Actual historical metadata rejoined the original one-update claim d390980c, FAILED terminal4b2d7b0d, checkpoint manifestb2f7d33b, failed-fit/diagnostic/schedule/job/plan, original0a2e7639b42b9423b90743feadcda4078aa21816 source and all194 old path pins. The opaque493424-byte state was hashed only, yielding223ced42edec29ec0afd4ea5265b2e0a557a98787e57be47e841e8491511a281. Old checkpoint provenance stays exact on both load routes; new checkpoints and fit claims receive truthful current provenance. Model20f451/trainingd527, seed11, batch16 and100 epochs remain frozen. State/model/optimizer/RNG values were not decoded or validated numerically.

The existing held-lock route chooses the private registered reader. Its source call graph and original lifecycle/admission/verify bodies contain no nested lifecycle lock; the normal route still uses genuine read_input. A real leaf read passed under an owned nonrecursive flock without constructing Run/Admission/Owner. Twenty-four real nested descriptor-close matrices retained every exact primary and secondary exception object through the full exception graph, selected the first fatal, and attempted every descriptor close exactly once. Hostile cause/context/dictionary/formatting properties did not replace the selected fatal. Real late replacement, growth, truncation, disappearance and symlink cases refused, as did aggregate/deadline/lexical-link controls. These are bounded sampled filesystem checks, not continuous immutability, writer exclusion, blocked-syscall preemption, kernel quota or full-capacity proof.

Actual policy, consumers, target commit/design, gate, recovery and native release remain unresolved or NULL in the drafts. Registered accepted proof labels alone do not establish independent authorship or external retrieval. Genuine active-Run integration, preclaim dependency checks, actual release/admission, replacement COMPLETE100 reference, numerical continuation/agreement and prediction were not executed. No economic timing/returns/fees/funding claim was tested; the change has no financial-result claim and its scientific AST is unchanged. Complete failed-scope preservation/recovery, exact installed source/caller/runtime and final same-policy consumer registration still require Root's separately authorized work. This review approves no budget adoption, refund, family transfer, new trial, numerical launcher or paper authority.
'''
(H/'REPORT01.md').write_text(report)
save('READBACK01.json',{'manifest_members_reauthenticated':len(readback),'rows':readback})
machine={'schema_version':1,'decision':'ACCEPTED_SOURCE_ONLY_OPERATIONAL_PROVENANCE_COMPATIBILITY02','author_manifest_sha256':sha((P/'MANIFEST01.json').read_bytes()),'predecessor_review_manifest_sha256':sha((R/'MANIFEST01.json').read_bytes()),'sources':sources,'material_findings':[],'resolved_finding':'OPC-PREDICT-POLICY-01','controls':{'author_focused_replayed':231,'inherited_replayed':508,'independent_source_filesystem':540,'actual_historical_metadata':52,'real_nested_descriptor_matrices':24,'manifest_members_before_and_after':223},'source_footprint':{'historical_paths':194,'historical_distinct_hashes':193,'target_paths':195,'target_distinct_hashes':194,'original_bodies_unchanged':191},'historical_source':'0a2e7639b42b9423b90743feadcda4078aa21816','actual_policy':None,'actual_consumers':None,'actual_target_source':None,'actual_gate':None,'actual_recovery':None,'actual_native_release':None,'source_adopted':False,'policy_adopted':False,'genuine_runtime_objects_constructed':False,'numerical_packages_imported':False,'checkpoint_deserialized':False,'no_role_boundary':'Legacy strict equality remains. Root must bind explicit same policy to all three fixed compatibility consumers before claim.','review_scope':'Source and metadata only; no actual adoption, proof authorship/recovery authentication, runtime admission, numerical result, capacity or budget authority.'}
save('MACHINE01.json',machine)
rows=[];excluded={'MANIFEST01.json','FREEZE01.out','FREEZE01.err'}
for root,dirs,files in os.walk(H,followlinks=False):
 for name in dirs+files:
  p=Path(root)/name;rel=str(p.relative_to(H))
  if rel in excluded:continue
  st=p.lstat();r={'path':rel,'mode':stat.S_IMODE(st.st_mode),'links':st.st_nlink}
  if stat.S_ISREG(st.st_mode):assert st.st_size<=4194304;r.update(kind='file',bytes=st.st_size,sha256=sha(p.read_bytes()))
  elif stat.S_ISDIR(st.st_mode):r.update(kind='directory')
  elif stat.S_ISLNK(st.st_mode):r.update(kind='symlink',target=os.readlink(p))
  else:raise AssertionError(rel)
  rows.append(r)
rows.sort(key=lambda r:r['path']);save('MANIFEST01.json',{'schema_version':1,'status':machine['decision'],'scope':'Whole new independent review tree; original source bytes and opaque synthetic controls; no real state copy','exclusions':sorted(excluded),'members':rows,'typed_members':len(rows),'regular_files':sum(r['kind']=='file' for r in rows),'regular_bytes':sum(r.get('bytes',0) for r in rows)})
print(json.dumps({'manifest':sha((H/'MANIFEST01.json').read_bytes()),'machine':sha((H/'MACHINE01.json').read_bytes()),'report':sha((H/'REPORT01.md').read_bytes()),'members':len(rows),'regular_bytes':sum(r.get('bytes',0) for r in rows),'sources':sources}))
