from pathlib import Path
import json,hashlib,ast,copy,os
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'held-consumer-canonical-parent-review01-2026-10-05';A=F/'held-consumer-canonical-root-binding01-2026-10-05';P=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-canonical-root-launch-20261005-01');OLD=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-root-launch-20261003-01');CAP=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-canonical-native-20261005-01/source');ID='original-import-canonical-held-success-20261005-01'
def h(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_bytes())
def ref(p):return {'path':str(p),'sha256':h(p.read_bytes())}
def put(n,d):
 p=D/n;b=(json.dumps(d,sort_keys=True,separators=(',',':'))+'\n').encode()
 with p.open('xb') as f:f.write(b)
 p.chmod(0o444);print(n,h(b))
prep=load(A/'PARENT_PREPARATION01.json');caller=(P/'launch_success01.py').read_text();semantic=(P/'held_outcome02.py').read_text()
assert h(caller.encode())==prep['caller_sha256']=='c90812faff70c431807900a118447d30711ac3eca239a4ee1ec11ec5f6139ea9'
assert h(semantic.encode())==prep['semantic_sha256']=='34f7945642eac91babe1f180b70c2d42f3b04daaf3e4c556f24eecab8ede4b95'
inverse=caller;assert inverse.count(prep['new_allocation_function'])==1;inverse=inverse.replace(prep['new_allocation_function'],'')
assert len(prep['literal_caller_edits'])==6
for edit in prep['literal_caller_edits']:
 assert inverse.count(edit['new'])==1;inverse=inverse.replace(edit['new'],edit['old'],1)
assert inverse==(OLD/'launch_success01.py').read_text()
sem_inverse=semantic
for edit in prep['semantic_constant_edits']:
 assert sem_inverse.count(edit['new'])==1;sem_inverse=sem_inverse.replace(edit['new'],edit['old'],1)
assert sem_inverse==(OLD/'held_outcome02.py').read_text() and len(prep['semantic_constant_edits'])==2
assert ast.dump(ast.parse(inverse))==ast.dump(ast.parse((OLD/'launch_success01.py').read_text()))
tree=ast.parse(caller);functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
prepared=functions['prepared'];launch=functions['launch'];calls=[(n.func.id if isinstance(n.func,ast.Name) else n.func.attr,n.lineno) for n in ast.walk(prepared) if isinstance(n,ast.Call) and isinstance(n.func,(ast.Name,ast.Attribute))]
assert sum(name=='allocation_scope' for name,line in calls)==1
assert next(line for name,line in calls if name=='allocation_scope')>next(line for name,line in calls if name=='sources')
prepare_line=min(n.lineno for n in ast.walk(launch) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='prepared')
mkdir_line=min(n.lineno for n in ast.walk(launch) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='mkdir');assert prepare_line<mkdir_line
scope={'hashlib':hashlib,'json':json,'IDENTITY':ID}
for name in ('require','sha','parse','reference','allocation_scope'):
 exec(compile(ast.Module(body=[functions[name]],type_ignores=[]),'actual-'+name,'exec'),scope)
class Reader:
 def __init__(self,mutate=False):self.mutate=mutate
 def body(self,n):
  b=(CAP/n).read_bytes()
  return b+b' ' if self.mutate and n=='CUMULATIVE_ALLOCATION05_DRAFT01.json' else b
registration=load(CAP/'held-fixture-registration01.json');release=load(P/'release-unreleased01.json');request=load(P/'request-unreleased01.json');scope['allocation_scope'](Reader(),registration,release)
controls=[]
def reject(label,g,r,reader=None):
 try:scope['allocation_scope'](reader or Reader(),g,r)
 except ValueError as e:controls.append({'case':label,'refused':True,'reason':str(e)})
 else:raise AssertionError(label+' was accepted')
g=copy.deepcopy(registration);g['experiments']['another-unallocated-case']=copy.deepcopy(g['experiments'][ID]);reject('another_gate_identity_shares_extension',g,release)
g=copy.deepcopy(registration);g['experiments'][ID]['cumulative_budget_extension']['review']['sha256']='0'*64;reject('selected_review_pin_changed',g,release)
r=copy.deepcopy(release);r['cases']['second_target_publication_failure']['disposition']='available';reject('historical_conditional_made_available',registration,r)
r=copy.deepcopy(release);r['cases']['second_target_publication_failure']['identity']='another-failure';reject('conditional_identity_transferred',registration,r)
reject('pinned_allocation_bytes_changed',registration,release,Reader(True))
assert all(request['evidence'][k] is None for k in ('release_review','external_recovery','external_recovery_review'))
assert all(release[k] is None for k in ('release_review_sha256','external_capsule_recovery_sha256','external_recovery_review_sha256'))
assert request['status']!='released-one-use-native-parent' and request['remaining']
assert request['capsule_commit']==release['capsule_commit']=='468d756c16b3825e83a931c082ab4072764a873d'
assert release['source_files']==registration['experiments'][ID]['source_files'] and release['cases']['success']['experiment']==registration['experiments'][ID]
assert request['caller']=={'path':'launch_success01.py','sha256':h(caller.encode())} and request['semantic_parser']=={'path':'held_outcome02.py','sha256':h(semantic.encode())}
assert request['release']=={'path':'release-unreleased01.json','sha256':h((P/'release-unreleased01.json').read_bytes())}
assert request['parent_limits']=={'max_allocated_bytes':33554432,'max_logical_bytes':16777216,'max_entries':1024,'max_depth':8,'max_scan_seconds':5}
for p in [P/'attempt',CAP/'research_runs'/ID,CAP/'fixture_outer'/ID,CAP/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/ID]:assert not os.path.lexists(p)
put('SOURCE_CHECK01.json',{'schema_version':1,'decision':'accepted-exact-parent-draft-source-only','caller':ref(P/'launch_success01.py'),'semantic':ref(P/'held_outcome02.py'),'baseline_caller':ref(OLD/'launch_success01.py'),'baseline_semantic':ref(OLD/'held_outcome02.py'),'preparation':ref(A/'PARENT_PREPARATION01.json'),'request':ref(P/'request-unreleased01.json'),'release_draft':ref(P/'release-unreleased01.json'),'exact_caller_inverse':True,'exact_semantic_inverse':True,'allocation_before_reservation':True,'allocation_positive_actual_metadata_passed':True,'focused_refusals':controls,'all3_release_recovery_proofs_null':True,'parent_limits_unchanged':request['parent_limits'],'fresh_attempt_native_claim_namespaces_absent':True,'source':'468d756c16b3825e83a931c082ab4072764a873d','package_anchor':'55e7d50431654aba952b4541ca506524d9feece1','execution_release':False,'qualification':'Five caller constants, one allocation function and its single pre-reservation call; semantic two constants only. Exact inverse preserves original lifecycle/cleanup/outcome/limits. Actual draft allocation predicate accepts only reviewed canonical identity and keeps original conditional unavailable. No Parent prepared/admission/launch, array decode, claim or Owner executed. Recovery selection and final proofs remain pending; this directory stays open for that binding.'})
