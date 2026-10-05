from pathlib import Path
import json,hashlib,stat,ast,difflib,importlib.util,sys
M=Path.cwd();F=M/'research/onchain-paper-replication-2026-09-24/full_sources';S=F/'financial-wrapper-serialized-storage-binding-source01-2026-10-05';P=F/'financial-wrapper-serialized-storage-root-preparation01-2026-10-05';D=Path(__file__).parent;CAP=M.parent/'onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source';H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def put(n,x):p=D/n;assert not p.exists();p.write_text(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n');p.chmod(0o444);print(n,H(p))
manifest=read(S/'MANIFEST01.json');assert H(S/'MANIFEST01.json').startswith('e97d4e2b')
for row in manifest['members']:
 p=S/row['path'];assert H(p)==row['sha256'] and p.stat().st_size==row['bytes'] and stat.S_IMODE(p.stat().st_mode)==row['mode']==0o444
assert set(p.name for p in S.iterdir())=={r['path'] for r in manifest['members']}|{'MANIFEST01.json'}
chain=[(F/'financial-wrapper-continuation-successor-outcome-review01-2026-10-05/FULL_TERMINAL_RECOVERY_PROOF01.json','2263ea2cd9f6e6b2fe6100498a917fb971328d9e4ae3478e4f544a07f93d908b'),(F/'financial-wrapper-continuation-successor-review01-2026-10-05/FULL_CURRENT_RECOVERY_PROOF01.json','bdf0f39710054d34f2274eec35a192dc13200ff146b4a79d3f4822235efba7df'),(F/'financial-wrapper-continuation-outcome-review01-2026-10-05/FULL_REFUSAL_RECOVERY_PROOF01.json','a5357602f130838bbf52fd6fe54288401e91bfd045c96aac73fa128f4be41a42')]
for p,h in chain:assert H(p)==h
claims=[read(p) for p,h in chain];assert claims[0]['accepted_unchanged_byte_basis']['sha256']==chain[1][1] and claims[1]['accepted_baseline']['sha256']==chain[2][1]
base=F/'financial-wrapper-continuation-successor-source01-2026-10-05'
for name in ['operational_source_compatibility.py','preclaim01.py']:
 diff=(S/(name+'.ndiff')).read_text().splitlines(True);assert ''.join(difflib.restore(diff,1))==(base/name).read_text() and ''.join(difflib.restore(diff,2))==(S/name).read_text()
assert (S/'financial_wrapper_fixture.py').read_bytes()==(base/'financial_wrapper_fixture.py').read_bytes()
old=(F/'financial-wrapper-parent-storage-scheduling-source01-2026-10-05/parent01.py').read_text();new=(P/'parent-unbound01.py').read_text();a=ast.parse(old);b=ast.parse(new)
fa={n.name:ast.dump(n) for n in a.body if isinstance(n,ast.FunctionDef)};fb={n.name:ast.dump(n) for n in b.body if isinstance(n,ast.FunctionDef)};assert fa.keys()==fb.keys() and {k for k in fa if fa[k]!=fb[k]}=={'validate_release','preflight'} and fa['launch']==fb['launch']
assert H(P/'parent-unbound01.py')=='57c61bbdc298e7a98e1366ead1b014106d32cf7ec9a6600596fa8d2b66a49a49'
assert len(old.splitlines())==len(new.splitlines());lines=[i for i,(l,r) in enumerate(zip(old.splitlines(),new.splitlines()),1) if l!=r];assert lines==[11,12,14,33,78,93]
assign={n.targets[0].id:n.value for n in b.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name)};assert ast.literal_eval(assign['SOURCE_BINDING']) is None
identity=ast.literal_eval(assign['IDENTITY']);assert identity=='financial-wrapper-classification-eager-continue100-serialized-storage-successor-20261005-01'
oldplan=read(CAP/'fixture_inputs/financial_wrapper_continuation_successor01/continue-plan.json');newplan=read(P/'continue-plan.json');assert {k for k in oldplan if oldplan[k]!=newplan[k]}=={'experiment','namespace'} and newplan['experiment']==newplan['namespace']==identity
q=read(P/'REQUEST_UNBOUND_DRAFT01.json');assert q['proofs']=={'cumulative':None,'full_recovery':None,'independent_source_input_runtime':None} and q['final_review'] is None
oldgate=read(CAP/'fixture_inputs/financial_wrapper_continuation_successor01/gates.json');gate=read(P/'GATES_UNBOUND_DRAFT01.json');assert set(gate)==set(oldgate)
assert {k:gate[k] for k in gate if k!='experiments'}=={k:oldgate[k] for k in oldgate if k!='experiments'}
assert len(gate['experiments'])==6 and all(gate['experiments'][k]==v for k,v in oldgate['experiments'].items())
previous=oldgate['experiments']['financial-wrapper-classification-eager-continue100-resource-successor-20261005-01'];current=gate['experiments'][identity]
assert set(current)==set(previous);assert {k:current[k] for k in current if k not in ['inputs','source_files','question']}=={k:previous[k] for k in previous if k not in ['inputs','source_files','question']}
assert current['source_files'] is None and current['question'].startswith(previous['question'])
inputs=current['inputs'];assert len(inputs)==36 and set(inputs)-set(previous['inputs'])=={'successor_previous_recovery','successor_original_refusal'}
changed={k for k in previous['inputs'] if previous['inputs'][k]!=inputs[k]};assert changed=={'continuation_source_successor','continuation_source_successor_review','continuation_source_successor_recovery','source_closure','successor_refusal','wrapper_plan'}
for n in ast.walk(b):
 if isinstance(n,ast.Set):
  try:vals=ast.literal_eval(n)
  except (ValueError,TypeError):continue
  if 'successor_refusal' in vals:assert vals==set(inputs)
for role in changed|{'successor_previous_recovery','successor_original_refusal'}:
 row=inputs[role]
 if role in {'continuation_source_successor_review','continuation_source_successor_recovery'}:assert row['sha256'] is None;continue
 path=P/row['path'] if (P/row['path']).exists() else CAP/row['path'];assert H(path)==row['sha256']
edgepath=P/inputs['continuation_source_successor']['path'];edge=read(edgepath);closure=read(P/inputs['source_closure']['path']);originalraw=(CAP/'fixture_inputs/financial_wrapper_compatibility01/policy.json').read_bytes();original=json.loads(originalraw)
spec=importlib.util.spec_from_file_location('checked_serialized_helper',S/'operational_source_compatibility.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
effective=helper.validate_successor(original,originalraw,edge,H(S/'operational_source_compatibility.py'),chain[0][0].read_bytes(),chain[1][0].read_bytes(),chain[2][0].read_bytes())
assert len(edge['installed'])==195 and closure['installed']==edge['installed']
previousclosure=read(CAP/'fixture_inputs/financial_wrapper_continuation_successor01/source_closure.json');assert set(closure)==set(previousclosure) and {k:v for k,v in closure.items() if k!='installed'}=={k:v for k,v in previousclosure.items() if k!='installed'}
assert {k for k in closure['installed'] if closure['installed'][k]!=previousclosure['installed'][k]}=={helper.HELPER}
assert closure['installed'][helper.HELPER]==H(S/'operational_source_compatibility.py') and closure['installed'][helper.PREFIX+'financial_wrapper_fixture.py']==H(S/'financial_wrapper_fixture.py')
assert {k for k in effective if effective[k]!=original[k]}=={'target','consumers'}
assert helper.sha(originalraw)==helper.ORIGINAL_POLICY_SHA
assert not {'numpy','torch','scipy','pandas'}&set(sys.modules)
x={'schema_version':1,'decision':'accepted-changed-source-and-exact-prospective-edge-only','candidate_manifest_sha256':H(S/'MANIFEST01.json'),'helper_sha256':H(S/'operational_source_compatibility.py'),'fixture_sha256':H(S/'financial_wrapper_fixture.py'),'preclaim_sha256':H(S/'preclaim01.py'),'refusal_chain':[{'path':str(p),'sha256':h} for p,h in chain],'source_exact_ndiff_inverse':True,'legacy_original_contract_and_reference_checks_unchanged':True,'Parent_unbound_sha256':H(P/'parent-unbound01.py'),'Parent_scheduling_launch_function_exact':True,'Parent_changed_binding_lines':lines,'new_input_roles':['successor_previous_recovery','successor_original_refusal'],'new_input_count':36,'original_five_gate_definitions_unchanged':True,'family_budget_and_native_job_unchanged':True,'fresh_identity':identity,'plan_sha256':H(P/'continue-plan.json'),'plan_only_changed_fields':['experiment','namespace'],'prospective_registration_sha256':H(P/'GATES_UNBOUND_DRAFT01.json'),'edge_sha256':H(edgepath),'closure_sha256':H(P/inputs['source_closure']['path']),'all195_maps_authenticated':True,'changed_from_previous_installed_map':[helper.HELPER],'science_and_all_non_source_provenance_comparison_unchanged':True,'tests':{'changed_tests':2,'passed':2,'tool_chunk':'6d805b','seconds':0.003,'original_11_and_scheduling_5_reused':True},'numerical_imports':False,'source_integration_scope':'Only reviewed installed helper plus external preclaim; fixture unchanged. Fresh source_files and source recovery proof remain pending; no actual release, gate adoption or claim authority.','actual_source_recovery_pending':True,'launch_authorized':False,'findings':[]}
put('SOURCE_CHECK01.json',x)
proof={'schema_version':1,'kind':'continuation_source_successor_review','decision':'accepted','policy_sha256':H(edgepath),'original_policy_sha256':helper.ORIGINAL_POLICY_SHA,'historical_map_sha256':helper.sha(helper.canonical(original['target']['installed'])),'target_map_sha256':helper.sha(helper.canonical(edge['installed'])),'checker_sha256':H(S/'operational_source_compatibility.py'),'refusal_sha256':helper.REFUSAL_SHA};put('SOURCE_REVIEW_PROOF01.json',proof)
