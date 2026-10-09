import pathlib,json,hashlib,subprocess,collections,datetime
R=pathlib.Path(__file__).resolve().parent;F=R.parent;ROOT=pathlib.Path.cwd();E=F/'real-data-pilot-full24-entry01-2026-10-09';name='eth-paper-real-data-end-to-end-resource-20261009-24';L=ROOT/'research_runs'/name;N=ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/name
j=lambda p:json.loads(pathlib.Path(p).read_bytes());h=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest();evidence={}
def load(p):evidence[str(p.relative_to(ROOT))]=h(p);return j(p)
claim=load(L/'claim.json');failed=load(L/'failed.json');assert failed['claim_sha256']==h(L/'claim.json') and failed['status']=='failed' and claim['effective_attempt_budget']==95
assert failed['reason']=='ValueError: numerical source closure differs'
outputs={}
for n,digest in failed['output_sha256'].items():assert h(L/'outputs'/n)==digest;outputs[n]=load(L/'outputs'/n)
s=outputs['pilot-summary.json'];assert outputs['cell-ledger.json']==[s['cell']] and s['cell']['status']=='failed' and s['training'] is None and s['retained_target_count']==0 and s['events']==[]
t=s['throughput'];assert len(t['graphs'])==7 and t['unavailable_graphs']==7 and t['complete_graphs']==t['failed_graphs']==t['attempted_mcm_seconds']==0
assert sum(g['expected_motif_cells'] for g in t['graphs'])==415968128
for g in t['graphs']:assert g['status']=='unavailable' and g['reason']=='not_attempted_after_failure' and g['completed_motif_cells'] is None and g['elapsed_seconds'] is None
assert outputs['archive-terminal.json']['status']=='failed' and outputs['archive-terminal.json']['spent']=={'commands':0,'logical_bytes':0,'rounded_bytes':0}
guard=load(N/'guard/final.json');owner=load(N/'owner.json');launch=load(N/'launch.json');observer=load(N/'observer.json');child=load(N/'guard/child_exit.json');cpu=load(N/'guard/cpu_ready.json');io=load(E/'ROOT_IO_CLOSED01.json');storage=load(E/'FINAL_STORAGE01.json');early=load(E/'RESOURCE_OBSERVATION01.json')
assert guard['cleanup_verified'] and guard['child_exit_code']==child['exit_code']==io['actual_parent_exit_code']==1
assert io['supervisor_reaped'] and io['outer_log_handles_closed'] and io['supervisor_pid']==launch['supervisor_pid']==owner['supervisor_pid']
assert owner['monitor_pid']==guard['monitor_pid'] and owner['nonce']==launch['nonce']
assert claim['source']==launch['source_commit']==storage['source']=='b05fe1d90fdc0952d0293e72793474de884b1201'
assert observer['owner_sha256']==h(N/'owner.json') and observer['cgroup_empty'] and observer['status']=='failed'
for n,digest in observer['evidence_sha256'].items():assert h(N/n)==digest
for k,n in [('guard','guard/final.json'),('launch','launch.json'),('owner','owner.json')]:assert storage['original_metadata_sha256'][k]==h(N/n)
assert storage['actual_current_cgroup_absent'] and storage['original_monitor_process_absent'] and not pathlib.Path(guard['cgroup']).exists()
pids=sorted({owner['supervisor_pid'],owner['monitor_pid'],cpu['pid'],child['workload_pid']})
ps=subprocess.run(['ps','-o','pid=,ppid=,stat=,args=','-p',','.join(map(str,pids))],text=True,capture_output=True);assert ps.returncode==1 and ps.stdout==''
assert all(not pathlib.Path('/proc',str(p)).exists() for p in pids)
for k in ('max','oom','oom_kill','oom_group_kill'):assert guard['memory_events'][k]==0
assert guard['memory_events']['high']==131 and guard['memory_swap_max_bytes']==0
assert guard['peak_sampled_memory_current_bytes']==5298184192 and int(early['kernel_readback']['memory.peak'])==5370712064 and early['elapsed_seconds']<guard['elapsed_seconds']
refs=claim['inputs'];pairpath=ROOT/refs['pair_policy']['path'];pair=load(pairpath)
package=ROOT/'tradingagents/research/onchain_replication';required={'tradingagents/research/onchain_replication/'+p.name for p in package.glob('*.py')}|{'tradingagents/research/'+p.name for p in package.parent.glob('*.py')}|{'tradingagents/__init__.py'}
assert len(required)==193 and len(pair['numerical_source']['files'])==181 and not(set(pair['numerical_source']['files'])-required)
missing=sorted(required-set(pair['numerical_source']['files']));assert len(missing)==12 and required<=set(claim['experiment']['source_files']) and len(claim['experiment']['source_files'])==379
counts=collections.Counter();claims=[]
for p in (ROOT/'research_runs').glob('*/claim.json'):
 c=j(p)
 if c.get('family',{}).get('mechanism_id')!=claim['family']['mechanism_id']:continue
 terminal=[n for n in ('complete','failed') if (p.parent/(n+'.json')).exists()];assert len(terminal)==1
 counts[terminal[0]]+=1;claims.append({'experiment':c['experiment_id'],'claim_sha256':h(p),'terminal_sha256':h(p.parent/(terminal[0]+'.json')),'status':terminal[0],'effective_attempt_budget':c.get('effective_attempt_budget',c['family']['attempt_budget'])})
assert counts=={'complete':20,'failed':27} and len(claims)+claim['family']['prior_attempts']==64 and max(x['effective_attempt_budget'] for x in claims)==95
history=load(ROOT/'research/onchain-paper-replication-2026-09-24/history.json');hc=collections.Counter(pathlib.Path(p).stem for p in history['metadata_hashes'] if pathlib.Path(p).name in ('complete.json','failed.json'));assert hc=={'complete':13,'failed':4}
receipt={'decision':'accepted_failed_disposition_and_native_cleanup','identity':name,'evidence':evidence,'failure':failed['reason'],'claim_sha256':h(L/'claim.json'),'failed_sha256':h(L/'failed.json'),'source':claim['source'],'native_exit':1,'supervisor_exit':1,'root_tool_terminal_join':'Pending durable original session23318 terminal receipt; not inferred from supervisor exit.','observed_absent_pids':pids,'ps':{'returncode':ps.returncode,'stdout':ps.stdout,'stderr':ps.stderr},'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cgroup_absent':True,'scientific_disposition':{'mcm_started':False,'completed_graphs':0,'unavailable_graphs':7,'all_cells_denominator':415968128,'training':None,'financial_fit_credit':0},'memory':{'native_elapsed_seconds':guard['elapsed_seconds'],'terminal_guard_sampled_peak_bytes':guard['peak_sampled_memory_current_bytes'],'early_kernel_peak_bytes':5370712064,'early_observation_elapsed_seconds':early['elapsed_seconds'],'high_events':131,'oom_events':0,'max_events':0,'swap_max_bytes':0,'qualification':'Kernel peak is actual earlier same-cgroup readback, not final lifetime peak. Guard peak is sampled memory.current, not kernel peak or process RSS.'},'source_diagnosis':{'required_sources':193,'declared_numerical_sources':181,'admitted_sources':379,'missing_numerical_source_names':missing},'accounting':{'local_closed':47,'local_complete':20,'local_failed':27,'historical_prior':17,'historical_complete':13,'historical_failed':4,'total_closed':64,'total_complete':33,'total_failed':31,'highest_claimed_allowance':95,'refunds':0,'actual_claims':claims},'qualification':'Original receipts and metadata only. No arrays/numerical execution, full binary semantic verification, preservation/recovery or deletion proof. Fifth requested PID has not yet been supplied; four original durable PIDs checked absent.'}
(R/'OUTCOME_REVIEW01.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'sha256':h(R/'OUTCOME_REVIEW01.json'),'missing':missing,'pids':pids}))
