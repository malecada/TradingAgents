from pathlib import Path
import ast,hashlib,json,os,stat
R=Path(__file__).resolve().parent;B=R.parent;MAIN=B.parents[2]
H=lambda b:hashlib.sha256(b).hexdigest();J=lambda p:json.loads(p.read_bytes())
qpath=B/'held-consumer-final-native-proof-root-preparation01-2026-10-03/ACTUAL_EXTERNAL_FINAL_BASELINE_RECOVERY01.json';q=J(qpath)
assert H(qpath.read_bytes())=='dc18f7ae66cf3ad67733e6f14b1941245a6e08ca365f3eac2bf35af8009f5962'
refs={}
for key,row in q['refs'].items():
 p=MAIN/row['path'];assert p.resolve()==p and p.is_file();b=p.read_bytes();assert len(b)==row['bytes'] and H(b)==row['sha256'];refs[key]=p
review_manifest=J(refs['actual_git_outcome_review_manifest'])
assert review_manifest['decision']=='ACCEPTED_ACTUAL_SELECTED_RECOVERED_GIT_JOINS_ONLY'
for row in review_manifest['members']:
 p=refs['actual_git_outcome_review_manifest'].parent/row['path'];s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==row['nlink'] and stat.S_IMODE(s.st_mode)==row['mode'];b=p.read_bytes();assert len(b)==row['bytes'] and H(b)==row['sha256']
assert set(p.name for p in refs['actual_git_outcome_review_manifest'].parent.iterdir())==set(r['path'] for r in review_manifest['members'])|{'MANIFEST01.json'}
proof=J(refs['actual_git_proof']);verdict=J(refs['actual_git_outcome_review_manifest'].parent/'READBACK02.json');terminal=J(refs['actual_git_terminal']);flat=J(refs['actual_flat_recovery'])
assert proof['source']==q['capsule_commit']==verdict['source'] and terminal['proof_sha256']==verdict['proof_sha256']==H(refs['actual_git_proof'].read_bytes()) and terminal['exit']==0
assert proof['recovery_sha256']==H(refs['actual_flat_recovery'].read_bytes())
assert proof['current_committed_files']==q['counts']['current_committed_files']==verdict['independent_current_rows']==246
assert proof['source_registration_joins']==q['counts']['source_registration_joins']==verdict['independent_source_registration_rows']==205
assert proof['opaque_inputs']==q['counts']['case_opaque_inputs']==verdict['independent_opaque_inputs']==33
assert proof['selected_c6_paths']==q['counts']['selected_original_c6_paths']==verdict['independent_selected_c6_rows']==26
assert proof['historical_lookups']==q['counts']['original_history_lookups']==verdict['independent_historical_lookups']==638
assert len(proof['object_files'])==q['counts']['recovered_object_files']==verdict['actual_object_files']==354
assert len(verdict['history'])==q['counts']['original_failed_claims']==4 and [x['effective_budget'] for x in verdict['history']]==[2,3,4,5] and all(x['status']=='failed' for x in verdict['history'])
assert verdict['checks']==5282 and verdict['actual_store_modified'] is False
for k in ('full_final_union_accepted','genuine_run_or_native_started','instantiated_original_posix_tree','later_appended_changed_proof_release_request_bodies_recovered','outside_stores_recovered','runtime_package_bodies_recovered','full_c6_tree_or_ancestry'):assert q[k] is False
for k in ('external_origin_proved','full_c6_ancestry','full_original_filesystem','original_posix_modes_instantiated','outside_stores_recovered','research_authority','runtime_recovered'):assert proof[k] is False
assert q['complete_immutable_unreleased_baseline_recovered'] is True and q['selected_recovered_git_joins_independently_accepted'] is True
assert q['counts']['actual_flat_files']==676 and q['counts']['capsule_logical_members']==925 and q['counts']['capsule_regular_bodies']==663 and q['counts']['external_logical_members']==12 and q['counts']['external_regular_bodies']==10
P=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-root-launch-20261003-01');C=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source')
caller=(P/'launch_success01.py').read_bytes();parser=(P/'held_outcome02.py').read_bytes();assert H(caller)==q['caller_sha256']=='7a197e2f57db3fff44fce453356d187f62dce5f119125e6814831eb6008f38dc' and H(parser)==q['semantic_parser_sha256']=='95affaa3867b0f50dedc706121b47304126c6def39715133414ef149b9eae153'
proposal=J(B/'held-consumer-final-composition-root-preparation01-2026-10-03/NATIVE_CONTRACT_PROPOSAL01.json');actual=J(P/'release-unreleased01.json');assert actual['status']=='UNRELEASED-investigation-template'
for p,h in proposal['source_files'].items():assert H((C/p).read_bytes())==h
assert H((C/proposal['registration']).read_bytes())==proposal['registration_sha256']
PROOFS=('release_review_sha256','external_capsule_recovery_sha256','external_recovery_review_sha256')
canonical=lambda v:json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
contract=lambda v:H(canonical({k:x for k,x in v.items() if k not in PROOFS}))
assert all(proposal[k] is None for k in PROOFS) and contract(proposal)==q['release_contract_sha256']=='17e513bb0fa4ae667c822d80118578ae487138a3c6ad1cdd1123b7d68c435110'
# Actual source predicate checks only, using genuine review decisions below.
# Neither prepared/main nor any capsule API or process is invoked.
review={'schema_version':1,'decision':'accepted-native-parent-release','identity':'original-import-held-success-20261003-01','capsule_commit':q['capsule_commit'],'caller_sha256':q['caller_sha256'],'semantic_parser_sha256':q['semantic_parser_sha256'],'release_contract_sha256':q['release_contract_sha256']}
recovery_review={'schema_version':1,'decision':'accepted-external-final-baseline-recovery','capsule_commit':q['capsule_commit'],'caller_sha256':q['caller_sha256'],'semantic_parser_sha256':q['semantic_parser_sha256'],'release_contract_sha256':q['release_contract_sha256'],'actual_external_recovery_sha256':H(qpath.read_bytes()),'scope':'Complete immutable unreleased baseline plus independently accepted selected recovered Git joins only. Final added/changed proof, release and request body recovery and independent complete-union/request review remain mandatory before launch. No native outcome or sufficient execution authority.'}
def require(v,m):
 if not v:raise ValueError(m)
tree=ast.parse(caller);prepared=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='prepared');stmts=[]
for n in prepared.body:
 if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and len(n.value.args)>1 and isinstance(n.value.args[1],ast.Constant) and n.value.args[1].value in ('independent exact release review differs','independent exact recovered final baseline differs'):stmts.append(n)
assert len(stmts)==2
ns={'require':require,'review':review,'recovery_review':recovery_review,'IDENTITY':review['identity'],'SOURCE':q['capsule_commit'],'PARSER_SHA':q['semantic_parser_sha256'],'request':{'caller':{'sha256':q['caller_sha256']}},'release':proposal,'contract':contract,'evidence':{'external_recovery':{'sha256':H(qpath.read_bytes())}}}
code=compile(ast.Module(stmts,type_ignores=[]),'actual_parent_prepared_predicates','exec');exec(code,ns)
for key,field in (('review','caller_sha256'),('recovery_review','actual_external_recovery_sha256')):
 original=ns[key];ns[key]={**original,field:'0'*64}
 try:exec(code,ns)
 except ValueError:pass
 else:raise AssertionError('mutated exact predicate accepted')
 ns[key]=original
assert not os.path.lexists(P/'attempt')
for case in proposal['cases'].values():
 for base in ('research_runs','fixture_outer','research_artifacts/onchain-paper-replication-2026-09-24/runs'):assert not os.path.lexists(C/base/case['identity'])
for name,value in [('NATIVE_PARENT_RELEASE_REVIEW01.json',review),('EXTERNAL_BASELINE_RECOVERY_REVIEW01.json',recovery_review)]:
 (R/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
result={'schema_version':1,'decision':'accepted_actual_baseline_and_documentary_native_contract_predicates_final_union_required','baseline_receipt_sha256':H(qpath.read_bytes()),'authenticated_ref_bodies':len(refs),'git_review_manifest_members':len(review_manifest['members']),'selected_actual_git_outcome_decision':review_manifest['decision'],'current_source_body_rechecks':205,'capsule_commit':q['capsule_commit'],'contract_sha256':contract(proposal),'actual_parent_predicates_checked':2,'mutation_refusals':2,'unreleased_original_parent_preserved':True,'final_union_accepted':False,'claims_or_native_started':False,'scope':'No Git/store/proof rerun. Actual outcome review and its complete immutable evidence authenticated; preceding own remote/flat/source reviews retained.'}
(R/'READBACK01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))
