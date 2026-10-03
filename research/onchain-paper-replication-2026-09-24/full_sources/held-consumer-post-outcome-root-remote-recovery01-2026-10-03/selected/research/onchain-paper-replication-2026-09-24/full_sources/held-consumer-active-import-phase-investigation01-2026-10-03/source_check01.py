import ast,hashlib,json,subprocess,datetime
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[3];C=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source')
head='d443208795f59292c156c5b81b687594efacea4d'
obs=json.loads((D/'OBSERVATION01.json').read_text());names=set(json.loads((D/'MARKERS02.json').read_text())['source_hashes'])
names|={'tradingagents/research/onchain_replication/'+n+'.py' for n in ['compact_matcher','compact_pair_log','compact_mcm','imported_mcm_identity','compact_owner']}
claim=json.loads((C/'research_runs/original-import-held-success-20261003-01/claim.json').read_text());pins={}
for n in sorted(names):
 raw=(C/n).read_bytes();h=hashlib.sha256(raw).hexdigest();assert claim['experiment']['source_files'][n]==h
 recorded=subprocess.run(['git','show',head+':'+n],cwd=C,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=10).stdout
 assert recorded==raw;pins[n]=h
base=C/'tradingagents/research/onchain_replication/original_dictionary.py';candidate=R/'research/onchain-paper-replication-2026-09-24/full_sources/original-dictionary-canonical-validation-candidate01-2026-10-03/candidate01.py'
def membership(path):
 f=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='validate')
 start=next(i for i,n in enumerate(f.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='indices' for t in n.targets))
 loop=next(i for i in range(start,len(f.body)) if isinstance(f.body[i],ast.For))
 calls=0
 def canonical(v):
  nonlocal calls;calls+=1;return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
 def require(v,m):
  if not v:raise ValueError(m)
 ns=dict(s={'graphs':list(range(512))},reps=list(range(32)),groups=[[i] for i in range(32)],canonical=canonical,require=require)
 exec(compile(ast.fix_missing_locations(ast.Module(body=f.body[start:loop+1],type_ignores=[])),str(path), 'exec'),ns)
 assert ns['indices']==list(range(32));return calls
old=membership(base);new=membership(candidate);assert (old,new)==(32768,544)
# Static normal-source Git invocation census; original request grouping rules.
claims=[]
for p in sorted((C/'research_runs').glob('*/claim.json')):
 x=json.loads(p.read_text());e=x['experiment'];pinned=dict(e['source_files'])
 for k in ('charter','selection'):
  if e.get(k):pinned[e[k]['path']]=e[k]['sha256']
 batches=0;count=0;size=0
 for name in pinned:
  for commit in {x['source'],x['design_source']}:
   b=(commit+':'+name+'\n').encode();assert b'\r' not in b and b.count(b'\n')==1
   if count==128 or size+len(b)>65536:batches+=1;count=size=0
   count+=1;size+=len(b)
 batches+=bool(count)
 assert x['bindings'] is None and not e.get('selection')
 claims.append(dict(id=x['experiment_id'],pins=len(pinned),source_batches=batches,registration_batches=1,extension_blob_calls=2 if e.get('cumulative_budget_extension') else 0))
normal_claim_calls=sum(x['source_batches']+x['registration_batches']+x['extension_blob_calls'] for x in claims)
sourcepairs=[];total=0
for i,(n,h) in enumerate(claim['experiment']['source_files'].items()):
 total+=2*(C/n).stat().st_size
 if (i+1)%128==0:sourcepairs.append(total);total=0
if total:sourcepairs.append(total)
assert max(sourcepairs)<8*1024*1024
out=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sources_current_claim_and_git_join=pins,source=head,synthetic_membership_only={'baseline':old,'candidate':new,'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'sample_count':512,'representatives':32,'actual_samples_read':False,'full_validate_executed':False},claims=claims,claim_verification_processes_per_fresh_admit=normal_claim_calls,admission_source_pair_batch_bytes=sourcepairs,normal_successful_admit_git_processes=6+2*len(sourcepairs)+normal_claim_calls+6+1,static_multiplicity={'prepared_checks_per_target_lease':4,'target_leases_per_compact_matcher_check':2,'full_validations_per_matcher_check':8,'membership_canonical_calls_per_matcher_check':8*old},qualification='Source path census, not profiler or measured invocation count; failures/other callback paths differ. No numerical modules, original sample bodies, arrays or active helper invocation.')
(D/'SOURCE_CHECK01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
