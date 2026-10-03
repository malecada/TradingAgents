from pathlib import Path
import ast,hashlib,json,copy
H=Path(__file__).resolve().parent;F=H.parent;R=H.parents[3];A=F/'held-consumer-cumulative-admission-preparation01-2026-10-03';B=F/'held-consumer-cumulative-admission-preparation02-2026-10-03'
def read(p):assert p.stat().st_size<=4*1024**2;return p.read_bytes()
def sha(b):return hashlib.sha256(b).hexdigest()
def doc(p):return json.loads(read(p))
assert sha(read(B/'MANIFEST02.json'))=='2038797145ef9876fe69dd95d5cd695b2d2341efe43e529547078b3f854ca8da'
for row in doc(B/'MANIFEST02.json')['files']:
 raw=read(B/row['path']);assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
changed={'successor-allocation04-proposal.json','cumulative-extension04-proposal.json','CHARTER_PROPOSAL01.md'}
for row in doc(A/'MANIFEST01.json')['files']:
 if row['path'] not in changed:assert read(A/row['path'])==read(B/row['path'])
a=doc(A/'successor-allocation04-proposal.json');b=doc(B/'successor-allocation04-proposal.json');reverse=copy.deepcopy(b);reverse['case_denominators']['success']=a['case_denominators']['success'];assert reverse==a
x=doc(A/'cumulative-extension04-proposal.json');y=doc(B/'cumulative-extension04-proposal.json');assert y['allocation']['sha256']==sha(read(B/y['allocation']['path']));reverse=copy.deepcopy(y);reverse['allocation']=x['allocation'];assert reverse==x
old=read(A/'CHARTER_PROPOSAL01.md').decode();new=read(B/'CHARTER_PROPOSAL01.md').decode();oldparas=old.split('\n\n');newparas=new.split('\n\n');assert len(oldparas)==len(newparas);different=[i for i,(p,q) in enumerate(zip(oldparas,newparas)) if p!=q];assert different==[3]
c=doc(B/'DENOMINATOR_CORRECTION02.json');p=R/c['actual_prior_policy']['path'];raw=read(p);assert sha(raw)==c['actual_prior_policy']['sha256'] and len(raw)==791;chunk=json.loads(raw)['stage_policy']['score_chunk_cells'];assert chunk==64
S=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-03/source/tradingagents/research/onchain_replication/held_score_consumer.py');tree=ast.parse(read(S));function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_read_all') if any(isinstance(n,ast.FunctionDef) and n.name=='_read_all' for n in tree.body) else None
assign=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='count' for t in n.targets) and 'chunk_cells' in ast.unparse(n.value))
result=[]
for cells in [64,96]:
 ns={'cells':cells,'chunk_cells':chunk};exec(compile(ast.Module(body=[assign],type_ignores=[]),str(S),'exec'),ns);result.append(ns['count'])
assert result==[1,2]==b['case_denominators']['success']['expected_score_batch_members'];assert b['case_denominators']['success']['motif_columns_each']==32 and c['execution_admitted'] is False and c['final_current_policy_registered'] is False
prior=doc(F/'held-consumer-cumulative-admission-review01-2026-10-03/READBACK01.json');assert prior['spent']==4 and prior['highest_adopted']==5 and y['consumed_before']==4 and y['cumulative_ceiling']==6
out={'decision':'accepted-prospective-accounting-only','proposal_manifest':sha(read(B/'MANIFEST02.json')),'extension_sha256':sha(read(B/'cumulative-extension04-proposal.json')),'allocation_sha256':y['allocation']['sha256'],'prior_history_review':sha(read(F/'held-consumer-cumulative-admission-review01-2026-10-03/REVIEW_ADMISSION01.md')),'actual_consumer_source_sha256':sha(read(S)),'actual_count_statement':ast.unparse(assign),'derived_counts':result,'history_arithmetic_unchanged':True,'adoption':False,'machine_review_created':False,'registration_release':False}
(H/'READBACK02.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print('PASS exact14manifestbodies, original8claim/terminalbytes and history unchanged; inverse allocation/extension/charter delta only; actualconsumer count formula yields1/2. Narrow prospective accounting accepted; not adoption.')
