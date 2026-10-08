import ast,copy,hashlib,json,os,stat
from pathlib import Path
R=Path.cwd(); F=R/'research/onchain-paper-replication-2026-09-24/full_sources';N=F/'real-data-pilot-final20-2026-10-08';O=F/'real-data-pilot-final19-2026-10-08';H=Path(__file__).resolve().parent
NAME='eth-paper-real-data-end-to-end-resource-20261008-20';OLD=NAME[:-2]+'19'; evidence={};checks=[]
def pin(p,h=None):
 assert p.suffix not in ('.npy','.npz','.bin','.body'),p
 data=p.read_bytes();digest=hashlib.sha256(data).hexdigest();assert h is None or digest==h,(p,digest,h);evidence[str(p.relative_to(R))]=digest;return data

def load(p):return json.loads(pin(p))
def check(n,x):
 assert x,n
 checks.append(n)
def need(x,m):
 if not x:raise ValueError(m)
def raw(x):return (json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
binding=load(N/'BINDING_DRAFT01.json');gate=load(N/'gate01.json');oldgate=load(O/'gate01.json');exp=gate['experiments'][NAME];prior=oldgate['experiments'][OLD]
for role,v in binding.items():
 if isinstance(v,dict) and 'path' in v:
  # Private dispatch is hashed only; never parsed or emitted.
  body=pin(R/v['path'],v['sha256']);check('binding_length_'+role,len(body)==v['bytes'])
check('old_experiments_identical',all(gate['experiments'][k]==v for k,v in oldgate['experiments'].items()))
check('only_one_new_experiment',set(gate['experiments'])-set(oldgate['experiments'])=={NAME})
check('gate_others_identical',{k:v for k,v in gate.items() if k!='experiments'}=={k:v for k,v in oldgate.items() if k!='experiments'})
for path,h in exp['source_files'].items():pin(R/path,h)
for role,v in exp['inputs'].items():pin(R/v['path'],v['sha256'])
check('all_input_refs_exact',load(N/'ALL_INPUT_REFS05.json')==exp['inputs'])
refs=load(N/'INPUT_REFS05.json');bound=load(N/'TRANSPORT_BINDING05.json');prepared=load(N/'PREPARATION_RESULT05.json');draft=load(N/'INPUT_DRAFT02.json');baseline=load(N/'BASELINE02.json')
for role,v in refs.items():
 check('registered_materialized_'+role,all(exp['inputs'][role][k]==v[k] for k in ('path','sha256')))
 if role!='archive_transport':check('materialized_body_'+role,load(R/v['path'])==bound['inputs'][role])
private=R/binding['transport']['path'];check('private_permissions',stat.S_IMODE(private.stat().st_mode)==0o600 and stat.S_IMODE(private.parent.stat().st_mode)==0o700)
check('private_single_link',private.stat().st_nlink==1 and private.resolve()==private)
# Actual unchanged public inverse-binding function, no package imports.
text=pin(N/'preflight01.py').decode();tree=ast.parse(text);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='inverse_binding')
env={'copy':copy,'Path':Path,'need':need,'OPAQUE_ROLE':'archive_transport'};exec(compile(ast.Module(body=[fn],type_ignores=[]),'<inverse_binding>','exec'),env)
archive=load(N/'templates02/archive_policy.json')
env['inverse_binding'](prepared,archive,bound,binding['transport'],raw,lambda b:hashlib.sha256(b).hexdigest());checks.append('actual_public_binder_inverse')
check('transport_request_join',bound['source_request']==load(N/'TRANSPORT_REQUEST05.json'))
check('baseline_exact_join',draft['protocol']['physical_baseline']['evidence']==binding['baseline'])
obs=baseline['result']['observation'];check('baseline_totals',all(draft['protocol']['physical_baseline'][k]==obs[o] for k,o in [('logical_bytes','logical_file_bytes'),('allocated_bytes','allocated_bytes'),('entries','entries')]))
# Literal predecessor inversion establishes unchanged guards and resource checks.
oldtext=pin(O/'preflight01.py').decode();oldtree=ast.parse(oldtext)
def const(t,name):return ast.literal_eval(next(n.value for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id==name for x in n.targets)))
newhelper=const(tree,'SUCCESSOR');oldhelper=const(oldtree,'SUCCESSOR')
inverse=text.replace(repr(newhelper),repr(oldhelper)).replace(NAME,OLD).replace('DEPENDENCIES04.json','DEPENDENCIES02.json').replace('effective_attempt_budget!=91','effective_attempt_budget!=90').replace("'effective_attempt_budget':91","'effective_attempt_budget':90")
check('literal_preflight_inverse',inverse==oldtext)
check('literal_root_io_inverse',pin(N/'root_io.py').decode().replace(NAME,OLD)==pin(O/'root_io.py').decode())
helper=R/newhelper['path'];pin(helper,newhelper['sha256']);deps=load(helper.with_name('DEPENDENCIES04.json'))
for v in deps.values():check('helper_source_closure_'+v['path'].split('/')[-1],exp['source_files'].get(v['path'])==v['sha256'])
check('loader_source_closure',exp['source_files'].get(newhelper['path'])==newhelper['sha256'])
check('dependencies_source_closure',str(helper.with_name('DEPENDENCIES04.json').relative_to(R)) in exp['source_files'])
pilot=load(N/'inputs05/pilot.json');oldpilot=load(O/'inputs01/pilot.json');job=load(N/'inputs05/execution_job.json')
check('diagnostic_exact',pilot['scoring_diagnostic']=={'schema_version':1,'max_completed_pairs':1024,'checkpoint_every_pairs':64,'checkpoint_relative':'scoring-diagnostic/progress.json'})
check('cell_exact',exp['cells']==[pilot['cell_id']])
check('outputs_exact',exp['outputs']==prior['outputs']+[pilot['outputs']['diagnostic']] and len(exp['outputs'])==len(set(exp['outputs'])))
check('pilot_original_science_preserved',{k:v for k,v in pilot.items() if k not in ('resource_policy','outputs','scoring_diagnostic','cell_id')}=={k:v for k,v in oldpilot.items() if k not in ('resource_policy','outputs','scoring_diagnostic','cell_id')})
check('resource_envelope_unchanged',json.dumps(pilot['resource_policy'],sort_keys=True).replace(NAME,OLD)==json.dumps(oldpilot['resource_policy'],sort_keys=True))
check('job_resource_join',pilot['resource_policy']==job['resources']==const(tree,'EXPECTED_RESOURCES'))
for role in ('original_import','resource_population_plan','mcm_output_policy'):check('preserved_'+role,load(N/'inputs05'/f'{role}.json')==load(O/'inputs01'/f'{role}.json'))
for role in exp['inputs']:
 if role not in refs and role!='pair_policy':check('unchanged_input_'+role,exp['inputs'][role]==prior['inputs'][role])
check('seven_graph_metadata_digest',hashlib.sha256(json.dumps(draft['graphs'],sort_keys=True).encode()).hexdigest()==const(tree,'GRAPH_METADATA_SHA'))
check('single_retention_stage',prepared['residuals']['source_bounds']['matching_stages']==1)
check('single_matrix',prepared['inventory']['categories']['retained_original_matrices']['regular_files']==1)
check('all_seven_graph_reservations',len(prepared['inventory']['by_week'])==7)
check('inventory_budget_join',prepared['inventory']['storage_budget_unchanged']==job['resources']['storage_budget'])
allow=exp['cumulative_budget_extension'];review=json.loads(pin(R/allow['review']['path'],'c685a1bd902f81dab42607ce6f9260ae1235f3863f04172a9b941c0b7f251cec'));extension=json.loads(pin(R/allow['extension']['path'],review['extension_sha256']))
check('extension_ref_exact',allow['extension']['sha256']==review['extension_sha256'])
check('extension_independently_accepted',review['decision']=='accepted')
check('gate_only_expected_changes',{k for k in prior.keys()|exp.keys() if prior.get(k)!=exp.get(k)}=={'cells','outputs','question','charter','cumulative_budget_extension','source_files','inputs'})
# Namespace absence only; actual preflight must repeat at release.
ns=load(N/'INITIAL_NAMESPACE_OBSERVATION01.json')
for p in ns['paths_absent']:check('namespace_absent_'+p,not (R/p).exists() and not (R/p).is_symlink())
for name in ('launch-attempt01.json','outer-exit01.json'):check('entry_absent_'+name,not (N/name).exists())
for role in ('gate','draft','preparation','baseline','transport','transport_binding'):check('six_preflight_join_'+role,evidence[binding[role]['path']]==binding[role]['sha256'])
(H/'CHECKS01.json').write_text(json.dumps({'checks':checks,'evidence':evidence,'identity':NAME,'status':'CHECKS_PASS','source_count':len(exp['source_files']),'input_count':len(exp['inputs'])},indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':'PASS','checks':len(checks),'sources':len(exp['source_files']),'inputs':len(exp['inputs'])}))
