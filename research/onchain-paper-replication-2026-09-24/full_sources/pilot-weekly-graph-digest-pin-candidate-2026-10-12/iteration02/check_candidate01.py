"""Synthetic immutable-buffer controls; no Target/Owner or numerical engine run."""
import ast,copy,hashlib,json,os,resource,runpy,tempfile,types,unittest
from pathlib import Path
os.sched_setaffinity(0,{2,3});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60))
P=Path(__file__).resolve().parent;R=P.parents[3]
fixture=P.parent/'pilot-graph-hash-serialization-candidate-2026-10-12/check_serialization01.py'
ns=runpy.run_path(str(fixture));np=ns['np'];graph=ns['graph'];original_hash=ns['base']['graph_hash'];validate=ns['ctx']['validate_graph'];GraphSnapshot=ns['ctx']['GraphSnapshot']
def helper():
 tree=ast.parse((P/'weekly_graph_digest_pin.py').read_text());tree.body=[n for n in tree.body if not (isinstance(n,ast.ImportFrom) and n.level)]
 calls={'validate':0,'hash':0}
 def checked(g):calls['validate']+=1;return validate(g)
 def hashed(g):calls['hash']+=1;return original_hash(g)
 env={'np':np,'GraphSnapshot':GraphSnapshot,'validate_graph':checked,'graph_hash':hashed};exec(compile(tree,str(P/'weekly_graph_digest_pin.py'),'exec'),env)
 return env,calls
class Checks(unittest.TestCase):
 def pin(self,g):
  env,calls=helper();pin=env['WeeklyDigestPin'](g,original_digest=original_hash(g));return env,calls,pin
 def test_initial_and_fresh_validation(self):
  g=graph(1025);env,calls,pin=self.pin(g);self.assertIsNotNone(pin._pin);before=dict(calls)
  for _ in range(4):self.assertEqual(pin.verify(g),original_hash(g))
  self.assertEqual(calls['validate']-before['validate'],4);self.assertEqual(calls['hash'],before['hash'])
 def test_all_fields_changed(self):
  changes={'asset':'BTC','start_utc':'2025-12-31T00:00:00Z','end_utc':'2026-01-01T12:00:00Z','available_at':'2026-01-03T00:00:00Z','source_hashes':('c'*64,),'graph_config_hash':'c'*64,'node_ids':tuple('new'+str(i) for i in range(4)),'node_features':np.ones((4,4)),'edge_index':np.array([[1,2,3],[0,1,2]],dtype='i8'),'edge_features':np.ones((3,2)),'raw_count':4,'admitted_count':4,'exclusion_counts':types.MappingProxyType({'extra':1}),'edge_aggregates':np.ones((3,2))}
  self.assertEqual(set(changes),set(envname for envname in self.pin(graph(4))[0]['_FIELDS']))
  for name,value in changes.items():
   with self.subTest(name=name):
    g=graph(4);env,calls,pin=self.pin(g);before=original_hash(g);object.__setattr__(g,name,value)
    try:expected=original_hash(g)
    except Exception as e:
     with self.assertRaises(type(e)):pin.verify(g)
    else:self.assertEqual(pin.verify(g),expected);self.assertNotEqual(expected,before)
 def test_layout_dtype_base_replacement(self):
  for field in ('dtype','shape','strides','base_dtype','array_replace'):
   g=graph(4);env,calls,pin=self.pin(g)
   if field=='dtype':g.node_features.dtype='i8'
   elif field=='shape':g.node_features.shape=(4,2,2)
   elif field=='strides':g.node_features.strides=(8,32)
   elif field=='base_dtype':g.node_features.base.dtype='u8'
   else:object.__setattr__(g,'node_features',np.frombuffer(g.node_features.tobytes(),dtype='f8').reshape(4,4))
   try:expected=original_hash(g)
   except Exception as e:
    with self.assertRaises(type(e)):pin.verify(g)
   else:self.assertEqual(pin.verify(g),expected);self.assertIsNone(pin._pin)
 def test_mapping_backing_mutation(self):
  g=graph(4);counts={};object.__setattr__(g,'exclusion_counts',types.MappingProxyType(counts));env,calls,pin=self.pin(g);counts['zero']=0
  self.assertEqual(pin.verify(g),original_hash(g));self.assertIsNone(pin._pin)
 def test_mutable_foreign_subclass_fallback(self):
  class Sub(np.ndarray):pass
  for kind in ('mutable','owner_readonly','foreign','subclass','metadata','mapping'):
   g=graph(4);a=np.array(g.node_features)
   if kind=='owner_readonly':a.flags.writeable=False
   elif kind=='foreign':a=np.frombuffer(memoryview(a.tobytes()),dtype='f8').reshape(4,4)
   elif kind=='subclass':a=a.view(Sub)
   elif kind=='metadata':a=np.array(a,dtype=np.dtype('f8',metadata={'x':1}));a.flags.writeable=False
   if kind=='mapping':object.__setattr__(g,'exclusion_counts',{})
   else:object.__setattr__(g,'node_features',a)
   env,calls,pin=self.pin(g);self.assertIsNone(pin._pin,kind);before=calls['hash']
   for _ in range(2):self.assertEqual(pin.verify(g),original_hash(g))
   self.assertEqual(calls['hash']-before,2)
 def test_mutable_buffer_fresh_and_nonfinite(self):
  g=graph(4);storage=np.array(g.node_features);view=storage.view();view.flags.writeable=False;object.__setattr__(g,'node_features',view);env,calls,pin=self.pin(g);self.assertIsNone(pin._pin)
  first=pin.verify(g);storage[0,0]=1;self.assertEqual(pin.verify(g),original_hash(g));self.assertNotEqual(first,pin.verify(g));storage[0,0]=np.nan
  with self.assertRaisesRegex(ValueError,'nonfinite'):pin.verify(g)
 def test_optional_aggregate_and_tuple_domains(self):
  g=graph(4);a=np.ones((3,2));object.__setattr__(g,'edge_aggregates',np.frombuffer(a.tobytes(),dtype='f8').reshape(3,2));object.__setattr__(g,'edge_features',np.frombuffer(np.log1p(a).tobytes(),dtype='f8').reshape(3,2));env,calls,pin=self.pin(g);self.assertIsNotNone(pin._pin);self.assertEqual(pin.verify(g),original_hash(g))
  class String(str):pass
  for name,value in (('node_ids',list(g.node_ids)),('source_hashes',(String('a'*64),))):
   g=graph(4);object.__setattr__(g,name,value);env,calls,pin=self.pin(g);self.assertIsNone(pin._pin);self.assertEqual(pin.verify(g),original_hash(g))
 def test_original_digest_join(self):
  g=graph(4);env,calls=helper();pin=env['WeeklyDigestPin'](g,original_digest='0'*64);self.assertIsNone(pin._pin);self.assertEqual(pin.verify(g),original_hash(g))
 def test_unsupported_domains(self):
  env,calls=helper()
  for dtype in (object,[('f','f8')],np.dtype('f8',metadata={'x':1}),np.longdouble):
   a=np.zeros((4,4),dtype=dtype);a=np.frombuffer(a.tobytes(),dtype=a.dtype).reshape(a.shape) if not a.dtype.hasobject else a
   self.assertIsNone(env['_array_pin'](a))
 def test_initial_mapping_race_disables_pin(self):
  g=graph(4);counts={};object.__setattr__(g,'exclusion_counts',types.MappingProxyType(counts));digest=original_hash(g);env,calls=helper();original=env['graph_hash']
  def changing(snapshot):
   self.assertIsNot(snapshot,g)
   for name in env['_ARRAYS']:self.assertIs(getattr(snapshot,name),getattr(g,name))
   value=original(snapshot);counts['zero']=0;return value
  env['graph_hash']=changing;pin=env['WeeklyDigestPin'](g,original_digest=digest);self.assertIsNone(pin._pin);env['graph_hash']=original;self.assertEqual(pin.verify(g),original_hash(g));self.assertNotEqual(pin.verify(g),digest)
 def test_racy_rejoin_falls_back(self):
  g=graph(4);env,calls,pin=self.pin(g)
  def race(*args):raise RuntimeError('mapping changed during iteration')
  env['_rejoin']=race;before=calls['hash'];self.assertEqual(pin.verify(g),original_hash(g));self.assertIsNone(pin._pin);self.assertEqual(calls['hash'],before+1)
 def test_default_and_authority_calls_retained(self):
  old=ast.parse((P/'BASELINE_imported_mcm_identity.py').read_text());new=ast.parse((P/'imported_mcm_identity.py').read_text())
  def functions(tree):return {n.name:n for c in tree.body if isinstance(c,ast.ClassDef) and c.name=='Target' for n in c.body if isinstance(n,ast.FunctionDef)}
  a,b=functions(old),functions(new)
  for name in a:
   if name not in ('__init__','final'):self.assertEqual(ast.dump(a[name]),ast.dump(b[name]))
  final=copy.deepcopy(b['final'])
  class Restore(ast.NodeTransformer):
   def visit_Call(self,n):
    if isinstance(n.func,ast.Attribute) and n.func.attr=='_graph_digest':return ast.Call(ast.Name('graph_hash',ast.Load()),[ast.Attribute(ast.Name('self',ast.Load()),'graph',ast.Load())],[])
    return self.generic_visit(n)
  self.assertEqual(ast.dump(a['final']),ast.dump(Restore().visit(final)))
  self.assertIn("graph_hash(graph)==key",(P/'imported_mcm_identity.py').read_text())
if __name__=='__main__':unittest.main()
