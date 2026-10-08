"""Independent source-only review; no package imports or live process access."""
from pathlib import Path
import ast,copy,datetime,difflib,hashlib,json,stat
H=Path(__file__).resolve().parent;F=H.parent;R=H.parents[3];D=F/'real-data-pilot-bind-redundant-admission-correction01-2026-10-08';evidence={}
def raw(p):
 s=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<1024**2
 b=p.read_bytes();z=p.lstat();assert len(b)==s.st_size and (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns)
 evidence[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def read(p):return json.loads(raw(p))
def ref(p):return {'path':str(p.relative_to(R)),'sha256':hashlib.sha256(raw(p)).hexdigest()}
man=read(D/'MANIFEST01.json')
for name,v in man['files'].items():assert hashlib.sha256(raw(D/name)).hexdigest()==v['sha256'] and len(raw(D/name))==v['bytes']
source=R/'tradingagents/research/onchain_replication/matching_owner.py';before=raw(D/'baseline_matching_owner.py');after=raw(D/'matching_owner.py');assert raw(source)==before
assert hashlib.sha256(before).hexdigest()=='995fe76c18049d6a5b8417881ef86446fa49966ecc25c8aee96cf807d98e5281'
assert hashlib.sha256(after).hexdigest()=='b6c1e2b312eb7132a781835aeb037ffac93d378699fa07852692664235ae47c9'
old=b'    run._active();run._check_source()\n';new=b'    run._active()\n';assert before.count(old)==1 and before.replace(old,new)==after
assert after.replace(new,old,1)==before
x=ast.parse(before);y=ast.parse(after);xb=next(n for n in x.body if isinstance(n,ast.FunctionDef) and n.name=='bind');yb=next(n for n in y.body if isinstance(n,ast.FunctionDef) and n.name=='bind')
assert ast.unparse(xb.body[2])=='run._check_source()';del xb.body[2];assert ast.dump(x)==ast.dump(y)
assert [ast.unparse(n) for n in yb.body[:4]]==["require(isinstance(run, ResearchRun), 'actual admitted ResearchRun required')",'run._active()','ad = run.admission','execution = json.loads(run.read_input(job_input))']
compile(after,str(D/'matching_owner.py'),'exec')
for name,rev in [('FORWARD01.patch',False),('INVERSE01.patch',True)]:
 a,b=(after,before) if rev else (before,after);p='tradingagents/research/onchain_replication/matching_owner.py'
 patch=''.join(difflib.unified_diff(a.decode().splitlines(True),b.decode().splitlines(True),fromfile='a/'+p,tofile='b/'+p));assert patch.encode()==raw(D/name)
delta=read(D/'SOURCE_DELTA01.json')
for p,digest in delta['source_dependencies'].items():assert hashlib.sha256(raw(R/p)).hexdigest()==digest
life=ast.parse(raw(R/'tradingagents/research/lifecycle.py'));cls=next(n for n in life.body if isinstance(n,ast.ClassDef) and n.name=='ResearchRun');methods={n.name:n for n in cls.body if isinstance(n,ast.FunctionDef)}
read_input=methods['read_input'];lock=read_input.body[1];assert isinstance(lock,ast.With) and ast.unparse(lock.items[0].context_expr)=='_lock(self.admission.root)'
assert [ast.unparse(n) for n in lock.body[:2]]==['self._active()','self._check_source()']
assert ast.unparse(lock.body[-1])=='return data'
assert "digest(data) != info['sha256']" in ast.unparse(lock) and "self._fail_unlocked('input hash changed after admission')" in ast.unparse(lock)
check=methods['_check_source'];assert ast.unparse(check.body[0].value).startswith('admit(')
# This method validates the current admission; it does not replace run.admission.
assert not any(isinstance(n,(ast.Assign,ast.AnnAssign,ast.AugAssign)) and any(isinstance(t,ast.Attribute) and ast.unparse(t)=='self.admission' for t in getattr(n,'targets',[])) for n in ast.walk(check))
assert 'current.registration_sha256 != self.admission.registration_sha256' in ast.unparse(check)
assert 'current.experiment != self.admission.experiment' in ast.unparse(check) and 'current.inputs != self.admission.inputs' in ast.unparse(check)
# Inspect the actual extracted-AST harness and original logs, without rerunning it.
test=raw(D/'test_bind01.py').decode();assert "n.name in ('require','bind')" in test
assert 'ResearchRun._check_source(run)' in test and 'run=ResearchRun(ad)' in test and 'ResearchRun.start(' not in test
assert "return ns['bind'](run,representation='unused',plan_input='unused',producer='unused',policy_input='unused')" in test
assert "run.directory=root/'synthetic-active-state'" in test
red=raw(D/'RED01.log').decode();green=raw(D/'GREEN01.log').decode()
assert "'source': 2, 'job_parse': 1" in red and '1 failed, 3 passed' in red
assert "'source': 1, 'job_parse': 1" in green and '4 passed' in green
raw(Path(__file__))
result={'schema_version':1,'decision':'accepted-source-only','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate':ref(D/'matching_owner.py'),'baseline':ref(D/'baseline_matching_owner.py'),'live_source':ref(source),'live_source_unchanged':True,'evidence':dict(sorted(evidence.items())),
'finding':'No material correctness issue in the exact one-expression deletion on the genuine ResearchRun path. The immediate read_input still performs the same source admission and active/input checks under the lifecycle lock before parsing; _check_source does not update the saved admission object.',
'exact_byte_and_ast_delta':'Only bind initial run._check_source() expression removed. Forward/inverse exact; every other AST node and byte unchanged.',
'actual_source_seams':{'bind':'tradingagents/research/onchain_replication/matching_owner.py:166-171','active':'tradingagents/research/lifecycle.py:134-138','source_check':'tradingagents/research/lifecycle.py:145-154','locked_input_read':'tradingagents/research/lifecycle.py:156-169'},
'concurrency':'The removed check was outside the lifecycle lock. Its retained counterpart executes under read_input lock; the earlier outer _active remains and the locked _active rechecks state. All subsequent full numerical-source/runtime/owner/guard checks, in-lock creation checks, recursive bind and publications are byte-identical. The existing read-to-use concurrency model is unchanged; no broader atomicity is claimed.',
'author_harness_scope':'Actual complete bind/require function ASTs execute with genuine ResearchRun active/read_input/_check_source/admit methods against invented committed metadata. The four tests stop at malformed-job refusal and cover exactly source-call counts2to1/parse1, changed source before parse, inactive refusal and unchanged malformed schema error. Synthetic active receipt is outside the actual lifecycle ledger; no ResearchRun.start or Owner occurs. Source refusal may create the temporary ledger lock through read_input; the report discloses it.',
'validation':'Independent bounded manifest/dependency hashes, exact source/inverse/AST check and lifecycle/harness inspection passed. Original RED1failed3passed and GREEN4passed logs authenticated. No additional tests were needed for this one-expression change; no prior matrix was repeated.',
'adoption_condition':'Source-only acceptance of exact b6c1e2b candidate. Live19 remains frozen and untouched. Root alone may adopt after its original94052 process is genuinely terminal and preserved. This receipt grants no new registration, launch, threshold amendment or replay.',
'not_tested':['Full bind/Owner construction, runtime inventory, numerical-source anchor authentication and native lifecycle were not executed by this review; their unchanged source and earlier accepted evidence are reused.','No live-worker timing, elapsed speedup, RAM saving, capacity or successful scientific progress was measured or accepted.','No real claim/owner, original empirical arrays/data, private transport, process attachment, network or live-source/Git mutation.']}
out=H/'SOURCE_REVIEW01.json'
with out.open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
manifest={'schema_version':1,'decision':'accepted-source-only','files':[ref(H/'review01.py'),ref(out)]}
with (H/'MANIFEST01.json').open('x') as f:json.dump(manifest,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'decision':result['decision'],'review':ref(out),'manifest':ref(H/'MANIFEST01.json')}))
