from pathlib import Path
import json,hashlib,subprocess,datetime
H=Path('research/onchain-paper-replication-2026-09-24/full_sources'); O=H/'pilot34-terminal-outcome-review01-2026-10-11'; E=H/'real-data-pilot-full34-entry-preparation01-2026-10-11'
refs={}; checks=[]
def ref(p):
 b=p.read_bytes(); r={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};refs[str(p)]=r;return r
def read(p): ref(p);return json.loads(p.read_text())
def ck(x,s):
 checks.append({'check':s,'pass':bool(x)})
 if not x: raise AssertionError(s)
def write(n,v): (O/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
t=read(E/'ROOT_TERMINAL_OPERATION01.json'); d={}
for k,r in t['original_receipts'].items():
 p=Path(r['path']);ck(ref(p)==r,'terminal receipt '+k);d[k]=read(p)
c,f,g,ce,fs,io,op=(d[k] for k in ('claim','failed','guard_final','child_exit','final_storage','root_io','operator_delivery'))
ck(f['claim_sha256']==t['original_receipts']['claim']['sha256'],'failed claim binding')
ck(c['experiment_id']==f['experiment_id']==t['experiment']==op['experiment']==fs['experiment'],'same original identity')
ck(f['status']=='failed' and f['reason']==t['original_failure_reason']=='SystemExit: owned execution interrupted; never relaunch this identity','original permanent failure retained')
ck(c['source']==op['source']==fs['source']==g['owner_identity']['source_commit'],'original source joins')
ck(c['effective_attempt_budget']==105,'actually adopted 105')
request=read(E/'OPERATOR_INTERRUPTION_REQUEST01.json')
ck(all(request[k]==op[k] for k in request if k not in ('actual_signal_delivery','actual_terminal_exit')),'request delivery exact common metadata')
ck(op['signal']=='SIGINT' and op['pid']==ce['workload_pid'] and 'successfully' in op['actual_signal_delivery'],'operator original child delivery')
ck(g['child_exit_code']==ce['exit_code']==io['actual_parent_exit_code']==1,'child guard parent exits')
ck(g['phase']=='failed' and g['cleanup_verified'] and not g['elapsed_time_kill'],'guard disposition not wall timeout')
ck(g['elapsed_seconds']==t['original_guard_elapsed_seconds'],'guard elapsed')
ck(all(g['memory_events'][k]==0 for k in ('oom','oom_kill','oom_group_kill')),'recorded OOM counters zero')
ck(ce['terminal_memory_snapshot']==g['terminal_memory_snapshot'],'last terminal memory readback')
ck(g['optional_memory_telemetry']==t['original_last_kernel_telemetry'],'terminal telemetry preserved')
ck(io['outer_log_handles_closed'] and io['supervisor_reaped'] and fs['supervisor_reaped'] and fs['outer_log_handles_closed'],'outer handles and supervisor closure')
ck(fs['original_metadata_sha256']['guard']==t['original_receipts']['guard_final']['sha256'],'final storage authenticates guard')
outputs={}
for name,sha in f['output_sha256'].items():
 p=Path('research_runs')/t['experiment']/'outputs'/name;ck(ref(p)['sha256']==sha,'original output '+name)
 if name!='resource-population.json':outputs[name]=read(p)
p=outputs['pilot-summary.json'];q=p['throughput']
ck(p['training'] is None and not p['financial_fit_complete'] and not p['full_size_capacity'],'training and whole capacity unavailable')
ck(q['complete_graphs']==0 and q['failed_graphs']==1 and q['unavailable_graphs']==6,'original graph dispositions')
ck(all(v['completed_motif_cells'] is None and v['completed_nodes'] is None for v in q['graphs']),'original null graph completion retained')
ck(p['original_motifs']==32 and p['original_samples']==512 and p['full_graphs']==7,'unchanged scientific scope')
ck(outputs['cell-ledger.json'][0]['status']=='failed' and outputs['cell-ledger.json'][0]['paper_financial_fits']==0,'failed spent cell no financial fit')
batches=t['published_partial_batches'];prev=0
for i,r in enumerate(batches):
 b=read(Path(r['path']));ck(all(refs[r['path']][k]==r[k] for k in ('sha256','bytes')),'batch body '+str(i));ck(all(b[k]==r[k] for k in ('batch','start','stop','computed','reused','elapsed_seconds')),'batch observed fields '+str(i));ck(b['batch']==i and b['start']==prev and b['stop']-prev==b['computed']+b['reused']==4096,'contiguous batch '+str(i));prev=b['stop']
ck(len(batches)==9 and prev==t['published_partial_cells']==36864,'nine partial batches')
ck(len(list(Path(batches[0]['path']).parent.glob('*.json')))==9,'numeric summary directory has exactly nine JSON names')
br=c['experiment']['cumulative_budget_extension']['review'];budget=read(Path(br['path']));ck(refs[br['path']]['sha256']==br['sha256'],'reuse accepted105 review')
ck('33 complete/40 failed' in budget['scope'] and '73 permanently spent' in budget['scope'],'accepted predecessor accounting')
ck(t['accounting']=={'active':0,'closed':74,'complete':33,'failed':41,'highest_actually_adopted':105,'preserved_preclaim_reserved':3,'refund':False,'transfer':False,'unchanged_pending':28},'prior73 plus one failed34 accounting')
unit=g['unit'];r=subprocess.run(['systemctl','--user','show',unit,'--property=ActiveState,SubState,MainPID,Result,ExecMainStatus,ControlGroup'],capture_output=True,text=True,timeout=5)
props=dict(line.split('=',1) for line in r.stdout.splitlines() if '=' in line)
fresh={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':['systemctl','--user','show',unit,'--property=ActiveState,SubState,MainPID,Result,ExecMainStatus,ControlGroup'],'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'properties':props,'original_pids_present':{pid:Path('/proc',pid).exists() for pid in t['observed_original_pids_present']},'original_cgroup_present':Path(g['cgroup']).exists()}
write('FRESH_CLEANUP01.json',fresh);ref(O/'FRESH_CLEANUP01.json')
ck(r.returncode==0 and props==t['actual_unit_readback']['properties'],'fresh unit exact terminal properties')
ck(not any(fresh['original_pids_present'].values()) and not fresh['original_cgroup_present'],'fresh observed original PIDs and cgroup absent')
result={'decision':'accepted','scope':'Actual failed34 terminal metadata, nine partial batch summaries, original output hashes and fresh bounded cleanup; no empirical recomputation or complete lifetime process census.','checks':checks,'references':refs,'accounting':t['accounting'],'partial':{'batches':9,'cells':prev,'computed':sum(x['computed'] for x in batches),'reused':sum(x['reused'] for x in batches),'sum_numeric_elapsed_seconds':sum(x['elapsed_seconds'] for x in batches)},'original_failure_reason':f['reason'],'started_at':c['started_at'],'ended_at':f['ended_at'],'guard_elapsed_seconds':g['elapsed_seconds'],'root_tool_receipt':{'session':30142,'exit_code':1,'chunk':'40dc69','basis':'Root supplied actual tool observation, cross-referenced terminal record; not inferable from source or independently replayed.'},'unknowns':['Full original PID history remains unknown.','Partial summaries authenticate metadata, not numerical correctness or durable whole-MCM completion.','Original graph completion nulls and training null remain; no real joint update or financial fit.','Kernel peak is a last readback, not necessarily lifetime final peak; zero recorded OOM counters do not establish capacity.','Actual full outcome external recovery remains pending.','Accounting reuses accepted105 predecessor73 review and adds exactly original failed34; no full historical recount.'],'external_recovery_verified':False,'source_or_budget_mutated':False}
write('REVIEW01.json',result)
(O/'REPORT.md').write_text('Accepted actual terminal metadata and observed cleanup. Pilot34 remains permanently failed after deliberate SIGINT interruption; original reason and null dispositions are retained. Nine numeric summaries cover 36,864 partial cells; whole-MCM and training completion are unavailable. Original outputs, guard, child exit, final storage and RootIO hashes join. Fresh unit readback is failed/MainPID0 with empty ControlGroup; the four observed original PIDs and original cgroup are absent. Full PID history remains unknown. Accounting reuses accepted105 predecessor73 and adds this one failed attempt:74closed=33complete+41failed,0active;28pending+3reserved unchanged. Root tool30142/40dc69/exit1 is supplied actual tool evidence, not a source deduction. Full external outcome recovery is still pending. See REVIEW01.json for exact references and limits.\n')
write('MANIFEST01.json',{'status':'FROZEN_TERMINAL_METADATA_REVIEW','files':{p.name:ref(p) for p in sorted(O.iterdir()) if p.name!='MANIFEST01.json'}})
print(json.dumps({'review':ref(O/'REVIEW01.json'),'manifest':ref(O/'MANIFEST01.json'),'checks':len(checks),'partial':result['partial']}))
