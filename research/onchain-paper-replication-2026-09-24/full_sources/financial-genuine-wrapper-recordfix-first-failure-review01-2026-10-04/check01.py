import ast,datetime,hashlib,importlib.util,json,os,stat,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-native-20261004-01/source');PARENT=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-root-launch-20261004-01');ROOT=BASE/'financial-genuine-wrapper-root-recordfix-first-native01-2026-10-04';ID='financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01';JOB=CAP/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/ID;RUN=CAP/'research_runs'/ID
checks=[];begin=datetime.datetime.now(datetime.timezone.utc).isoformat()
def check(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_bytes())
# Snapshot exact bounded metadata receipts and complete empty directory membership.
originals=[]
for label,root in [('root',ROOT),('parent-attempt',PARENT/'attempt'),('job',JOB),('claim',RUN)]:
 dst=HERE/label;dst.mkdir(mode=0o700);rows=[]
 def walk(p,rel):
  s=p.lstat();r={'path':rel,'mode':stat.S_IMODE(s.st_mode)};check(not stat.S_ISLNK(s.st_mode),'no receipt redirect '+label+'/'+rel)
  if stat.S_ISDIR(s.st_mode):
   r['kind']='directory';rows.append(r)
   if rel!='.':(dst/rel).mkdir(mode=0o700)
   for c in sorted(p.iterdir()):walk(c,c.name if rel=='.' else rel+'/'+c.name)
   return
  check(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2,'bounded receipt '+label+'/'+rel);b=p.read_bytes();r.update(kind='file',bytes=len(b),sha256=sha(b));(dst/rel).write_bytes(b);rows.append(r)
 walk(root,'.');originals.append({'label':label,'root':str(root),'members':rows})
q=load(PARENT/'REQUEST_FINAL02.json');claim=load(RUN/'claim.json');failed=load(RUN/'failed.json');rt=load(ROOT/'ACTUAL_TERMINAL01.json');ri=load(ROOT/'ROOT_INTENT01.json');pt=load(PARENT/'attempt/parent-terminal.json');cleanup=load(PARENT/'attempt/owned-tree-cleanup.json');guard=load(JOB/'guard/final.json');owner=load(JOB/'owner.json');launch=load(JOB/'launch.json');observer=load(JOB/'observer.json');cells=load(JOB/'postmortem-cells.json')
check(sha((RUN/'claim.json').read_bytes())=='4c543d71fad5255be61087eaa3619d9e88cbbdc12fa1398bd7fa7fe6fb75c128'==failed['claim_sha256']==rt['claim_sha256'],'actual claim pin')
check(sha((RUN/'failed.json').read_bytes())=='35158c0ecebfe4dc75203ba87d5372f2f85643c0b5f828a99e17aa28fe79c450'==rt['failed_sha256']==observer['terminal_sha256'],'actual failed pin')
check(failed['status']=='failed' and failed['reason']=='ValueError: repeat run prohibited; use a separately justified registration' and failed['output_sha256']=={},'genuine unexpected failed semantics')
check(rt['actual_exit']==1 and rt['actual_session']==58508 and rt['actual_start_tool']=='b185ed' and rt['actual_completion_tool']=='ea4290','actual root tool terminal')
check(pt['actual_parent_exit'] is None and rt['original_parent_self_exit'] is None and pt['actual_child_exit']==1 and pt['outcome_semantics_accepted'] is False,'original null and failed child preserved')
for name,pin in rt['streams'].items():b=(ROOT/name).read_bytes();check(len(b)==pin['bytes'] and sha(b)==pin['sha256'],'root stream '+name)
check(owner==guard['owner_identity'] and all(owner[k]==v for k,v in launch.items()) and owner['experiment']==ID and owner['source_commit']==q['source'],'native owner genuine joins')
check(sha((JOB/'owner.json').read_bytes())==observer['owner_sha256'],'observer owner pin')
for name,h in observer['evidence_sha256'].items():check(sha((JOB/name).read_bytes())==h,'observer evidence '+name)
check(sha((JOB/'postmortem-cells.json').read_bytes())==observer['cell_ledger_sha256'],'postmortem ledger join')
check(load(JOB/'unsealed-journals.json')==[] and observer['unsealed_journals']==0 and observer['financial_completion'] is False and observer['status']=='failed','journal and observer status')
reg=load(CAP/q['registration']);exp=reg['experiments'][ID];job=load(CAP/exp['inputs']['execution_job']['path']);policy=job['resources'];check(all(guard[k]==v for k,v in policy.items()),'all original registered native policy values')
check(guard['kernel_controls']=={'memory.high':'3221225472','memory.max':'3221225472','memory.swap.max':'0'},'actual kernel memory controls')
check(guard['native_unit_limits']=={'file_size_bytes':4194304} and guard['native_unit_properties']['LimitFSIZE']=='4194304' and guard['native_unit_properties']['LimitFSIZESoft']=='4194304','actual native file limits')
check(len(guard['cpus'])==2 and all(set(v)<=set(guard['cpus']) and v for v in guard['cpu_thread_readback'].values()),'actual final CPU subset masks')
ready=load(JOB/'guard/cpu_ready.json');release=load(JOB/'guard/release.json');child=load(JOB/'guard/child_exit.json');check(ready and release and child['exit_code']==1,'actual ready/release/child evidence present')
check(guard['phase']=='failed' and guard['child_exit_code']==1 and guard['cleanup_verified'] is True and guard['elapsed_time_kill'] is False and all(v==0 for v in guard['memory_events'].values()),'original failed nonOOM nontimeout guard')
check(guard['peak_sampled_memory_current_bytes']==325218304 and 'memory_peak_bytes' not in guard and rt['actual_guard']['memory_peak_bytes'] is None,'sampled memory distinguished from unknown peak')
check(guard['elapsed_seconds']==4.233806165982969 and not os.path.lexists(guard['cgroup']),'actual elapsed and cgroup currently absent')
check(pt['cleanup']['unit']==guard['unit'] and pt['cleanup']['cgroup']==guard['cgroup'] and pt['cleanup']['cgroup_absent'] is True and pt['cleanup']['native_pid_census_is_complete_history'] is False,'Parent native cleanup joins/limits')
check(sha((PARENT/'attempt/owned-tree-cleanup.json').read_bytes())==pt['cleanup']['subreaper_cleanup_sha256'],'actual cleanup body pin')
check(cleanup['subreaper_used'] is True and cleanup['remaining_original_identities']==[],'actual owned descendants closure')
pids={ri['pid'],owner['supervisor_pid'],owner['monitor_pid'],child['workload_pid']}|{int(p) for p in guard['cpu_thread_readback']}|{r['pid'] for r in cleanup['owned_pid_start_records']}
for label,row in pt['cleanup']['actual_control_operations'].items():check(row['exit_code']==0,'actual native cleanup operation '+label);pids.add(row['pid'])
check(ri['pid']==rt['actual_parent_pid']==328901 and ri['start_ticks']==rt['actual_parent_start_ticks']=='14922665','Root original PID/start join')
for pid in sorted(pids):check(not Path('/proc/'+str(pid)).exists(),'actual observed PID currently absent '+str(pid))
unit=subprocess.run(['systemctl','--user','show',guard['unit'],'--property=ActiveState,SubState,Result,ControlGroup,ExecMainStatus','--no-pager'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,check=False);props=dict(line.split('=',1) for line in unit.stdout.decode().splitlines() if '=' in line);check(unit.returncode==0 and props['ActiveState']=='failed' and props['SubState']=='failed' and props['ControlGroup']=='','current exact failed unit read-only')
# Actual genuine verify_claim is stdlib/read-only Git, independently pinned before import.
verifypath=CAP/'tradingagents/research/verify.py';check(sha(verifypath.read_bytes())==q['source_files']['tradingagents/research/verify.py'],'genuine verify_claim source pinned');spec=importlib.util.spec_from_file_location('actual_failed_claim_verifier',verifypath);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);check(v.verify_claim(RUN)==claim,'genuine verify_claim current committed ancestry')
check(claim['source']==claim['design_source']==q['source']=='649fb8a11089524aaef7843dffeeb90a3a55ca17' and claim['effective_attempt_budget']==18,'source and effective budget18')
claims=[]
for p in sorted((CAP/'research_runs').iterdir()):
 if (p/'claim.json').is_file():claims.append(load(p/'claim.json'))
check(len(claims)==1 and claims[0]['experiment_id']==ID,'one actual current claim spent')
check(claim['family']['attempt_budget']==18 and claim['family']['prior_attempts']==0 and 'cumulative_budget_extension' not in claim['experiment'],'no refund transfer extension')
missing=[]
for name in exp['outputs']:
 p=RUN/'outputs'/name;check(not os.path.lexists(p),'declared lifecycle output absent '+name);missing.append(name)
check(sorted(r['id'] for r in cells)==sorted(exp['cells']) and all(r['status']=='unavailable' and r['reason']=='owned worker ended before durable cell disposition; no retry' for r in cells),'complete registered cell denominator remains unavailable')
pre=load(BASE/'financial-genuine-wrapper-recordfix-launch-command-investigation01-2026-10-04/PRELAUNCH_READBACK_TEMPLATE01.json')
for name in ('fit_namespace','wrapper_namespace'):check(not os.path.lexists(pre['namespace_requirements'][name]['path']),'actual no checkpoint/output namespace '+name)
check(not os.path.lexists(RUN/'complete.json'),'no completed coercion')
# Reauthenticate all current source bodies and original Git object identities after actual run.
old=load(BASE/'financial-genuine-wrapper-recordfix-native-eligibility-observation01-2026-10-04/OBSERVATION01.json')
for row in old['source_git_rows']:
 p=CAP/row['path'];b=p.read_bytes();check(p.resolve()==p and sha(b)==row['sha256'],'unchanged tracked source '+row['path']);check(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['oid'],'unchanged Git source body '+row['path'])
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=CAP).decode().strip();check(head==q['source'],'actual HEAD unchanged325 source')
for rel,h in q['source_files'].items():check(sha((CAP/rel).read_bytes())==h,'all324 source pins '+rel)
for name,h in q['helper_hashes'].items():check(sha((PARENT/name).read_bytes())==h,'unchanged Parent helper '+name)
check(sha((PARENT/'parent01.py').read_bytes())==q['caller_sha256'] and sha((PARENT/'REQUEST_FINAL02.json').read_bytes())=='28f2ae5340d38ac71450c8947c5b1ad30ac4192481da81596684445c9cf9b52e','actual Parent/Q unchanged')
# Exact original repeat predicate, actual claim scalar: no admit/start/replay call.
srcs={n:(CAP/'tradingagents/research'/n).read_bytes() for n in ('admission.py','lifecycle.py','onchain_replication/job.py','onchain_replication/financial_wrapper_fixture.py')}
(HERE/'sources').mkdir()
for n,b in srcs.items():(HERE/'sources'/n.replace('/','__')).write_bytes(b)
ad=ast.parse(srcs['admission.py']);repeat=next(n for n in ast.walk(ad) if isinstance(n,ast.If) and any(isinstance(x,ast.Constant) and x.value=='repeat run prohibited; use a separately justified registration' for x in ast.walk(n)) and n.lineno==317)
for own,expected in ((None,True),(ID,False)):
 result=eval(compile(ast.Expression(repeat.test),'<actual repeat predicate>','eval'),{'prior':[claim],'experiment':ID,'_own_claim':own});check(result is expected,'actual repeat predicate own='+str(own))
stack=(JOB/'guard/child.log').read_text();check('line 368, in worker' in stack and 'line 138, in authorize' in stack and 'line 318, in admit' in stack,'actual failure origin stack joins exact source')
# Snapshot all source-owned evidence before report, no outcome verifier adapter fabricated.
out={'decision':'ACCEPTED_UNEXPECTED_FAILED_SPENT_ONE_NO_CHECKPOINT','begin':begin,'end':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':len(checks),'check_names':checks,'originals':originals,'claim_sha256':sha((RUN/'claim.json').read_bytes()),'failed_sha256':sha((RUN/'failed.json').read_bytes()),'root_terminal_sha256':sha((ROOT/'ACTUAL_TERMINAL01.json').read_bytes()),'actual_root_exit':1,'original_parent_self_exit':None,'actual_child_exit':1,'guard_elapsed_seconds':guard['elapsed_seconds'],'peak_sampled_memory_current_bytes':guard['peak_sampled_memory_current_bytes'],'memory_peak_bytes':None,'recorded_memory_events':guard['memory_events'],'current_cgroup_absent':True,'currently_absent_observed_pids':sorted(pids),'complete_historical_native_pid_census':False,'actual_current_unit_properties':props,'unit_query_exit':unit.returncode,'unit_query_stderr':unit.stderr.decode(),'effective_budget':18,'spent_current_claims':1,'no_refund_or_transfer':True,'declared_unavailable_cells':cells,'missing_declared_outputs':missing,'checkpoint_available':False,'paper_financial_fit_credit':0,'current_source':head,'tracked_source_count':len(old['source_git_rows']),'source_pins_count':len(q['source_files']),'genuine_verify_claim_ran':True,'bound_outcome_verifier_executed':False,'full_failed_scope_capture':None,'actual_external_recovery':None,'actual_flat_recovery':None,'repeat_identity_permitted':False,'future_release':False}
with (HERE/'READBACK01.json').open('x') as f:json.dump(out,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('check_names','originals')}))
