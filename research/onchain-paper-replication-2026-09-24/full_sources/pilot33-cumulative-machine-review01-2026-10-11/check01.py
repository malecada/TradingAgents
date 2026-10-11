"""Prospective104 metadata accounting only; no admission, claim, numerical or Git action."""
import ast,hashlib,json,re,resource,signal
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(384*1024**2,384*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(20,20));signal.alarm(40)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];D=F/'real-data-pilot-full33-cumulative-preparation01-2026-10-11';O=F/'real-data-pilot-full32-cumulative-preparation01-2026-10-11';V=F/'pilot32-cumulative-machine-review01-2026-10-11';refs={};checks={}
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
 for row in manifest['rows']:b=rb(R/row['path']);ck(sha(b)==row['sha256'] and len(b)==row['bytes'],'frozen proposal '+Path(row['path']).name)
 a=j(D/'CUMULATIVE_ALLOCATION_PROPOSED104_01.json');x=j(D/'EXTENSION_PROPOSED104_01.json');ck(sha((D/'CUMULATIVE_ALLOCATION_PROPOSED104_01.json').read_bytes())=='022ce89a0f60b20cd6548bd01b4a17e24e19ddf0bbfdd3333b83399a95ff07d3' and sha((D/'EXTENSION_PROPOSED104_01.json').read_bytes())=='4ddbe4e1664bf5dd78c02f41cd8816f04f82f328845e6b5bb23f703132211789','exact parent proposal anchors')
 olda=j(O/'CUMULATIVE_ALLOCATION_PROPOSED103_01.json');oldx=j(O/'EXTENSION_PROPOSED103_01.json');prior=j(V/'EXTENSION103_REVIEW01.json');pv=j(V/'VALIDATION01.json');pm=j(V/'MANIFEST01.json')
 for name in ('EXTENSION103_REVIEW01.json','VALIDATION01.json'):ck(refs[str((V/name).relative_to(R))]['sha256']==pm['files'][name]['sha256'],'prior accepted manifest '+name)
 ck(prior['decision']=='accepted' and prior['extension_sha256']==sha((O/'EXTENSION_PROPOSED103_01.json').read_bytes()) and pv['decision']=='ACCEPT_EXACT103_BUDGET_PROPOSAL_ONLY','accepted103 actual metadata baseline')
 ck(x['claims']==a['closed_claims'] and x['claims'][:-1]==oldx['claims']==olda['closed_claims'] and len(x['claims'])==55,'exact immutable54 plus single actual32 append')
 row=x['claims'][-1];ck(row['experiment']=='eth-paper-real-data-end-to-end-resource-20261011-32' and row['terminal_status']=='failed','sole appended original failed32')
 for new,old,changed in [(a,olda,{'consumed_before','equation','identities','prior_adopted_cumulative_ceiling','prior_reviewed_reserved_ceiling','proposed_cumulative_ceiling','question','qualification','closed_claims'}),(x,oldx,{'allocation','claims','consumed_before','cumulative_ceiling','initial_experiment','reason'})]:ck(set(new)==set(old) and {k for k in new if new[k]!=old[k]}==changed,'exact changed-field inverse '+('allocation' if new is a else 'extension'))
 ck(set(x['allocation'])=={'path','sha256'} and x['allocation']['path']==str((D/'CUMULATIVE_ALLOCATION_PROPOSED104_01.json').relative_to(R)) and x['allocation']['sha256']==refs[x['allocation']['path']]['sha256'],'strict exact allocation binding')
 ck(a['unchanged_pending_allocation']==olda['unchanged_pending_allocation']=={'financial_fit_batches':15,'missing_body_batches':12,'remaining_graph_matching_mcm_resource':1} and a['preserved_reserved_preclaim_allowances']==olda['preserved_reserved_preclaim_allowances'] and len(a['preserved_reserved_preclaim_allowances'])==3,'28 pending and3 permanent reserved categories unchanged')
 ck(all(a[k]==0 for k in ('refunds','category_transfers','historical_claims_reopened','new_financial_fits')) and a['maximum_unique_financial_fits_unchanged']==1420,'no refund transfer reopening or financial fit increment')
 ck(a['identities']==[x['initial_experiment']]==['eth-paper-real-data-end-to-end-resource-20261011-33'] and a['new_fixed_allocation']=={'full_seven_graph_joint_update_resource_pilot_claims':1},'one exact fresh33 fixed allowance')
 ck(a['consumed_before']==x['consumed_before']==72 and a['prior_adopted_cumulative_ceiling']==a['prior_reviewed_reserved_ceiling']==103 and 72+28+3+1==a['proposed_cumulative_ceiling']==x['cumulative_ceiling']==104,'104 equals72 spent plus28 pending plus3 reserved plus1 new')
 actual32=j(F/'pilot32-terminal-outcome-review01-2026-10-11/REVIEW01.json');ck(refs[str((F/'pilot32-terminal-outcome-review01-2026-10-11/REVIEW01.json').relative_to(R))]['sha256']=='bbcd9d0e7474890fecc034e6ea7969c13a885f15ac593cf81e2d1d732bd196e9','accepted actual32 terminal review')
 claim=j(R/'research_runs'/row['experiment']/'claim.json');terminal=j(R/'research_runs'/row['experiment']/'failed.json');ck(row['claim_sha256']==actual32['claim_sha256']==refs[str(Path('research_runs')/row['experiment']/'claim.json')]['sha256'] and row['terminal_sha256']==actual32['failed_sha256']==refs[str(Path('research_runs')/row['experiment']/'failed.json')]['sha256'] and terminal['claim_sha256']==row['claim_sha256'],'new actual32 raw claim terminal byte joins')
 ck(claim['effective_attempt_budget']==103 and claim['family']==x['base_family'] and terminal['status']=='failed' and not (R/'research_runs'/row['experiment']/'complete.json').exists(),'actual32 spent103 same family single failed terminal')
 ck(x['base_family']==oldx['base_family'] and x['base_family']['prior_attempts']==17 and pv['historical_counts_reused']=={'complete':13,'failed':4} and pv['actual_closed_counts']=={'complete':20,'failed':34},'immutable17 historical plus prior54 closed counts reused')
 counts={k:sum(r['terminal_status']==k for r in x['claims']) for k in ('complete','failed')};ck(counts=={'complete':20,'failed':35} and counts['complete']+13==33 and counts['failed']+4==39,'actual55 plus historical17 equals72closed33C39F')
 census=j(F/'pilot31-cumulative-machine-review01-2026-10-11/VALIDATION01.json');known={Path(p).parent.name for p in census['references'] if p.startswith('research_runs/') and p.endswith('/claim.json')};current={p.name for p in (R/'research_runs').iterdir() if not p.name.startswith('.')};ck(current==known|{'eth-paper-real-data-end-to-end-resource-20261011-31','eth-paper-real-data-end-to-end-resource-20261011-32'},'current directory census only prior31 and32 additions; no omitted new active identity')
 ck(not (R/'research_runs'/x['initial_experiment']).exists() and all(not (R/'research_runs'/v['identity']).exists() for v in a['preserved_reserved_preclaim_allowances']),'fresh33 unclaimed and reserved preclaims not reopened')
 # Read only genuine claim metadata needed by unmodified effective_budget; no cohort matrix replay.
 relevant=[]
 for record in x['claims']:
  p=R/'research_runs'/record['experiment']/'claim.json';c=claim if record is row else j(p);assert c['family']==x['base_family'] and c['experiment_id']==record['experiment'];relevant.append(c)
 ck(max(c.get('effective_attempt_budget',51) for c in relevant)==103,'actual highest adopted remains103')
 charter=rb(D/'CHARTER01.md').decode();source_review=j(F/'pilot32-preparation-interval-correction-review01-2026-10-11/REVIEW01.json');ck(refs[str((F/'pilot32-preparation-interval-correction-review01-2026-10-11/REVIEW01.json').relative_to(R))]['sha256']=='7e400323f3bbb419fe826f73386fc16803e1ee865dae9ed866512d36b364a2df' and source_review['decision']=='ACCEPT_SOURCE_ONLY_DISCARDED_IMPORTED_SCOPE_REMOVAL' and source_review['candidate']['sha256']=='becaab002648c440852553ebf1e662702affee96283a07bcb90bdfc2ca7379ca','charter selected exact independently accepted source candidate')
 ck(all(v in charter for v in ('Original32motifs/512spent samples/sevenWHOLEgraphs/415968128MCM cells','GAT→attentionLSTM real joint update/checkpoint','Original60second lease remains','Actual saving from the removed traversal is unknown','6GiBmax/5GiBhigh/swap0/twoCPUs/8h/2.5GiBstartup+hostreserve/1GiBFSIZE/10GiBdiskfloor','16GiBlogical/20GiBallocated','becaab002648c440852553ebf1e662702affee96283a07bcb90bdfc2ca7379ca')),'charter fixed method caps60s and unknown saving; no cap ladder')
 review={'schema_version':1,'decision':'accepted','extension_sha256':sha((D/'EXTENSION_PROPOSED104_01.json').read_bytes()),'reviewer':'Independent pilot33 cumulative accounting reviewer','scope':'Exact cumulative proposal only:104=72 permanently spent(17 historical+55 actual closed;33 complete/39 failed)+28 unchanged pending+3 preserved closed preclaim reserves+1 fresh fixed unused33. Prior54 immutable rows and historical17 reused; actual32 claim/failed hashes appended; unmodified genuine effective_budget reauthenticates all55 terminal bindings. Highest adopted remains103, no adoption/refund/transfer/reopening/new financial fits; maximum1420 unchanged. Original scientific method,60s lease and resource limits remain fixed; selected becaab00 source review7e400323 does not establish actual saving. Actual failed32 external recovery acceptance, exact source installation/current caller/registration/transport/full-entry and fresh public preparation recovery remain separate prerequisites. No Main/Git/registration/Owner/claim/native/scientific execution or launch authority.'}
 review_body=(json.dumps(review,indent=2,sort_keys=True)+'\n').encode();rp=str((P/'EXTENSION104_REVIEW01.json').relative_to(R));reference={'extension':{'path':str((D/'EXTENSION_PROPOSED104_01.json').relative_to(R)),'sha256':review['extension_sha256']},'review':{'path':rp,'sha256':sha(review_body)}}
 source=rb(R/'tradingagents/research/budget_extensions.py');ck(sha(source)=='59d22880e9ff7909508db6b0c15a7a833df30be365af4e31d643ed64afabb25a','unchanged actual budget validator')
 ns={'hashlib':hashlib,'json':json,'re':re};exec(compile(ast.Module(body=[n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='effective_budget'],type_ignores=[]),'actual-pure-budget-metadata','exec'),ns)
 def read_bound(v):
  assert set(v)=={'path','sha256'};b=review_body if v['path']==rp else rb(R/v['path']);assert sha(b)==v['sha256'];return b
 ck(ns['effective_budget'](R,x['program_id'],x['initial_experiment'],{'cumulative_budget_extension':reference},x['base_family'],relevant,read_bound)==104,'actual pure effective_budget validates55 raw terminal bindings and returns104; no adoption')
 with (P/'EXTENSION104_REVIEW01.json').open('xb') as f:f.write(review_body)
 save('VALIDATION01.json',{'decision':'ACCEPT_EXACT104_BUDGET_PROPOSAL_ONLY','checks':checks,'references':refs,'equation':'104=72+28+3+1','actual_closed_counts':counts,'historical_counts_reused':{'complete':13,'failed':4},'highest_adopted':103,'review_ref':reference['review'],'new_claim_or_adoption':False})
 print(json.dumps({'checks':len(checks),'review':reference['review'],'equation':'104=72+28+3+1'},sort_keys=True))
except BaseException as e:save('FAILED_CHECK01.json',{'error':repr(e),'checks':checks,'references':refs});raise
