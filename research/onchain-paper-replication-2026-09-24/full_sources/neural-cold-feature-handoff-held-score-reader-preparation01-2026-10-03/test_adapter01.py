"""Actual adapter logic and exact reader; authority classes explicitly synthetic."""
import ast,hashlib,json,os,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).parent
sys.path.insert(0,str(HERE))
import exact_members02 as reader
import owned_io

def enc(v):return (json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def require(v,m):
 if not v:raise ValueError(m)
class Owner:
 def lease(self):require(not self.poisoned and not self.closed,'poisoned owner')
class Stage:
 def integrity(self):require(self.owner.active is self,'changed stage')
 def lease(self):self.owner.lease();self.integrity();require(not self.closed,'closed stage')
class Held:
 def check(self,o):require(self.active and self.owner is o,'expired token')
class Target:
 def check(self):self.owner.lease();self.calls+=1
 def derive_scope(self):return self.scope.copy()
class Stream:pass

def load():
 p=HERE/'held_score_reader.py'
 if not p.exists():return None
 tree=ast.parse(p.read_text());tree.body=[n for n in tree.body if not (isinstance(n,ast.ImportFrom) and (n.module or '').startswith('tradingagents'))]
 ns={'__name__':'qualified_held_reader','__file__':str(p),'owners':types.SimpleNamespace(Owner=Owner,Stage=Stage,_HeldTransition=Held,verify_current=lambda o:o.lease(),io=types.SimpleNamespace(CleanupFailure=owned_io.CleanupFailure)),
     'imported':types.SimpleNamespace(Target=Target),'streams':types.SimpleNamespace(MCMScoreStream=Stream,completed_evidence=lambda s:s.evidence),
     'canonical_bytes':lambda v:json.dumps(v,sort_keys=True,separators=(',',':')).encode(),'digest':sha,'thaw':lambda v:v,'graph_identity':lambda m:m}
 exec(compile(tree,str(p),'exec'),ns)
 # Genuine source admission is NOT simulated: explicit extracted-source qualification.
 ns['_source_check']=lambda owner:None
 return types.SimpleNamespace(**ns)

class AdapterTests(unittest.TestCase):
 def setUp(self):
  self.m=load();self.assertIsNotNone(self.m,'genuine held reader implementation missing')
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  o=self.owner=Owner();o.identity='1'*64;o.poisoned=False;o.closed=False;o._binding_sha256='2'*64;o.root=self.root;o.policy={'score_chunk_cells':32,'max_retained_logical_bytes':1048576}
  run=types.SimpleNamespace(admission=types.SimpleNamespace(source='a'*40,inputs={'job':{'sha256':sha(b'{}')}}),read_input=lambda k:b'{}')
  o.bound=types.SimpleNamespace(_run=run,record={'resource_only':True,'job_input':'job','job_sha256':sha(b'{}'),'source_commit':'a'*40})
  st=self.stage=Stage();st.owner=o;st.name='mcm-'+'3'*64;st.root=self.root/st.name;st.root.mkdir();st.kind='mcm';st.closed=False;st.pairs=64;st.reservation=1048576;st.scope={'workflow':'4'*64};st.intent=enc({'stage':st.name});st.intent_sha256=sha(st.intent);(st.root/'intent.json').write_bytes(st.intent);st.inode=(st.root.stat().st_dev,st.root.stat().st_ino);o.active=st;o.stages={st.name:st}
  t=self.target=Target();t.owner=o;t.calls=0;t.graph=types.SimpleNamespace(node_ids=('a','b'));t.dictionary=types.SimpleNamespace(identity='5'*64,matching_config_hash='6'*64,representatives=tuple(str(i).zfill(64) for i in range(32)))
  t.scope={k:str(i+1)*64 for i,k in enumerate(reader.SCOPES)};t.scope['workflow']='4'*64;t.scope['dictionary']='5'*64
  h=self.held=Held();h.owner=o;h.active=True
  s=self.stream=Stream();s.root=st.root/'stream';s.root.mkdir();(s.root/'batches').mkdir();s.owner=o.identity;s.n=2;s.k=32;s.cells=64;s.closed=True;s.active=None;s._imported=s._imported_pin=t;s.scope=t.scope.copy();s.workload=t.scope['workflow'];s.nodes=t.graph.node_ids;s.motifs=t.dictionary.representatives
  start=dict(schema_version=1,scope=t.scope,owner=o.identity,rows=2,motifs=32,chunk_cells=32,dtype='<f8',order='row-major');br=s.root/'batches';self.write(br/'start.json',start);startsha=sha(enc(start));head=startsha
  for index in range(2):
   raw=bytes([index])*256;headrow=dict(schema_version=1,start_sha256=startsha,previous=head,index=index,start_cell=index*32,cells=32,payload_sha256=sha(raw));self.write(br/f'chunk-{index:012d}.json',headrow);(br/f'chunk-{index:012d}.bin').write_bytes(raw);head=sha(enc(headrow))
  term=dict(schema_version=1,start_sha256=startsha,head=head,status='complete',cells=64,chunks=2,reason='',pending=[]);self.write(br/'terminal.json',term)
  start=dict(schema_version=1,kind='mcm-score-stream',scope=t.scope,owner=o.identity,rows=2,motifs=32,batch_start_sha256=startsha,chunk_cells=32);self.write(s.root/'start.json',start);s.start_sha=sha(enc(start));s.head='7'*64
  s.batches=types.SimpleNamespace(root=br,closed=True,chunks=2,chunk_cells=32,start_sha=startsha)
  complete=dict(schema_version=1,start_sha256=s.start_sha,head=s.head,cells=64,chunks=2,batch_terminal_sha256=sha(enc(term)));self.write(s.root/'complete.json',complete)
  s.evidence=((t,s.batches,s.root,s.owner,s.start_sha,s.head,2,32,64,2,32,startsha),enc(complete),sha(enc(complete)))
 def write(self,p,v):p.write_bytes(enc(v))
 def test_read_exact_bytes_and_close(self):
  with self.m.open_held(self.target,self.stage,self.held,self.stream) as r:
   self.assertEqual(r.members,('chunk-000000000000.bin','chunk-000000000001.bin'));self.assertEqual(r.read_part(r.members[1],8,16),b'\1'*16)
  self.assertFalse(self.owner.poisoned);self.assertTrue(r.closed)
 def test_mutation_missing_and_swapped_inode_poison(self):
  with self.assertRaises(BaseException):
   with self.m.open_held(self.target,self.stage,self.held,self.stream) as r:
    p=self.stream.root/'batches'/r.members[0];old=p.read_bytes();p.unlink();p.write_bytes(old);r.read_part(r.members[0],0,8)
  self.assertTrue(self.owner.poisoned)
 def test_header_order_refused(self):
  p=self.stream.root/'batches/chunk-000000000001.json';v=json.loads(p.read_bytes());v['start_cell']=0;self.write(p,v)
  with self.assertRaises(BaseException):
   with self.m.open_held(self.target,self.stage,self.held,self.stream):pass
  self.assertTrue(self.owner.poisoned)
 def test_token_and_target_mutation_refused(self):
  with self.assertRaises(BaseException):
   with self.m.open_held(self.target,self.stage,self.held,self.stream) as r:
    self.held.active=False;r.read_part(r.members[0],0,8)
  self.assertTrue(self.owner.poisoned)
 def test_first_body_fatal_survives_close_failure_once(self):
  fatal=MemoryError('body');calls=[];patcher=None
  def badcheck(r):calls.append(1);raise OSError('reader close uncertainty')
  try:
   with self.m.open_held(self.target,self.stage,self.held,self.stream):
    patcher=patch.object(reader.LocalContent,'check',badcheck);patcher.start();raise fatal
  except BaseException as got:self.assertIs(got,fatal)
  else:self.fail('fatal lost')
  finally:
   if patcher is not None:patcher.stop()
  self.assertEqual(len(calls),2);self.assertTrue(self.owner.poisoned)
 def test_first_actual_close_fatal_promotes_ordinary_body(self):
  fatal=SystemExit(9);patcher=None
  try:
   with self.m.open_held(self.target,self.stage,self.held,self.stream):
    patcher=patch.object(reader.LocalContent,'check',side_effect=fatal);patcher.start();raise ValueError('body')
  except BaseException as got:self.assertIs(got,fatal)
  else:self.fail('actual fatal lost')
  finally:
   if patcher is not None:patcher.stop()
  self.assertTrue(self.owner.poisoned)
 def test_missing_member_and_read_extent_refuse(self):
  with self.assertRaises(BaseException):
   with self.m.open_held(self.target,self.stage,self.held,self.stream) as r:
    (self.stream.root/'batches'/r.members[1]).unlink();r.read_part(r.members[0],0,8)
  self.assertTrue(self.owner.poisoned)
 def test_unaligned_range_refuses_and_revokes(self):
  with self.assertRaises(BaseException):
   with self.m.open_held(self.target,self.stage,self.held,self.stream) as r:r.read_part(r.members[0],1,8)
  self.assertTrue(self.owner.poisoned)
 def test_rebinding_and_expired_close_refuse(self):
  with self.assertRaises(BaseException):
   with self.m.open_held(self.target,self.stage,self.held,self.stream) as r:
    with self.assertRaises(AttributeError):r.target=object()
    with self.assertRaises(AttributeError):del r._objects
    self.stage.closed=True
  self.assertTrue(self.owner.poisoned)
if __name__=='__main__':unittest.main()
