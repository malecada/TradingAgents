"""Prospective105 metadata accounting only; no admission, claim, numerical or Git action."""
import ast,hashlib,json,re,resource,signal
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(384*1024**2,384*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(20,20));signal.alarm(40)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];D=F/'real-data-pilot-full34-cumulative-preparation01-2026-10-11';O=F/'real-data-pilot-full33-cumulative-preparation01-2026-10-11';V=F/'pilot33-cumulative-machine-review01-2026-10-11';refs={};checks={}
def sha(b):return hashlib.sha256(b).hexdigest()
def rb(p):
 assert not ({'.git','.venv','keys','apis','research_artifacts'}&set(p.parts));assert not p.is_symlink() and p.stat().st_size<2*1024**2
 b=p.read_bytes();refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':sha(b)};return b
def j(p):return json.loads(rb(p))
def ck(v,n):
 checks[n]=bool(v)
 if not v:raise AssertionError(n)
def save(name,v):
 with (P/name).open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
try:
 manifest=j(D/'MANIFEST01.json')
 for key in ('allocation','extension','charter','actual_prior_terminal_review'):
  row=manifest[key];b=rb(R/row['path']);ck(sha(b)==row['sha256'],'frozen proposal '+key)
 a=j(D/'CUMULATIVE_ALLOCATION_PROPOSED105_01.json');x=j(D/'EXTENSION_PROPOSED105_01.json');ck(sha((D/'CUMULATIVE_ALLOCATION_PROPOSED105_01.json').read_bytes())=='95ac76412f6e982657407e398e5d3abbcf57714e188350320b5d2d9330598264' and sha((D/'EXTENSION_PROPOSED105_01.json').read_bytes())=='8c46d83287b7a5fb14a2e0c2686ad9be09bea7638e3fe0bd397af79f3a0d6cbf','exact parent proposal anchors')
 olda=j(O/'CUMULATIVE_ALLOCATION_PROPOSED104_01.json');oldx=j(O/'EXTENSION_PROPOSED104_01.json');prior=j(V/'EXTENSION104_REVIEW01.json');pv=j(V/'VALIDATION01.json');pm=j(V/'MANIFEST01.json')
 for name in ('EXTENSION104_REVIEW01.json','VALIDATION01.json'):ck(refs[str((V/name).relative_to(R))]['sha256']==pm['files'][name]['sha256'],'prior accepted manifest '+name)
 ck(prior['decision']=='accepted' and prior['extension_sha256']==sha((O/'EXTENSION_PROPOSED104_01.json').read_bytes()) and pv['decision']=='ACCEPT_EXACT104_BUDGET_PROPOSAL_ONLY','accepted104 actual metadata baseline')
 ck(x['claims']==a['closed_claims'] and x['claims'][:-1]==oldx['claims']==olda['closed_claims'] and len(x['claims'])==56,'exact immutable55 plus single actual33 append')
 row=x['claims'][-1];ck(row['experiment']=='eth-paper-real-data-end-to-end-resource-20261011-33' and row['terminal_status']=='failed','sole appended original failed33')
 for new,old,changed in [(a,olda,{'consumed_before','equation','identities','prior_adopted_cumulative_ceiling','prior_reviewed_reserved_ceiling','proposed_cumulative_ceiling','question','qualification','closed_claims'}),(x,oldx,{'allocation','claims','consumed_before','cumulative_ceiling','initial_experiment','reason'})]:ck(set(new)==set(old) and {k for k in new if new[k]!=old[k]}==changed,'exact changed-field inverse '+('allocation' if new is a else 'extension'))
 ck(set(x['allocation'])=={'path','sha256'} and x['allocation']['path']==str((D/'CUMULATIVE_ALLOCATION_PROPOSED105_01.json').relative_to(R)) and x['allocation']['sha256']==refs[x['allocation']['path']]['sha256'],'strict exact allocation binding')
 ck(a['unchanged_pending_allocation']==olda['unchanged_pending_allocation']=={'financial_fit_batches':15,'missing_body_batches':12,'remaining_graph_matching_mcm_resource':1} and a['preserved_reserved_preclaim_allowances']==olda['preserved_reserved_preclaim_allowances'] and len(a['preserved_reserved_preclaim_allowances'])==3,'28 pending and3 permanent reserved categories unchanged')
 ck(all(a[k]==0 for k in ('refunds','category_transfers','historical_claims_reopened','new_financial_fits')) and a['maximum_unique_financial_fits_unchanged']==1420,'no refund transfer reopening or financial fit increment')
 ck(a['identities']==[x['initial_experiment']]==['eth-paper-real-data-end-to-end-resource-20261011-34'] and a['new_fixed_allocation']=={'full_seven_graph_joint_update_resource_pilot_claims':1},'one exact fresh34 fixed allowance')
 ck(a['consumed_before']==x['consumed_before']==73 and a['prior_adopted_cumulative_ceiling']==a['prior_reviewed_reserved_ceiling']==104 and 73+28+3+1==a['proposed_cumulative_ceiling']==x['cumulative_ceiling']==105,'105 equals73 spent plus28 pending plus3 reserved plus1 new')
 actual33=j(F/'pilot33-terminal-outcome-review01-2026-10-11/REVIEW01.json');ck(refs[str((F/'pilot33-terminal-outcome-review01-2026-10-11/REVIEW01.json').relative_to(R))]['sha256']=='5047103b1a6cad4f95767dc504fd5d751f70b791169527d6480608f2d40e5279','accepted actual33 terminal review')
 claim=j(R/'research_runs'/row['experiment']/'claim.json');terminal=j(R/'research_runs'/row['experiment']/'failed.json');ck(row['claim_sha256']==actual33['claim_sha256']==refs[str(Path('research_runs')/row['experiment']/'claim.json')]['sha256'] and row['terminal_sha256']==actual33['failed_sha256']==refs[str(Path('research_runs')/row['experiment']/'failed.json')]['sha256'] and terminal['claim_sha256']==row['claim_sha256'],'new actual33 raw claim terminal byte joins')
 ck(claim['effective_attempt_budget']==104 and claim['family']==x['base_family'] and terminal['status']=='failed' and not (R/'research_runs'/row['experiment']/'complete.json').exists(),'actual33 spent104 same family single failed terminal')
 ck(x['base_family']==oldx['base_family'] and x['base_family']['prior_attempts']==17 and pv['historical_counts_reused']=={'complete':13,'failed':4} and pv['actual_closed_counts']=={'complete':20,'failed':35},'immutable17 historical plus prior55 closed counts reused')
 counts={k:sum(r['terminal_status']==k for r in x['claims']) for k in ('complete','failed')};ck(counts=={'complete':20,'failed':36} and counts['complete']+13==33 and counts['failed']+4==40,'actual55 plus historical17 equals73closed33C39F')
 census=j(F/'pilot31-cumulative-machine-review01-2026-10-11/VALIDATION01.json');known={Path(p).parent.name for p in census['references'] if p.startswith('research_runs/') and p.endswith('/claim.json')};current={p.name for p in (R/'research_runs').iterdir() if not p.name.startswith('.')};ck(current==known|{'eth-paper-real-data-end-to-end-resource-20261011-31','eth-paper-real-data-end-to-end-resource-20261011-32','eth-paper-real-data-end-to-end-resource-20261011-33'},'current directory census only prior31/32/33 additions; no omitted new active identity')
 ck(not (R/'research_runs'/x['initial_experiment']).exists() and all(not (R/'research_runs'/v['identity']).exists() for v in a['preserved_reserved_preclaim_allowances']),'fresh34 unclaimed and reserved preclaims not reopened')
 # Read only genuine claim metadata needed by unmodified effective_budget; no cohort matrix replay.
 relevant=[]
 for record in x['claims']:
  p=R/'research_runs'/record['experiment']/'claim.json';c=claim if record is row else j(p);assert c['family']==x['base_family'] and c['experiment_id']==record['experiment'];relevant.append(c)
 ck(max(c.get('effective_attempt_budget',51) for c in relevant)==104,'actual highest adopted remains104')
 charter=rb(D/'CHARTER01.md').decode()
 ck(manifest['identity']==x['initial_experiment'] and manifest['claim'] is False and manifest['admission'] is False and manifest['source_candidate']['sha256']=='abd86e24681f0df4ef3ca82cfb016662d9af5a46a38a32bafc65e7c92f2dacf8','prospective candidate reference only; source acceptance and admission separate')
 ck(all(v in charter for v in ('Original32motifs/512spent samples','frozenmodel20f451/trainingd527','full415968128cells','unchanged60-second lease','native6GiBmax/5GiBhigh/swap0/twoCPU/8hours/10GiBfloor','Actual phase durations, speed and capacity remain unmeasured','Independent exact source, cumulative allowance and caller reviews plus actual complete failed33 outcome recovery must precede empirical execution')),'charter fixed method scheduler caps and unmeasured runtime; separate source and recovery prerequisites')
 review={'schema_version':1,'decision':'accepted','extension_sha256':sha((D/'EXTENSION_PROPOSED105_01.json').read_bytes()),'reviewer':'Independent pilot34 cumulative accounting reviewer','scope':'Exact cumulative proposal only:105=73 permanently spent(17 historical+56 actual closed;33 complete/40 failed)+28 unchanged pending+3 preserved closed preclaim reserves+1 fresh fixed unused34. Prior55 immutable rows and historical17 reused; actual33 claim/failed hashes appended; unchanged genuine effective_budget reauthenticates all56 terminal bindings. Highest adopted remains104; no adoption/refund/transfer/reopening/new financial fits; maximum1420 unchanged. Original method,60-second scheduler and resource caps remain fixed. Candidate abd86e source/caller review and complete failed33 external recovery are separate prerequisites; candidate correctness, phase timing, speed and capacity are not accepted here. Final registration/binding/current-entry recovery/live preflight also remain required. No Main/Git/registration/Owner/claim/native/scientific execution or launch authority.'}
 review_body=(json.dumps(review,indent=2,sort_keys=True)+'\n').encode();rp=str((P/'EXTENSION105_REVIEW01.json').relative_to(R));reference={'extension':{'path':str((D/'EXTENSION_PROPOSED105_01.json').relative_to(R)),'sha256':review['extension_sha256']},'review':{'path':rp,'sha256':sha(review_body)}}
 source=rb(R/'tradingagents/research/budget_extensions.py');ck(sha(source)=='59d22880e9ff7909508db6b0c15a7a833df30be365af4e31d643ed64afabb25a','unchanged actual budget validator')
 ns={'hashlib':hashlib,'json':json,'re':re};exec(compile(ast.Module(body=[n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='effective_budget'],type_ignores=[]),'actual-pure-budget-metadata','exec'),ns)
 def read_bound(v):
  assert set(v)=={'path','sha256'};b=review_body if v['path']==rp else rb(R/v['path']);assert sha(b)==v['sha256'];return b
 ck(ns['effective_budget'](R,x['program_id'],x['initial_experiment'],{'cumulative_budget_extension':reference},x['base_family'],relevant,read_bound)==105,'actual pure effective_budget validates56 raw terminal bindings and returns105; no adoption')
 with (P/'EXTENSION105_REVIEW01.json').open('xb') as f:f.write(review_body)
 save('VALIDATION01.json',{'decision':'ACCEPT_EXACT105_BUDGET_PROPOSAL_ONLY','checks':checks,'references':refs,'equation':'105=73+28+3+1','actual_closed_counts':counts,'historical_counts_reused':{'complete':13,'failed':4},'highest_adopted':104,'review_ref':reference['review'],'new_claim_or_adoption':False})
 print(json.dumps({'checks':len(checks),'review':reference['review'],'equation':'105=73+28+3+1'},sort_keys=True))
except BaseException as e:save('FAILED_CHECK01.json',{'error':repr(e),'checks':checks,'references':refs});raise
