"""Metadata-only deterministic drafts and actual-validator refusal checks."""
import ast,hashlib,importlib.util,json,os,resource,runpy,signal,sys
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{0,1});os.nice(10);signal.alarm(30)
H=Path(__file__).resolve().parent;spec=importlib.util.spec_from_file_location('draft_builder',H/'build.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
a=b.build();again=b.build();assert b.raw(a)==b.raw(again)
checks=['deterministic_current_metadata_build'];t=a['templates'];bounds=a['graph_bounds'];total=a['totals'];assert len(bounds)==7 and total['cells']==415968128 and total['batches']==101559 and total['origin_bytes']==9*total['cells'] and total['summary_payload_cap']==8192*total['batches'];checks.append('seven_graph_full_denominator_exact')
for v in bounds.values():
 assert v['cells']==v['rows']*32 and v['batches']==(v['cells']+4095)//4096 and v['origin_bytes']==9*v['cells'] and v['summary_payload_cap']==8192*v['batches']
base=json.loads((b.ROOT/a['baseline_inputs']['pilot']['path']).read_bytes());new=t['pilot']
for key in ('asset','seed','batch_size','lookback_days','graph_inputs','indices','decisions','graph_sequences','population_plan_input','model_input','training_input','model_execution','max_checkpoint_bytes'):
 assert new[key]==base[key],key
assert 'scoring_diagnostic' not in new and 'partial_progress' not in new and 'diagnostic' not in new['outputs'];checks.append('full_original_update_metadata_and_no_planned_stop')
original=json.loads((b.ROOT/a['baseline_inputs']['producer_plan']['path']).read_bytes());assert t['producer_plan']['producers']['original32']['descriptor']['configs']==original['producers']['original32']['descriptor']['configs'];checks.append('dictionary32_512_and_scientific_matching_unchanged')
compact=json.loads((b.ROOT/a['baseline_inputs']['compact_policy']['path']).read_bytes())
for key in ('log','pair','schedule','score_chunk_cells','restart_retention'):assert t['compact_policy']['stage_policy'][key]==compact['stage_policy'][key]
checks.append('legacy_log_schedule_and_pair_caps_preserved')
m=t['mcm_policy'];cap=m['max_entries'];e=m['batched']['execution'];assert e['max_origin_bytes']==cap*9 and e['max_summary_bytes']==8192*((cap+4095)//4096) and e['max_entries']==4096 and e['max_retained_bytes']==64*1024**2 and e['max_key_bytes']==8*1024**2;checks.append('schema6_exact_cache_and_common_max_graph_caps')
# Actual installed validators, isolated stdlib-only. No invented completed budget.
ns={'require':b.require,'FORMAT':'ordered-mcm-batch-closure-v2'}
source=ast.parse((b.PACKAGE/'compact_mcm_batched.py').read_text())
for name in ('selected','validate'):
 node=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name==name);exec(compile(ast.Module(body=[node],type_ignores=[]),'actual_installed_schema6','exec'),ns)
assert ns['selected'](m)
try:ns['validate'](m,cap)
except ValueError as error:checks.append('actual_schema6_refuses_unresolved_capacity:'+str(error))
else:raise AssertionError('unresolved MCM capacity admitted')
tp=runpy.run_path(str(b.PACKAGE/'typed_payload_policy.py'))
oldtyped=json.loads((b.ROOT/a['baseline_inputs']['typed_payload']['path']).read_bytes());tp['validate'](oldtyped)
for key in bounds:
 for kind in tp['LEGACY_KINDS']:assert t['typed_payload']['graphs'][key]['kinds'][kind]==oldtyped['graphs'][key]['kinds'][kind]
 n=t['typed_payload']['graphs'][key]['kinds'][tp['BATCHED_KIND']];assert n['max_operations']==2*bounds[key]['groups'] and n['max_chunks']==3*bounds[key]['groups'] and n['max_recovered_bytes']==2*n['max_preserved_bytes']
try:tp['validate'](t['typed_payload'])
except ValueError as error:checks.append('actual_typed_validator_refuses_unresolved_capacity:'+str(error))
else:raise AssertionError('unresolved typed capacity admitted')
assert total['groups']==6352 and total['archive_tar_payload_upper_bound']==22488330240;checks.append('exact_group6352_tar22488330240')
assert m['schema_version']==6 and m['batched']['group_batches']==16 and m['batched']['retention']=='typed-grouped-recover-before-retire-v1'
for key,row in bounds.items():
 assert row['groups']==(row['batches']+15)//16 and row['offload_anchor_memory_bytes']==32*row['groups']
 assert t['typed_payload']['graphs'][key]['kinds'][tp['BATCHED_KIND']]['chunk_bytes']<=4*1024**2
history=t['archive_transport']['control_history'];assert history['success_control_bytes']==16384 and history['success_diagnostic_bytes']==2048 and history['shard_bytes']==4194304;checks.append('explicit_history_preserves_diagnostics_shard_freshness')
assert len(a['ancestry'])==len(a['ancestry_source_hex'])==26 and all(row['status']=='exact_original_public_source' and b.sha(bytes.fromhex(a['ancestry_source_hex'][Path(row['preserved_member']).name]))==row['sha256'] for row in a['ancestry']);checks.append('all26_original_source_bodies_hash_joined')
for role,body in a['original_metadata_hex'].items():assert b.sha(bytes.fromhex(body))==a['baseline_inputs'][role]['sha256']
checks.append('exact_original_import_claim_gate_stage_metadata_preserved')
assert a['capacity_constraints']['journal_body_max_bytes']==1024 and a['capacity_constraints']['ascii_path_max_bytes']==512 and a['capacity_constraints']['input_name_max_bytes']==128;checks.append('conditional_capacity_constraints_explicit')
# Known output route is actual local publication schema; no archived-output key.
assert set(t['mcm_output_policy'])=={'schema_version','backend','max_artifact_bytes','max_workflow_output_bytes'} and t['mcm_output_policy']['schema_version']==1
assert t['mcm_output_policy']['max_artifact_bytes']>=4*cap+8192 and t['mcm_output_policy']['max_workflow_output_bytes']>=7*(t['mcm_output_policy']['max_artifact_bytes']+8192);checks.append('local_output1_original_full_f32_bounds')
# The wrapped emitted files cannot silently be used as released policy objects.
for path in (H/'draft02').glob('*.template.json'):assert json.loads(path.read_text())['status']=='DRAFT_NOT_RELEASED'
assert all(not x.startswith(('numpy','torch','scipy')) for x in sys.modules);checks.append('no_numerical_imports')
report={'status':'PASS_METADATA_ONLY_DRAFT','checks':checks,'graph_count':7,'cells':total['cells'],'batches':total['batches'],'new_authority_or_admission':False,'actual_validators_accept_complete_successor':False,'affinity':sorted(os.sched_getaffinity(0))}
(H/'RESULT01.json').write_bytes(b.raw(report));print(json.dumps(report))
