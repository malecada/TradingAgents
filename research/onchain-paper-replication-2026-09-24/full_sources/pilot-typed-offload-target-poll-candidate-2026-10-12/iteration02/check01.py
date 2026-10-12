"""AST engineering fixtures, never genuine Owner/Run/Admission authority."""
import ast,json,types,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;S=P.parents[3]/'tradingagents/research/onchain_replication'
def require(ok,msg):
 if not ok:raise ValueError(msg)
def load(path,names,ns):
 tree=ast.parse(path.read_text());tree.body=[x for x in tree.body if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and x.name in names]
 for node in ast.walk(tree):
  if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
   node.body=[x for x in node.body if not isinstance(x,ast.ImportFrom)]
 exec(compile(tree,str(path),'exec'),ns);return ns
N=types.SimpleNamespace
I={};exec(compile((S/'imported_authority_interval.py').read_text(),str(S/'imported_authority_interval.py'),'exec'),I)
class Fixture:
 def __init__(self,selected=True,cost=9):
  self.t=0;self.events=[];self.cost=cost;self.hook=None
  cfg=dict(schema_version=1,kind=I['KIND'],live_interval_ms=1000,fingerprint_interval_ms=2000,full_interval_ms=10000,max_stale_ms=60000,max_calls_between_full=1000,assumption=I['ASSUMPTION'])
  self.interval=I['Interval'](cfg,clock=lambda:self.t)
  f=self
  class Owner:
   def boundary(self):f.work('boundary')
  class Target:
   def __init__(self,owner):self.owner=owner;self.execution=N(_owner=owner)
   def lease(self):
    f.events.append('poll');f.interval.validate(lambda:f.events.append('full'),lambda:f.events.append('finger'),lambda:f.events.append('live'))
    if f.hook:f.hook(self)
  self.owner=Owner();self.target=Target(self.owner)
  fields={'schema_version','backend','transport_identity','remote_namespace','local_free_floor_bytes','max_stage_verifications','max_writer_metadata_bytes','max_read_metadata_bytes','max_stage_bytes','max_workflow_metadata_bytes','max_remote_payload_bytes','max_decoded_transfer_bytes'}
  pol={k:10**9 for k in fields};pol.update(schema_version=1,backend='backend',transport_identity='transport',remote_namespace='remote',max_stage_verifications=2,max_read_metadata_bytes=100,max_stage_bytes=1000,max_writer_metadata_bytes=100)
  descriptor={'compact_archive_execution':{'backend':'backend','policy_sha256':'sha'}}
  item=dict(native_backend='native',compact_archive_input='archive',descriptor=descriptor)
  job={'payload':{'representation_jobs':{'r':dict(item,plan_input='plan')}}};plan={'producers':{'p':item}}
  def read(name):self.work(name);return json.dumps({'execution_job':job,'plan':plan}[name]).encode()
  run=N(read_input=read,admission=N(inputs={'archive':{'path':'archive','sha256':'sha'}},root=Path('/synthetic')))
  self.owner.bound=N(_run=run,record=dict(representation='r',producer='p',workflow_identity='key',source_commit='source'))
  self.owner.policy=dict(backend='native',log=dict(max_events=1,chunk_events=1),schedule=dict(max_total_checkpoints=1));self.owner.required=['mcm'];self.owner.identity='owner'
  def verify(owner):self.events.append('verify')
  ns=dict(require=require,Target=Target,json=json,re=__import__('re'),FIELDS=fields,BACKEND='backend',thaw=lambda x:x,freeze=lambda x:x,cache_key=lambda x:'key',compact_owner=N(Owner=Owner,verify_current=verify,matching_owner=N(metadata=lambda *a:(pol,'sha'))),writer=N(_policy=lambda *a:{'max_chunks':1},archive=N(_transport=lambda x:'transport'),events=N(RECORD_BYTES=1)),read_controls=N(policy=lambda p:p,capacity=lambda *a:{'logical_bytes':1},selected=lambda w:None),io=N(META_LIMIT=1))
  source=P/('archive_owner_policy.py' if selected else 'BASELINE_archive_owner_policy.py')
  load(source,{'_poll_target','_writer','_inputs','_record','Selection'},ns);self.ns=ns
  self.interval.validate(lambda:None,lambda:None,lambda:None)
 def work(self,name):self.events.append(name);self.t+=self.cost
 def record(self,selected=True):return self.ns['_record'](self.owner,'archive',object(),**({'target':self.target} if selected else {}))
class Checks(unittest.TestCase):
 def test_original_red(self):
  f=Fixture(False);f.record(False);f.record(False)
  with self.assertRaisesRegex(ValueError,'stale interval'):f.target.lease()
  self.assertEqual(f.t,108)
 def test_twelve_admissions_green(self):
  f=Fixture();a=f.record();b=f.record();f.target.lease();self.assertEqual(a,b);self.assertEqual(f.t,108)
  self.assertEqual([e for e in f.events if e in ('boundary','execution_job','plan')],['boundary','execution_job','plan']*4)
 def test_none_exact_order_result(self):
  a=Fixture(False);b=Fixture();self.assertEqual(a.record(False),b.record(False));self.assertEqual(a.events,b.events)
 def test_indivisible(self):
  f=Fixture(cost=61)
  with self.assertRaisesRegex(ValueError,'stale interval'):f.record()
 def test_poll_failure_stops_original_calls(self):
  for failure in (ValueError('source changed'),RuntimeError('environment changed'),KeyboardInterrupt()):
   f=Fixture();f.hook=lambda t:(_ for _ in ()).throw(failure)
   with self.assertRaises(type(failure)) as ctx:f.record()
   self.assertIs(ctx.exception,failure);self.assertNotIn('execution_job',f.events)
 def test_fake_owner_execution_replacement(self):
  for mutate in (lambda f:setattr(f,'target',object()),lambda f:setattr(f.target,'owner',object()),lambda f:setattr(f.target.execution,'_owner',object())):
   f=Fixture();mutate(f)
   with self.assertRaises(ValueError):f.record()
  f=Fixture();f.hook=lambda t:setattr(t,'execution',N(_owner=f.owner))
  with self.assertRaisesRegex(ValueError,'changed during poll'):f.record()
 def test_selection_forwards(self):
  f=Fixture();r=f.record();s=f.ns['Selection'](f.owner,'archive',object(),r);s.check(target=f.target);self.assertEqual(s.writer_policy('mcm',target=f.target)['remote_prefix'],'remote-key')
 def test_precap_no_cap_and_replacements(self):
  ns=dict(require=require,_poll_target=lambda o,t:t.lease());load(P/'typed_payload_operations.py',{'_Operation'},ns)
  cls=ns['_Operation'];f=Fixture();o=object.__new__(cls);o.owner=f.owner;o._target=o._target_pin=f.target;o.parent=object();o.context=N(_cap=o.parent);o.held=N(check=lambda x:None)
  o._poll_target_pre_cap();self.assertFalse(hasattr(o,'cap'))
  o._target=object()
  with self.assertRaisesRegex(ValueError,'replaced'):o._poll_target_pre_cap()
  o._target=o._target_pin;f.hook=lambda t:setattr(o.context,'_cap',object())
  with self.assertRaisesRegex(ValueError,'changed after poll'):o._poll_target_pre_cap()
 def test_source_control_flow(self):
  old=ast.parse((P/'BASELINE_typed_payload_operations.py').read_text());new=ast.parse((P/'typed_payload_operations.py').read_text())
  # Operation contextmanager cleanup/fatal behavior untouched.
  pick=lambda t,n:next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name==n)
  self.assertEqual(ast.dump(pick(old,'operation')),ast.dump(pick(new,'operation')))
  c=next(x for x in new.body if isinstance(x,ast.ClassDef) and x.name=='_Operation');init=next(x for x in c.body if isinstance(x,ast.FunctionDef) and x.name=='__init__')
  installed=False
  for stmt in init.body:
   if isinstance(stmt,ast.Assign) and any(ast.unparse(t)=='self.context._cap' for t in stmt.targets):installed=True;continue
   if installed:self.assertNotIn('_poll_target',ast.unparse(stmt))
if __name__=='__main__':unittest.main(verbosity=2)
