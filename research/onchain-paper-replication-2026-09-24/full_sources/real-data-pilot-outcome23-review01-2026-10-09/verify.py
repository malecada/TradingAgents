import ast,datetime,hashlib,json,math,os,resource,signal,stat,struct,subprocess
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(60)
R=Path.cwd();H=Path(__file__).resolve().parent;F=H.parent;pins={}
def raw(p):
 p=Path(p);s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_size<=4*1024**2
 b=p.read_bytes();assert p.stat()==s;pins[str(p.relative_to(R) if p.is_absolute() else p)]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b
def read(p):return json.loads(raw(p))
def sha(p):return hashlib.sha256(raw(p)).hexdigest()
def req(v,m):
 if not v:raise ValueError(m)
src=R/'tradingagents/research/onchain_replication/compact_pair_log.py';tree=ast.parse(raw(src));ns={'FRAME':struct.Struct('<QB7xQdQ32s32s32s'),'ZERO':'0'*64,'math':math,'require':req};exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['_empty','_advance']],type_ignores=[]),str(src),'exec'),ns)
def inspect(date,num):
 ident=f'eth-paper-real-data-end-to-end-resource-{date}-{num}';run=R/'research_runs'/ident;native=R/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/ident
 c=read(run/'claim.json');fail=read(run/'failed.json');assert fail['claim_sha256']==sha(run/'claim.json') and fail['status']=='failed' and 'PlannedScoringStop' in fail['reason'];assert not (run/'complete.json').exists()
 for name,h in fail['output_sha256'].items():assert sha(run/'outputs'/name)==h
 d=read(run/'outputs/real-pilot-scoring-diagnostic.json');summary=read(run/'outputs/pilot-summary.json');progress=read(run/'artifacts/scoring-diagnostic/progress.json');guard=read(native/'guard/final.json');owner=read(native/'owner.json');launch=read(native/'launch.json')
 assert guard['owner_identity']==owner and owner['experiment']==ident and owner['source_commit']==c['source']==launch['source_commit'];assert guard['child_exit_code']==1 and guard['cleanup_verified'];assert all(guard['memory_events'][k]==0 for k in ['oom','oom_kill','oom_group_kill','max'])
 assert d==summary['scoring_diagnostic'] and d['completed_scalar_pairs']==1024 and d['planned_stop_reached'];assert not d['full_mcm_complete'] and not d['model_update_complete'] and d['paper_financial_fits']==0
 t=summary['throughput'];assert len(t['graphs'])==7 and [x['status'] for x in t['graphs']]==['failed']+['unavailable']*6;assert all(x['completed_motif_cells'] is None and x['completed_nodes'] is None for x in t['graphs']);assert summary['training'] is None and t['one_update_phase_seconds'] is None
 archive=read(run/'outputs/archive-receipt.json');w=archive['representations']['original32']['workflow_identity'];rep=R/'research_artifacts/onchain_representations'/w/ident;compact=R/'research_artifacts/onchain_compact_mcm'/w/ident;ro=read(rep/'owner.json');assert ro['source_commit']==c['source'] and ro['experiment']==ident and ro['workflow_identity']==w
 bound=read(rep/'compact/owner.json')['binding'];assert bound['claim_sha256']==sha(run/'claim.json') and bound['experiment']==ident and Path(bound['journal_directory'])==rep
 graph=d['graph_hash'];stage=rep/'compact'/('mcm-'+graph);log=stage/'matching';start=read(log/'start.json');state=ns['_empty']();head=sha(log/'start.json');steps=[];completions=[]
 for file in sorted(log.glob('events-*.bin')):
  b=raw(file);assert len(b)%168==0
  for off in range(0,len(b),168):
   frame=b[off:off+136];checksum=b[off+136:off+168];assert hashlib.sha256(bytes.fromhex(head)+frame).digest()==checksum;head=checksum.hex();state=ns['_advance'](state,frame,start['limits'],start['max_iterations']);row=ns['FRAME'].unpack(frame)
   if row[1] in (1,2):steps.append(row[4]);completions.append((row[2],row[5],struct.pack('<d',row[3])))
 assert state=={'events':2048,'started_pairs':1024,'completed_pairs':1024,'progress_events':0,'pending':None}
 logfail=read(log/'failed.json');assert logfail['events']==2048 and logfail['status']=='failed';assert not (log/'terminal.json').exists()
 tail=stage/'stream/tails/tail-000000000000';ts=read(tail/'start.json');head=sha(tail/'start.json');b=raw(tail/'records.bin');assert len(b)==1023*80
 for i in range(1023):
  frame=b[i*80:i*80+48];checksum=b[i*80+48:(i+1)*80];assert hashlib.sha256(bytes.fromhex(head)+frame).digest()==checksum;head=checksum.hex();ordinal,score,purpose=struct.unpack('<Qd32s',frame);assert (ordinal,purpose,struct.pack('<d',score))==completions[i]
 assert not (tail/'terminal.json').exists();assert d['tail_observation']['durable_tail_cells']==1023;assert read(native/'unsealed-journals.json')==[]
 for x in [rep/'failed.json',compact/('mcm-'+graph)/'failed.json',stage/'checkpoints/failed.json']:read(x)
 roots=[run,native,R/'research_artifacts/onchain-paper-replication-2026-09-24/pilot-parent'/ident,rep,compact,R/archive['context']]
 result={'id':ident,'source':c['source'],'claim_sha256':sha(run/'claim.json'),'failed_sha256':sha(run/'failed.json'),'diagnostic':d,'persisted_checkpoint':progress,'native_elapsed_seconds':guard['elapsed_seconds'],'kernel_peak_bytes':guard['optional_memory_telemetry']['unit']['kernel_peak_bytes'],'memory_events':guard['memory_events'],'guard_supervisor_pid':guard.get('supervisor_pid'),'guard_supervisor_pid_field_present':'supervisor_pid' in guard,'owner_supervisor_pid':owner['supervisor_pid'],'journal_state':state,'journal_failure':logfail,'iterations_sum':sum(steps),'iterations_min':min(steps),'iterations_max':max(steps),'iterations_sequence_sha256':hashlib.sha256(json.dumps(steps).encode()).hexdigest(),'tail_cells_chain_joined':1023,'tail_terminal_present':False,'journal_terminal_present':False,'graph_dispositions':t['graphs'],'last_partial_observation':summary['partial_mcm_progress']['last_observation'],'roots':[str(x.relative_to(R)) for x in roots]}
 return result,c,roots,guard
r22,c22,_,g22=inspect('20261008',22);r23,c23,roots,g23=inspect('20261009',23)
f=F/'real-data-pilot-final23-2026-10-09';terminal=read(f/'ROOT_TERMINAL01.json');io=read(f/'ROOT_IO_CLOSED01.json');storage=read(f/'FINAL_STORAGE01.json');assert terminal['session_id']==1248 and terminal['actual_return']['exit_code']==1 and terminal['actual_return']['chunk_id']=='2915ac';assert io['actual_parent_exit_code']==1 and io['supervisor_reaped'] and io['supervisor_pid']==1119667
absence={str(pid):not Path(f'/proc/{pid}').exists() for pid in [1119667,1120074,1120445,1120448]};assert all(absence.values());assert not Path(g23['cgroup']).exists()
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==c23['source']
source_checks={p:sha(R/p)==h for p,h in c23['experiment']['source_files'].items()};assert all(source_checks.values())
changed=[p for p,h in c23['experiment']['source_files'].items() if p.startswith('tradingagents/') and c22['experiment']['source_files'].get(p)!=h]
inventory=[]
for root in roots:
 files=[];dirs=0
 for p in root.rglob('*'):
  s=p.lstat();assert not stat.S_ISLNK(s.st_mode)
  if stat.S_ISDIR(s.st_mode):dirs+=1
  else:
   assert stat.S_ISREG(s.st_mode);files.append({'path':str(p.relative_to(R)),'bytes':s.st_size,'mode':stat.S_IMODE(s.st_mode)})
   if p.suffix in ['.json','.log'] and s.st_size<=4*1024**2:raw(p)
 inventory.append({'root':str(root.relative_to(R)),'files':files,'directories':dirs,'logical_bytes':sum(x['bytes'] for x in files)})
assert r22['iterations_sequence_sha256']==r23['iterations_sequence_sha256']
result={'decision':'accepted_narrow_closed_failed_outcome','observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid_absence':absence,'cgroup_absent':g23['cgroup'],'source_current_pins':len(source_checks),'changed_registered_tradingagents_sources_from22':changed,'run23':r23,'run22_comparison':r22,'scope':'No numerical replay, full MCM, update, financial, capacity or external recovery credit. Binary event/tail chains checked as scalar records; arrays not opened. Matching failed marker is not a successful terminal seal; tail lacks a terminal seal. Historical unsealed-journals empty is retained separately.','preservation_roots':inventory,'exclusions':['original graph/dictionary/sample stores','private transport connection/runtime caches','other claims/workflows','global shared lock and parent directories not owned exclusively'],'evidence':pins}
(H/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'decision':result['decision'],'source_checks':len(source_checks),'selected_evidence':len(pins),'iterations':r23['iterations_sum'],'roots':[{k:v for k,v in x.items() if k!='files'} for x in inventory],'changed_sources':changed}))
