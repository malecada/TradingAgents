from pathlib import Path
import ast,hashlib,json,os,subprocess
H=Path(__file__).resolve().parent;F=H.parent;R=H.parents[3];P=F/'held-consumer-cumulative-admission-preparation01-2026-10-03';C=F/'original-import-native-successor-preparation06-2026-10-03/capsule04';X=F/'original-import-native-successor-preparation06-2026-10-03/outcome-recovery01/recovered-terminal-capsule04';S=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-03/source')
def read(p):assert p.is_file() and not p.is_symlink() and p.stat().st_size<=4*1024**2;return p.read_bytes()
def sha(b):return hashlib.sha256(b).hexdigest()
def doc(p):return json.loads(read(p))
def blob(root,source,path):return subprocess.check_output(['git','-C',str(root),'cat-file','blob',source+':'+path],env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_OPTIONAL_LOCKS':'0'},timeout=15)
man=doc(P/'MANIFEST01.json');assert sha(read(P/'MANIFEST01.json'))=='c6b540a68f7fa215b9be03828c214ec5b50e1da166a466fd923c49d5142929ce'
for r in man['files']:b=read(P/r['path']);assert len(b)==r['bytes'] and sha(b)==r['sha256']
ext=doc(P/'cumulative-extension04-proposal.json');alloc=doc(P/ext['allocation']['path']);assert sha(read(P/ext['allocation']['path']))==ext['allocation']['sha256']
fields={'schema_version','program_id','base_family','cumulative_ceiling','consumed_before','initial_experiment','allocation','claims','reason'};assert set(ext)==fields
source=read(R/'tradingagents/research/budget_extensions.py');t=ast.parse(source);fieldnode=next(n for n in ast.walk(t) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='fields' for x in n.targets));assert ast.literal_eval(fieldnode.value)==fields
history=[]
for i,r in enumerate(ext['claims'],1):
 name=r['experiment'];p='research_runs/'+name;raw=read(P/'prior_claims'/name/'claim.json');term=read(P/'prior_claims'/name/'failed.json');assert raw==read(C/p/'claim.json')==read(X/p/'claim.json') and term==read(C/p/'failed.json')==read(X/p/'failed.json');assert sha(raw)==r['claim_sha256'] and sha(term)==r['terminal_sha256']
 c=json.loads(raw);v=json.loads(term);assert c['family']==ext['base_family'] and c['program_id']==ext['program_id'] and c['effective_attempt_budget']==i+1 and v['status']=='failed' and v['experiment_id']==name and v['claim_sha256']==sha(raw)
 regraw=blob(C,c['source'],c['registration']);assert regraw==blob(X,c['source'],c['registration']) and sha(regraw)==c['registration_sha256'];reg=json.loads(regraw);assert reg['experiments'][name]==c['experiment'] and reg['families'][c['experiment']['family']]==c['family'] and reg['program_id']==c['program_id']
 ref=c['experiment'].get('cumulative_budget_extension');ceiling=c['family']['attempt_budget']
 if ref:
  e=blob(C,c['source'],ref['extension']['path']);rv=blob(C,c['source'],ref['review']['path']);assert sha(e)==ref['extension']['sha256'] and sha(rv)==ref['review']['sha256'];a=json.loads(e);review=json.loads(rv);assert a['base_family']==c['family'] and review['decision']=='accepted' and review['extension_sha256']==sha(e);ceiling=a['cumulative_ceiling'];assert c['experiment']['source_files'][a['allocation']['path']]==a['allocation']['sha256']
 assert ceiling==i+1
 for n,pin in v['output_sha256'].items():assert sha(read(C/p/'outputs'/n))==pin and read(C/p/'outputs'/n)==read(X/p/'outputs'/n)
 assert not os.path.lexists(C/p/'complete.json') and not os.path.lexists(X/p/'complete.json')
 history.append({'identity':name,'ceiling':ceiling,'source':c['source'],'claim':sha(raw),'terminal':sha(term),'registered_contract':sha(regraw)})
assert len(history)==ext['consumed_before']==4 and ext['base_family']['prior_attempts']==0 and ext['base_family']['attempt_budget']==2 and max(r['ceiling'] for r in history)==5 and 4+len(alloc['new_attempts'])==ext['cumulative_ceiling']==6
for row in alloc['unlaunched_superseded']+alloc['new_attempts']:
 for root in [C,X,S]:assert not os.path.lexists(root/'research_runs'/row['identity'])
assert all(x['maximum_claims']==1 for x in alloc['new_attempts']);assert ext['initial_experiment']==alloc['new_attempts'][0]['identity'];assert 'Companion held success is COMPLETE' in alloc['new_attempts'][1]['depends_on'] and 'If companion fails' in alloc['new_attempts'][1]['depends_on']
policy=doc(C/'fixture_inputs/success/compact_policy.json');chunk=policy['stage_policy']['score_chunk_cells'];counts=[(n*32+chunk-1)//chunk for n in [2,3]];assert chunk==64 and counts==[1,2] and alloc['case_denominators']['success']['ordered_members_each']==32
report={'decision':'WITHHELD-denominator-correction-required','accounting_arithmetic_verified':True,'base':2,'prior':0,'highest_adopted':5,'spent':4,'proposed':6,'history':history,'blocker':{'code':'HCA1','declared_ordered_members_each':32,'retained_score_chunk_cells':64,'source_derived_members':[1,2],'motifs_each':32,'qualification':'No current policy bound; do not conflate motif columns with score-batch members.'},'schema_source_sha256':sha(source),'verify_source_sha256':sha(read(R/'tradingagents/research/verify.py')),'proposed_review_created':False,'adoption':False,'execution_release':False}
(H/'READBACK01.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print('PASS four original/recovered claim+terminal+Gitregistration+savedceilings2/3/4/5;4+2=6; unchangedspent; WITHHELD HCA1 actualmembers1/2 vsproposal32each')
