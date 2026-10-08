import ast,copy,hashlib,json,stat
from pathlib import Path
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';N=F/'real-data-pilot-final21-2026-10-08';O=F/'real-data-pilot-final20-2026-10-08';H=Path(__file__).resolve().parent;NAME='eth-paper-real-data-end-to-end-resource-20261008-21';OLD=NAME[:-2]+'20';checks=[]
prior=json.loads((F/'index-capacity02-review01-2026-10-08/RELEASE_REVIEW02.json').read_bytes());ev=dict(prior['evidence']);oldbinding=json.loads((O/'BINDING02.json').read_bytes());ev.pop(oldbinding['transport']['path'])
def read(p):
 b=p.read_bytes();ev[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def load(p):return json.loads(read(p))
def check(n,v):
 assert v,n
 checks.append(n)
def need(v,m):
 if not v:raise ValueError(m)
# Frozen precursor reviews reused.
owner_review=load(H.parent/'SOURCE_REVIEW01.json');identity_review=load(H.parent/'METADATA_IDENTITY_REVIEW01.json');budgetreview=load(H.parent/'EXTENSION92_REVIEW01.json')
gate=load(N/'gate01.json');oldgate=load(O/'gate03.json');exp=gate['experiments'][NAME];oldexp=oldgate['experiments'][OLD];binding=load(N/'BINDING_DRAFT01.json')
check('exact_new_experiment',set(gate['experiments'])-set(oldgate['experiments'])=={NAME})
check('historical_experiments_unchanged',all(gate['experiments'][k]==v for k,v in oldgate['experiments'].items()))
check('family_and_other_gate_fields_unchanged',{k:v for k,v in gate.items() if k!='experiments'}=={k:v for k,v in oldgate.items() if k!='experiments'})
for p,h in exp['source_files'].items():check('source_'+p,hashlib.sha256(read(R/p)).hexdigest()==h)
for role,v in exp['inputs'].items():check('input_'+role,hashlib.sha256(read(R/v['path'])).hexdigest()==v['sha256'])
check('331sources59inputs',len(exp['source_files'])==331 and len(exp['inputs'])==59)
changed={p:h for p,h in exp['source_files'].items() if p.startswith('tradingagents/') and oldexp['source_files'].get(p)!=h}
check('only_two_main_changes',changed=={'tradingagents/research/onchain_replication/matching_owner.py':owner_review['candidate']['sha256'],'tradingagents/research/onchain_replication/real_pilot_storage.py':identity_review['candidate_storage']['sha256']})
for v in binding.values():
 if isinstance(v,dict) and {'path','sha256'}<=v.keys():check('bound_reference_'+v['path'],hashlib.sha256(read(R/v['path'])).hexdigest()==v['sha256'])
draft=load(R/binding['draft']['path']);prepared=load(R/binding['preparation']['path']);baseline=load(R/binding['baseline']['path']);bound=load(R/binding['transport_binding']['path']);oldprep=load(O/'PREPARATION_RESULT06.json')
inv=copy.deepcopy(prepared['inventory']);oldinv=copy.deepcopy(oldprep['inventory'])
for k in ('total_with_declared_baseline','storage_budget_unchanged'):inv.pop(k);oldinv.pop(k)
check('modeled_growth_exact',inv==oldinv and inv['new_logical_bytes']+inv['allocation_overhead_bytes']==13513030747)
check('baseline_ref',draft['protocol']['physical_baseline']['evidence']==binding['baseline'])
obs=baseline['result']['observation'];check('baseline_values',all(draft['protocol']['physical_baseline'][k]==obs[v] for k,v in [('logical_bytes','logical_file_bytes'),('allocated_bytes','allocated_bytes'),('entries','entries')]))
text=read(N/'preflight01.py').decode();oldtext=read(O/'preflight03.py').decode()
seam="    # Validate the genuine resource-owner schema before graph loading or reservation.\n    from tradingagents.research.onchain_replication.matching_owner import _pair_limits\n    pair_limits=json.loads(read_path(ROOT/admission.inputs['pair_policy']['path']))['limits']\n    compact_limits=json.loads(read_path(ROOT/admission.inputs['compact_policy']['path']))['stage_policy']['pair']\n    need(pair_limits==compact_limits,'resource-owner and compact limits differ')\n    _pair_limits(pair_limits,resource=True)\n"
check('one_exact_new_seam',text.count(seam)==1)
inverse=text.replace(seam,'').replace(NAME,OLD).replace('fixed21-','fixed20-').replace("HERE/'gate01.json'","HERE/'gate03.json'").replace("HERE/'BINDING01.json'","HERE/'BINDING02.json'").replace("HERE/'RELEASE_REVIEW01.json'","HERE/'RELEASE_REVIEW02.json'").replace('effective_attempt_budget!=92','effective_attempt_budget!=91').replace("'effective_attempt_budget':92","'effective_attempt_budget':91")
check('literal_preflight_inverse',inverse==oldtext)
check('seam_before_header_runtime',text.index(seam)<text.index('index_capacity=capacity_module.validate(')<text.index('runtime_inventory=subprocess.check_output('))
root=read(N/'root_io.py').decode();check('rootio_inverse',root.replace(NAME,OLD).replace('from preflight01 import check','from preflight03 import check')==read(O/'root_io03.py').decode())
check('read_only_check_before_launch',root.index('args, preflight = check()')<root.index('result = launch_checked(args,preflight'))
def const(s,name):return ast.literal_eval(next(n.value for n in ast.parse(s).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)))
helper=const(text,'SUCCESSOR');check('new_helper_source_closure',exp['source_files'][helper['path']]==helper['sha256']);deps=load((R/helper['path']).with_name('DEPENDENCIES04.json'))
for v in deps.values():check('helper_pin_'+v['path'],exp['source_files'][v['path']]==v['sha256'])
check('helper_dependencies_in_source',str((R/helper['path']).with_name('DEPENDENCIES04.json').relative_to(R)) in exp['source_files'])
refs=load(N/'INPUT_REFS01.json')
for role,v in refs.items():
 check('materialized_ref_'+role,all(exp['inputs'][role][k]==v[k] for k in ('path','sha256')))
 if role!='archive_transport':check('public_materialized_'+role,load(R/v['path'])==bound['inputs'][role])
for role,v in draft['protocol']['references'].items():
 if role in exp['inputs'] and role not in refs:check('other_runtime_ref_'+role,all(exp['inputs'][role][k]==v[k] for k in ('path','sha256')))
pilot=load(R/exp['inputs']['pilot']['path']);oldpilot=load(O/'inputs06/pilot.json');job=load(R/exp['inputs']['execution_job']['path']);compact=load(R/exp['inputs']['compact_policy']['path']);pair=load(R/exp['inputs']['pair_policy']['path'])
check('pilot_science_diagnostic_unchanged',{k:v for k,v in pilot.items() if k!='resource_policy'}=={k:v for k,v in oldpilot.items() if k!='resource_policy'})
check('resources_identity_only',json.dumps(pilot['resource_policy'],sort_keys=True).replace(NAME,OLD)==json.dumps(oldpilot['resource_policy'],sort_keys=True))
check('resources_three_way_join',pilot['resource_policy']==job['resources']==const(text,'EXPECTED_RESOURCES'))
check('runtime_pair_compact_join',pair['limits']==compact['stage_policy']['pair'])
check('cell_outputs_unchanged',exp['cells']==oldexp['cells']==[pilot['cell_id']] and exp['outputs']==oldexp['outputs'] and pilot['outputs']['diagnostic'] in exp['outputs'])
check('graph_metadata_unchanged',hashlib.sha256(json.dumps(draft['graphs'],sort_keys=True).encode()).hexdigest()==const(text,'GRAPH_METADATA_SHA'))
for role in ('model','training','original_dictionary','original_dictionary_config'):check('scientific_ref_'+role,exp['inputs'][role]==oldexp['inputs'][role])
check('budget92_exact_review',exp['cumulative_budget_extension']['review']['sha256']==hashlib.sha256((H.parent/'EXTENSION92_REVIEW01.json').read_bytes()).hexdigest() and exp['cumulative_budget_extension']['extension']['sha256']==budgetreview['extension_sha256'])
# Reuse exact inverse-only binder function; private transport is never decoded.
fn=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='inverse_binding');env={'copy':copy,'Path':Path,'need':need,'OPAQUE_ROLE':'archive_transport'};exec(compile(ast.Module(body=[fn],type_ignores=[]),'<public inverse>','exec'),env)
archive=load(R/draft['protocol']['references'][draft['protocol']['template_roles']['archive']]['path']);env['inverse_binding'](prepared,archive,bound,binding['transport'],lambda v:(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode(),lambda b:hashlib.sha256(b).hexdigest());checks.append('public_binder_inverse')
private=R/binding['transport']['path'];check('private_modes',stat.S_IMODE(private.stat().st_mode)==0o600 and stat.S_IMODE(private.parent.stat().st_mode)==0o700)
check('sole_private_reference',[p for p in ev if p.startswith('research_artifacts/real_pilot_runtime/pilot-transport-')]==[binding['transport']['path']])
for p in (R/'research_runs'/NAME,R/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/NAME,R/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/NAME,R/'research_artifacts/onchain-paper-replication-2026-09-24/pilot-parent'/NAME,N/'launch-attempt01.json',N/'outer-exit01.json'):check('fresh_absent_'+str(p.relative_to(R)),not p.exists() and not p.is_symlink())
for role in ('gate','draft','preparation','baseline','transport','transport_binding'):check('required_six_join_'+role,ev[binding[role]['path']]==binding[role]['sha256'])
result={'schema_version':1,'decision':'accepted','identity':NAME,'evidence':ev,'checks':checks,'accepted_gate':binding['gate'],'scope':'Combined changed-entry review only. Fresh21 source331/input59 joins; only two accepted Main changes; actual resource-only owner helper called on pair/compact equality before headers/graph loading and RootIO. Literal inverse proves remaining entry unchanged aside identity/helpers/budget92. Original science/diagnostic/resources/history preserved; modeled growth unchanged13513030747 with separately observed baseline. Sole opaque private dispatch hashed only. Failed20 recovered; prospective92 exact independent review reused. Ready for actual final binding and focused seal, not launch/admission or full capacity proof. Original preparation refusals retained.'}
(H/'BINDING_REVIEW01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'decision':'accepted','checks':len(checks),'sha256':hashlib.sha256((H/'BINDING_REVIEW01.json').read_bytes()).hexdigest()}))
