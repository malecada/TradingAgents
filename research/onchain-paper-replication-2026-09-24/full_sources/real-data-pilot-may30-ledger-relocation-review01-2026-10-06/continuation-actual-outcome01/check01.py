from pathlib import Path
import json,hashlib,stat,os,subprocess,math
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';N='eth-paper-real-pilot-may30-ledger-continuation-20261006-01';T=F/'real-data-pilot-may30-ledger-continuation01-2026-10-06';B=F/'real-data-pilot-may30-ledger-continuation-bodyproof01-2026-10-06';P=R/'research_artifacts/onchain-paper-replication-2026-09-24';S=P/'sources'/N;D=P/'runs'/N;C=R/'research_runs'/N;O=Path(__file__).resolve().parent;E={}
def raw(p,h=None):
 assert p.resolve(strict=True)==p and p.is_file() and p.stat().st_nlink==1 and p.stat().st_size<4*1024**2
 b=p.read_bytes();v=hashlib.sha256(b).hexdigest()
 if h:assert v==h,(str(p),v,h)
 E[str(p.relative_to(R))]=v;return b
def obj(p,h=None):return json.loads(raw(p,h))
def sig(p):
 assert p.resolve(strict=True)==p
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1
 return [s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,stat.S_IMODE(s.st_mode)]
def put(n,v):(O/n).write_text(json.dumps(v,indent=2)+'\n')
root=obj(T/'ROOT_TERMINAL01.json','5950e19194f28c5c86b5f798cf21fb524504a5e121fe7f478f5f64d3354c7944');claim=obj(C/'claim.json','8b815f3f47dc0bd5b3e55c179c5049b13e59e365d6cee2fd558b3c23934109d6');complete=obj(C/'complete.json','5ad4ec18a7bfd877da8c59d13736a402f15cd1eccf8645fa14eb47208e478fde');gate=obj(T/'gate01.json',complete['registration_sha256']);experiment=gate['experiments'][N]
assert claim['experiment']==experiment and claim['source']==claim['design_source']==complete['source']==root['source_commit']=='4eb9752bbb812a029480d83bcaf9ed7c4d7e3ef8'
assert complete['claim_sha256']==E[str((C/'claim.json').relative_to(R))] and claim['effective_attempt_budget']==72 and claim['bindings'] is claim['bindings_sha256'] is None
assert claim['experiment_id']==complete['experiment_id']==root['identity']==N and complete['status']=='complete' and complete['cell_count']==1 and complete['unavailable_count']==0
for p,h in experiment['source_files'].items():raw(R/p,h)
for ref in claim['inputs'].values():raw(R/ref['path'],ref['sha256'])
from tradingagents.research.onchain_replication.environment import inventory
assert inventory(R)==obj(R/claim['inputs']['environment']['path'])
for p,h in complete['output_sha256'].items():raw(C/'outputs'/p,h)
assert set(complete['output_sha256'])==set(experiment['outputs'])
assert obj(C/'outputs/cell-ledger.json')==complete['cells'];cell=complete['cells'][0]
assert cell['id']=='graph-2022-05-30' and cell['status']=='complete' and cell['continued_from']=='eth-paper-real-pilot-graph-20220530-20261005-01'
assert cell['raw_count']==7507236 and cell['admitted_count']==3548344 and cell['source_rows_redecoded']==0 and cell['admitted_count']+sum(cell['exclusion_counts'].values())==cell['raw_count']
index=obj(C/'outputs/artifact-index.json');proof=obj(B/'BODY_HASH01.json','0a503d5637c4a6d53e7916b9def287add75d2bdff8e48a38964c32585870d82a');tool=obj(B/'ACTUAL_PASS_TOOL01.json','3055417eea1a3b732f9fd804ff10b1a64e01f905e02d93efbb566a00a36a741b')
assert tool['actual_exit_code']==0 and tool['actual_completion_chunk']=='308d5a' and tool['proof']['sha256']==E[str((B/'BODY_HASH01.json').relative_to(R))]
assert proof['status']=='passed' and proof['identity']==N and proof['prior_import_error']['body_reads']==0 and proof['prior_import_error']['exit_code']==1
man=obj(R/cell['manifest_path'],cell['manifest_sha256']);coverage=obj(R/cell['coverage_path'],cell['coverage_sha256']);assert proof['manifest']=={'path':cell['manifest_path'],'sha256':cell['manifest_sha256']}
assert len(proof['arrays'])==len(man['arrays'])==5 and sum(a['bytes'] for a in proof['arrays'].values())==proof['bytes_read']==432741928
assert (proof['nodes'],proof['edges'])==(1581441,2426106)
shapes={'node_features':([1581441,4],'float64',8),'node_ids':([1581441],'<U42',168),'edge_index':([2,2426106],'int64',8),'edge_features':([2426106,2],'float64',8),'edge_aggregates':([2426106,2],'float64',8)}
rows=[]
for key,a in proof['arrays'].items():
 q=R/a['path'];v=sig(q);assert v==a['stat_identity_before']==a['stat_identity_after']
 assert man['arrays'][key]=={'path':q.name,'bytes':a['bytes'],'sha256':a['sha256']} and index[a['path']]=={'bytes':a['bytes'],'sha256':a['sha256']}
 head=a['header'];shape,dtype,width=shapes[key];assert head=={'dtype':dtype,'fortran_order':False,'payload_offset':128,'shape':shape,'version':[1,0]}
 assert 128+math.prod(shape)*width==a['bytes']==v[3]
 rows.append({'path':a['path'],'bytes':a['bytes'],'sha256':a['sha256'],'mode':v[6],'stat_identity7':v,'header':head})
for path,d in index.items():
 if not path.endswith('.npy'):assert len(raw(R/path,d['sha256']))==d['bytes']
assert len(index)==10 and {str(q.relative_to(R)) for q in S.rglob('*') if q.is_file()}==set(index)
assert coverage['claim_sha256']==complete['claim_sha256'] and coverage['graph_manifest_sha256']==cell['manifest_sha256'] and coverage['plan_sha256']==claim['inputs']['continuation_plan']['sha256']
assert len(coverage['members'])==7 and sum(x['expected_rows'] for x in coverage['members'])==7507236 and sorted(x['sha256'] for x in coverage['members'])==cell['source_hashes']
meta=man['metadata'];assert meta['source_hashes']==cell['source_hashes'] and meta['raw_count']==cell['raw_count'] and meta['admitted_count']==cell['admitted_count'] and meta['exclusion_counts']==cell['exclusion_counts']
summary=obj(C/'outputs/source-summary.json');assert summary==obj(S/'result.json') and summary['predecessor_status']=='failed' and summary['source_rows_inherited']==7507236 and summary['source_rows_redecoded']==0 and summary['financial_run_admitted'] is False and summary['workspace'] is None
intent=obj(S/'intent.json');assert intent['claim_sha256']==complete['claim_sha256'] and intent['source_commit']==claim['source'] and intent['no_source_reingestion'] is True
oldfail=obj(R/claim['inputs']['old_failed']['path'],claim['inputs']['old_failed']['sha256']);assert oldfail['status']=='failed'
assert not (C/'failed.json').exists()
guard=obj(D/'guard/final.json',root['guard_final_sha256']);child=obj(D/'guard/child_exit.json');outer=obj(T/'outer-exit01.json');observer=obj(D/'observer.json');owner=obj(D/'owner.json');launch=obj(D/'launch.json')
assert root['actual_root_tool_exit_code']==outer['exit_code']==guard['child_exit_code']==child['exit_code']==0 and guard['phase']=='complete' and guard['cleanup_verified'] is True and guard['cleanup_stop_returncode']==5
assert observer['terminal_sha256']==E[str((C/'complete.json').relative_to(R))] and observer['owner_sha256']==E[str((D/'owner.json').relative_to(R))] and observer['all_cells_complete'] is observer['cgroup_empty'] is True and observer['financial_completion'] is False
assert owner==guard['owner_identity'] and owner['source_commit']==claim['source'] and owner['nonce']==launch['nonce']
for p,h in observer['evidence_sha256'].items():raw(D/p,h)
known=set(root['selected_recorded_pids'])|{child['workload_pid']}|{int(x) for x in guard['cpu_thread_readback']}
assert all(not Path('/proc',str(pid)).exists() for pid in known) and not Path(guard['cgroup']).exists()
u=subprocess.check_output(['systemctl','--user','show',guard['unit'],'--property=ActiveState,SubState,MainPID,ControlGroup'],text=True);props=dict(x.split('=',1) for x in u.splitlines());assert props=={'MainPID':'0','ControlGroup':'','ActiveState':'inactive','SubState':'dead'}
assert guard['elapsed_seconds']==170.91376929399848 and guard['memory_events']=={'high':0,'low':0,'max':0,'oom':0,'oom_group_kill':0,'oom_kill':0} and guard['memory_swap_max_bytes']==0 and len(guard['cpus'])==2
job=obj(T/'execution-job01.json')
for k,v in job['resources'].items():assert guard[k]==v
for n in ['launch-attempt01.json','PREFLIGHT_ACTUAL01.json','REMOTE_CONFIRMATION01.json','RELEASE_REVIEW01.json']:obj(T/n)
put('CURRENT_BODY_STAT_JOINS01.json',{'identity':N,'body_proof':tool['proof'],'rows':rows,'reviewer_payload_reads':0,'scope':'Fresh current stat/header-descriptor/manifest joins to Root one-pass proof; no second header or body read.'})
E[str((O/'CURRENT_BODY_STAT_JOINS01.json').relative_to(R))]=hashlib.sha256((O/'CURRENT_BODY_STAT_JOINS01.json').read_bytes()).hexdigest()
review={'decision':'accepted','identity':N,'status':'complete','source':claim['source'],'claim_sha256':complete['claim_sha256'],'terminal_sha256':E[str((C/'complete.json').relative_to(R))],'graph_manifest_sha256':cell['manifest_sha256'],'complete_cells':1,'unavailable_cells':0,'original_failed_parent_retained':True,'actual_root_exit_code':0,'actual_outer_exit_code':0,'original_guard_child_exit_code':0,'original_guard_cleanup_verified':True,'original_cleanup_stop_returncode':5,'original_selected_recorded_pids':root['selected_recorded_pids'],'all_known_recorded_pids_checked_absent':sorted(known),'lifetime_pid_history_complete':False,'cgroup_absent':True,'current_unit':props,'source_rows_inherited':7507236,'source_rows_redecoded':0,'admitted_count':3548344,'nodes':1581441,'edges':2426106,'payload_count':5,'payload_bytes':432741928,'scientific_bindings':None,'native_supervisor_owner_receipt_present':True,'financial_completion':False,'accounting':{'spent_after':42,'effective_ceiling':72,'unused':30,'original_failure_refunded':False},'native_seconds':guard['elapsed_seconds'],'sampled_peak_current_bytes':guard['peak_sampled_memory_current_bytes'],'last_unit_kernel_peak_bytes':guard['optional_memory_telemetry']['unit']['kernel_peak_bytes'],'memory_telemetry_qualification':guard['optional_memory_telemetry']['qualification'],'evidence':E,'qualification':'Actual one graph completion and metadata/body-proof joins only. Root one-pass opaque arrays proof inherited with exact current stats; reviewer performed no payload/SQL/numerical reads or rerun. No scientific Owner synthesized; genuine native supervisor owner remains distinct from null research bindings. External preservation/recovery of this new increment remains pending. No MCM/model/fit/financial/full-pilot capacity conclusion.'}
put('OUTCOME_REVIEW01.json',review)
print(json.dumps({'decision':'accepted','outcome_sha256':hashlib.sha256((O/'OUTCOME_REVIEW01.json').read_bytes()).hexdigest(),'known_pids':sorted(known),'payload_reads':0,'nodes':1581441,'edges':2426106}))
