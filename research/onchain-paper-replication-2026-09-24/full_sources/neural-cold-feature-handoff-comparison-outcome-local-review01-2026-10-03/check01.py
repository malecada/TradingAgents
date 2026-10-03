"""Independent bounded byte/metadata review. No array decode or authority replay."""
from pathlib import Path
import hashlib,json,os,stat,subprocess,time
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;OUT=BASE/'neural-cold-feature-handoff-comparison-outcome01-2026-10-03';COL=OUT/'collection01'
start=time.monotonic();checks=[]
def need(ok,why):
 if not ok:raise ValueError(why)
def body(p,limit=4*1024**2):
 s=p.lstat();need(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=limit,'regular bounded file '+str(p));raw=p.read_bytes();need(p.lstat()==s,'changed file '+str(p));return raw
def sha(p,limit=4*1024**2):return hashlib.sha256(body(p,limit)).hexdigest()
def doc(p,limit=4*1024**2):return json.loads(body(p,limit))
def census(root):
 rows=[];size=0;todo=[root]
 while todo:
  p=todo.pop();need(time.monotonic()-start<180,'review scan bound');rel=p.relative_to(root).as_posix();s=p.lstat();need(not stat.S_ISLNK(s.st_mode),'symlink');need(len(p.relative_to(root).parts)<=32,'depth')
  if stat.S_ISDIR(s.st_mode):
   if rel!='.':rows.append({'path':rel,'kind':'directory','mode':stat.S_IMODE(s.st_mode)})
   with os.scandir(p) as it:children=list(it)
   need(len(children)<=32768,'directory count');todo.extend(Path(x.path) for x in children)
  else:
   need(stat.S_ISREG(s.st_mode) and s.st_nlink==1,'special/hardlink');size+=s.st_size;need(size<=1024**3,'tree bytes');rows.append({'path':rel,'kind':'file','mode':stat.S_IMODE(s.st_mode),'bytes':s.st_size,'sha256':sha(p)})
  need(len(rows)+len(todo)<=32768,'tree count')
 return sorted(rows,key=lambda x:x['path'])
q=doc(OUT/'COLLECTION_REQUEST01.json');wait=doc(OUT/'COLLECTION_WAIT01.json');report=doc(COL/'collection.json');root=Path(q['root']);need(wait['exit_code']==0 and wait['first_error_type'] is None,'collector actual wait');need(sha(OUT/'COLLECTION_REQUEST01.json')=='89b718215212a5291f684ef86e25a9c099f5732f185bc3eb705682f70aede5c3','request');need(body(COL/'request.json')==body(OUT/'COLLECTION_REQUEST01.json'),'retained request');need(not body(OUT/'collector.stderr'),'collector stderr')
originals={'capsule':root,**{f'{kind}-{phase}':Path(q['reservation_roots'][phase][kind]) for phase in ('materialize','compare') for kind in ('wrapper','parent')}}
allrows={};counts={}
for name,refs in report['member_pages'].items():
 rows=[]
 for ref in refs:
  p=COL/'members'/name/ref['path'];raw=body(p,8192);need(len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],'page binding');rows.extend(json.loads(raw))
 need(len({x['path'] for x in rows})==len(rows),'unique members');rows=sorted(rows,key=lambda x:x['path']);need(census(COL/'data'/name)==rows,'retained full tree '+name);need(stat.S_IMODE((COL/'data'/name).stat().st_mode)==report['tree_root_modes'][name],'retained root mode')
 if name in originals:
  need(census(originals[name])==rows,'original full tree '+name);need(stat.S_IMODE(originals[name].stat().st_mode)==report['tree_root_modes'][name],'original root mode')
 allrows[name]=rows;counts[name]={'members':len(rows),'files':sum(x['kind']=='file' for x in rows),'directories':sum(x['kind']=='directory' for x in rows),'bytes':sum(x.get('bytes',0) for x in rows)}
checks.append('All original/retained whole names, modes, kinds, lengths and SHA256 joined; no additional members')
external=doc(COL/'data/external-evidence/reference-index.json')['references'];need(len(external)==24,'external count')
for item in external:
 p=Path(item['original']['path']);need(sha(p)==item['original']['sha256']==item['sha256']==sha(COL/'data/external-evidence'/item['retained']),'external original equality')
checks.append('24 original external references retained byte-exact')
def git(*args):return subprocess.check_output(['git','-c','gc.auto=0','-C',str(root),*args],timeout=10).decode().strip()
B='361339125a3f1cd57e7ba8611f5a994ae649fa0b';A='9742c6ec817dd0917f9f35a52e4b83965ca1cd29'
need(git('rev-parse','HEAD')==B and git('rev-list','--parents','-n','1',B)==B+' '+A,'B sole A child')
need(git('diff','--name-only',A,B).splitlines()==['cold-comparison-registration02.json','cold_prep/CHARTER_COMPARE_REGISTERED02.md','cold_prep/compare-evolution02.json','cold_prep/compare-phase-contract02.json'],'exact four additions');need(all(x.startswith('A\t') for x in git('diff','--name-status',A,B).splitlines()),'additions only')
inv=doc(Path(q['inventory']['path']));need(sha(Path(q['inventory']['path']))==q['inventory']['sha256'],'inventory ref');need(inv['source_count']==195 and inv['package_count']==147,'source cardinality')
for x in inv['source_inventory']:need(sha(root/x['target'])==x['sha256'],'selected source '+x['target'])
checks.append('Original B2 sole-parent A2/four additions and all195 selected source bodies unchanged;147 package members')
reg=doc(root/'cold-comparison-registration02.json');identity='compact-cold-comparison-20261003-01';exp=reg['experiments'][identity];need(len(exp['inputs'])==44,'compare44');need(reg['families']['compact-cold-genuine-authority']['attempt_budget']==2 and reg['families']['compact-cold-genuine-authority']['prior_attempts']==0,'finite budget')
for x in exp['inputs'].values():need(sha(root/x['path'])==x['sha256'],'registered original input')
run=root/'research_runs'/identity;claim=doc(run/'claim.json');failed=doc(run/'failed.json');need(failed['claim_sha256']==sha(run/'claim.json') and failed['status']=='failed','failed lifecycle');need(claim['registration_sha256']==sha(root/'cold-comparison-registration02.json'),'failed claim reg');need(not (run/'complete.json').exists(),'not complete');need(len(exp['cells'])==1,'cell denominator');need(not any((run/'outputs'/n).exists() for n in exp['outputs']),'four outputs absent')
mrun=root/'research_runs/compact-cold-inputs-20261003-01';mt=doc(mrun/'complete.json');need(mt['status']=='complete' and mt['claim_sha256']==sha(mrun/'claim.json'),'materialize terminal');need(not (mrun/'failed.json').exists(),'materialize nonfailed')
need(report['outcomes']['compare']['strict_scientific_disposition']=='FAILED_AUTHENTICATED_TERMINAL' and report['outcomes']['materialize']['strict_scientific_disposition']=='MATERIALIZATION_COMPLETE_SCIENCE_PENDING','truthful disposition');need(report['paper_financial_completion'] is False,'no financial completion');checks.append('44 actual comparison inputs pinned; two spent engineering attempts,1 complete materialization/1 failed comparison/1 failed registered comparison cell/4 outputs absent')
runtime=doc(root/'cold_prep/runtime.json');need(len(runtime['distribution_records'])==251,'runtime251');total=0
for x in runtime['distribution_records']:
 p=Path(x['record']);total+=p.stat().st_size;need(total<=64*1024**2,'runtime record total');need(sha(p)==x['record_sha256'],'runtime record')
need(sha(Path(runtime['resolved_executable']))==runtime['executable_sha256'],'interpreter');checks.append('251 original runtime RECORD hashes and resolved interpreter unchanged; no numerical import')
guard=doc(root/f'research_artifacts/onchain-paper-replication-2026-09-24/runs/{identity}/guard/final.json');need(guard['cleanup_verified'] is True and not Path(guard['cgroup']).exists(),'cgroup absent');need(guard['child_exit_code'] is None and guard['cleanup_unit_properties']['ExecMainStatus']=='125' and guard['cleanup_unit_properties']['Result']=='timeout','distinct actual native exits');need(guard['peak_sampled_memory_current_bytes']==443465728 and all(v==0 for v in guard['memory_events'].values()),'native observations')
pids=set(report['outcomes']['compare']['cleanup']['recorded_pids'])|{int(p) for p in guard['cpu_thread_readback']};need(len(pids)==12 and all(not Path('/proc',str(p)).exists() for p in pids),'12 original PID/TIDs absent')
checks.append('12 original PID/TIDs and original cgroup absent;native timeout1800.835859874s/443465728B sampled peak/events0/child exit null/native125 kept distinct')
result={'schema_version':1,'status':'LOCAL_COLLECTION_ACCEPTED_ARCHIVE_PENDING','checks':checks,'root':str(root),'source':B,'collection_sha256':sha(COL/'collection.json'),'counts':counts,'external_refs':len(external),'runtime_records':251,'runtime_record_bytes':total,'original_comparison_pids':sorted(pids),'native_elapsed_seconds':guard['elapsed_seconds'],'archive_reviewed':False,'remote_recovery_reviewed':False,'numerical_decode_or_replay':False,'elapsed_seconds':time.monotonic()-start}
(HERE/'READBACK01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))
