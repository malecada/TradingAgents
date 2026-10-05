from pathlib import Path
import json,hashlib,ast,subprocess,copy
M=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'held-consumer-canonical-anchor-metadata-review01-2026-10-05';A=F/'held-consumer-canonical-anchor-supplement01-2026-10-05';B=F/'held-consumer-canonical-root-binding01-2026-10-05';S=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-canonical-native-20261005-01/source');OLD=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source')
def h(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_bytes())
def ref(p):return {'path':str(p),'sha256':h(p.read_bytes())}
def put(n,v):
 p=D/n;b=(json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
 with p.open('xb') as f:f.write(b)
 p.chmod(0o444);print(n,h(b))
def git(*args):return subprocess.check_output(['git','-c','protocol.allow=never',*args],cwd=S)
new=(A/'capsule_builder01.py').read_text();old=(A/'baseline_capsule_builder01.py').read_text();assert h(new.encode())=='d30c30e41810df094298582ef2e9ac01e3292e178b0d52277466a4c08118a636'
assert old.encode()==(S/'fixture_tools/capsule_builder01.py').read_bytes()
add="HELD_CANONICAL_ANCHOR='55e7d50431654aba952b4541ca506524d9feece1'\nHELD_CANONICAL_PARENT='d443208795f59292c156c5b81b687594efacea4d'\nHELD_CANONICAL_DICTIONARY='e05aa225b6bcf8f4e14a644d0a03f2a9aff6cb36ae4a5b02a3dded72d94580b9'\n"
block="    canonical=anchor==HELD_CANONICAL_ANCHOR\n    if canonical:\n        require(parents==[HELD_CANONICAL_PARENT],'canonical anchor sole parent differs')\n        _held_git(root,'merge-base','--is-ancestor',HELD_SOURCE04,HELD_CANONICAL_PARENT)\n    source04=anchor==HELD_SOURCE04_ANCHOR or canonical"
extra="    if canonical:expected['tradingagents/research/onchain_replication/original_dictionary.py']=HELD_CANONICAL_DICTIONARY\n"
assert all(new.count(x)==1 for x in (add,block,extra))
inverse=new.replace(add,'').replace(block,'    source04=anchor==HELD_SOURCE04_ANCHOR').replace(extra,'');assert inverse==old and ast.dump(ast.parse(inverse))==ast.dump(ast.parse(old))
anchor='55e7d50431654aba952b4541ca506524d9feece1';parent='d443208795f59292c156c5b81b687594efacea4d';assert git('show','-s','--format=%P',anchor).decode().split()==[parent]
assert git('rev-parse','HEAD').decode().strip()==anchor
git('merge-base','--is-ancestor','fa9712c36daf2896ef3f6a8a8a5d99ec696cfdf4',parent)
expected=load(F/'held-consumer-canonical-root-recipe02-2026-10-04/SOURCE_EXPECTATIONS02.json')['candidate'];package={n:p for n,p in expected.items() if n.startswith('tradingagents/')};assert len(expected)==199 and len(package)==148
names=git('ls-tree','-r','--name-only',anchor).decode().splitlines();roster=[n for n in names if n=='tradingagents/__init__.py' or (n.endswith('.py') and str(Path(n).parent) in ('tradingagents/research','tradingagents/research/onchain_replication'))];assert sorted(roster)==sorted(package)
# Check the exact new sole-parent predicate independently, including a merge parent counterexample.
tree=ast.parse(new);func=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='held_source_plan');branch=next(n for n in func.body if isinstance(n,ast.If) and isinstance(n.test,ast.Name) and n.test.id=='canonical');calls=[]
def require(v,m):
 if not v:raise ValueError(m)
code=compile(ast.Module(body=[branch],type_ignores=[]),'exact-canonical-branch','exec');base={'canonical':True,'HELD_CANONICAL_PARENT':parent,'HELD_CANONICAL_ANCHOR':anchor,'HELD_SOURCE04':'fa9712c36daf2896ef3f6a8a8a5d99ec696cfdf4','root':S,'require':require,'_held_git':lambda root,*args:calls.append(args)}
exec(code,{**base,'parents':[parent]});assert len(calls)==1
for parents in ([],['0'*40],[parent,'1'*40]):
 try:exec(code,{**base,'parents':parents})
 except ValueError:pass
 else:raise AssertionError('wrong/multiple parent accepted')
meta=load(B/'METADATA_BINDING01.json');roles=meta['roles'];assert len(roles)==8
for role,row in roles.items():
 original=(S/'fixture_inputs/held/roles01'/(role+'.json')).read_bytes();assert original==(OLD/'fixture_inputs/held/roles01'/(role+'.json')).read_bytes()
 actual=(B/'metadata-draft01/roles'/(role+'.json')).read_bytes();exp=original.replace(str(OLD).encode(),str(S).encode()) if role in ('native_environment','native_policy') else original
 assert actual==exp and h(original)==row['original_sha256'] and h(actual)==row['draft_sha256'] and len(actual)==row['bytes']
readback=load(B/'RUNTIME_ROLE_READBACK01.json');runtime=load(B/'metadata-draft01/roles/runtime.json');assert readback['record_count']==len(readback['distribution_records'])==len(runtime['distribution_records'])==251
by={r['name']:r for r in runtime['distribution_records']};assert len(by)==251
for row in readback['distribution_records']:
 r=by[row['name']];assert row['version']==r['version'] and row['path']==r['record'] and row['sha256']==r['record_sha256'] and Path(row['path']).stat().st_size==row['bytes']
assert readback['record_bytes']==sum(r['bytes'] for r in readback['distribution_records']) and readback['execution_admitted'] is False and readback['native_controls_verified'] is False
cases=load(B/'ROOT_REBOUND_CASE_DRAFTS01.json');changed=[]
for case,draft in cases.items():
 n=draft['experiment']['inputs']['pair_policy']['path'];oldpolicy=load(OLD/n);policy=load(B/'metadata-draft01/inputs'/n);exp=copy.deepcopy(oldpolicy);exp['numerical_source']={'commit':anchor,'files':package};assert policy==exp
 delta=[n for n in package if package[n]!=oldpolicy['numerical_source']['files'][n]];assert delta==['tradingagents/research/onchain_replication/original_dictionary.py']
 contract=load(B/'metadata-draft01/contracts'/(case+'.json'));want=copy.deepcopy(draft['case_contract']);want['experiment_id']='original-import-canonical-held-success-20261005-01' if case=='success' else None
 raw=(B/'metadata-draft01/inputs'/n).read_bytes();want['additional_inputs']['pair_policy']['reference']={'path':n,'sha256':h(raw),'bytes':len(raw)};assert contract==want
 changed.append({'case':case,'policy_sha256':h(raw),'contract_sha256':h((B/'metadata-draft01/contracts'/(case+'.json')).read_bytes())})
assert meta['allocated_fresh_identities']==['original-import-canonical-held-success-20261005-01'] and meta['gate_adopted'] is False and meta['execution_admitted'] is False
put('CHECK01.json',{'schema_version':1,'decision':'accepted-explicit-anchor-and-metadata-source-only','candidate':ref(A/'capsule_builder01.py'),'baseline':ref(A/'baseline_capsule_builder01.py'),'metadata_source':ref(B/'metadata_binding01.py'),'metadata_binding':ref(B/'METADATA_BINDING01.json'),'runtime_readback':ref(B/'RUNTIME_ROLE_READBACK01.json'),'exact_byte_and_AST_inverse':True,'actual_anchor':anchor,'actual_sole_parent':parent,'actual_complete_package_roster':148,'wrong_empty_multiple_parent_refused':3,'source_count':199,'pair_rebindings':changed,'root_only_roles':2,'unchanged_roles':6,'runtime_records_joined':251,'runtime_RECORD_bodies_rehashed_by_this_review':False,'legacy_and_current_source_Git_roster_checks_preserved':True,'second_case_identity':None,'second_case_new_allocation':False,'execution_release':False,'qualification':'Only exact explicit canonical anchor and e05aa dictionary pin are additive. Existing source/Git/full-roster and legacy validation remain byte-identical after inverse. Two pair policies change only numerical_source; all other backend/limits remain exact. Runtime readback authenticated against fixed role pins and extents; reused Root actual251 RECORD read rather than rescanning unchanged runtime. No numerical imports, source installation, gate/admission/Owner/claim, recovery or execution authority.'})
