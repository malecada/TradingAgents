"""Independent fixed failed-pilot metadata review and retained body inventory."""
from pathlib import Path
import hashlib,json,os,stat

ROOT=Path.cwd()
N='eth-paper-real-data-end-to-end-resource-20261005-01'
SOURCE='74886d1be05ce64e8eca939be42e08c6e5700d9c'
F=Path('research/onchain-paper-replication-2026-09-24/full_sources')
D=F/'real-data-pilot-final01-2026-10-06'
H=F/'real-data-pilot-final-release-completion01-2026-10-06/failed-outcome01'
C=Path('research_runs')/N
P=Path('research_artifacts/onchain-paper-replication-2026-09-24')
A=P/'runs'/N
L=P/'pilot-parent'/N
X=Path('research_artifacts/archive-dispatch-ethpilot-20261006')
IDENTITY='e7b2a93577e73995bf10ce326f943bfed1b3958aea50020d6c40becf94ae5a97'
J=Path('research_artifacts/onchain_representations')/IDENTITY/N
DYNAMIC=('launch-attempt01.json','ROOT_RUNNING01.json','ROOT_IO_CLOSED01.json','FINAL_STORAGE01.json','ROOT_TERMINAL01.json')
cache={}
def signature(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def raw(p):
    p=Path(p)
    if p not in cache:
        q=ROOT/p;s=q.lstat()
        assert q.resolve(strict=True)==q and stat.S_ISREG(s.st_mode) and s.st_nlink==1
        assert s.st_size<=4*1024**2
        b=q.read_bytes();assert len(b)==s.st_size and signature(s)==signature(q.lstat())
        cache[p]=b
    return cache[p]
def sha(p):return hashlib.sha256(raw(p)).hexdigest()
def read(p):
    assert Path(p).name!='resource-population.json'  # hash-only outcome population body
    return json.loads(raw(p))
def ref(p):return {'path':str(p),'sha256':sha(p)}
def write(name,value):
    p=H/name
    with p.open('x') as f:f.write(json.dumps(value,sort_keys=True,indent=2)+'\n')
    return p

roots=(C,A,L,X,J)
files=[];directories=[]
for root in roots:
    assert (ROOT/root).resolve(strict=True)==ROOT/root
    for p in sorted([root,*root.rglob('*')]):
        s=p.lstat()
        assert not stat.S_ISLNK(s.st_mode) and (ROOT/p).resolve(strict=True)==ROOT/p
        if stat.S_ISDIR(s.st_mode):
            directories.append({'path':str(p),'mode':stat.S_IMODE(s.st_mode),'device':s.st_dev,'inode':s.st_ino,'allocated_bytes':s.st_blocks*512})
        else:
            assert stat.S_ISREG(s.st_mode) and s.st_nlink==1
            files.append(p)
files.extend(D/name for name in DYNAMIC)
assert len(files)==len(set(files))==38
inventory=[]
for p in sorted(files):
    b=raw(p);s=p.stat()
    inventory.append({'path':str(p),'sha256':sha(p),'bytes':len(b),'mode':stat.S_IMODE(s.st_mode),'device':s.st_dev,'inode':s.st_ino,'allocated_bytes':s.st_blocks*512,'links':s.st_nlink})
evidence={str(p):sha(p) for p in files}
claim=read(C/'claim.json');failed=read(C/'failed.json');summary=read(C/'outputs/pilot-summary.json')
assert claim['experiment_id']==failed['experiment_id']==N and claim['source']==SOURCE
assert claim['bindings'] is None and claim['bindings_sha256'] is None
assert failed['claim_sha256']==sha(C/'claim.json')=='c31e711212a37bac2bca2782c1c1b12c24bb13bd000ddc3434f40e7818ada0d9'
assert failed['status']=='failed' and not (C/'complete.json').exists()
assert len(failed['output_sha256'])==len(claim['experiment']['outputs'])==8
assert set(failed['output_sha256'])==set(claim['experiment']['outputs'])
for name,pin in failed['output_sha256'].items():assert sha(C/'outputs'/name)==pin
assert summary['cell']==read(C/'outputs/cell-ledger.json')[0]
assert len(read(C/'outputs/cell-ledger.json'))==1 and summary['cell']['status']=='failed'
assert summary['training'] is None and summary['events']==[] and summary['retained_target_count']==0
t=summary['throughput']
assert t['graph_denominator']==len(t['graphs'])==t['unavailable_graphs']==7
assert t['complete_graphs']==t['failed_graphs']==t['verified_completed_motif_cells']==t['paper_financial_fits']==0
assert t['attempted_mcm_seconds']==0 and t['one_update_phase_seconds'] is None
assert all(g['status']=='unavailable' and g['reason']=='not_attempted_after_failure' and g['completed_motif_cells'] is None and g['elapsed_seconds'] is None for g in t['graphs'])
assert summary['financial_fit_complete'] is False
placeholder=read(C/'outputs/resource-binding.json')
assert placeholder==read(C/'outputs/resource-journal.json') and placeholder['status']=='failed'

jobpath=Path(claim['inputs']['execution_job']['path']);job=read(jobpath)
assert sha(jobpath)==claim['inputs']['execution_job']['sha256']
selected=job['payload']['representation_jobs']['original32'];descriptor=selected['descriptor']
observed=descriptor['compact_execution']['policy_sha256'];expected=claim['inputs']['compact_policy']['sha256']
assert observed=='f89dddb0ea710494fe63de22386f2c422ed42738731045e96036508d08be9df9'
assert expected=='fedb41e0f7828117ec401e15698c77433dd765da9f274487d0ddc4fddc06435b' and observed!=expected
assert set(descriptor['required_graphs'])=={g['graph_hash'] for g in t['graphs']}
compactpath=Path(claim['inputs']['compact_policy']['path']);assert sha(compactpath)==expected
for p in (jobpath,compactpath):evidence[str(p)]=sha(p)
for name in ('original_import_stage.py','real_pilot_import_caller.py'):
    p=Path('tradingagents/research/onchain_replication')/name
    assert sha(p)==claim['experiment']['source_files'][str(p)]
    evidence[str(p)]=sha(p)
trace=raw(A/'guard/child.log').decode()
assert 'original_import_stage.py", line 111, in attach' in trace
assert 'ValueError: compact owner policy descriptor differs' in trace
assert failed['reason']==summary['cell']['reason']=='ValueError: compact owner policy descriptor differs'

jc,jf,jo,js=(read(J/name) for name in ('claim.json','failed.json','owner.json','start.json'))
assert jc['resource_only'] is True and jc['owner']==jf['owner']==js['owner']==jo
assert jo['experiment']==N and jo['source_commit']==SOURCE and jo['workflow_identity']==IDENTITY
assert jc['descriptor']==descriptor and jf['status']=='failed' and jf['events']==[]
assert jf['reason']==failed['reason'] and set(jf['required_graphs'])==set(descriptor['required_graphs'])
assert jf['workflow_identity'] is None and js['workflow_identity'] is None
assert jc['job_sha256']==sha(jobpath) and jc['registration_sha256']==claim['registration_sha256']
assert set(p.name for p in J.iterdir())=={'claim.json','start.json','failed.json','owner.json'}

receipt=read(C/'outputs/archive-receipt.json');terminal=read(X/'terminal.json');intent=read(X/'intent.json')
assert read(C/'outputs/archive-terminal.json')==terminal
assert receipt['context']==str(X) and receipt['intent_sha256']==terminal['intent_sha256']==sha(X/'intent.json')
assert receipt['inode']==[X.stat().st_dev,X.stat().st_ino]
assert intent['claim_sha256']==sha(C/'claim.json') and intent['source_commit']==SOURCE and intent['experiment']==N
assert intent['execution_admitted'] is False and terminal['status']=='failed'
assert terminal['spent']=={'commands':0,'logical_bytes':0,'rounded_bytes':0}
assert all(v['acknowledged_records']==v['acknowledged_encoded_bytes']==v['shards']==0 and v['journal_failed'] is False for v in terminal['control_history'].values())
assert all(not any((X/name).iterdir()) for name in ('controls','diagnostic-controls','diagnostics'))
assert read(X/'close-failed.json')['intent_sha256']==sha(X/'intent.json')

root=read(D/'ROOT_TERMINAL01.json');io=read(D/'ROOT_IO_CLOSED01.json');storage=read(D/'FINAL_STORAGE01.json')
launch=read(A/'launch.json');owner=read(A/'owner.json');guard=read(A/'guard/final.json');observer=read(A/'observer.json')
for p,pin in root['evidence'].items():assert sha(Path(p))==pin
assert root['source']==launch['source_commit']==owner['source_commit']==storage['source']==SOURCE
assert root['experiment']==launch['experiment']==owner['experiment']==N
assert io['supervisor_pid']==launch['supervisor_pid']==owner['supervisor_pid']
assert io['actual_parent_exit_code']==root['root_actual_exit']['exit_code']==guard['child_exit_code']==1
assert root['root_actual_exit']=={'exit_code':1,'session':31993,'terminal_chunk':'0bb0e3'}
assert io['supervisor_reaped'] is True and io['outer_log_handles_closed'] is True
assert owner['nonce']==launch['nonce'] and owner['monitor_pid']==guard['monitor_pid']
assert guard['cleanup_verified'] is True and guard['elapsed_seconds']==434.466017962 and guard['phase']=='failed'
assert guard['cleanup_stop_returncode']==0 and read(A/'guard/child_exit.json')['exit_code']==1
assert root['actual_native']['elapsed_seconds']==guard['elapsed_seconds']
for name in ('memory_events','optional_memory_telemetry','peak_sampled_memory_current_bytes'):assert root['actual_native'][name]==guard[name]
for key,name in (('guard','guard/final.json'),('launch','launch.json'),('owner','owner.json')):assert storage['original_metadata_sha256'][key]==sha(A/name)
assert storage['actual_current_cgroup_absent'] is True and storage['original_monitor_process_absent'] is True
assert storage['actual_current_unit_properties']['MainPID']=='0' and storage['actual_current_unit_properties']['ControlGroup']==''
assert not Path(guard['cgroup']).exists()
assert len(root['current_selected_pid_exists'])==7 and all(v is False and not Path('/proc',pid).exists() for pid,v in root['current_selected_pid_exists'].items())
assert root['selected_active_native_units']==[]
assert observer['terminal_sha256']==sha(C/'failed.json') and observer['owner_sha256']==sha(A/'owner.json')
for p,pin in observer['evidence_sha256'].items():assert sha(A/p)==pin
assert observer['financial_completion'] is False and observer['cgroup_empty'] is True
assert observer['cell_ledger_sha256']==sha(A/'postmortem-cells.json')
postmortem=read(A/'postmortem-cells.json');assert len(postmortem)==1 and postmortem[0]['status']=='unavailable'
assert not (C/'artifacts').exists() and not (P/'sources'/N).exists()

body={'schema_version':1,'decision':'accepted','experiment':N,'source':SOURCE,
    'scope':'Exact retained small regular outcome bodies only; five outcome roots and five final-entry dynamic records. Suitable scope inventory for incremental BYTE preservation, not proof of external backup.',
    'files':inventory,'directories':directories,'regular_files':len(inventory),
    'logical_bytes':sum(r['bytes'] for r in inventory),'directory_count':len(directories),
    'all_body_hashes_verified':True,'contains_private_connection_or_runtime_payload':False,
    'population_output':'resource-population.json retained with hash-only integrity verification; no scientific values reproduced.',
    'exclusions':['Earlier committed source/gate/BINDING/input records','All graph/raw/price/dictionary/sample/runtime payload bodies','Unrelated historical trials','Shared parent directories outside the five owned roots'],
    'scope_note':'The separate four-body resource journal is included. A capture omitting it is only a narrower capture and cannot establish this full inventory. No external backup/readback was performed.'}
bp=write('BODY_REVIEW01.json',body)
outcome={'schema_version':1,'decision':'accepted','experiment':N,'source':SOURCE,
    'scope':'Independent authentication of permanent failed outcome, complete registered denominator and retained bounded evidence; no success/capacity acceptance.',
    'claim_sha256':sha(C/'claim.json'),'evidence':dict(sorted(evidence.items())),
    'body_review':ref(bp),'root_actual_exit':root['root_actual_exit'],'cleanup_verified':True,
    'native':{'elapsed_seconds':guard['elapsed_seconds'],'child_exit_code':guard['child_exit_code'],
       'cleanup_stop_returncode':guard['cleanup_stop_returncode'],'memory_events':guard['memory_events'],
       'peak_sampled_memory_current_bytes':guard['peak_sampled_memory_current_bytes'],
       'last_unit_kernel_peak_bytes':guard['optional_memory_telemetry']['unit']['kernel_peak_bytes']},
    'failure':{'reason':failed['reason'],'source_location':'tradingagents/research/onchain_replication/original_import_stage.py:111',
       'input_location':str(jobpath)+':1','descriptor_compact_policy_sha256':observed,'admitted_compact_policy_sha256':expected,
       'impact':'Exact registered input composition cannot pass Owner attachment; the genuine attempt is FAILED/spent before all MCM work or the training update.',
       'action':'Preserve this identity and evidence. Any separately authorized successor must join the selected and producer compact policy descriptor to its exact admitted policy before entry; do not patch or rerun this spent claim.'},
    'attempted_extent':{'registered_claim':True,'native_worker':True,'resource_population_output':True,
       'graph_loading':'Caller source places graph loading before the observed attachment failure; raw graph validity not reviewed.',
       'resource_journal_created':True,'archive_context_created':True,'Owner_attachment_completed':False,
       'archive_execution_admitted':False,'archive_spent':terminal['spent'],
       'graph_denominator':7,'graphs_completed':0,'graphs_failed_during_MCM':0,'graphs_unavailable_not_attempted':7,
       'verified_completed_motif_cells':0,'retained_targets':0,'training':None,'paper_financial_fits':0,
       'registered_cell_ledger':read(C/'outputs/cell-ledger.json'),
       'supervisor_postmortem_cell_ledger':postmortem},
    'binding_distinction':{'original_claim_bindings':None,'original_claim_bindings_sha256':None,
       'output_binding_and_journal':'Identical failed placeholders, not actual journal bodies.',
       'actual_resource_journal':str(J),'actual_resource_journal_body_count':4,
       'journal_top_level_workflow_identity':None,'journal_owner_workflow_identity':IDENTITY,
       'qualification':'Original nulls and supervisor unavailable-cell record remain unchanged; the separate failed resource journal and worker failed-cell ledger are authenticated individually.'},
    'absence_extent':{'claim_complete_json_absent':True,'training_artifact_directory_absent':True,
       'new_source_namespace_absent':True,'journal_contains_only_four_metadata_bodies':True,
       'archive_control_and_diagnostic_directories_empty':True,'selected_seven_PIDs_currently_absent':True,
       'recorded_cgroup_currently_absent':True,'active_units':'Root actual terminal record empty; reviewer did not invoke native/systemctl commands.',
       'lifetime_process_history':None},
    'disposition':'Permanent FAILED/spent. No relaunch, refund, transfer, scientific completion or strategy validation.',
    'not_tested':['No financial timing/leakage/return/cashflow/fees/funding or predictive claim tested.',
       'No graph/raw/price/label/dictionary/sample/runtime bodies inspected, no numerical imports/fits or experiment rerun.',
       'No network/native/claim invocation, external recovery proof or lifetime PID reconstruction.',
       'Kernel last-peak and sampled storage evidence do not establish full-pilot capacity or continuous maxima.']}
op=write('OUTCOME_REVIEW01.json',outcome)
mp=write('MANIFEST01.json',{'schema_version':1,'decision':'accepted','experiment':N,'files':[ref(H/'review01.py'),ref(bp),ref(op)]})
print(json.dumps({'outcome':ref(op),'body':ref(bp),'manifest':ref(mp),'regular_files':len(inventory),'logical_bytes':body['logical_bytes'],'directories':len(directories),'decision':'accepted'},sort_keys=True))
