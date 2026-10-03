"""Actual extracted source + canonical owned_io; synthetic metadata/bytes only."""
import ast,copy,hashlib,json,os,pathlib,runpy,stat,sys,tempfile,time,types,unittest
from unittest.mock import patch
H=pathlib.Path(__file__).parent
IO=types.SimpleNamespace(**runpy.run_path(str(H.parent/'batch-output-exact-member-reader-candidate02-2026-10-03/owned_io.py')))
def load():
 tree=ast.parse((H/'archive_non_tail.py').read_text());nodes=[]
 for node in tree.body:
  if isinstance(node,ast.FunctionDef):
   if node.name=='_source_body':node.body=[n for n in node.body if not isinstance(n,ast.ImportFrom)]
   nodes.append(node)
 ns=dict(hashlib=hashlib,json=json,os=os,stat=stat,sys=sys,time=time,Path=pathlib.Path,META=8192,BLOCK=32768,KEY='non_tail_transport_input',CleanupFailure=IO.CleanupFailure,source_io=IO)
 # Read actual simple META assignment rather than hiding the baseline128KiB.
 for n in tree.body:
  if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='META':ns['META']=ast.literal_eval(n.value)
 exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-pure-candidate','exec'),ns);return ns
class Tests(unittest.TestCase):
 def setUp(self):self.m=load()
 def fixture(self):
  selected={'operation':'produce','plan_input':'plan','producer':'p','descriptor':{'dictionary_origin':'imported-original-v1','required_graphs':['a'*64]},'pair_checkpoint_input':'pair','non_tail_transport_input':'policy'}
  plan={'schema_version':2,'producers':{'p':selected|{'binding_output':'binding.json','journal_output':'journal.json'}}}
  run=types.SimpleNamespace(admission=types.SimpleNamespace(inputs={n:{} for n in ('plan','pair','policy')},experiment={'outputs':['binding.json','journal.json','receipt.json','terminal.json']}),read_input=lambda n:json.dumps(plan).encode())
  return run,{'kind':'compact_resource','payload':{'representation_jobs':{'rep':selected}}},plan
 def test_complete_matching_selection(self):
  r,e,p=self.fixture();self.assertEqual(self.m['_selection_graphs'](r,e,'policy'),{'a'*64})
 def test_all_mismatches_refuse(self):
  for field,val in [('descriptor',{'required_graphs':['b'*64]}),('operation','other'),('pair_checkpoint_input','foreign'),('producer','foreign'),('non_tail_transport_input','other')]:
   with self.subTest(field=field):
    r,e,p=self.fixture();p['producers']['p'][field]=val
    with self.assertRaises(ValueError):self.m['_selection_graphs'](r,e,'policy')
 def test_missing_input_or_plan_header(self):
  for mode in ('missing','schema','bool','duplicate','unsorted'):
   r,e,p=self.fixture()
   if mode=='missing':del r.admission.inputs['pair']
   elif mode=='schema':del p['schema_version']
   elif mode=='bool':p['schema_version']=True
   else:
    graphs=['a'*64,'a'*64] if mode=='duplicate' else ['b'*64,'a'*64];e['payload']['representation_jobs']['rep']['descriptor']['required_graphs']=graphs
   with self.subTest(mode=mode),self.assertRaises(ValueError):self.m['_selection_graphs'](r,e,'policy')
 def test_metadata_8k_boundary(self):
  self.assertEqual(self.m['META'],8192)
  self.assertEqual(len(self.m['encode']('a'*8189)),8192)
  with self.assertRaises(ValueError):self.m['encode']('a'*8190)
 def test_owned_fd_exact_read(self):
  with tempfile.TemporaryDirectory(dir=H) as d:
   p=pathlib.Path(d)/'source.py';p.write_bytes(b'body');self.assertEqual(self.m['_source_body'](p),b'body')
 def test_firstfatal_and_close_once(self):
  with tempfile.TemporaryDirectory(dir=H) as d:
   p=pathlib.Path(d)/'source.py';p.write_bytes(b'body');first=MemoryError('original');realclose=os.close;closed=[]
   def close(fd):closed.append(fd);realclose(fd);raise OSError('later')
   with patch.object(os,'read',side_effect=first),patch.object(os,'close',side_effect=close):
    with self.assertRaises(MemoryError) as caught:self.m['_source_body'](p)
   self.assertIs(caught.exception,first);self.assertEqual(len(closed),2);self.assertEqual(len(set(closed)),2)
 def test_success_body_uncertain_close_fails(self):
  with tempfile.TemporaryDirectory(dir=H) as d:
   p=pathlib.Path(d)/'source.py';p.write_bytes(b'body');realclose=os.close;closed=[]
   def close(fd):closed.append(fd);realclose(fd);raise OSError('later')
   with patch.object(os,'close',side_effect=close),self.assertRaises(IO.CleanupFailure):self.m['_source_body'](p)
   self.assertEqual(len(closed),2)
 def test_read_growth_bound(self):
  with tempfile.TemporaryDirectory(dir=H) as d:
   p=pathlib.Path(d)/'source.py';p.write_bytes(b'body');realread=os.read;sizes=[]
   def read(fd,count):
    sizes.append(count)
    if len(sizes)==1:
     with p.open('ab') as stream:stream.write(b'extra')
    return realread(fd,count)
   with patch.object(os,'read',side_effect=read),self.assertRaisesRegex(ValueError,'grew'):self.m['_source_body'](p)
   self.assertEqual(sizes,[5])
 def test_path_replacement_links_and_size(self):
  with tempfile.TemporaryDirectory(dir=H) as d:
   root=pathlib.Path(d);p=root/'source.py';p.write_bytes(b'body');q=root/'link';q.symlink_to(p)
   with self.assertRaises(ValueError):self.m['_source_body'](q)
   q.unlink();os.link(p,q)
   with self.assertRaises(ValueError):self.m['_source_body'](p)
   q.unlink();p.write_bytes(b'x'*(1048576+1))
   with self.assertRaises(ValueError):self.m['_source_body'](p)
   p.write_bytes(b'body');realread=os.read;done=[]
   def replace(fd,count):
    b=realread(fd,count)
    if not done:q.write_bytes(b'body');q.replace(p);done.append(1)
    return b
   with patch.object(os,'read',side_effect=replace),self.assertRaises(ValueError):self.m['_source_body'](p)
 def test_whole_other_sources_and_inverse_ast(self):
  for n in ('archive_dispatch.py','archive_transport.py'):self.assertEqual((H/n).read_bytes(),(H/(n+'.baseline01')).read_bytes())
  old=ast.parse((H/'archive_non_tail.py.baseline01').read_text());new=ast.parse((H/'archive_non_tail.py').read_text());allowed={'validate_policy'}
  for a in old.body:
   if isinstance(a,ast.FunctionDef) and a.name not in allowed:
    b=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name==a.name);self.assertEqual(ast.dump(a),ast.dump(b))
   if isinstance(a,ast.ClassDef):
    b=next(n for n in new.body if isinstance(n,ast.ClassDef) and n.name==a.name)
    for m in a.body:
     if isinstance(m,ast.FunctionDef) and not (a.name=='Context' and m.name=='__init__'):
      n=next(n for n in b.body if isinstance(n,ast.FunctionDef) and n.name==m.name);self.assertEqual(ast.dump(m),ast.dump(n))
 def test_inverse_complete_module_bytes(self):
  old=(H/'archive_non_tail.py.baseline01').read_text();new=(H/'archive_non_tail.py').read_text()
  def init(text):return next(n for c in ast.parse(text).body if isinstance(c,ast.ClassDef) and c.name=='Context' for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
  a=init(old);b=init(new);lines=new.splitlines(keepends=True);lines[b.lineno-1:b.end_lineno]=old.splitlines(keepends=True)[a.lineno-1:a.end_lineno];restored=''.join(lines)
  start=restored.index('def _source_body(');end=restored.index('class Context:',start);restored=restored[:start]+restored[end:]
  restored=restored.replace('META=8192;BLOCK=32768','META=131072;BLOCK=32768',1).replace("META*(8+3*p['max_commands'])","META*(8+2*p['max_commands'])",1)
  self.assertEqual(restored,old)
 def test_actual_constructor_prefix_before_birth(self):
  import threading
  tree=ast.parse((H/'archive_non_tail.py').read_text());ctx=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Context');init=next(n for n in ctx.body if isinstance(n,ast.FunctionDef) and n.name=='__init__');stop=next(i for i,n in enumerate(init.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='self.root.mkdir');init.body=init.body[:stop];init.name='prefix';ast.fix_missing_locations(init)
  with tempfile.TemporaryDirectory(dir=H) as d:
   root=pathlib.Path(d).resolve();path=root/'tradingagents/research/onchain_replication/archive_non_tail.py';path.parent.mkdir(parents=True);path.write_bytes(b'synthetic source only');(root/'research_artifacts').mkdir()
   base,execution,plan=self.fixture();execution['resources']={'storage_budget':{'root':str(root)}}
   policy=dict(schema_version=1,kind='non-tail-durable-population-v1',category='non-tail-original-members',namespace='only-synthetic',deadline_seconds=60,max_rounded_bytes=1000000,max_commands=64,max_parts=32,max_control_bytes=33554432,part_bytes=128,receipt_output='receipt.json',terminal_output='terminal.json',slots=[dict(graph='a'*64,role='score-batches',max_bytes=10000,max_members=32)])
   class Run:
    def __init__(self):
     self.admission=types.SimpleNamespace(root=root,experiment_id='synthetic',source='1'*40,inputs={**base.admission.inputs,'job':{}},experiment={**base.admission.experiment,'source_files':{'tradingagents/research/onchain_replication/archive_non_tail.py':hashlib.sha256(path.read_bytes()).hexdigest()}});self._claim_sha256='2'*64
    def _active(self):pass
    def _check_source(self):pass
    def _check_inputs(self):pass
    def read_input(self,n):return json.dumps({'policy':policy,'job':execution,'plan':plan}[n]).encode()
   launch={'experiment':'synthetic','source_commit':'1'*40};ns=self.m;ns.update(ResearchRun=Run,__file__=str(path),get_ident=threading.get_ident,job=types.SimpleNamespace(PREFIX=pathlib.Path('job')),matching_owner=types.SimpleNamespace(metadata=lambda *a:(launch,'3'*64),_guard=lambda *a:None))
   exec(compile(ast.Module(body=[init],type_ignores=[]),'actual-constructor-prefix-synthetic-seams','exec'),ns)
   run=Run();obj=types.SimpleNamespace();ns['prefix'](obj,run,policy_input='policy',job_input='job');self.assertFalse(obj.root.exists())
   plan['producers']['p']['descriptor']={'required_graphs':['b'*64]}
   with self.assertRaisesRegex(ValueError,'selection differs'):ns['prefix'](types.SimpleNamespace(),run,policy_input='policy',job_input='job')
   self.assertFalse(obj.root.exists())
if __name__=='__main__':unittest.main(verbosity=2)
