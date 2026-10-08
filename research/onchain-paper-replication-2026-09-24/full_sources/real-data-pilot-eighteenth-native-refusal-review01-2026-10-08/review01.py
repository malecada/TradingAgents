"""Bounded original public setup-refusal evidence/selection review. No execution."""
from pathlib import Path
import datetime, hashlib, json, os, stat, subprocess
H=Path(__file__).resolve().parent;F=H.parent;R=H.parents[3];D=F/'real-data-pilot-final18-2026-10-08'
NAME='eth-paper-real-data-end-to-end-resource-20261008-18';SOURCE='131bee378970e06cce0a225157e73f9b755af95e'
PREFIX=R/'research_artifacts/onchain-paper-replication-2026-09-24';B=PREFIX/'runs'/NAME;P=PREFIX/'pilot-parent'/NAME
cache={};evidence={}
def raw(p):
    p=Path(p);p=p if p.is_absolute() else R/p
    assert p.is_relative_to(F) or p.is_relative_to(B) or p.is_relative_to(P) or p.parent==R/'tradingagents/research/onchain_replication'
    if p not in cache:
        s=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<1024**2
        b=p.read_bytes();z=p.lstat();assert (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns)
        cache[p]=b
    evidence[str(p.relative_to(R))]=hashlib.sha256(cache[p]).hexdigest();return cache[p]
def read(p):return json.loads(raw(p))
def pin(v):
    b=raw(v['path']);assert hashlib.sha256(b).hexdigest()==v['sha256']
    if 'bytes' in v:assert len(b)==v['bytes']
terminal=read(D/'ROOT_TERMINAL01.json')
assert terminal['source']==SOURCE and terminal['identity']==NAME
assert terminal['disposition']=='CLOSED_NATIVE_SETUP_REFUSAL_PRECLAIM_NEVER_REUSE_NO_REFUND'
for v in terminal['evidence'].values():pin(v)
io=read(D/'ROOT_IO_CLOSED01.json');storage=read(D/'FINAL_STORAGE01.json');launch=read(B/'launch.json');owner=read(B/'owner.json');guard=read(B/'guard/final.json');observer=read(B/'observer.json');child=read(B/'guard/child_exit.json');ready=read(B/'guard/cpu_ready.json');monitor=read(B/'monitor-file-limit.json')
assert raw(B/'guard/live.json')==raw(B/'guard/final.json')
for p,h in observer['evidence_sha256'].items():assert hashlib.sha256(raw(B/p)).hexdigest()==h
assert observer['owner_sha256']==hashlib.sha256(raw(B/'owner.json')).hexdigest() and observer['status']=='not_admitted'
assert json.loads(raw(P/'stdout.log'))==observer and raw(P/'stderr.log')==b'' and raw(B/'guard/child.log')==b''
for k,p in [('guard',B/'guard/final.json'),('launch',B/'launch.json'),('owner',B/'owner.json')]:assert storage['original_metadata_sha256'][k]==hashlib.sha256(raw(p)).hexdigest()
assert launch['source_commit']==owner['source_commit']==storage['source']==SOURCE and launch['nonce']==owner['nonce']
assert guard['owner_identity']==owner and guard['monitor_pid']==owner['monitor_pid']==258301
assert launch['supervisor_pid']==owner['supervisor_pid']==io['supervisor_pid']==257933
assert monitor['pid']==258301 and monitor['before_claim'] and monitor['source_commit']==SOURCE
assert ready['pid']==258636 and guard['cpu_thread_readback']=={'258636':[0,1]}
assert io['actual_parent_exit_code']==terminal['actual_root_exit_code']==1 and io['supervisor_reaped'] and io['outer_log_handles_closed']
assert guard['child_exit_code'] is None and child['exit_code']==125 and child['reason']=='signal before release' and child['workload_pid'] is None
assert guard['cleanup_verified'] and guard['phase']=='failed' and not guard['retry']
assert guard['limit_reason']==terminal['failure_reason']=='RuntimeError: host reserve fell during cgroup setup'
assert guard['host_mem_available_bytes']==9102376960<guard['start_reserve_bytes']==9126805504
assert guard['elapsed_seconds']==terminal['elapsed_native_seconds']==0.5318632510006864
assert all(v==0 for v in guard['memory_events'].values()) and guard['peak_sampled_memory_current_bytes']==14045184
assert terminal['actual_research_claim'] is None and terminal['reserved_allowance_ceiling']==89 and terminal['highest_actually_claimed_ceiling_unchanged']==88
assert terminal['actual_original_root_session']==60718 and terminal['actual_original_terminal_chunk']=='b14669'
# Independent current cleanup observation is read-only; no stop/signal call.
pids=[257933,258301,258636];assert all(not Path('/proc',str(pid)).exists() for pid in pids)
cgroup=Path(guard['cgroup']);assert cgroup.is_relative_to('/sys/fs/cgroup/user.slice') and cgroup.name==guard['unit'] and not cgroup.exists()
u=subprocess.check_output(['systemctl','--user','show',guard['unit'],'--property=ControlGroup,ActiveState,SubState,ExecMainStatus,Result,MainPID'],text=True)
unit=dict(line.split('=',1) for line in u.splitlines() if '=' in line);assert unit==terminal['current_unit_properties']==storage['actual_current_unit_properties']
assert unit['MainPID']=='0' and unit['ControlGroup']=='' and unit['ExecMainStatus']=='125' and unit['ActiveState']=='failed'
active=subprocess.check_output(['systemctl','--user','list-units','--state=active,activating','--no-legend','onchain-replication-*.service'],text=True);assert not active.strip()
absent=[R/'research_runs'/NAME,PREFIX/'sources'/NAME,R/'research_artifacts/archive-dispatch-ethpilot-20261008-18',B/'guard/release.json',B/'pilot-summary.json',B/'resource-journal.json',B/'postmortem-cells.json']
assert all(not p.exists() and not p.is_symlink() for p in absent)
assert not list((R/'research_artifacts/onchain_representations').glob('*/'+NAME))
# Inspect only frozen metadata and two control source bodies, not scientific inputs.
release=read(D/'RELEASE_REVIEW01.json')
for p in [R/'tradingagents/research/onchain_replication/resources.py',R/'tradingagents/research/onchain_replication/job.py',D/'inputs01/pilot.json',D/'gate01.json']:
    b=raw(p);assert hashlib.sha256(b).hexdigest()==release['evidence'][str(p.relative_to(R))]
    if p.suffix=='.py':assert subprocess.check_output(['git','show',SOURCE+':'+str(p.relative_to(R))],cwd=R)==b
resources=raw(R/'tradingagents/research/onchain_replication/resources.py').decode().splitlines();assert "raise RuntimeError('host reserve fell during cgroup setup')" in resources[606]
assert "receipt/'release.json'" in resources[610] and 'subprocess.Popen(command' in resources[291]
gate=read(D/'gate01.json')['experiments'][NAME];pilot=read(D/'inputs01/pilot.json');assert gate['cells']==['real-eth-one-update'] and len(pilot['graph_inputs'])==7
first=read(D/'PREFLIGHT_REFUSAL01.json');elig=read(D/'ELIGIBILITY_AFTER_REFUSAL01.json');attempt=read(D/'launch-attempt01.json')
assert first['original_root_session']==14369 and first['root_io_capture_was_invoked'] is False and first['failed_check_memory_available_bytes'] is None
assert attempt['source']==SOURCE and attempt['experiment']==NAME and attempt['effective_attempt_budget']==89
assert attempt['host_mem_available_bytes']>=9126805504 and elig['memory_available_bytes']==9230630912
# Complete actual owned roots plus finite dynamic entry records. No shared parents.
dynamic=[D/n for n in ['PREFLIGHT_REFUSAL01.json','PREFLIGHT_REFUSAL01.log','ELIGIBILITY_AFTER_REFUSAL01.json','REMOTE_CONFIRMATION01.json','launch-attempt01.json','ROOT_IO_CLOSED01.json','FINAL_STORAGE01.json','ROOT_TERMINAL01.json']]
files=[];directories=[]
for root in [B,P]:
    for path in [root,*sorted(root.rglob('*'))]:
        s=path.lstat();assert path.resolve(strict=True)==path
        if stat.S_ISDIR(s.st_mode):directories.append({'path':str(path.relative_to(R)),'kind':'directory','mode':stat.S_IMODE(s.st_mode)})
        else:assert stat.S_ISREG(s.st_mode);files.append(path)
files+=dynamic;assert len(files)==len(set(files))
records=[]
for path in sorted(files):
    b=raw(path);s=path.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1
    assert len(b)==s.st_size and hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256(b).digest()
    records.append({'path':str(path.relative_to(R)),'kind':'regular','mode':stat.S_IMODE(s.st_mode),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'nlink':s.st_nlink,'stat_identity':[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]})
selection={'schema_version':1,'decision':'accepted','experiment':NAME,'source':SOURCE,'scope':'Exact native18 setup-refusal public increment: all two actual owned roots plus eight dynamic initial-refusal/eligibility/remote/attempt/closure records.','files':records,'directories':directories,'regular_count':len(records),'directory_count':len(directories),'original_regular_bytes':sum(x['bytes'] for x in records),'dynamic_entry_records':[str(x.relative_to(R)) for x in dynamic],'absent_namespaces':[str(x.relative_to(R)) for x in absent[:3]],'representation_namespace_absent':True,'exclusions':['Unchanged source/gate/templates/inputs/reviews/history and previous captured increments','Private transport bodies/shared runtime and historical scientific stores','Shared parents outside the two owned roots'],'qualification':'Preserve exact names/modes/bytes/directories including all zero-byte logs. Earlier14369 outer refusal remains separate from actual60718 native attempt. Selection grants no deletion, numerical release or recovery claim.'}
def save(name,value):
    with (H/name).open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
save('INCREMENT_SELECTION01.json',selection)
raw(Path(__file__))
result={'schema_version':1,'decision':'accepted','identity':NAME,'source':SOURCE,'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'disposition':terminal['disposition'],'evidence':dict(sorted(evidence.items())),
'actual_root_exit':1,'guard_child_exit':None,'separate_child_exit':125,'separate_child_reason':'signal before release','workload_pid':None,'claim':None,
'actual_elapsed_native_seconds':guard['elapsed_seconds'],'host_mem_available_bytes':9102376960,'required_startup_bytes':9126805504,'shortfall_bytes':9126805504-9102376960,
'guard_sampled_peak_bytes':14045184,'memory_events':guard['memory_events'],'current_pids_absent':pids,'current_cgroup_absent':True,'current_unit_properties':unit,'current_active_native_units':[],
'registered_cell_denominator':[{'cell_id':c,'status':'unavailable','reason':'native setup refused before worker release; no scientific cell attempted or lifecycle claim'} for c in gate['cells']],
'registered_graph_denominator':[{'graph_sha256':h,'input_role':v,'status':'unavailable','reason':'worker never released'} for h,v in sorted(pilot['graph_inputs'].items())],
'original_resource_journal':'absent; worker never released','original_pilot_summary':'absent; worker never released','original_cell_ledger':'absent; no ResearchRun claim; reviewer denominator is explicit derived metadata, not a fabricated original ledger',
'absence':[str(p.relative_to(R)) for p in absent],'representation_namespace_absent':True,
'accounting':{'closed_claims':58,'complete_claims':33,'failed_claims':25,'highest_actually_claimed_ceiling':88,'pending':28,'closed_preclaim_reservations':3,'closed_preclaim_identities':['03','08','18'],'reserved_ceiling_for_18':89,'reuse':False,'refund':False},
'earlier_refusal':'Original14369 outer preflight refusal and historical unused eligibility are preserved separately. Actual60718 native setup attempt now permanently reserves/closes18 and supersedes that prior future-eligibility conclusion.',
'qualification':'Raw hash joins, original ownership and current native cleanup accepted. Host startup reserve refusal precedes release.json publication (resources.py:605-612) and worker Popen (resources.py:288-292). The claimed value is a setup refusal, not a kernel OOM, workload capacity test, scientific failed claim or method result. Previous and current RAM readings are not attributed workload overhead.',
'not_tested':['No financial/scientific data, numerical imports, MCM/update/training, full417 closure rerun, private/runtime bodies, source mutation, claim or native launch.','Root tool session/chunk/exit identity is attributed to ROOT_TERMINAL01; repository raw RootIO/observer/guard/parent evidence independently joined.','Original artifact preservation externally recoverable only after Root capture and actual returned archive review.']}
save('OUTCOME_REVIEW01.json',result)
print(json.dumps({'decision':'accepted','regular_count':len(records),'directory_count':len(directories),'regular_bytes':selection['original_regular_bytes'],'selection_sha256':hashlib.sha256((H/'INCREMENT_SELECTION01.json').read_bytes()).hexdigest(),'outcome_sha256':hashlib.sha256((H/'OUTCOME_REVIEW01.json').read_bytes()).hexdigest()}))
