"""One metadata/source composition check; no admission, numerical import or claims."""
from pathlib import Path
import ast,copy,hashlib,json,os,stat
ROOT=Path.cwd(); F=Path('research/onchain-paper-replication-2026-09-24/full_sources')
HERE=F/'real-data-pilot-final-binding-review01-2026-10-06'; FINAL=F/'real-data-pilot-final01-2026-10-06'
NAME='eth-paper-real-data-end-to-end-resource-20261005-01'
sha=lambda b:hashlib.sha256(b).hexdigest()
def raw(v):return (json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def read(p):return json.loads(Path(p).read_bytes())
def need(x,m):
 if not x:raise ValueError(m)
def refread(ref):
 p=Path(ref['path']);need(not p.is_absolute() and p.resolve()==ROOT/p,'canonical metadata')
 body=p.read_bytes();need(sha(body)==ref['sha256'],'metadata pin '+str(p))
 if 'bytes'in ref:need(len(body)==ref['bytes'],'metadata extent')
 return json.loads(body)
binding=read(FINAL/'BINDING_DRAFT03.json');need(binding['binding_review'] is None,'unbound reviewer slot')
g=refread(binding['gate']);e=g['experiments'][NAME];need(len(g['experiments'])==1,'one experiment')
d=refread(binding['draft']);prepared=refread(binding['preparation']);baseline=refread(binding['baseline']);bound=refread(binding['transport_binding'])
need(sha((FINAL/'gate01.json').read_bytes())=='85a60fd9659cae88afab9d143cfcd4b61319f359b54faab2c72645f28b71e544','exact final gate')
base=read(F/'real-data-pilot-sixth-graph01-2026-10-06/gate01.json');be=next(iter(base['experiments'].values()))
for k in ('families','datasets','program_id','schema_version'):need(g[k]==base[k],'unchanged '+k)
for k in ('runtime_hashes','cumulative_budget_extension'):need(e[k]==be[k],'carry '+k)
need(e['parent'] is None and e['selection'] is None and e['stage']=='development' and e['reuse']=='exploratory' and e['family']=='paper','scope fields')
need(e['cells']==['real-eth-one-update'] and len(e['outputs'])==len(set(e['outputs']))==8,'cell/output cardinality')
for ext in e['cumulative_budget_extension'].values():refread(ext)
need(len(e['inputs'])==59 and len(e['source_files'])==194,'actual gate cardinalities')
for p,h in e['source_files'].items():
 need(p!=binding['transport']['path'],'private excluded from source')
 need(sha(Path(p).read_bytes())==h,'current source pin '+p)
roster=read(F/'real-data-pilot-final-gate-composition01-2026-10-06/CURRENT_SOURCE_ROSTER01.json')['files'];need(len(roster)==178 and all(e['source_files'][p]==h for p,h in roster.items()),'178 accepted current source roster')
for name,h in e['runtime_hashes'].items():need(sha((Path('tradingagents/research')/name).read_bytes())==h,'runtime pin')
preflight=FINAL/'preflight01.py';accepted=F/'real-data-pilot-final-preflight-preparation03-2026-10-06/preflight01.py'
need(preflight.read_bytes()==accepted.read_bytes(),'exact source03 entry copy')
need((FINAL/'root_io.py').read_bytes()==(F/'real-data-pilot-root-io-preparation01-2026-10-06/root_io.py').read_bytes(),'exact Root IO copy')
need(d['protocol']['physical_baseline']['evidence']==binding['baseline'],'baseline ref')
baseline03=refread(baseline['metadata_adapter_basis']);need(baseline['observation']==baseline03['observation']==baseline['result']['observation'],'baseline wrapper inverse')
for key,obs in [('allocated_bytes','allocated_bytes'),('logical_bytes','logical_file_bytes'),('entries','entries')]:need(d['protocol']['physical_baseline'][key]==baseline['observation'][obs],'baseline declared amount')
need(sha(json.dumps(d['graphs'],sort_keys=True).encode())=='73779a7d29bdf98530b3886282339f76edb4feac28b11470a8c147250fe34247','accepted actual seven graph metadata')
need(bound['source_request']['prepared']==binding['preparation'],'binder source preparation')
archive=refread(prepared['builder03_spec']['references']['archive_policy'])
need(bound['source_request']['archive_policy']==prepared['builder03_spec']['references']['archive_policy'],'binder archive request')
# Invoke only accepted pure inverse and opaque validator functions, no module imports.
names={'need','reference','inverse_binding','validate_opaque'};tree=ast.parse(preflight.read_text());chosen=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
need({n.name for n in chosen}==names,'accepted helper functions')
ns={'Path':Path,'ROOT':ROOT,'OPAQUE_ROLE':'archive_transport','copy':copy,'os':os,'stat':stat,'hashlib':hashlib}
exec(compile(ast.Module(body=chosen,type_ignores=[]),str(preflight),'exec'),ns)
ns['inverse_binding'](prepared,archive,bound,binding['transport'],raw,sha)
ns['validate_opaque'](binding['transport']) # exact bounded hash/stat only, no decode/output
need(bound['inputs'].keys()=={'archive_policy','execution_job','mcm_output_policy','original_import','pilot','producer_plan','resource_population_plan','typed_payload'},'eight public docs')
inputs=e['inputs'];irefs=read(FINAL/'INPUT_REFS02.json');need(set(inputs)==set(irefs) and all(v=={'dataset':'eth','path':irefs[k]['path'],'sha256':irefs[k]['sha256']} for k,v in inputs.items()),'actual input roster')
expected=dict(prepared['builder03_result']['opaque_references'])
for role,body in bound['inputs'].items():
 need(inputs[role]['dataset']=='eth','dataset')
 p=Path(inputs[role]['path']);need(p.parent==FINAL/'inputs02','final public controls location')
 need(p.read_bytes()==raw(body) and sha(p.read_bytes())==inputs[role]['sha256'],'published exact public body '+role)
 expected.pop(role,None)
for role,r in expected.items():need(all(inputs[role][k]==r[k] for k in ('path','sha256')),'preserved opaque ref '+role)
need(all(inputs['archive_transport'][k]==binding['transport'][k] for k in ('path','sha256')),'sole private input ref')
need(set(inputs)==set(expected)|set(bound['inputs'])|{'archive_transport','execution_workspace'},'exact full role union')
workspace=refread(inputs['execution_workspace']);need(workspace=={'root':str(ROOT),'ledger':str(ROOT/'research_runs'),'artifacts':str(ROOT/'research_artifacts'),'git_common':'/home/malecada/master_thesis/TradingAgents/.git'},'exact workspace4fields')
job=bound['inputs']['execution_job'];s=job['payload']['representation_jobs']['original32'];item=bound['inputs']['producer_plan']['producers']['original32'];need(all(item[k]==v for k,v in s.items()),'job/producer equality')
pair=refread(inputs['pair_policy']);need(pair['numerical_source']=={'commit':'9bacbbeebe39095916f8a85ac4ee0b2623085560','files':roster},'actual current pair numerical anchor')
oldpair=read(F/'real-data-pilot-selected-feature-protocol01-2026-10-06/draft07/templates/pair_policy.json');v=copy.deepcopy(pair);v['numerical_source']=oldpair['numerical_source'];need(v==oldpair,'pair method/limits inverse')
for v in (s,item):need(v['descriptor']['pair_execution']=={'backend':pair['backend'],'policy_sha256':inputs['pair_policy']['sha256']},'both pair hashes')
control=bound['inputs']['original_import'];oldcontrol=read(F/'real-data-pilot-selected-feature-protocol01-2026-10-06/draft07/templates/original_import.json');v=copy.deepcopy(control);v['required_graphs']=oldcontrol['required_graphs'];need(v==oldcontrol,'original32/512 evidence preserved')
need(control['sample_count']==512 and control['motif_count']==32 and len(control['required_graphs'])==7,'original cardinalities')
for r in control['refs'].values():need(inputs[r['input']]['sha256']==r['sha256'],'original11 role hash')
recipe=read(F/'real-data-pilot-final-gate-composition01-2026-10-06/INPUT_ROLE_RECIPE01.json')
for role,r in recipe['june13_protected_roles'].items():need(all(inputs[role][k]==r[k] for k in ('path','sha256')),'June13 protected21 '+role)
need(len(recipe['june13_protected_roles'])==21,'protected cardinality')
original26=read(FINAL/'ORIGINAL26_MAIN_OBJECT_READBACK01.json');need(original26['actual_current_main_git_object_readback'] is True and original26['original_source_count']==26,'Root actual26 proof')
need({r['path']:r['sha256'] for r in original26['source_objects']}==recipe['original26_source_files'] and sum(r['bytes'] for r in original26['source_objects'])==122632,'26 original exact inherited metadata joins')
observation=read(FINAL/'RUNTIME_OBSERVATION01.json');need(observation['include_torch'] is True and observation['current_comparison_equal'] is True and refread(observation['exact_original_environment'])==observation['actual_inventory'],'actual Root runtime metadata')
need(inputs['environment']['sha256']==observation['exact_original_environment']['sha256'],'environment reference')
pilot=bound['inputs']['pilot'];population=bound['inputs']['resource_population_plan'];need(set(e['outputs'])==set(pilot['outputs'].values())|set(population['outputs'].values())|{'archive-receipt.json','archive-terminal.json'},'exact outputs union')
need(job['resources']==pilot['resource_policy'],'one native resource policy')
need(pilot['asset']=='ETH' and pilot['seed']==11 and pilot['batch_size']==16 and pilot['lookback_days']==28 and pilot['indices'] is None,'frozen science/defaults')
need(inputs['model']['sha256']=='20f451c08143dd81491b5c9fa0a90243ee6a9363df1fbbfcbd9c45b32f9b054d' and inputs['training']['sha256']=='d5276b75491e130bd03d43de28120f72dd792e42af4446382a6c127d387b8ec0','science pins')
need('include_torch=True' in preflight.read_text() and "if available<job['resources']['start_reserve_bytes']" in preflight.read_text(),'live Torch/RAM predicates retained')
unused=[ROOT/'research_runs'/NAME,ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/NAME,ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/NAME,ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/pilot-parent'/NAME,ROOT/FINAL/'launch-attempt01.json',ROOT/FINAL/'outer-exit01.json']
need(all(not p.exists() and not p.is_symlink() for p in unused),'unused identity paths')
result={'schema_version':1,'status':'PASSED_METADATA_SOURCE_COMPOSITION','source_pins':194,'current_package':178,'inputs':59,'public_bound_controls':8,'workspace_fields':4,'june13_protected_roles':21,'original_source_objects_recorded':26,'original_source_bytes_recorded':122632,'source_anchor':'9bacbbeebe39095916f8a85ac4ee0b2623085560','fixed_identity_paths_observed_absent':True,'opaque_validation':'accepted helper stat/hash only; no decode/print','gate_sha256':binding['gate']['sha256'],'review_does_not_grant_physical_eligibility':True,'no_git_numerical_network_native_or_claim_calls':True,'six_binding_evidence':{binding[k]['path']:binding[k]['sha256'] for k in ('gate','draft','preparation','baseline','transport','transport_binding')}}
(HERE/'CHECKS01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,sort_keys=True))
