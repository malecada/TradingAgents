"""Focused synthetic predecessor joins and exact entry deltas; no admission/run."""
import ast,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;MAIN=HERE.parents[3];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def predicate(root):
 tree=ast.parse((HERE/'preflight01.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='preceding_storage');scope={'Path':Path,'ROOT':root,'json':json,'file_hash':sha};exec(compile(ast.Module(body=[fn],type_ignores=[]),'preceding-storage-only','exec'),scope);return scope['preceding_storage']
def fixture(case):
 root=HERE/('synthetic-'+case);root.mkdir();inputs={}
 def put(role,v):
  p=root/(role+'.json');p.write_text(json.dumps(v));inputs[role]={'path':p.name,'sha256':sha(p)};return v
 old='real-pilot-second-graph-preservation-20261006-01';new='real-pilot-second-graph-preservation-metadata-20261006-01'
 expected=['research_artifacts/onchain-paper-replication-2026-09-24/sources/eth-paper-real-pilot-graph-20220509-20261005-01/aggregation/ledger.sqlite','research/onchain-paper-replication-2026-09-24/storage/'+old+'/11-recovered.bin']
 rows=[{'path':'synthetic-original-'+str(i),'bytes':i,'mode':436} for i in range(36)];rows[11]={'path':expected[0],'bytes':3599704064,'mode':436}
 selected=put('storage_selection',{'count':36,'files':rows,'total_bytes':sum(r['bytes'] for r in rows),'directories':[{'path':'synthetic-dir','mode':509}]})
 restore=put('storage_restore',{**rows[11],'remote_object':'old/11.bin','remote_restore':'old/11-restore.json'});put('storage_recovered_restore',restore);kept=put('storage_kept',{**restore,'original_retained':True,'recovered_body_retained':True,'body_roundtrip_verified':True})
 put('storage_body_get_receipt',{'status':'complete','returncode':0,'expected_bytes':3599704064,'received_bytes':3599704063 if case=='short-get' else 3599704064})
 put('storage_failed_native_final',{'phase':'complete' if case=='reclassified-old' else 'failed','child_exit_code':None,'cleanup_verified':True,'cgroup':str(root/'absent-old'),'monitor_pid':2**40})
 put('storage_failed_outer_exit',{'entry_selected_exit_code':1,'guard_child_exit_code':None});put('storage_failed_root_terminal',{'actual_root_tool_exit_code':1,'separate_actual_worker_exit_code':-15})
 failed=put('storage_failed_closure_review',{'decision':'accepted-failed-parent-partial-byte-evidence','identity':old,'parent_status':'failed','authenticated_body_get_count':36,'evidence':{v['path']:v['sha256'] for v in inputs.values()}})
 records=[dict(r) for r in rows];records[11]=kept
 union=put('storage_complete',{'identity':new,'parent':old,'parent_status':'FAILED','count':36,'files':records,'fresh_body_transfers':0,'fresh_restoration_metadata_rows':[35],'bytes_preserved':selected['total_bytes'],'directories':selected['directories'],'parent_proof':{'review':inputs['storage_failed_closure_review']}})
 put('storage_recovered_complete',union);put('storage_native_final',{'phase':'complete','child_exit_code':None if case=='unknown-new-child' else 0,'cleanup_verified':True,'cgroup':str(root/'absent-new'),'monitor_pid':2**40})
 put('storage_outer_exit',{'entry_selected_exit_code':0,'guard_child_exit_code':0,'cleanup_verified':True})
 put('storage_closure_review',{'decision':'accepted','identity':new,'full_scope_byte_recovery':True,'evidence':{inputs[k]['path']:inputs[k]['sha256'] for k in ('storage_complete','storage_recovered_complete','storage_native_final','storage_outer_exit')}})
 put('storage_retirement_complete',{'identity':'real-pilot-second-graph-ledger-retirement-20261006-01','payload_bytes_retired':7199408128,'removed':expected if case!='wrong-two-paths' else [expected[0],'unrelated.bin'],'preservation_union':new,'old_preservation_parent_status':'FAILED','remote_restore':kept,'arrays_retained':True,'all_other_originals_and_recoveries_retained':True})
 put('storage_retirement_root_exit',{'actual_root_exit_code':0});return root,inputs
results=[]
for case in ('accepted','reclassified-old','unknown-new-child','wrong-two-paths','short-get'):
 root,inputs=fixture(case)
 try:value=predicate(root)(inputs)
 except ValueError as e:
  expected={'reclassified-old':'permanent FAILED','unknown-new-child':'actual NEW','wrong-two-paths':'second-ledger retirement','short-get':'ledger11 restoration/get'}[case];assert expected in str(e);results.append({'case':case,'refused':str(e)})
 else:assert case=='accepted' and value['retired_bytes']==7199408128;results.append({'case':case,'pass':True})
changes=json.loads((HERE/'CHANGES01.json').read_bytes())
for name,c in changes.items():
 body=(HERE/name).read_text();assert sha(HERE/name)==c['after_sha256']
 for e in reversed(c['literal_edits']):assert body.count(e['after'])==1;body=body.replace(e['after'],e['before'])
 assert hashlib.sha256(body.encode()).hexdigest()==c['before_sha256']
assert not changes['launch01.py']['literal_edits']
prep=ast.parse((HERE/'prepare01.py').read_text());main=next(n for n in prep.body if isinstance(n,ast.FunctionDef) and n.name=='main')
closure=next(i for i,n in enumerate(main.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='preceding_storage')
writes=[i for i,n in enumerate(main.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='write'];assert closure<min(writes)
for flag in ('--union-review','--union-review-sha256'):
 calls=[n for n in ast.walk(main) if isinstance(n,ast.Call) and n.args and isinstance(n.args[0],ast.Constant) and n.args[0].value==flag];assert len(calls)==1 and any(k.arg=='required' and k.value.value is True for k in calls[0].keywords)
# Execute only original stdlib path enumeration, not imports/graph preparation.
job=MAIN/'tradingagents/research/onchain_replication/job.py';tree=ast.parse(job.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='required_sources');scope={'Path':Path,'__file__':str(job)};exec(compile(ast.Module(body=[fn],type_ignores=[]),'source-paths-only','exec'),scope);sources=scope['required_sources']();assert len(sources)==171 and len(sources)+7==178
telemetry={name:sha(MAIN/('tradingagents/research/onchain_replication/'+name)) for name in ('compact_mcm.py','real_pilot_import_caller.py','real_pilot_partial_progress.py')}
draft=MAIN/'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-third-graph-input-preparation01-2026-10-06/draft01/MAY16_DRAFT01.json';v=json.loads(draft.read_bytes());assert v['identity']=='eth-paper-real-pilot-graph-20220516-20261005-01' and v['parent'] is None and v['effective_budget_unchanged']==71
record={'cases':results,'all_literal_inverses':True,'launch_byte_unchanged':True,'closure_before_first_generated_write':True,'actual_package_source_count':len(sources),'prospective_total_source_count':178,'installed_telemetry_hashes':telemetry,'sealed_May16_draft_sha256':sha(draft),'no_gate_or_admission_or_native_execution':True,'qualification':'synthetic compact predecessor gate only; actual union outcome, retirement and capacity not established'};(HERE/'CHECK01.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
