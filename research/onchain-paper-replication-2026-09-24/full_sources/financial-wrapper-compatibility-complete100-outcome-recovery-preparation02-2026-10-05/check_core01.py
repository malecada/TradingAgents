from pathlib import Path
import sys,json,hashlib,copy,ast
D=Path(__file__).resolve().parent;sys.path[:0]=[str(D),str(D/'utilities')];import outcome01 as O
P=D.parent/'financial-wrapper-compatibility-complete100-outcome-recovery-preparation01-2026-10-05';R=O.R
q=json.loads((D/'LANE01_DRAFT01.json').read_text());core=O.request_core_sha256(q)
# Pure construction control only: this is NOT an independent release or public entry.
sidecar={'kind':'ENGINEERING_BYTES_NOT_RELEASE_AUTHORITY','request_core_sha256':core};side_raw=R.encode(sidecar);ref={'name':'engineering-sidecar.json','sha256':R.digest(side_raw)}
q['release']=ref;full=R.encode(q);assert O.request_core_sha256(q)==core and R.digest(full)!=core
assert sidecar['request_core_sha256']!=R.digest(full) # old full-q signing predicate refuses this finite construction
(D/'ENGINEERING_SIDECAR01.json').write_bytes(side_raw);(D/'ENGINEERING_REQUEST01.json').write_bytes(full)
checks=['finite core then sidecar then full request construction','old full-q equality false','new core equality true']
for field in O.REQUEST_FIELDS-{'release','schema_version'}:
 mutated=copy.deepcopy(q);mutated[field]=['changed',mutated[field]];assert O.request_core_sha256(mutated)!=core;checks.append('signed '+field)
for mutate in (lambda x:x.update(extra='unsigned'),lambda x:x.pop('release'),lambda x:x.update(schema_version=True),lambda x:x.update(release={'name':'../unsafe','sha256':'0'*64}),lambda x:x.update(release={'name':'ok','sha256':'z'*64})):
 mutated=copy.deepcopy(q);mutate(mutated)
 try:O.request_core_sha256(mutated)
 except (ValueError,KeyError):checks.append('strict refusal')
 else:raise AssertionError('malformed signing schema accepted')
v=json.loads((D/'INVERSE01.json').read_text());s=(P/'outcome01.py').read_text()
for a,b in v['changes']:assert s.count(a)==1;s=s.replace(a,b)
assert s==(D/'outcome01.py').read_text()
old={n.name:ast.dump(n) for n in ast.parse((P/'outcome01.py').read_text()).body if isinstance(n,ast.FunctionDef)};new={n.name:ast.dump(n) for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)};assert all(new[n]==v for n,v in old.items() if n!='run')
for p in D.glob('*.py'):
 if p.name not in ('outcome01.py','check_core01.py'):assert p.read_bytes()==(P/p.name).read_bytes()
for p in (D/'utilities').iterdir():assert p.read_bytes()==(P/'utilities'/p.name).read_bytes()
(D/'CHECKS01.json').write_text(json.dumps({'checks':checks,'count':len(checks),'full_inverse':True,'unchanged_generators_and_callers':True,'engineering_only_no_actual_release':True,'actual_public_entry':False,'independently_authored_public_entry_test':'reviewer required'},indent=2)+'\n');print(len(checks))
