"""Actual failed closure; structural/hash metadata only, never numerical replay."""
import hashlib,importlib.abc,importlib.util,json,os,pathlib,subprocess,sys
P=pathlib.Path(__file__).resolve().parent;F=P.parent;A=F/'neural-cold-feature-handoff-root-compare-request02-2026-10-03';C=pathlib.Path('/home/malecada/master_thesis/onchain-fixture-isolation/neural-cold-proof-native-20261003-02/source');I='compact-cold-comparison-20261003-01';FIRST='compact-cold-inputs-20261003-01';B='361339125a3f1cd57e7ba8611f5a994ae649fa0b';G=C/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/I/'guard';O=C/'proof_outer'/I;S=C/'proof_supervise'/I;W=pathlib.Path('/home/malecada/master_thesis/onchain-fixture-isolation/compact-cold-root-launches-20261003')/I;PAR=A/'actual-parent-wait01';R=C/'research_runs'/I;E=C/'research_artifacts/compact-cold-engineering-20261003'/I
assert pathlib.Path.cwd()==C;refs={};sha=lambda b:hashlib.sha256(b).hexdigest()
def doc(p):
 b=p.read_bytes();assert len(b)<=4194304;refs[str(p)]={'sha256':sha(b),'bytes':len(b)};return json.loads(b)
os.environ.update(GIT_NO_LAZY_FETCH='1',GIT_NO_REPLACE_OBJECTS='1',GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='protocol.allow',GIT_CONFIG_VALUE_0='never')
def git(*args):return subprocess.check_output(['git',*args],cwd=C,timeout=10)
assert git('rev-parse','HEAD').decode().strip()==B
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.split('.')[0] in {'numpy','torch','scipy','pandas','pyarrow'}:raise RuntimeError('no numerical import')
sys.meta_path.insert(0,Block());sys.path.insert(0,str(C));from tradingagents.research.verify import verify_claim,verify_run
claim=verify_claim(R);vr=verify_run(R);firstvr=verify_run(C/'research_runs'/FIRST);assert vr['status']=='failed' and vr['output_count']==0 and firstvr['status']=='complete'
failed=doc(R/'failed.json');assert failed['claim_sha256']==sha((R/'claim.json').read_bytes())=='6a9e5932716d102c4821d75a6023be892a47996b93efe6f94cea66dff8325048';assert failed['reason']=='SystemExit: owned execution interrupted; never relaunch this identity';assert not (R/'complete.json').exists() and not list((R/'outputs').iterdir())
assert claim['source']==B and len(claim['inputs'])==44 and claim['experiment']['cells']==['cold-genuine-comparison'];assert sorted(claim['experiment']['outputs'])==['binding.json','cold-handoff.json','journal.json','proof-compare.json']
assert claim['family']['attempt_budget']==2 and claim['family']['prior_attempts']==0
for name,r in claim['inputs'].items():assert sha((C/r['path']).read_bytes())==r['sha256']
assert set(p.name for p in (C/'research_runs').iterdir())=={'.lock',FIRST,I}
inv=doc(C/'cold_prep/source_inventory.json');assert len(inv['source_inventory'])==195
for r in inv['source_inventory']:
 b=(C/r['target']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256'] and git('show',B+':'+r['target'])==b
anchor=doc(C/'cold_prep/anchor.json');assert len(anchor['files'])==147
for n,h in anchor['files'].items():assert sha((C/n).read_bytes())==h and sha(git('show',anchor['commit']+':'+n))==h
runtime=doc(C/'cold_prep/runtime.json');assert len(runtime['distribution_records'])==251
spec=importlib.util.spec_from_file_location('review_runtime',C/'proof_tools/runtime_gate01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);runtime_result=m.check(C,runtime)
final=doc(G/'final.json');child=doc(G/'child_exit.json');ready=doc(G/'cpu_ready.json');owner=doc(G.parent/'owner.json');launch=doc(G.parent/'launch.json');assert final['phase']=='failed' and final['limit_reason']=='RuntimeError: registered wall-clock limit exceeded' and final['child_exit_code'] is None
assert final['cleanup_verified'] is True and final['cleanup_stop_returncode']==0 and final['cleanup_unit_properties']=={'ActiveState':'failed','ControlGroup':'','ExecMainStatus':'125','Result':'timeout','SubState':'failed'}
assert child['exit_code']==125 and child['reason']=='signal' and child['terminal_memory_snapshot']['memory_events']==final['memory_events'];assert not any(final['memory_events'].values());assert final['kernel_controls']=={'memory.high':'3221225472','memory.max':'3221225472','memory.swap.max':'0'}
assert final['native_unit_properties']=={'LimitFSIZE':'4194304','LimitFSIZESoft':'4194304','RuntimeMaxUSec':'30min'}
assert final['owner_identity']==owner and owner['source_commit']==B and owner['experiment']==I and owner['monitor_pid']==final['monitor_pid'] and all(owner[k]==v for k,v in launch.items())
pw=doc(PAR/'wait.json');pi=doc(PAR/'intent.json');pc=doc(PAR/'child.json');pf=doc(PAR/'failure.json');wi=doc(W/'intent.json');wc=doc(W/'child.json');wo=doc(W/'observation.json');wf=doc(W/'failure.json');sc=doc(S/'claim.json');sch=doc(S/'child.json');se=doc(S/'exit.json');sl=doc(S/'late-failure.json');oi=doc(O/'intent.json');osp=doc(O/'supervisor.json');of=doc(O/'failed.json');ol=doc(O/'late-failure.json');disp=doc(O/'disposition.json')
assert pw['wrapper_exit_code']==1 and pw['wrapper_pid']==pc['pid']==wi['parent_pid'];assert pw['source']==B and pw['request']==wo['request']==wi['request'];assert pw['command']==pc['command']==pi['command'];assert pw['identity']==I and pw['output_root']==str(W)
assert pf['wrapper_exit_code']==1 and pf['child_terminal_synthesized'] is False and wf['revokes_observation'] is True and not (W/'tail-complete.json').exists()
assert wo['source']==B and wo['supervisor_exit_code']==1 and wo['result'] is None and wo['disposition']=='actual-failed-receipt-present';assert wc['pid']==sc['owner_pid']==se['supervisor_pid']
assert sch['pid']==se['controller_pid']==oi['caller_pid'] and se['controller_exit_code']==1 and se['controller_pid_absent'] is True and se['accepted_receipt'] is None and se['status']=='failed'
assert of['status']==ol['status']==sl['status']=='failed' and disp['observed_disposition']=='lifecycle_failed' and disp['synthetic_lifecycle_receipt'] is False;assert not (O/'accepted.json').exists()
for r in wo['original_receipts'].values():assert sha(pathlib.Path(r['path']).read_bytes())==r['sha256']
for n,r in se['controller_logs'].items():assert sha((C/r['path']).read_bytes())==r['sha256'] and (C/r['path']).stat().st_size==r['bytes']
active=doc(P/'active-guard-observation01.json');pids={pi['parent_pid'],pc['pid'],wc['pid'],sc['owner_pid'],sch['pid'],oi['caller_pid'],osp['pid'],owner['monitor_pid'],owner['supervisor_pid'],ready['pid'],child['workload_pid'],*map(int,final['cpu_thread_readback']),*map(int,active['cpu_thread_readback'])};assert all(not pathlib.Path('/proc',str(pid)).exists() for pid in pids);assert not pathlib.Path(final['cgroup']).exists()
unit=subprocess.run(['systemctl','--user','show',final['unit'],'--property=ActiveState,SubState,Result,ExecMainStatus,ControlGroup'],capture_output=True,timeout=10);assert unit.returncode==0;(P/'UNIT_PROPERTIES01.txt').write_bytes(unit.stdout);assert b'ControlGroup=\n' in unit.stdout and b'ActiveState=failed\n' in unit.stdout
# Original partial stage metadata: verify declared cardinality; not score values,
# scientific publication authority or trajectory/tensor equivalence.
plan=doc(C/claim['inputs']['plan']['path']);descriptor=plan['producers']['synthetic-producer']['descriptor'];required=descriptor['required_graphs'];assert len(required)==18
bases=list((C/'research_artifacts/onchain_representations').glob('*/'+I+'/compact'));assert len(bases)==1;stages=bases[0];assert {p.name for p in stages.iterdir() if p.is_dir()}=={'dictionary',*('mcm-'+h for h in required)}
stage_rows=[]
for name in sorted({'dictionary',*('mcm-'+h for h in required)}):
 p=stages/name/'stage-complete.json';v=doc(p);expected=992 if name=='dictionary' else 128;assert v['completed_pairs']==expected and v['execution_admitted'] is False
 stage_rows.append({'path':str(p.relative_to(C)),'sha256':sha(p.read_bytes()),'recorded_completed_pairs':v['completed_pairs'],'execution_admitted':v['execution_admitted']})
assert doc(E/'failed.json')=={'retained':True,'status':'failed','type':'SystemExit'};assert not (E/'complete.json').exists();assert not list(E.rglob('*.pt'))
result={'schema_version':1,'status':'ACCEPTED_AS_CLOSED_FAILED_NOT_SCIENTIFIC_SUCCESS','source':B,'identity':I,'claim_sha256':sha((R/'claim.json').read_bytes()),'failed_sha256':sha((R/'failed.json').read_bytes()),'actual_verify_run':vr,'original_materialize_verify_run':firstvr,'registered_failed_cell':'cold-genuine-comparison','registered_outputs_missing':claim['experiment']['outputs'],'completed_comparison_cells':0,'registered_comparison_cells_without_success':1,'count_qualification':'Separate reviewer denominator; original failed terminal has no fabricated cells/output records. verify_run failed count0 is structural, not removal of registered one cell.','family_declared':claim['family'],'actual_complete_claims':1,'actual_failed_claims':1,'budget_exhausted':True,'elapsed_native_seconds':final['elapsed_seconds'],'limit_reason':final['limit_reason'],'peak_sampled_memory_current_bytes':final['peak_sampled_memory_current_bytes'],'guard_final_child_exit':None,'separate_child_exit':125,'native_result':'timeout','all_memory_events':final['memory_events'],'native_cleanup_verified':True,'recorded_original_pids_tids_absent':sorted(pids),'cgroup_absent':final['cgroup'],'source_count':195,'anchor_count':147,'inputs':44,'runtime_records':251,'raw_stage_completion_metadata':stage_rows,'stage_pair_total_reported':sum(x['recorded_completed_pairs'] for x in stage_rows),'raw_stage_qualification':'Original low-level metadata presence and counts only; no decoded score validation, no accepted scientific Published/terminal or numerical comparison.','numerical_comparison_reports_or_checkpoints_present':False,'memory_saving_proved':False,'full_graph_capacity_proved':False,'financial_fits_completed':0,'raw_refs':refs,'no_numerical_import_admission_start_replay_or_original_mutation':True}
assert not any(n.split('.')[0] in {'numpy','torch','scipy','pandas','pyarrow'} for n in sys.modules)
(P/'READBACK01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['raw_refs','raw_stage_completion_metadata']},indent=2))
