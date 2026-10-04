import ast,hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent
sha=lambda b:hashlib.sha256(b).hexdigest()
def save(n,v):(H/n).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
source_names=['operational_source_compatibility.py','financial_wrapper_fixture.py','training.py','workflow_storage.py']
sources={n:{'sha256':sha((H/n).read_bytes()),'bytes':(H/n).stat().st_size} for n in source_names}
readback=json.loads((H/'SOURCE_READBACK01.json').read_text());checks=json.loads((H/'CHECKS01.json').read_text());more=json.loads((H/'CHECKS03.json').read_text())
evidence={}
for directory,names in [('financial-wrapper-operational-provenance-compatibility-investigation01-2026-10-04',['MANIFEST01.json','PROTOCOL_REQUIREMENTS01.md']),('financial-wrapper-storage-watch-concurrent-publication-correction03-2026-10-04',['MANIFEST01.json','workflow_storage.py']),('financial-wrapper-storage-watch-concurrent-publication-review03-2026-10-04',['MANIFEST01.json','REPORT01.md'])]:
 for name in names:
  p=B/directory/name;raw=p.read_bytes();evidence[str(p)]={'sha256':sha(raw),'bytes':len(raw)}
requirements={
 'status':'DRAFT_NOT_RELEASED_SOURCE_ONLY_REQUIRES_INDEPENDENT_REVIEW',
 'actual_target_source':None,'actual_target_design':None,'actual_gate':None,'actual_policy':None,'actual_compatibility_review':None,'actual_compatibility_recovery':None,'actual_reference_COMPLETE':None,'actual_native_release':None,
 'fixed_role':'operational_source_compatibility','proof_roles':['operational_source_compatibility_review','operational_source_compatibility_recovery'],
 'mandatory_historical_aliases':['closure_input','claim_input','failed_input','checkpoint_input','plan_input','job_input'],
 'existing_prior_descriptor_roles_unchanged':['parent_job_input','parent_plan_input','fit_claim_input','failed_fit_input','diagnostic_input','schedule_input','claim_input','terminal_input','checkpoint_input'],
 'original_checkpoint_member_roles':'Every original checkpoint member remains independently registered by exact path/hash; no state bytes emitted or decoded here.',
 'before_new_reference':'Commit and independently review exact195 implementation map, policy, all3 fixed consumer identities/cells and all inputs/proof roles; preserve previous failed scopes externally and freshly; independently review whole new caller/source/recovery and cumulative budget.',
 'before_continuation':'Complete and independently accept/recover the new100 reference on the identical195 implementation map/policy. Preclaim metadata/source/parent/checkpoint/reference authentication must be implemented/admitted separately by Root; these worker predicates require an already genuine active Run and are not a preclaim API.',
 'reference_policy':'Original reference and evaluation provenance equality remain strict; no old or failed reference is converted to COMPLETE.',
 'budget':{'highest_actual_claim_budget':19,'spent_failed_claims':3,'remaining_existing_allowances':16,'original_phase_requirements_remaining':17,'prospective20':None,'refund_or_transfer':False},
 'no_hash_cycle':'Policy binds helper/body maps but no containing future Git commit. Proof bodies bind policy/helper/maps. Genuine current Admission binds actual source=design, and outputs carry that NEW commit/map. Root final external release separately binds actual committed source.',
 'review_proof_limit':'The strict proof roles check registered, source-pinned JSON consistency; an accepted label is not independently authenticated authorship or external retrieval. Root must supply genuine separately authored review and actual recovery evidence and admit the final external release.',
 'relocation':'Historical diagnostic/failed-fit absolute paths are checked literally. A moved checkpoint or relabeled old manifest is refused; no relocation exemption is provided.',
 'future_cardinality':'Root must deduplicate exact final role/input/source maps; prior338pins/eightroles no longer apply.',
 'no_numerical_or_financial_authority':True}
save('ROOT_REQUIREMENTS01.json',requirements)
machine={'status':'SOURCE_CANDIDATE_FROZEN_NOT_ADOPTED','author':'combined_worker_review','sources':sources,'source_footprint':{'historical_paths':194,'historical_distinct_hashes':193,'target_paths':195,'target_distinct_hashes':len(set(readback['target_map'].values())),'original_paths_byte_identical':191,'replaced_paths':3,'added_helper_paths':1},'historical_commit':'0a2e7639b42b9423b90743feadcda4078aa21816','later_source_with_same194map':'9dc5c79f738920b52947b4e63fed0397f1b5b207','final_control_rows':checks['count']+more['count'],'control_breakdown':{'check02_final_rows':checks['count'],'check03_actual_AST_and_nested_cleanup_rows':more['count']},'preserved_harness_failure':{'script':'check01.py','stderr':'CHECK01.err','reason':'Text search for _lock( matched the own helper function name, not a lock call; check02 uses actual AST Call nodes. First failed harness is not counted as passing.'},'inverse':{'file':'SOURCE_INVERSES02.json','sha256':sha((H/'SOURCE_INVERSES02.json').read_bytes()),'full_literal_and_AST':True,'unaffected_numerical_functions':True},'evidence':evidence,'genuine_runtime_calls_executed':False,'checkpoint_body_read_or_deserialized':False,'actual_native_or_capacity_tested':False,'external_recovery_performed':False,'research_allowance_changed':False,'implementation_limit':'Fixed classification/eager historical interrupt1 edge only. No transitive/general scientific compatibility. Source candidate requires independent review and Root full admission.'}
save('MACHINE01.json',machine)
(H/'REPORT01.md').write_text('''# Prospective operational provenance bridge — source preparation only

The candidate implements one explicit historical source edge, with no installed authority. Historical checkpoint/claim source0a2 and its194-path/193-distinct-hash map stay unchanged. The target implementation has195 paths: watcher, wrapper and training control statements change;191 original bodies remain byte-identical; one shared validator is added. Every path is checked, so equal hash sets cannot hide missing or swapped paths. The exact target watcher91e21 is the independently reviewed correction03. Model20f451, training configurationd527, scientific execution, tolerances, checkpoint/cache loaders and the entire fit_cell/predict_cell AST are unchanged.

The optional committed/source-pinned operational_source_compatibility role activates the exact finite policy. Without it, the original equality statements remain literal defaults. An incomplete policy, unknown delta, wrong historical pin, unexpected helper, malformed future consumer or reflexive/reverse source relation refuses. The template intentionally has unresolved identities, role aliases and original provenance; it is not executable approval. The helper's own digest is authenticated from its actual registered source bytes, avoiding an embedded self-hash cycle. The policy excludes the containing future Git commit; genuine Admission and final Root release must bind that separately.

At wrapper._parent and training._reserve, the candidate independently rejoins the genuine verify_claim result, fixed original failed claim/terminal, exact original job-selected interruption plan, path-complete original closure, failed-fit claim, PlannedInterruption terminal, diagnostic, schedule and registered opaque checkpoint member hashes. Both original and current provenance remain complete and different. All non-source fields must be exactly equal. The generic loader receives the unchanged old provenance; future outputs keep actual NEW source_commit/source_hashes. A separate immutable operational-source-compatibility.json lineage record is written before the new fit claim. Neither old manifests nor old claims are rewritten.

The ordinary wrapper uses genuine read_input. Training already holds lifecycle._lock and calls a fixed private path that uses bounded descriptor-anchored registered-byte reads, never read_input or authorize under that lock. No caller-supplied boolean or substitute Run is accepted. Each helper-owned read has4MiB file,64MiB cumulative reservation and120-second sampled checks; all acquired descriptors are closed, first fatal identity and nested secondary objects are retained. These limits describe the new reader, not a new whole-runtime I/O quota: inherited genuine admission/verification/read_input APIs keep their own behavior. No continuous filesystem immutability, syscall preemption or capacity is asserted.

The complete100 reference, continuation and prediction must use one prospectively frozen target closure/policy. The original reference provenance equality remains unchanged; a genuine COMPLETE reference on the same target map and policy is additionally required for continuation. The edge is limited to the fixed classification/eager interrupted parent. It is not a general source-version exemption or financial experiment result.

Validation comprises506 final source/opaque-control rows: real194-body hash joins, each195 target-path mutation, finite policy/refusal cases, literal and AST inverses, actual original comparison expressions showing RED on the operational delta, and real descriptor fatal/cleanup matrices including two nested close failures. The first harness's function-name text-search failure is retained in CHECK01.err; the corrected test inspects AST Call nodes. No genuine Run/Owner/Admission was constructed or invoked, no checkpoint values were opened or decoded, and no numerical package was imported.

Root still must independently review these exact sources; freeze actual policy/roles/consumer identities; authenticate all raw historical/current inputs before any claim; register the complete new source/gate and same-program cumulative allowance; preserve and externally/freshly recover complete failed histories and the new source/caller/reviews; and issue a genuine final native release. Proof-role accepted labels are only pinned consistency fields, not fabricated independent authorship or recovery. No new preclaim API is implemented here. Three FAILED claims remain spent, with16 existing allowances versus17 original remaining phase requirements; no20 amendment is adopted. All1420 paper fits remain pending.
''')
# Complete typed final tree, including drafts, raw failures, empty stderr and literal link.
rows=[]
for root,dirs,files in os.walk(H,followlinks=False):
 for name in sorted(dirs+files):
  p=Path(root)/name;r=str(p.relative_to(H));st=p.lstat();row={'path':r,'mode':stat.S_IMODE(st.st_mode)}
  if stat.S_ISLNK(st.st_mode):row.update(kind='symlink',target=os.readlink(p))
  elif stat.S_ISDIR(st.st_mode):row.update(kind='directory')
  elif stat.S_ISREG(st.st_mode):
   raw=p.read_bytes();assert len(raw)<=4*1024**2;row.update(kind='file',bytes=len(raw),sha256=sha(raw))
  else:raise ValueError(r)
  rows.append(row)
rows.sort(key=lambda r:r['path']);save('MANIFEST01.json',{'schema_version':1,'scope':'complete preparation tree except this self-manifest','members':rows,'typed_members':len(rows),'regular_files':sum(r['kind']=='file' for r in rows),'regular_bytes':sum(r.get('bytes',0) for r in rows),'status':'FROZEN_SOURCE_ONLY_NO_ADOPTION'})
print(json.dumps({'manifest_sha256':sha((H/'MANIFEST01.json').read_bytes()),'machine_sha256':sha((H/'MACHINE01.json').read_bytes()),'report_sha256':sha((H/'REPORT01.md').read_bytes()),'sources':sources,'typed_members':len(rows)}))
