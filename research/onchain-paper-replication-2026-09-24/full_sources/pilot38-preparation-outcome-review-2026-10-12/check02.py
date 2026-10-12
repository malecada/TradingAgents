"""Finite metadata/source/process readback; no research imports or execution."""
import ast, datetime, hashlib, json, os, stat, subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[4]
D=Path(__file__).resolve().parent
F=R/'research/onchain-paper-replication-2026-09-24/full_sources'
N='eth-paper-real-data-end-to-end-resource-20261012-38'
E=F/'real-data-pilot-full38-entry-preparation01-2026-10-12'
run=R/'research_runs'/N; native=R/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/N
A=R/'research_artifacts/onchain_representations/45609a355eec57bcf7fe42650dc961fa1b94b12295041d72d55b8d919354be8f'/N
refs={}; checks=[]
def sha(p):
 p=Path(p); st=p.lstat(); assert stat.S_ISREG(st.st_mode) and not p.is_symlink(),str(p)
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''): h.update(b)
 v=h.hexdigest(); refs[str(p.relative_to(R))]=v; return v
def read(p): sha(p); return json.loads(Path(p).read_bytes())
def yes(name, v):
 assert v,name
 checks.append(name)
def save(name,value):
 with (D/name).open('x') as f: json.dump(value,f,indent=2,sort_keys=True); f.write('\n')
claim=read(run/'claim.json'); failed=read(run/'failed.json'); source=claim['source']
reason='EntryPreparationComplete: registered first-graph entry prepared; no MCM stage or financial fit completed'
yes('original source and identity',source=='989e805ed5ae59126f096135eea43095eaebc81d' and claim['experiment_id']==N)
yes('original failed terminal joins original claim',failed['status']=='failed' and failed['reason']==reason and failed['claim_sha256']==sha(run/'claim.json'))
yes('effective110 and corrected fixed cell',claim['effective_attempt_budget']==110 and claim['experiment']['cells']==['real-eth-first-graph-entry-preparation-resource38'])
gate=read(R/claim['registration']); yes('actual registered gate',sha(R/claim['registration'])==claim['registration_sha256']=='cd22da5d2d036b54e9f7d17af64d9d51e331e5e7b503d3123acc7c46e9de1489')
binding=read(E/'BINDING01.json'); release=read(E/'RELEASE_REVIEW01.json')
yes('exact released binding',sha(E/'BINDING01.json')=='4b1419e0b9de72903bbadca84ca2a30e9aa33d61f7d48196a3f4b2ff233cdac2' and sha(E/'RELEASE_REVIEW01.json')=='b160e8a087cef9f15a98ad2a3a37fc93d6773640bda3f6c18243f4fc60426a8a')
sources=claim['experiment']['source_files'];yes('1036 sources / 73 inputs',len(sources)==1036 and len(claim['inputs'])==73)
for p,h in sources.items():yes('source '+p,sha(R/p)==h==release['evidence'][p])
for role,v in claim['inputs'].items():
 yes('input '+role,sha(R/v['path'])==v['sha256']==release['evidence'][v['path']] and binding['input_refs'][role]=={'path':v['path'],'sha256':v['sha256']})
# Opaque input is hashed as bytes only above; it is never decoded.
outputs={}
for name,h in failed['output_sha256'].items():
 p=run/'outputs'/name;yes('output '+name,sha(p)==h);outputs[name]=h
yes('nine original outputs',len(outputs)==9)
summary=read(run/'outputs/pilot-summary.json'); through=summary['throughput']; cells=read(run/'outputs/cell-ledger.json')
yes('original failed cell ledger',len(cells)==1 and cells[0]['status']=='failed' and cells[0]['reason']==reason and cells[0]['paper_financial_fits']==0)
yes('zero verified totals with original graph nulls preserved',through['verified_completed_motif_cells']==through['verified_completed_nodes']==through['complete_graphs']==0 and through['failed_graphs']==1 and through['unavailable_graphs']==6 and len(through['graphs'])==7 and all(g['completed_motif_cells'] is None and g['completed_nodes'] is None for g in through['graphs']))
yes('first graph / unavailable denominator',through['graphs'][0]['status']=='failed' and through['graphs'][0]['reason']==reason and all(g['status']=='unavailable' for g in through['graphs'][1:]) and sum(g['expected_motif_cells'] for g in through['graphs'])==415968128)
yes('no training / retained targets',summary['training'] is None and summary['retained_target_count']==0 and summary['financial_fit_complete'] is False and summary['original_motifs']==32 and summary['original_samples']==512)
journal=read(A/'failed.json'); owner=read(A/'owner.json'); start=read(A/'start.json'); artclaim=read(A/'claim.json'); co=read(A/'compact/owner.json'); imp=read(A/'compact/dictionary-import/import-complete.json')
yes('genuine owned failed journal',journal['status']=='failed' and journal['reason']==reason and journal['events']==[] and journal['owner']==owner==start['owner'] and owner['experiment']==N and owner['source_commit']==source and journal['required_graphs']==[g['graph_hash'] for g in through['graphs']])
yes('compact binding joins original claim/source/job',co['binding']['claim_sha256']==sha(run/'claim.json') and co['binding']['source_commit']==source and co['binding']['experiment']==N and co['binding']['job_sha256']==claim['inputs']['execution_job']['sha256'])
yes('actual dictionary import receipt and intent',imp['owner']==sha(A/'compact/owner.json') and imp['intent_sha256']==sha(A/'compact/dictionary-import/intent.json') and imp['execution']['current_source']==source and imp['execution']['current_binding']==co['original_import']['current_binding'])
yes('historical import without recomputation',imp['current_matching_pairs']==0 and imp['historical_work_recomputed'] is False and imp['execution']['mcm_execution_admitted'] is False and len(imp['numeric']['ordered_motifs'])==32)
files=[]
for p in sorted(A.rglob('*')):
 yes('artifact path not redirected '+str(p.relative_to(A)),not p.is_symlink())
 if p.is_file():files.append({'path':str(p.relative_to(R)),'sha256':sha(p),'bytes':p.stat().st_size})
yes('exact owned eight-body namespace no MCM stage',len(files)==8 and sorted(str(p.relative_to(A)) for p in A.rglob('*') if p.is_file())==sorted(['owner.json','failed.json','start.json','claim.json','archive-operations/start.json','compact/owner.json','compact/dictionary-import/intent.json','compact/dictionary-import/import-complete.json']))
sp=R/'tradingagents/research/onchain_replication/compact_mcm_batched.py';src=sp.read_text();tree=ast.parse(src); funcs={x.name:x for x in tree.body if isinstance(x,ast.FunctionDef)};prod=funcs['produce'];stop=funcs['_stop_after_entry']
entry=next(x for x in next(x for x in prod.body if isinstance(x,ast.Try)).body if isinstance(x,ast.With)); calls=[x for x in ast.walk(entry) if isinstance(x,ast.Call)]
yes('three full-entry boundaries in preparation frame',sum(isinstance(x.func,ast.Name) and x.func.id=='_entry_lease' for x in calls)==3)
stopcall=next(x for x in ast.walk(prod) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='_stop_after_entry');stagecalls=[x for x in ast.walk(prod) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr in ('_begin','mkdir')]
yes('stop precedes every MCM directory/stage birth',entry.end_lineno<stopcall.lineno<min(x.lineno for x in stagecalls))
raises=[x for x in ast.walk(tree) if isinstance(x,ast.Raise) and isinstance(x.exc,ast.Call) and isinstance(x.exc.func,ast.Name) and x.exc.func.id=='EntryPreparationComplete']
yes('unique genuine preparation stop',len(raises)==1 and stop.lineno<raises[0].lineno<=stop.end_lineno)
yes('unchanged60000ms and live target/owner safeguards',all(x in ast.get_source_segment(src,stop) for x in ["scheduler.policy['max_stale_ms']==60000","<=60000","type(target) is Target","type(lease) is Lease","owner.active is None","owner.stages['dictionary-import'].closed"]))
observer=read(native/'observer.json');guard=read(native/'guard/final.json');launch=read(native/'launch.json'); nativeowner=read(native/'owner.json');closed=read(E/'ROOT_IO_CLOSED01.json');storage=read(E/'FINAL_STORAGE01.json')
yes('observer original terminal/owner/ledger',observer['terminal_sha256']==sha(run/'failed.json') and observer['owner_sha256']==sha(native/'owner.json') and observer['cell_ledger_sha256']==outputs['cell-ledger.json'] and observer['status']=='failed' and observer['cgroup_empty'] and observer['unsealed_journals']==0)
for p,h in observer['evidence_sha256'].items():yes('observer evidence '+p,sha(native/p)==h)
yes('native and root closed original failure',guard['child_exit_code']==closed['actual_parent_exit_code']==1 and guard['cleanup_verified'] and closed['supervisor_reaped'] and closed['outer_log_handles_closed'] and storage['actual_current_cgroup_absent'] and storage['original_monitor_process_absent'] and storage['source']==source)
for p,h in storage['original_metadata_sha256'].items():
 # Original closure map uses the original native relative paths.
 yes('closure metadata '+p,sha(native/({'guard':'guard/final.json','launch':'launch.json','owner':'owner.json'}[p]))==h)
pids={str(p):not Path('/proc',str(p)).exists() for p in (582648,583192,583721,583748)}
cmd=['systemctl','--user','show',guard['unit'],'--property=ActiveState,SubState,MainPID,ControlGroup,ExecMainStatus,Result']
c=subprocess.run(cmd,text=True,capture_output=True,timeout=10); (D/'UNIT01.stdout').write_text(c.stdout);(D/'UNIT01.stderr').write_text(c.stderr)
props=dict(line.split('=',1) for line in c.stdout.splitlines() if '=' in line)
closure={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pids_absent':pids,'cgroup':guard['cgroup'],'cgroup_absent':not Path(guard['cgroup']).exists(),'command':cmd,'exit_code':c.returncode,'properties':props}
save('LIVE_CLOSURE01.json',closure)
yes('fresh all four original PIDs absent',all(pids.values()))
yes('fresh original cgroup absent/unit terminal',closure['cgroup_absent'] and c.returncode==0 and props['MainPID']=='0' and props['ControlGroup']=='' and props['ActiveState']=='failed' and props['ExecMainStatus']=='1')
phase=read(run/'outputs/phase-timing.json');yes('timing non-authoritative / no numeric counters',phase['authority'] is False and phase['numeric_counts']=={})
parent=R/'research_artifacts/onchain-paper-replication-2026-09-24/pilot-parent'/N
for name in ['stdout.log','stderr.log']:sha(parent/name)
save('CHECK02.json',{'schema_version':1,'decision':'accepted','checks':checks,'source':source,'source_count':len(sources),'input_count':len(claim['inputs']),'evidence':refs,'owned_namespace':files,'original_output_sha256':outputs,'closure':closure,'source_stop_lines':[stop.lineno,stop.end_lineno],'source_produce_lines':[prod.lineno,prod.end_lineno]})
print(json.dumps({'decision':'accepted','checks':len(checks),'evidence':len(refs),'source_count':len(sources),'inputs':len(claim['inputs'])}))
