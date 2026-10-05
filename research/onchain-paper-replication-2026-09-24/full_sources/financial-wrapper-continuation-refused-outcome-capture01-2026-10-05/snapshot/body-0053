"""Actual pre-workload resource refusal, opaque metadata only; no native imports."""
from pathlib import Path
import ast,json,os,sys
H=Path(__file__).resolve().parent;F=H.parent
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-canonical-plan-root-launch-20261005-01')
ID='financial-wrapper-classification-eager-continue100-compatibility-20261004-01';A=P/'attempt';B=CAP/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/ID
sys.path.insert(0,str(F/'financial-wrapper-compatibility-complete100-recovery-review01-2026-10-05'))
from verify_capture01 import Reader,R
rd=Reader();pins={}
def raw(p,h=None):
 b=rd.read(p,h);pins[str(p)]={'sha256':R.digest(b),'bytes':len(b)};return b
def val(p,h=None):return json.loads(raw(p,h))
q=val(P/'REQUEST_FINAL01.json','a9a04d60abced0ae01f192a7fc3897bf3972891d374a98f33f15522b8dc20e18');rd.need(q['identity']==ID and q['source']=='d4c81c0961342bfe4c5771aabbef1d46a14cffb8','exact admitted source/request')
prior=F/'financial-wrapper-continuation-canonical-plan-review01-2026-10-05';val(prior/'MACHINE01.json','d1b306b9866457f644bce393cfd475f2ebdc4914fc617916fc1c6e2b309d426b');val(prior/'MANIFEST01.json','a303ce50f87dbbd21d57062be0694b6f8efdd461781bfc695b84936fead75798')
for ref in q['proofs'].values():raw(Path(ref['path']),ref['sha256'])
raw(Path(q['final_review']['path']),q['final_review']['sha256']);caller=raw(P/'parent01.py',q['caller_sha256'])
terminal=val(A/'parent-terminal.json');intent=val(A/'intent.json');spawn=val(A/'spawn.json');cleanup=val(A/'owned-tree-cleanup.json')
guard=val(B/'guard/final.json','ad31c6850e294954667b9148ee6f919302d5c691a0ae92c6e2ed8df10c9a76d5');rd.need(raw(B/'guard/live.json')==raw(B/'guard/final.json'),'actual final/live bytes identical')
owner=val(B/'owner.json');launch=val(B/'launch.json');observer=val(B/'observer.json');child=val(B/'guard/child_exit.json');ready=val(B/'guard/cpu_ready.json');filelimit=val(B/'monitor-file-limit.json')
rd.need(observer['status']=='not_admitted' and observer['owner_sha256']==pins[str(B/'owner.json')]['sha256'],'genuine not-admitted observer and actual Owner bytes')
for n,h in observer['evidence_sha256'].items():raw(B/n,h)
rd.need(set(observer)=={'status','owner_sha256','evidence_sha256'},'no fabricated lifecycle terminal')
rd.need(json.loads(raw(A/'stdout'))==observer and raw(A/'stderr')==b'' and raw(B/'guard/child.log')==b'','actual output and empty logs')
rd.need(terminal['actual_child_exit']==1 and terminal['actual_parent_exit'] is None and terminal['error_type'] is None and not terminal['outcome_semantics_accepted'] and not terminal['planned_interrupt_requested'] and not terminal['primary_exception_observed'],'actual supervisor1/null Parent semantics preserved')
rd.need(terminal['identity']==ID and terminal['source']==q['source'] and terminal['supervisor_result']['pid']==spawn['pid']==launch['supervisor_pid'],'actual launch identity chain')
rd.need(spawn['argv']==intent['command'] and intent['contract']==R.digest(R.encode({k:v for k,v in q.items() if k!='final_review'})) and intent['phase']=='continue100','exact original actual dispatch/core')
rd.need(intent['preclaim_metadata']['metadata_bytes_read']==7997640 and intent['preclaim_metadata']['input_hashes']==q['input_hashes'] and not intent['preclaim_metadata']['checkpoint_decoded'],'actual launch repeated exact public metadata preflight')
rd.need(guard['owner_identity']==owner and {k:owner[k] for k in launch}==launch and guard['command'][5]=='worker','genuine owner/launch/guard joins')
rd.need(guard['phase']=='failed' and guard['limit_reason']=='RuntimeError: host reserve fell during cgroup setup' and guard['retry'] is False and guard['child_exit_code'] is None,'genuine retained guard refusal, child null not replaced')
rd.need(guard['host_mem_available_bytes']==6437638144 and guard['start_reserve_bytes']==6442450944 and guard['start_reserve_bytes']-guard['host_mem_available_bytes']==4812800,'exact startup shortfall')
rd.need(child['exit_code']==125 and child['reason']=='signal before release' and child['workload_pid'] is None and child['snapshot_error'] is None and not os.path.lexists(B/'guard/release.json'),'actual pre-release child terminal, no numerical workload admitted')
reg=val(CAP/q['registration'],q['registration_sha256']);exp=reg['experiments'][ID];job=val(CAP/exp['inputs']['execution_job']['path'],exp['inputs']['execution_job']['sha256']);plan=val(CAP/exp['inputs']['wrapper_plan']['path'],exp['inputs']['wrapper_plan']['sha256'])
for k,v in job['resources'].items():rd.need(guard[k]==v,'unchanged actual registered resource '+k)
rd.need(guard['kernel_controls']=={'memory.high':'3221225472','memory.max':'3221225472','memory.swap.max':'0'} and ready['file_size_limit']==[4194304,4194304] and guard['native_unit_properties']['LimitFSIZE']==guard['native_unit_properties']['LimitFSIZESoft']=='4194304','actual enforced native memory/file caps')
rd.need(ready['cpus']==guard['cpus']==[0,1] and all(v==[0,1] for v in guard['cpu_thread_readback'].values()) and not guard['cpu_quota_controller_available'],'actual affinity, unavailable quota controller explicit')
rd.need(guard['storage_peak_allocated_bytes']<=1073741824 and guard['storage_peak_logical_file_bytes']<=1073741824 and guard['storage_peak_entries']<=32768 and all(v>=10737418240 for v in guard['disk_free_bytes'].values()) and guard['elapsed_seconds']<1800 and terminal['supervisor_result']['elapsed_seconds']<1840,'sampled storage/floor/elapsed bounds')
rd.need(not any(guard['memory_events'][k] for k in ('oom','oom_kill')),'no recorded OOM event')
missing=[CAP/'research_runs'/ID,CAP/'research_artifacts/onchain_fit_cells'/R.digest(plan['cell_id'].encode())/ID,CAP/'research_artifacts/financial_wrapper_engineering'/plan['namespace'],B/'guard/release.json']
rd.need(all(not os.path.lexists(p) for p in missing),'no lifecycle claim/fit/wrapper/workload release namespace')
# Inspect pinned source ordering; do not import or execute these numerical modules.
sources={}
for n in ('resources.py','job.py','financial_wrapper_fixture.py','training.py'):
 name='tradingagents/research/onchain_replication/'+n;sources[n]=raw(CAP/name,q['source_files'][name]).decode();ast.parse(sources[n])
resource=sources['resources.py'];rd.need(resource.index("raise RuntimeError('host reserve fell during cgroup setup')")<resource.index("state['phase'] = 'running'",resource.index("raise RuntimeError('host reserve fell during cgroup setup')"))<resource.index("_native_atomic(receipt/'release.json'"),'startup refusal precedes native release publication')
js=sources['job.py'];rd.need(js.index('live = resources.assert_guarded_worker',js.index('def worker'))<js.index('with ResearchRun.start',js.index('def worker')) and "if not (run_dir/'claim.json').exists():\n        result = {'status': 'not_admitted'" in js,'actual guarded worker before lifecycle; observer absence branch')
cl=terminal['cleanup'];rd.need(cl['subreaper_cleanup_sha256']==pins[str(A/'owned-tree-cleanup.json')]['sha256'] and cl['cgroup']==guard['cgroup'] and cl['unit']==guard['unit'] and cl['cgroup_absent'] and cl['joined_unit_stopped'] and cl['native_pid_census_is_complete_history'] is False and cl['native_pid_start_records']==[],'actual cleanup joins and honest incomplete history')
rd.need(cleanup['subreaper_used'] and cleanup['dedicated_no_preexisting_children'] and cleanup['remaining_original_identities']==[],'actual owned descendants cleanup')
pids={owner['monitor_pid'],launch['supervisor_pid'],ready['pid']};groups=set()
for row in cleanup['owned_pid_start_records']:pids.add(row['pid']);groups.add(row['pgrp'])
operations={}
for label,op in cl['actual_control_operations'].items():
 out=raw(A/label/'stdout');err=raw(A/label/'stderr');ct=val(A/label/'owned-tree-cleanup.json');rd.need(out.decode()==op['stdout'] and err.decode()==op['stderr'] and len(out)==op['stdout_bytes'] and len(err)==op['stderr_bytes'] and op['exit_code']==0,'actual control operation bytes and result')
 rd.need(ct['remaining_original_identities']==[] and ct['subreaper_used'],'control children cleaned');pids.add(op['pid'])
 for row in ct['owned_pid_start_records']:pids.add(row['pid']);groups.add(row['pgrp'])
 operations[label]={'exit_code':op['exit_code'],'pid':op['pid'],'stdout_sha256':R.digest(out),'stderr_sha256':R.digest(err)}
rd.need(set(operations)=={'before','stop','after'} and not os.path.lexists(cl['cgroup']),'actual controls and absent cgroup')
for pid in pids:rd.need(not os.path.lexists(Path('/proc')/str(pid)),'recorded PID absent')
# Use the accepted external raw proc reader, with its owned FD cleanup.
remote=F/'financial-wrapper-continuation-canonical-remote01-2026-10-05';rc=raw(remote/'caller01.py','159d99cee4623d4d7c5ad86f5019be6f686f842725f3a12ae4359eec1df28b12');node=next(n for n in ast.parse(rc).body if isinstance(n,ast.FunctionDef) and n.name=='raw');ns={'os':os,'FILE':4194304};exec(compile(ast.Module(body=[node],type_ignores=[]),'<accepted proc reader>','exec'),ns)
for p in Path('/proc').iterdir():
 if p.name.isdigit():
  try:b=ns['raw'](p/'stat');rd.total+=len(b);rd.tick()
  except (FileNotFoundError,ProcessLookupError,PermissionError):continue
  rd.need(int(b.decode().rsplit(')',1)[1].split()[2]) not in groups,'recorded process group absent')
# Retain literal complete changed evidence namespaces, without rereading old CAP.
manifest={}
for label,root in [('Parent_attempt',A),('native_run',B)]:
 m=R.scan(root);rd.tree(root,m)
 for row in m['members']:
  if row['kind']=='file':raw(root/row['path'],row['sha256'])
 manifest[label]={'root':str(root),'manifest':m}
rootref=json.loads((H/'ACTUAL_ROOT_EXIT_REF01.json').read_bytes());ar=val(Path(rootref['path']),rootref['sha256']);rd.need(ar['actual_root_exit_code']==1 and ar['actual_root_tool_session']==25715 and ar['terminal_chunk']=='584196' and ar['original_parent_exit_remains_null'] and ar['original_parent_terminal_sha256']==pins[str(A/'parent-terminal.json')]['sha256'],'separate actual Root exit1 and original terminal pin')
rd.finish();result={'schema_version':1,'decision':'ACCEPTED_ACTUAL_NOT_ADMITTED_STARTUP_RESOURCE_REFUSAL','source':q['source'],'identity':ID,'actual_root_exit':1,'actual_root_exit_ref':rootref,'actual_supervisor_child_exit':1,'original_Parent_exit':None,'native_guard_child_exit':None,'actual_launcher_exit':125,'workload_pid':None,'reason':guard['limit_reason'],'host_available_bytes':guard['host_mem_available_bytes'],'startup_required_bytes':guard['start_reserve_bytes'],'shortfall_bytes':4812800,'lifecycle_claim_created':False,'lifecycle_failed_terminal_created':False,'completed_continuation':False,'resumed_optimizer_updates':0,'final_comparison_performed':False,'final_checkpoint':None,'paper_fit_credit':0,'recorded_PIDs_absent':sorted(pids),'recorded_groups_absent':sorted(groups),'cgroup_absent':True,'native_process_history_complete':False,'control_operations':operations,'absent_namespaces':[str(p) for p in missing],'namespace_reuse_authorized':False,'retry_authorized':False,'caps_relaxed':False,'actual_evidence_pins':pins,'complete_changed_namespaces':manifest,'new_financial_claim_count':0,'previous_accounting_reused':'one COMPLETE,three FAILED,four spent,highest20/effective20,16 remaining; terminal launch namespace separately retained','runtime_evidence_reused':True,'checkpoint_decoded':False,'checks':rd.checks,'read_bytes':rd.total}
R.put(H/'OUTCOME_READBACK01.json',result);print(json.dumps({'decision':result['decision'],'sha256':R.digest(R.encode(result)),'checks':rd.checks,'read_bytes':rd.total}))
