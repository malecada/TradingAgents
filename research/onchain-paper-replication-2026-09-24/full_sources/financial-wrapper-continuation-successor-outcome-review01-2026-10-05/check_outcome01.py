from pathlib import Path
import hashlib,json,os,stat,datetime
B=Path('/home/malecada/master_thesis'); M=B/'TradingAgents-audit-fixes'; F=M/'research/onchain-paper-replication-2026-09-24/full_sources'; C=F/'heartbeat-root-checkpoint10-2026-10-04'; D=Path(__file__).parent
P=B/'onchain-financial-isolation/genuine-financial-wrapper-continue100-resource-successor-root-launch-20261005-01'; CAP=B/'onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source'; I='financial-wrapper-classification-eager-continue100-resource-successor-20261005-01'; S='a5bcc943167ad035b45e12ddf9864d46e685b124'; A=P/'attempt'; R=CAP/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/I
H=lambda b:hashlib.sha256(b).hexdigest()
def ref(p):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and not p.is_symlink();b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':H(b),'mode':stat.S_IMODE(s.st_mode)}
def read(p):return json.loads(p.read_bytes())
def put(n,v):
 p=D/n;assert not p.exists();p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n');p.chmod(0o444)
pre=F/'financial-wrapper-continuation-successor-review01-2026-10-05';assert ref(pre/'MANIFEST01.json')['sha256']=='e0d67730ee1a87c46033cd01858f463a1abbc18c131e2cf077af3c49620dd0d6'
root=read(C/'SUCCESSOR_NUMERICAL_ROOT_EXIT01.json');q=read(P/'REQUEST_FINAL01.json');intent=read(A/'intent.json');terminal=read(A/'parent-terminal.json');cleanup=read(A/'owned-tree-cleanup.json');spawn=read(A/'spawn.json');g=read(R/'guard/final.json');child=read(R/'guard/child_exit.json');owner=read(R/'owner.json');launch=read(R/'launch.json');obs=read(R/'observer.json');cpu=read(R/'guard/cpu_ready.json');monitor=read(R/'monitor-file-limit.json')
assert root['actual_root_exit']==1 and root['session_id']==87309 and root['final_chunk']=='c3fa6c'
for key in ['request','stdout','stderr']:
 got=ref(Path(root[key]['path']));assert all(got[k]==root[key][k] for k in ['bytes','sha256'])
assert ref(P/'REQUEST_FINAL01.json')['sha256']=='c08c95cce4bdfeb1131756c8fc7511447512fc04b5375ffc412bbfe16114c8b7'
assert q['identity']==intent['identity']==terminal['identity']==root['identity']==spawn['identity']==I
assert q['source']==intent['source']==terminal['source']==spawn['source']==S
assert intent['command']==spawn['argv'] and spawn['pid']==launch['supervisor_pid']==owner['supervisor_pid']
assert owner==g['owner_identity'] and owner['monitor_pid']==g['monitor_pid']==monitor['pid']
assert launch['nonce']==owner['nonce'] and launch['source_commit']==owner['source_commit']==S
assert obs['status']=='not_admitted' and ref(R/'owner.json')['sha256']==obs['owner_sha256']
for n,h in obs['evidence_sha256'].items():assert ref(R/n)['sha256']==h
assert terminal['actual_child_exit']==1 and terminal['actual_parent_exit'] is None and terminal['error_type']=='StorageMutationObservation' and terminal['supervisor_result'] is None and terminal['outcome_semantics_accepted'] is False
assert 'directory changed at namespace rejoin' in (C/'SUCCESSOR_NUMERICAL_ROOT01.stderr').read_text()
assert g['phase']=='failed' and g['child_exit_code'] is None and g['limit_reason']=='InterruptedError: guard received signal 15' and g['retry'] is False
assert child['exit_code']==125 and child['reason']=='signal before release' and child['workload_pid'] is None and child['snapshot_error'] is None
assert all(v==0 for v in child['terminal_memory_snapshot']['memory_events'].values())
assert g['memory_high_bytes']==g['memory_max_bytes']==g['reserve_bytes']==3221225472 and g['memory_swap_max_bytes']==0 and g['start_reserve_bytes']==6442450944
assert cpu['cpus']==g['cpus']==[0,1] and cpu['file_size_limit']==monitor['file_size_limit']==[4194304,4194304] and monitor['before_claim'] is True
assert g['wall_seconds']==1800 and intent['outer_active_seconds']==1840 and g['host_mem_available_bytes']>=6442450944
assert g['cleanup_verified'] is True and g['cleanup_stop_returncode']==0
cl=terminal['cleanup'];assert cl['joined_unit_stopped'] is True and cl['cgroup_absent'] is True and cl['unit']==g['unit'] and cl['cgroup']==g['cgroup'] and not Path(g['cgroup']).exists()
assert cl['native_pid_census_is_complete_history'] is False and cl['subreaper_cleanup_sha256']==ref(A/'owned-tree-cleanup.json')['sha256']
assert cleanup['subreaper_used'] is True and cleanup['remaining_original_identities']==[]
for k,rec in cl['actual_control_operations'].items():
 assert rec['exit_code']==0
 for s in ['stdout','stderr']:assert (A/k/s).read_bytes()==rec[s].encode() and rec[s+'_bytes']==len(rec[s].encode())
 sub=read(A/k/'owned-tree-cleanup.json');assert sub['remaining_original_identities']==[] and sub['subreaper_used'] is True
pins=[]
for row in cleanup['owned_pid_start_records']:
 pp=Path('/proc')/str(row['pid'])/'stat';current=None
 try: current=pp.read_text().rsplit(')',1)[1].split()[19]
 except FileNotFoundError:pass
 assert current!=row['ticks'];pins.append({'pid':row['pid'],'original_start_ticks':row['ticks'],'current_start_ticks':current,'original_identity_present':False})
absent=[CAP/'research_runs'/I,CAP/'research_artifacts/financial_wrapper_engineering'/I,R/'guard/release.json']
assert all(not p.exists() for p in absent)
assert set(p.name for p in CAP.joinpath('research_runs').iterdir() if p.is_dir())=={'financial-wrapper-classification-eager-complete100-compatibility-20261004-01','financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01','financial-wrapper-classification-eager-interrupt1-claimedrun-20261004-01','financial-wrapper-classification-eager-complete100-20261003-01'}
files=[ref(p) for rt in [A,R] for p in sorted(rt.rglob('*')) if p.is_file()]+[ref(C/n) for n in ['SUCCESSOR_NUMERICAL_ROOT_EXIT01.json','SUCCESSOR_NUMERICAL_ROOT01.stdout','SUCCESSOR_NUMERICAL_ROOT01.stderr']]
assert len(files)==27
put('RAW_EVIDENCE01.json',{'schema_version':1,'files':files,'regular_body_count':len(files),'body_bytes':sum(x['bytes'] for x in files)})
put('OUTCOME_CHECK01.json',{'schema_version':1,'decision':'accepted-operational-preclaim-refusal','identity':I,'source':S,'sampled_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'preparation_manifest':ref(pre/'MANIFEST01.json'),'root_exit':ref(C/'SUCCESSOR_NUMERICAL_ROOT_EXIT01.json'),'actual_root_exit':1,'original_parent_exit':None,'job_supervisor_exit':1,'original_guard_child_exit':None,'separate_native_launcher_exit':125,'workload_pid':None,'research_claim_present':False,'numerical_updates':0,'new_checkpoint_present':False,'continuation_agreement_tested':False,'new_identity_permanently_reserved':True,'identity_reuse_authorized':False,'claim_namespace_unchanged_four_names':True,'lifecycle_accounting':{'basis':'accepted preparation cumulative proof plus unchanged exact claim namespace','base':18,'prior':0,'highest':20,'spent':4,'complete':1,'failed':3,'remaining':16,'terminal_reserved_without_claim':2,'refund':False},'failure':'Parent sampled CAP storage rejoin observed concurrent directory mutation; termination reached native launcher before workload release. No RAM-capacity failure established.','cleanup':{'native_unit':g['unit'],'cgroup_absent_sampled':True,'original_owned_process_pins':pins,'universal_native_pid_history_complete':False},'absent_paths_sampled':[str(p) for p in absent],'raw_evidence':ref(D/'RAW_EVIDENCE01.json'),'externally_recovered_outcome':False,'qualifications':['Read-only metadata and raw operational evidence; no numerical imports or checkpoint decoding.','Original null exits remain null; separate Root exit does not rewrite them.','Storage sampling is non-atomic; no universal descendant-history or writer-exclusion claim.','Historical source/checkpoint/science and runtime roots reused from accepted closed preparation; not reread.','No model/optimizer/RNG/log equality, economic return, fee/funding, PnL, forecasting or strategy claim tested.']})
print(json.dumps({'raw':ref(D/'RAW_EVIDENCE01.json'),'check':ref(D/'OUTCOME_CHECK01.json')},indent=2))
