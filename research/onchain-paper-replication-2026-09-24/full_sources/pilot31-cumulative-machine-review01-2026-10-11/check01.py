"""Bounded actual claim metadata census and prospective budget-helper check only."""
import ast,copy,datetime,hashlib,json,re,resource,signal,stat
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,256*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(15,15));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2));signal.alarm(25)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];D=F/'real-data-pilot-full31-cumulative-preparation01-2026-10-11'
checks=[];refs={};read_bytes=0
def sha(b):return hashlib.sha256(b).hexdigest()
def ck(v,n):
    checks.append({'name':n,'pass':bool(v)})
    if not v:raise AssertionError(n)
def read(p):
    global read_bytes
    p=Path(p);s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_size<2*1024**2
    b=p.read_bytes();t=p.lstat();assert (s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(t.st_ino,t.st_size,t.st_mtime_ns,t.st_ctime_ns)
    read_bytes+=len(b);assert read_bytes<32*1024**2
    refs[str(p.relative_to(R))]={'bytes':len(b),'sha256':sha(b)};return b
def js(p):return json.loads(read(p))
m=js(D/'MANIFEST01.json');docs={}
for name in ['new_allocation','new_extension','original_allocation','original_extension']:
    ref=m[name];b=read(R/ref['path']);ck(sha(b)==ref['sha256'],'manifest pin '+name);docs[name]=json.loads(b)
a,x,oa,ox=[docs[k] for k in ['new_allocation','new_extension','original_allocation','original_extension']]
ck(m['new_allocation']['sha256']=='93451038a73d4c5143de1a6000021fcae431b007a2b4b23544a67569cde13fe6' and m['new_extension']['sha256']=='66e77b7e1c4eaf8f7dbecaf8006b52ce538f74afe06914c504e98941193a220c','Root exact draft pins')
ck(a['closed_claims']==x['claims'] and x['claims'][:-1]==ox['claims']==oa['closed_claims'] and len(x['claims'])==53,'append exactly one original closed row')
ck(x['claims'][-1]==m['new_actual_closed_row'] and x['claims'][-1]['experiment']=='eth-paper-real-data-end-to-end-resource-20261011-30','appended genuine30 only')
changed_a={'consumed_before','equation','identities','prior_adopted_cumulative_ceiling','prior_reviewed_reserved_ceiling','proposed_cumulative_ceiling','question','qualification','closed_claims'}
changed_x={'allocation','claims','consumed_before','cumulative_ceiling','initial_experiment','reason'}
for name,new,old,allowed in [('allocation',a,oa,changed_a),('extension',x,ox,changed_x)]:
    ck(set(new)==set(old) and {k for k in new if new[k]!=old[k]}==allowed,'exact changed-field inverse '+name)
    inverse=copy.deepcopy(new)
    for key in allowed:inverse[key]=old[key]
    ck(inverse==old,'inverse recovers entire prior '+name)
ck(a['unchanged_pending_allocation']=={'financial_fit_batches':15,'missing_body_batches':12,'remaining_graph_matching_mcm_resource':1} and len(a['preserved_reserved_preclaim_allowances'])==3,'unchanged28 pending and3 reserved')
ck(all(a[k]==0 for k in ['refunds','category_transfers','historical_claims_reopened','new_financial_fits']) and a['maximum_unique_financial_fits_unchanged']==1420,'no refund transfer reopening financial increment')
ck(a['new_fixed_allocation']=={'full_seven_graph_joint_update_resource_pilot_claims':1} and a['identities']==[x['initial_experiment']]==['eth-paper-real-data-end-to-end-resource-20261011-31'],'one fresh fixed31 identity')
historyb=read(R/'research/onchain-paper-replication-2026-09-24/history.json');history=json.loads(historyb)
ck(sha(historyb)=='68e4ea2f328996cef6966f2ec9f35c494b38f38182e33ae0fb7697383750aae0' and history['prior_attempts']==len(history['lineage'])==17,'original17 historical index anchor reused')
prior_review=read(F/'real-data-pilot-full30-cumulative-machine-review01-2026-10-11/EXTENSION101_REVIEW01.json')
ck(sha(prior_review)=='e98bb82c8c20dff02d0c16bd52fdf3d05bd7d28ea852d3d6f6817b42b7e2b3be','accepted prior101 review retained')
terminal_review=read(F/'pilot30-terminal-outcome-review01-2026-10-11/REVIEW01.json');ck(sha(terminal_review)=='7360d77f087f446c7049fb993ac267474a531b053c640c0238ff771c42578e64','actual30 independent outcome anchor')
# Metadata-only census across current immediate claim directories, no output/data reads.
relevant=[];all_ids=[];census={};family=x['base_family'];snapshot={r['experiment']:r for r in x['claims']}
ck(len(snapshot)==53,'unique53 snapshot identities')
for directory in sorted((R/'research_runs').iterdir()):
    if directory.name.startswith('.'):continue
    ck(directory.is_dir() and not directory.is_symlink() and (directory/'claim.json').is_file(),'complete claim directory '+directory.name)
    b=read(directory/'claim.json');c=json.loads(b);all_ids.append(c['experiment_id']);ck(c['experiment_id']==directory.name,'actual claim identity '+directory.name)
    if c['family']['mechanism_id']!=family['mechanism_id']:continue
    ck(c['family']==family and c['experiment_id'] in snapshot,'actual relevant family/snapshot membership '+directory.name)
    row=snapshot[c['experiment_id']];status=row['terminal_status'];terminal=js(directory/(status+'.json'))
    ck(status in ('complete','failed') and not (directory/('failed.json' if status=='complete' else 'complete.json')).exists(),'one actual closed terminal '+directory.name)
    ck(sha(b)==row['claim_sha256'] and refs[str((directory/(status+'.json')).relative_to(R))]['sha256']==row['terminal_sha256'] and terminal['claim_sha256']==row['claim_sha256'] and terminal['experiment_id']==directory.name and terminal['status']==status,'actual claim terminal hash join '+directory.name)
    relevant.append(c);census[directory.name]={'status':status,'effective_attempt_budget':c.get('effective_attempt_budget',family['attempt_budget']),'claim_sha256':sha(b),'terminal_sha256':row['terminal_sha256']}
ck(set(census)==set(snapshot) and len(relevant)==53,'complete actual current relevant census53')
ck(max(c['effective_attempt_budget'] for c in census.values())==a['prior_adopted_cumulative_ceiling']==101,'highest actual adopted101 retained')
historical_counts={status:sum(p.endswith('/'+status+'.json') for p in history['metadata_hashes']) for status in ['complete','failed']}
actual_counts={status:sum(c['status']==status for c in census.values()) for status in ['complete','failed']}
ck(historical_counts=={'complete':13,'failed':4} and actual_counts=={'complete':20,'failed':33},'historical13C4F plus actual20C33F')
ck(17+53==a['consumed_before']==x['consumed_before']==70 and sum(historical_counts.values())==17 and 70+28+3+1==a['proposed_cumulative_ceiling']==x['cumulative_ceiling']==102,'102 equals70 spent28pending3reserved1fresh')
for row in a['preserved_reserved_preclaim_allowances']:
    ck(row['research_claim'] is None and row['identity'] not in all_ids and not (R/'research_runs'/row['identity']).exists(),'closed preclaim reserve not reclaimed '+row['identity'])
ck(x['initial_experiment'] not in all_ids and not (R/'research_runs'/x['initial_experiment']).exists(),'fresh31 not claimed or partial directory')
review={'schema_version':1,'decision':'accepted','extension_sha256':m['new_extension']['sha256'],'reviewer':'Independent pilot31 cumulative accounting reviewer','scope':'Budget-extension proposal only:102=70 permanently spent(17 historical+53 actual closed;33complete/37failed)+28 unchanged pending+3 preserved closed preclaim reserves+1 fresh fixed unused31. Actual current53claim/terminal hash roster and highest adopted101 verified; original101 allocation and all prior rows retained. No refund/transfer/reopening/new financial fits; maximum1420 unchanged. Preserve60s freshness/native/resource/scientific/financial limits. No source installation, allowance adoption, full-entry/transport/native/launch authority or external failed30 recovery acceptance. Exact changed-source, current genuine admission and complete declared failed30 external recovery remain separate prerequisites.'}
reviewb=(json.dumps(review,indent=2,sort_keys=True)+'\n').encode();reviewpath=str((P/'EXTENSION102_REVIEW01.json').relative_to(R));reference={'extension':m['new_extension'],'review':{'path':reviewpath,'sha256':sha(reviewb)}}
source=read(R/'tradingagents/research/budget_extensions.py');ck(sha(source)=='59d22880e9ff7909508db6b0c15a7a833df30be365af4e31d643ed64afabb25a','unchanged actual budget validator source')
nodes=[n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='effective_budget'];ns={'hashlib':hashlib,'json':json,'re':re};exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-budget-validator','exec'),ns)
def bound(ref):
    b=reviewb if ref['path']==reviewpath else read(R/ref['path']);assert sha(b)==ref['sha256'];return b
ceiling=ns['effective_budget'](R,x['program_id'],x['initial_experiment'],{'cumulative_budget_extension':reference},family,relevant,bound)
ck(ceiling==102,'full actual metadata budget helper returns102 (not admission or launch)')
with (P/'EXTENSION102_REVIEW01.json').open('xb') as f:f.write(reviewb)
result={'decision':'ACCEPT_EXACT102_BUDGET_PROPOSAL_ONLY','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'references':refs,'read_bytes':read_bytes,'current_claim_directories':len(all_ids),'actual_closed_family_claims':census,'historical_counts_reused_from_original_index':historical_counts,'actual_family_counts':actual_counts,'total_counts':{'closed':70,'complete':33,'failed':37,'active':0},'highest_adopted':101,'equation':'102=70+28+3+1','machine_helper_result':ceiling,'machine_review':{'path':reviewpath,'sha256':sha(reviewb)},'machine_scope':'Actual full relevant metadata roster with prospective exact five-field review bytes; this does not execute admission/ResearchRun, pin installed candidate sources, adopt ceiling or release launch. Historical17 claim bodies not replayed; original frozen index/reviews reused.','new_claim_or_adoption':False}
with (P/'VALIDATION01.json').open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({k:result[k] for k in ['decision','current_claim_directories','total_counts','highest_adopted','equation','machine_helper_result','machine_review','read_bytes']},sort_keys=True));print('checks',len(checks))
