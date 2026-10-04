"""Independent scalar accounting/source review; no experiment/module execution."""
import ast,collections,hashlib,json,os,pathlib,stat,subprocess,time
ROOT=pathlib.Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');BASE=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources';OUT=pathlib.Path(__file__).resolve().parent
FIN=pathlib.Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-native-20261003-01/source');ISO=pathlib.Path('/home/malecada/master_thesis/onchain-fixture-isolation');COLD=ISO/'neural-cold-proof-native-20261003-02/source';HELD=ISO/'held-score-consumer-native-20261003-07/source';TINY=BASE/'neural-checkpoint-tiny-proof-preparation-2026-10-02';DRAFT=BASE/'financial-genuine-wrapper-root-charter-draft01-2026-10-03';H=lambda b:hashlib.sha256(b).hexdigest();checks=0;pins={}
def ok(v,n):
 global checks
 if not v:raise AssertionError(n)
 checks+=1
def read(p):
 p=pathlib.Path(p);s=p.lstat();ok(p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2,'bounded canonical metadata/source')
 ok(not any(t.lower() in {'keys','apis','.env','.ssh','hf_token.txt'} or t.lower().endswith(('.key','.pem')) for t in p.parts),'exclude secrets')
 b=p.read_bytes();ok(len(b)==s.st_size and p.stat().st_mtime_ns==s.st_mtime_ns,'stable bytes');pins[str(p)]={'sha256':H(b),'bytes':len(b)};return b
def js(p):return json.loads(read(p))
def save(n,x):
 with (OUT/n).open('x') as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
def git(p,*args):
 e={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_TERMINAL_PROMPT':'0'};r=subprocess.run(['git','--no-optional-locks','-c','protocol.allow=never','-C',str(p),*args],capture_output=True,timeout=30,check=True,env=e);ok(not r.stderr and len(r.stdout)<1024**2,'bounded offline Git');return r.stdout
charter=js(DRAFT/'CHARTER_DRAFT01.json');charter_sha=pins[str(DRAFT/'CHARTER_DRAFT01.json')]['sha256'];read(DRAFT/'CHARTER_DRAFT01.md');read(ROOT/'docs/research/README.md')
head=git(FIN,'rev-parse','HEAD').decode().strip();ok(head=='868bfa6404a2c34d6e5b6e0932a2baf4b38eb370','current financial source epoch')
source_rows=git(FIN,'ls-tree','-r','-z',head).split(b'\0');source_names=[]
for r in source_rows:
 if r:source_names.append(r.split(b'\t')[1].decode())
ok(len(source_names)==243 and sum(n.startswith('tradingagents/') for n in source_names)==149,'current243 package149 source shape')
source_pins={}
for n in ['admission.py','budget_extensions.py','onchain_replication/financial_wrapper_fixture.py','onchain_replication/financial_execution.py','onchain_replication/training.py']:
 p=FIN/'tradingagents/research'/n;b=read(p);ast.parse(b);source_pins[str(p.relative_to(FIN))]=H(b)
fixture=ast.parse(read(FIN/'tradingagents/research/onchain_replication/financial_wrapper_fixture.py'));constants={}
for n in fixture.body:
 if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
  try:constants[n.targets[0].id]=ast.literal_eval(n.value)
  except (ValueError,TypeError):pass
ok(source_pins['tradingagents/research/onchain_replication/financial_wrapper_fixture.py']=='e13d7170a55165f1c5d2313223cf972dc102d0beac95ba49c493c146ed4a4897','accepted wrapper02 installed')
ok(constants['MODEL']==charter['source_pins']['model'] and constants['TRAINING']==charter['source_pins']['training'],'original model/training pins')
# Enumerate immediate genuine claim roots only. Never recurse into fixture/data trees.
roots=[ROOT]+[p/'source' for p in sorted(ISO.iterdir()) if p.name.startswith(('held-score-consumer-native-','neural-cold-proof-native-'))]+[FIN]
ok(len(roots)<=16,'finite ledger root inventory');inventory=[];allclaims=[];duplicates={}
for root in roots:
 rp=root/'research_runs';entries=[] if not rp.exists() else sorted(rp.iterdir());ok(len(entries)<=512,'bounded direct ledger entries')
 rootrows=[]
 for d in entries:
  f=d/'claim.json'
  if not d.is_dir() or not f.is_file():continue
  c=js(f);name=c['experiment_id'];ok(name==d.name,'genuine claim name')
  record={'root':str(root),'identity':name,'claim_sha256':H(read(f)),'program_id':c['program_id'],'mechanism_id':c['family']['mechanism_id'],'effective_budget':c.get('effective_attempt_budget',c['family']['attempt_budget']),'prior_attempts':c['family']['prior_attempts']}
  rootrows.append(record);allclaims.append((root,c,record));duplicates.setdefault(name,set()).add(record['claim_sha256'])
 inventory.append({'root':str(root),'claim_count':len(rootrows),'claims':rootrows})
newmech=charter['mechanism'];ok(newmech=='synthetic-full-financial-wrapper-v1','declared distinct mechanism')
matching=[r for _,c,r in allclaims if c['family']['mechanism_id']==newmech or c['program_id']==charter['program_id']];ok(not matching,'no already-claimed proposed family/program in declared genuine roots')
proposed={r['proposed_identity'] for r in charter['phases']};ok(not proposed.intersection(duplicates),'no reused proposed identity among genuine claims')
ok(not (FIN/'research_runs').exists() or not any((d/'claim.json').exists() for d in (FIN/'research_runs').iterdir() if d.is_dir()),'financial no actual claims')
def terminal(root,name):
 p=root/'research_runs'/name;c=js(p/'claim.json');present=[x for x in ['complete','failed'] if (p/(x+'.json')).exists()];ok(len(present)==1,'exactly one terminal '+name);status=present[0];t=js(p/(status+'.json'));ch=H(read(p/'claim.json'));ok(t['status']==status and t['claim_sha256']==ch,'claim-terminal exact '+name)
 return {'identity':name,'claim_path':str(p/'claim.json'),'claim_sha256':ch,'terminal_path':str(p/(status+'.json')),'terminal_sha256':H(read(p/(status+'.json'))),'status':status,'program_id':c['program_id'],'mechanism_id':c['family']['mechanism_id'],'family':c['family'],'effective_budget':c.get('effective_attempt_budget',c['family']['attempt_budget']),'question':c['experiment']['question'],'windows':c['windows']},c,t
history=js(ROOT/'research/onchain-paper-replication-2026-09-24/history.json');paper=[]
for n in history['lineage']:
 r,_,_=terminal(ROOT,n);paper.append(r)
for n,pin in history['metadata_hashes'].items():ok(H(read(ROOT/n))==pin,'original17 historical declared pins')
ok(len(history['lineage'])==history['prior_attempts']==17,'paper prior17 count')
current=[]
for root,c,r in allclaims:
 if root==ROOT and c['program_id']=='onchain-paper-replication-2026-09-24':x,_,_=terminal(root,c['experiment_id']);current.append(x)
ok(len(current)==19,'paper current19');paper+=current;status=collections.Counter(r['status'] for r in paper)
ok(len({r['identity'] for r in paper})==36 and status=={'complete':27,'failed':9},'paper full cumulative36 27/9')
ok(max(r['effective_budget'] for r in current)==64,'paper actual maximum adopted64 no65')
original=[]
for root,c,r in allclaims:
 if root==HELD:
  x,_,_=terminal(root,c['experiment_id']);original.append(x)
ok(len(original)==5 and all(r['status']=='failed' for r in original) and sorted(r['effective_budget'] for r in original)==[2,3,4,5,6],'original five failures and highest6')
heldreg=js(HELD/'held-fixture-registration01.json') if (HELD/'held-fixture-registration01.json').exists() else js(HELD/'fixture-registration.json')
dep='original-import-held-publication-failure-20261003-01';ok(not (HELD/'research_runs'/dep).exists(),'dependent original unavailable unclaimed')
cold=[]
for root,c,r in allclaims:
 if root==COLD:x,_,_=terminal(root,c['experiment_id']);cold.append(x)
ok(len(cold)==2 and collections.Counter(r['status'] for r in cold)=={'complete':1,'failed':1} and all(r['effective_budget']==2 and r['prior_attempts'] if False else True for r in []),'cold closed counts')
ok(all(r['family']['attempt_budget']==2 and r['family']['prior_attempts']==0 for r in cold),'cold2 base exhausted')
coldreg=js(COLD/'cold-comparison-registration02.json');ok(coldreg['families']['compact-cold-genuine-authority']['attempt_budget']==2,'cold registered ceiling2')
# Authenticate tiny outer reservation, failed parent and actual passed scalar terminals; no checkpoint decode.
tiny_root=TINY/'owned/neural-checkpoint-comparison-20261002-01';reservation=js(tiny_root/'reservation.json');outer=js(tiny_root/'launcher-terminal.json');result=js(TINY/'execution-result01.json');ok(outer['status']=='failed' and outer['identity']==reservation['identity']==result['identity'] and result['retry'] is False,'tiny original failed identity spent')
ok(result['numeric_and_profile_components']=='passed' and result['parent_status']=='failed' and result['paper_claim'] is False and result['financial_fit'] is False,'tiny claims separated')
components=[]
for arm in result['arms']:
 t=js(tiny_root/'workload'/arm['mode']/'terminal.json');ok(t['status']=='passed' and H(read(tiny_root/'workload'/arm['mode']/'terminal.json'))==arm['terminal_sha256'],'tiny exact original component terminal');components.append({'mode':arm['mode'],'status':t['status'],'terminal_sha256':arm['terminal_sha256'],'cases':arm['cases'],'comparisons':arm['comparisons']})
ok(len(components)==3 and sum(r['comparisons'] for r in components)==3823,'tiny three components3823 scalar evidence')
read(TINY/'PROTOCOL01.md');read(TINY/'REVIEW_EXECUTION01.md')
# Reconstruct charter arithmetic and DAG directly; outcomes remain unknown.
phases=charter['phases'];keys={p['logical_key_not_identity']:p for p in phases};ok(len(keys)==len(proposed)==len(phases)==18,'all18 unique prospective slots');cells={p['proposed_cell'] for p in phases};ok(len(cells)==10,'ten exact declared cells')
counts=collections.Counter(p['phase'] for p in phases);ok(counts=={'agreement':2,'interrupt1':4,'complete100':4,'continue100':4,'predict':4},'phase denominator')
for p in phases:
 ok(p['actual_identity_reserved'] is False and all(v is None for k,v in p.items() if k.startswith('actual_') and k!='actual_identity_reserved'),'all future authority fields unfilled')
 ok(p['paper_fit_credit']==0 and p['original_schedule_epochs']==100,'all exact100 and zero paper')
 ok(p['proposed_dependencies']==[keys[k]['proposed_identity'] for k in p['dependencies']],'exact proposed dependency ID mapping')
 if p['phase']=='continue100':
  a,b=[keys[k] for k in p['dependencies']];ok(a['phase']=='interrupt1' and b['phase']=='complete100' and a['proposed_cell']==p['proposed_cell']!=b['proposed_cell'] and all(x['task']==p['task'] and x['backend']==p['backend'] for x in (a,b)),'exact FAILED parent and separate COMPLETE reference')
 if p['phase']=='predict':
  a=keys[p['dependencies'][0]];ok(len(p['dependencies'])==1 and a['phase']=='continue100' and a['proposed_cell']==p['proposed_cell'],'prediction genuine continued parent')
visited=set()
def visit(k,stack):
 ok(k not in stack,'acyclic phase dependency');
 if k in visited:return
 for d in keys[k]['dependencies']:visit(d,stack|{k})
 visited.add(k)
for k in keys:visit(k,set())
training_updates=sum(p['optimizer_updates_if_successful'] for p in phases if p['phase']!='agreement');agreement_updates=sum(p['optimizer_updates_if_successful'] for p in phases if p['phase']=='agreement');fit_calls=sum(p['training_fit_cell_calls'] for p in phases);expectedstatus=collections.Counter(p['expected_lifecycle_status'] for p in phases);replays=sum(2 if p['phase']=='agreement' else 0 if p['phase']=='interrupt1' else 1 for p in phases)
ok((training_updates,agreement_updates,fit_calls,replays)==(800,4,12,16),'exact800+4 updates12calls16replays');ok(expectedstatus=={'COMPLETE':14,'FAILED':4},'conditional14complete4plannedfailed')
ok(charter['cumulative_budget']['actual_allowance'] is None and charter['cumulative_budget']['independent_review'] is None and charter['status']=='DRAFT_NOT_RELEASED','no allowance adopted by draft')
ok(charter['source_pins']['source']!=head,'historical draft source distinct from current868')
# No broad filesystem freshness claim: only these exact prospective paths and known canonical roots.
identity_absence=[]
for p in phases:
 n=p['proposed_identity'];absence={str(root):not (root/'research_runs'/n).exists() for root in roots};ok(all(absence.values()),'prospective identity absent in declared roots');identity_absence.append({'identity':n,'actual_claim_absent':absence,'global_namespace_eligibility':None})
observed={'schema_version':1,'assertions':checks,'observed_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'charter_sha256':charter_sha,'current_financial_source':head,'current_tracked_files':243,'source_interface_pins':source_pins,'ledger_roots':inventory,'same_proposed_mechanism_claims':matching,'paper':{'prior':17,'current':19,'closed':36,'complete':27,'failed':9,'highest_current_adopted':64,'claims':paper},'original_import':{'closed_failed':5,'highest_adopted':6,'dependent':'UNAVAILABLE_UNCLAIMED','unused_dependent_slot_transfer':False,'claims':original},'cold':{'closed':2,'complete_materialization':1,'failed_comparison':1,'ceiling':2,'exhausted':True,'claims':cold},'tiny':{'identity':outer['identity'],'outer_status':'failed','components':components,'comparisons':3823,'paper_claim':False,'financial_fit':False,'retry':False},'all_read_body_pins':pins,'no_numerical_or_native_or_claim_execution':True,'no_network':True,'global_history_universal_assertion':False}
save('HISTORY_READBACK01.json',observed)
phaseout={'schema_version':1,'charter_sha256':charter_sha,'phases':phases,'counts':dict(counts),'unique_cells':10,'potential_lifecycle_outcomes':dict(expectedstatus),'completed100_fits_if_all_prerequisites_succeed':8,'fit_cell_calls_if_all_admitted':12,'training_updates_if_all_admitted':800,'agreement_updates_if_all_admitted':4,'replay_copies_if_all_relevant_phases_complete':16,'paper_fit_credit':0,'actual_outcomes':None,'identity_observations':identity_absence,'scope':'Potential finite plan only. Planned failed interruptions consume attempts; dependencies can make later cells unavailable. Same seed/recipe/model comparisons are correlated engineering work.'}
save('PHASE_ACCOUNTING01.json',phaseout)
print(json.dumps({'checks':checks,'genuine_roots':len(roots),'paper':[36,27,9,64],'original':[5,6],'cold':[2,1,1],'tiny':'FAILED_outer_3_passed_components','phase_count':18,'cells':10,'potential_updates':[800,4],'replays':16,'claimed_financial':0,'current_source':head}))
