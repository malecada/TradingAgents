from pathlib import Path
import hashlib,sys,types,importlib,tempfile,json,ast
D=Path(__file__).resolve().parent
A=D.parent/'real-data-pilot-imported-authority-lease01-2026-10-06';P=A/'candidate/tradingagents/research/onchain_replication'
pkg=types.ModuleType('independent_final_lease');pkg.__path__=[str(P)];sys.modules[pkg.__name__]=pkg
m=importlib.import_module(pkg.__name__+'.imported_authority_interval');h=importlib.import_module(pkg.__name__+'.imported_authority_lease')
p={'schema_version':1,'kind':m.KIND,'live_interval_ms':10,'fingerprint_interval_ms':20,'full_interval_ms':100,'max_stale_ms':500,'max_calls_between_full':1000,'assumption':m.ASSUMPTION}
now=[10.];v=m.Interval(p,clock=lambda:now[0]);v.validate(lambda:None,lambda:None,lambda:None);prior=v.full;now[0]=10.11
try:v.validate(lambda:now.__setitem__(0,10.55),lambda:None,lambda:None)
except ValueError as e:assert 'stale' in str(e)
else:raise AssertionError('stale crossing accepted')
assert v.closed and v.full==prior
now=[10.];v=m.Interval(p,clock=lambda:now[0]);v.validate(lambda:None,lambda:None,lambda:None);now[0]=10.11;live=[]
v.validate(lambda:now.__setitem__(0,10.16),lambda:None,lambda:live.append(now[0]));assert live==[10.11,10.16] and v.live==10.16
with tempfile.TemporaryDirectory(dir=D) as tmp:
 root=Path(tmp);f=root/'fixture.py';raw=b'from contextlib import contextmanager\n@contextmanager\ndef held():\n    yield 1\n';f.write_bytes(raw)
 mod=types.ModuleType('independent_final_context');mod.__file__=str(f);sys.modules[mod.__name__]=mod;exec(compile(raw,str(f),'exec'),vars(mod));sources={'fixture.py':hashlib.sha256(raw).hexdigest()}
 try:
  loaded=h._loaded(root,sources);h._authenticate_loaded(loaded,sources,root)
  replacement=compile('def changed():\n    yield 2\n',str(f),'exec');space={};exec(replacement,space);mod.held.__wrapped__.__code__=space['changed'].__code__
  try:h._authenticate_loaded(h._loaded(root,sources),sources,root)
  except ValueError:pass
  else:raise AssertionError('wrong wrapped code accepted')
 finally:sys.modules.pop(mod.__name__)
inverse=[]
for name,row in json.loads((A/'SOURCE_DELTA01.json').read_text()).items():
 s=(P/name).read_text();assert hashlib.sha256(s.encode()).hexdigest()==row['candidate_sha256'];ast.parse(s)
 for edit in reversed(row['edits']):assert s.count(edit['new'])==1;s=s.replace(edit['new'],edit['old'])
 assert s==Path(row['baseline']).read_text();assert hashlib.sha256(s.encode()).hexdigest()==row['baseline_sha256'];inverse.append(name)
s=(P/'imported_authority_lease.py').read_text();assert 'self.scheduler is self._scheduler_pin and self.scheduler.policy is self._policy_pin and self.scheduler.clock is self._clock_pin' in s
assert not {'numpy','torch','scipy'}&set(sys.modules)
r={'schema_version':1,'decision':'corrections-pass-source-only','stale_crossing_refused_old_timestamp_retained':True,'live_check_repeated_at_actual_finish':live,'known_contextmanager_accepted_wrong_wrapped_code_refused':True,'exact_inverse_files':inverse,'scheduler_policy_clock_pointer_predicate_inspected':True,'candidate_pins':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(P.glob('*.py'))},'numerical_native_or_genuine_authority_execution':False}
(D/'CHECK_CORRECTIONS03.json').write_text(json.dumps(r,sort_keys=True,indent=2)+'\n');print(json.dumps(r))
