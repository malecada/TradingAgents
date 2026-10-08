import ast,copy,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[4];P=Path(__file__).resolve().parent;S=P.parent;F=S/'real-data-pilot-final22-2026-10-08';O=S/'real-data-pilot-final21-2026-10-08'
def load(p):return json.loads(p.read_bytes())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(R)),'sha256':digest(p),'bytes':p.stat().st_size}
checks=[];evidence={}
def pin(x,opaque=False):
 p=R/x['path'];assert p.resolve()==p and p.is_file();assert digest(p)==x['sha256'],str(p)
 if 'bytes' in x:assert p.stat().st_size==x['bytes']
 evidence[x['path']]=x['sha256']
 return None if opaque else load(p) if p.suffix=='.json' else None
B=load(F/'BINDING_DRAFT01.json');G=pin(B['gate']);OG=load(O/'gate01.json');N=B['identity'];ON=N[:-2]+'21';E=G['experiments'][N];OE=OG['experiments'][ON]
assert all(G[k]==OG[k] for k in OG if k!='experiments');assert {k:v for k,v in G['experiments'].items() if k!=N}==OG['experiments'];assert E['parent'] is None
checks+=['historical_experiments_and_family_unchanged','parent_none']
assert E['inputs']==load(F/'ALL_INPUT_REFS01.json');assert len(E['source_files'])==345 and len(E['inputs'])==60
for path,sha in E['source_files'].items():pin({'path':path,'sha256':sha})
for role,x in E['inputs'].items():pin(x,role=='archive_transport')
for role,x in B.items():
 if isinstance(x,dict) and 'path' in x:pin(x,role=='transport')
checks+=['all_345_actual_source_bodies','all_60_input_pins_private_transport_hash_only']
assert E['source_files']['tradingagents/research/onchain_replication/real_pilot_import_caller.py']=='c7520b84b2f37cdb2676a26b281bcc3e7488bcbbad118f2f5225035749f117b2'
composition=load(R/B['consolidation_review']['path'])
for name,x in composition['files'].items():
 if name=='real_pilot_import_caller.py':continue
 assert E['source_files']['tradingagents/research/onchain_replication/'+name]==x['sha256']
checks+=['accepted_composition_plus_separately_reviewed_caller_and_annealing']
for x in E['cumulative_budget_extension'].values():pin(x)
extreview=load(R/E['cumulative_budget_extension']['review']['path']);assert extreview['decision']=='accepted' and extreview['extension_sha256']==E['cumulative_budget_extension']['extension']['sha256'];assert E['cumulative_budget_extension']['review']['sha256']=='73c077c977f0af85276f4a0ffb3aebdea388ab8937d3b8c5ff2ede8ac80c968c'
checks+=['accepted_prospective_93_review_exact_join']
def inp(e,role):return load(R/e['inputs'][role]['path'])
job=inp(E,'execution_job');oldjob=inp(OE,'execution_job');pilot=inp(E,'pilot');oldpilot=inp(OE,'pilot')
assert json.loads(json.dumps(oldjob['resources']).replace(ON,N))==job['resources'];assert {k:v for k,v in pilot.items() if k!='resource_policy'}=={k:v for k,v in oldpilot.items() if k!='resource_policy'};assert pilot['resource_policy']==job['resources'];assert len(pilot['graph_inputs'])==7
assert inp(E,'pair_policy')['limits']==inp(OE,'pair_policy')['limits']==inp(E,'compact_policy')['stage_policy']['pair'];assert E['inputs']['mcm_policy']==OE['inputs']['mcm_policy']
checks+=['seven_graphs_and_all_pilot_science_diagnostic_fields_unchanged','resource_caps_unchanged_except_explicit_identity','pair_limits_and_mcm_numeric_unchanged']
scratch=inp(E,'matching_ordered_edge_scratch');assert scratch['experiment']==N and scratch['chunk_edge_products']==1024 and scratch['incremental_explicit_numeric_scratch_bytes']==262144;assert E['source_files'][scratch['installed_source']['path']]==scratch['installed_source']['sha256'];assert scratch['independent_source_review']=={k:B['exact_annealing_review'][k] for k in ('path','sha256')}
for k,resource in [('native_memory_high_bytes_unchanged','memory_high_bytes'),('native_memory_max_bytes_unchanged','memory_max_bytes'),('native_wall_seconds_unchanged','wall_seconds')]:assert scratch[k]==job['resources'][resource]
assert 'matching/stream scratch' in ast.get_docstring(ast.parse((R/'tradingagents/research/onchain_replication/compact_mcm.py').read_text()))
checks+=['separate_registered_matching_scratch_excluded_from_mcm_allowance_unchanged_native_caps']
draft=load(R/B['draft']['path']);prepared=load(R/B['preparation']['path']);bound=load(R/B['transport_binding']['path']);assert hashlib.sha256(json.dumps(draft['graphs'],sort_keys=True).encode()).hexdigest()=='73779a7d29bdf98530b3886282339f76edb4feac28b11470a8c147250fe34247';assert prepared['inventory']['storage_budget_unchanged']==job['resources']['storage_budget']
# Execute only the actual pure inverse validator, not preflight or admission.
tree=ast.parse((F/'preflight01.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='inverse_binding');ns={'copy':copy,'Path':Path,'OPAQUE_ROLE':'archive_transport'}
def need(ok,msg):
 if not ok:raise AssertionError(msg)
ns['need']=need;exec(compile(ast.Module(body=[fn],type_ignores=[]),'isolated_inverse','exec'),ns)
archive=load(R/prepared['builder03_spec']['references'][prepared['builder03_spec']['template_roles']['archive']]['path'])
raw=lambda x:json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
# Binder's canonical raw function is source extracted to preserve exact encoding.
binder=S/'real-data-pilot-transport-binding-preparation01-2026-10-06/bind01.py';bt=ast.parse(binder.read_text());helpers=[n for n in bt.body if isinstance(n,ast.FunctionDef) and n.name in ('raw','sha')];bn={'json':json,'hashlib':hashlib};exec(compile(ast.Module(body=helpers,type_ignores=[]),'binder_helpers','exec'),bn)
ns['inverse_binding'](prepared,archive,bound,B['transport'],bn['raw'],bn['sha'])
for role,body in bound['inputs'].items():assert inp(E,role)==body
assert bound['source_request']['prepared']==B['preparation'];assert draft['protocol']['physical_baseline']['evidence']==B['baseline']
checks+=['actual_transport_inverse_only_three_accepted_modifications','all_bound_public_documents_equal_registered_inputs','exact_graph_metadata_and_baseline_reference']
# Reuse still-current inherited evidence; replace current sources and omit old opaque dispatch.
oldrelease=load(O/'RELEASE_REVIEW01.json');skipped=[]
for path,sha in oldrelease['evidence'].items():
 if path in evidence or path.startswith('research_artifacts/real_pilot_runtime/'):continue
 p=R/path
 if p.is_file() and digest(p)==sha:evidence[path]=sha
 else:skipped.append(path)
for p in [F/'preflight01.py',F/'root_io.py',F/'MATCHING_SCRATCH_RESERVATION01.json',F/'ALL_INPUT_REFS01.json',R/E['charter']['path']]:pin(ref(p))
# Explicit accepted metadata preparer and exact dependency closure.
dep=S/'real-data-pilot-storage-metadata-binding01-2026-10-08/DEPENDENCIES04.json';pin(ref(dep))
for x in load(dep).values():pin(x)
for p in [dep.with_name('successor04.py'),binder]:pin(ref(p))
assert digest(F/'root_io.py')=='e9a7009d5b6b9dc366c11f2227a8c76e0a080adccb2fc364a14427b9c31f4daf'
checks+=['unchanged_root_io_exact_pin','accepted_metadata_dependency_closure']
result={'schema_version':1,'decision':'accepted','identity':N,'accepted_gate':B['gate'],'checks':checks,'evidence':dict(sorted(evidence.items())),'scope':'Changed final22 metadata/source binding review only. Actual345 sources/60 inputs; accepted composition plus c752 caller and corrected exact annealing. Seven original graphs, science, diagnostic1024/64, native caps and MCM allowance unchanged. Extra262144B matching scratch is separately registered under unchanged caps. Prior terminal/recovery and accepted prospective93 evidence joined. Sole opaque dispatch hash-only. No numerical imports, Admission/Owner/claim/launcher execution; current committed seal and host eligibility remain Root obligations.'}
(P/'BINDING_REVIEW01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
(P/'CHECK01.json').write_text(json.dumps({'checks':checks,'inherited_noncurrent_omitted':skipped,'evidence_count':len(evidence)},indent=2)+'\n')
B['binding_review']=ref(P/'BINDING_REVIEW01.json');B['status']='BOUND_FINAL_PENDING_RELEASE';(P/'BINDING01.json').write_text(json.dumps(B,sort_keys=True,indent=2)+'\n')
evidence[B['binding_review']['path']]=B['binding_review']['sha256'];evidence[str((F/'BINDING01.json').relative_to(R))]=digest(P/'BINDING01.json')
release={'schema_version':1,'decision':'accepted','identity':N,'source_count':345,'input_count':60,'opaque_evidence_count':1,'final_binding_sha256':digest(P/'BINDING01.json'),'evidence':dict(sorted(evidence.items())),'scope':'Exact suggested final binding seal, conditional on Root copying BINDING01 bytes unchanged to final22. Reuses accepted immutable source and metadata reviews. No admission or launch performed; actual committed evidence/current eligibility must pass preflight. No scientific completion or capacity/peak-memory claim.'}
(P/'RELEASE_REVIEW01.json').write_text(json.dumps(release,sort_keys=True,indent=2)+'\n');print(json.dumps({'checks':len(checks),'evidence':len(evidence),'skipped':skipped,'binding_review':ref(P/'BINDING_REVIEW01.json'),'suggested_binding':ref(P/'BINDING01.json'),'release':ref(P/'RELEASE_REVIEW01.json')}))
