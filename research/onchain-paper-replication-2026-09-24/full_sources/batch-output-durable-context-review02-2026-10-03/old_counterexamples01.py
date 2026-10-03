"""Independent actual-source checks; synthetic authority stand-ins only, no claims."""
import ast,hashlib,json,os,pathlib,stat,sys,time,types,threading
from unittest.mock import patch
H=pathlib.Path(__file__).resolve().parent;P=H.parent/'batch-output-durable-context-preparation01-2026-10-03';ROOT=H.parents[3]
sha=lambda b:hashlib.sha256(b).hexdigest()
manifest=json.loads((P/'MANIFEST01.json').read_text());assert sha((P/'MANIFEST01.json').read_bytes())=='ab93265b16cb3cbb7e6bde0dc1e5b1309f713088b73de6398e469f59fe109ae7'
for r in manifest['files']:
 b=(P/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
deps=json.loads((P/'DEPENDENCIES01.json').read_text())['sources']
for r in deps:
 b=(ROOT/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
for n in ('archive_dispatch.py','archive_transport.py'):
 a=(ROOT/'tradingagents/research/onchain_replication'/n).read_bytes();b=(P/n).read_bytes();assert b.startswith(a);assert ast.dump(ast.parse(a))==ast.dump(ast.parse(b[:len(a)]))
 if n=='archive_transport.py':assert a==b
print('All frozen manifest/dependencies and original dispatch prefix/transport bytes PASS')
t=ast.parse((P/'archive_non_tail.py').read_text());pure=[n for n in t.body if isinstance(n,ast.FunctionDef)]
class CleanupFailure(BaseException):pass
ns=dict(hashlib=hashlib,json=json,os=os,stat=stat,sys=sys,time=time,Path=pathlib.Path,get_ident=threading.get_ident,META=131072,BLOCK=32768,KEY='non_tail_transport_input',CleanupFailure=CleanupFailure)
exec(compile(ast.Module(body=pure,type_ignores=[]),'actual-pure-source','exec'),ns)
# Run the actual constructor prefix through the final pre-birth condition. Do not
# execute namespace birth, current ResearchRun/Owner, guard or any scientific code.
ctx=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='Context');init=next(n for n in ctx.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
stop=next(i for i,n in enumerate(init.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='self.root.mkdir')
init.body=init.body[:stop];init.name='constructor_prefix';ast.fix_missing_locations(init)
synthetic=H/'synthetic-root';source=synthetic/'tradingagents/research/onchain_replication/archive_non_tail.py';source.parent.mkdir(parents=True,exist_ok=True);source.write_bytes((P/'archive_non_tail.py').read_bytes());(synthetic/'research_artifacts').mkdir(exist_ok=True)
policy=dict(schema_version=1,kind='non-tail-durable-population-v1',category='non-tail-original-members',namespace='counterexample',deadline_seconds=60,max_rounded_bytes=1000000,max_commands=64,max_parts=32,max_control_bytes=33554432,part_bytes=128,receipt_output='receipt.json',terminal_output='terminal.json',slots=[dict(graph='a'*64,role='score-batches',max_bytes=10000,max_members=32)])
selected={'operation':'produce','plan_input':'plan','producer':'p','non_tail_transport_input':'policy','descriptor':{'required_graphs':['a'*64]}}
plan={'producers':{'p':dict(selected,descriptor={'required_graphs':['b'*64]})}}
jobdoc={'kind':'compact_resource','payload':{'representation_jobs':{'r':selected}},'resources':{'storage_budget':{'root':str(synthetic)}}}
class SyntheticRun:
 def __init__(self):
  self.admission=types.SimpleNamespace(root=synthetic,experiment_id='synthetic-not-an-actual-claim',source='1'*40,inputs={'policy':{},'job':{},'plan':{}},experiment={'outputs':['receipt.json','terminal.json'],'source_files':{'tradingagents/research/onchain_replication/archive_non_tail.py':sha(source.read_bytes())}});self._claim_sha256='2'*64
 def _active(self):pass
 def _check_source(self):pass
 def _check_inputs(self):pass
 def read_input(self,n):return json.dumps({'policy':policy,'job':jobdoc,'plan':plan}[n]).encode()
launch={'experiment':'synthetic-not-an-actual-claim','source_commit':'1'*40}
ns.update(ResearchRun=SyntheticRun,__file__=str(source),job=types.SimpleNamespace(PREFIX=pathlib.Path('synthetic-job')),matching_owner=types.SimpleNamespace(metadata=lambda *a:(launch,'3'*64),_guard=lambda *a:None))
exec(compile(ast.Module(body=[init],type_ignores=[]),'actual-constructor-prefix-synthetic-seams','exec'),ns)
run=SyntheticRun();obj=types.SimpleNamespace();reads=[];first=MemoryError('first bootstrap read fatal')
class BrokenRead:
 def __enter__(self):return self
 def read(self,*args):reads.append(args);raise first
 def __exit__(self,*args):raise OSError('later bootstrap close error')
with patch.object(pathlib.Path,'open',return_value=BrokenRead()):
 try:ns['constructor_prefix'](obj,run,policy_input='policy',job_input='job')
 except OSError as e:assert str(e)=='later bootstrap close error'
 else:raise AssertionError('expected first fatal masking')
assert reads==[()];print('DNT1 CONFIRMED: exact constructor prefix calls unbounded Path.read_bytes; read MemoryError masked by close OSError')
obj=types.SimpleNamespace();ns['constructor_prefix'](obj,run,policy_input='policy',job_input='job');assert not obj.root.exists();assert selected['descriptor']!=plan['producers']['p']['descriptor'];print('DNT2 CONFIRMED: actual pre-birth constructor checks accept job graph A vs plan graph B; no namespace was born in this extracted check')
# The dependency listed in DEPENDENCIES is not imported/called by this source.
assert 'non_tail_context' not in {n.id for n in ast.walk(t) if isinstance(n,ast.Name)}
check=next(n for n in ctx.body if isinstance(n,ast.FunctionDef) and n.name=='check');assert 'get_ident() == self.thread' in ast.unparse(check)
reserve=next(n for n in next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='Operation').body if isinstance(n,ast.FunctionDef) and n.name=='reserve_next')
assert 'self.check()' in ast.unparse(reserve) and 'self.fail(e)' in ast.unparse(reserve)
print('NTC2/NTC3 are not inherited through local Reservations/finish; durable route has own thread and failure checks. No genuine concurrent/native proof.')
# Actual bounded owned-byte helper and first-fatal reducer controls.
owned=H/'owned-bytes01';owned.mkdir(exist_ok=True);fd=os.open(owned,os.O_RDONLY|os.O_DIRECTORY)
try:
 ns['write_file'](fd,'control.json',b'{}\n');assert ns['read_file'](fd,'control.json')==b'{}\n'
 realclose=os.close;closed=[]
 def close(child):closed.append(child);realclose(child);raise OSError('uncertain close')
 with patch.object(os,'read',side_effect=first),patch.object(os,'close',side_effect=close):
  try:ns['read_file'](fd,'control.json')
  except MemoryError as e:assert e is first
  else:raise AssertionError('bounded helper lost fatal')
 assert len(closed)==1
finally:os.close(fd)
print('Lower-level read_file bounded IO preserves first fatal; this does not repair separate constructor bootstrap.')
print(json.dumps({'status':'WITHHELD','findings':['DNT1','DNT2'],'numeric_imports':False,'namespace_birth_executed':False,'authority_checks':'synthetic seams only; no actual claim/Owner/guard'},sort_keys=True))
