"""Tiny stdlib/AST checks; scalar Target stand-ins are NOT admitted authority."""
import ast,copy,hashlib,importlib.util,json,pathlib,sys,types,unittest
HERE=pathlib.Path(__file__).resolve().parent
SOURCE=HERE/(sys.argv.pop(1) if len(sys.argv)>1 else 'held_tail_adapter.py')
spec=importlib.util.spec_from_file_location('pure_tail',HERE/'score_tail_archive.py')
tail=importlib.util.module_from_spec(spec);spec.loader.exec_module(tail)

def h(value):return hashlib.sha256(value.encode()).hexdigest()
class Target:
 def check(self):pass
 def sources(self):return {'source.py':h('source')}
 def derive_scope(self):return self.scope
class Semantic(unittest.TestCase):
 def helper(self,name):
  tree=ast.parse(SOURCE.read_text()); found=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name==name]
  self.assertEqual(len(found),1,'missing semantic boundary '+name)
  ns={'require':tail.require,'tail':tail,'imported':types.SimpleNamespace(Target=Target),'graph_identity':lambda m:m,'thaw':lambda x:dict(x)}
  exec(compile(ast.Module(body=found,type_ignores=[]),str(SOURCE),'exec'),ns)
  return ns[name]
 def setup_values(self):
  motifs=[h(str(i)) for i in range(32)]
  scope={k:h(k) for k in tail.SCOPE};scope['ordered_motifs']=h(json.dumps(motifs,separators=(',',':')))
  owner=object();target=Target();target.owner=owner;target.scope=scope
  target.graph=types.SimpleNamespace(node_ids=(0,))
  target.dictionary=types.SimpleNamespace(identity=scope['dictionary'],matching_config_hash=h('original'),representatives=motifs)
  c=dict(scope=copy.deepcopy(scope),ordered_motifs=list(motifs),original_matching_sha256=h('original'),rows=1,motifs=32,chunk_cells=32,owner=h('owner'))
  return owner,target,c
 def test_original_matching_and_order_come_from_typed_target(self):
  join=self.helper('_scientific_joins');owner,t,c=self.setup_values();join(owner,t,c)
  for key,value in [('original_matching_sha256',h('forged')),('ordered_motifs',list(reversed(c['ordered_motifs']))),('rows',2)]:
   bad=copy.deepcopy(c);bad[key]=value
   with self.assertRaises(ValueError):join(owner,t,bad)
  with self.assertRaises(ValueError):join(object(),t,c)
  with self.assertRaises(ValueError):join(owner,types.SimpleNamespace(**t.__dict__),c)
 def test_all_six_scientific_scope_fields_join(self):
  join=self.helper('_scientific_joins');owner,t,c=self.setup_values()
  for field in tail.SCOPE:
   bad=copy.deepcopy(c);bad['scope'][field]=h('changed '+field)
   with self.assertRaises(ValueError):join(owner,t,bad)
 def batch(self):
  _,_,c=self.setup_values()
  start=dict(schema_version=1,scope=c['scope'],owner=c['owner'],rows=1,motifs=32,chunk_cells=32,dtype='<f8',order='row-major')
  raw=tail.encode(start);c['batch_start_sha256']=tail.digest(raw)
  return c,start,raw
 def test_unchanged_32_cell_start_refuses_65536_capacity(self):
  check=self.helper('_batch_start');c,start,raw=self.batch();check(c,raw)
  changed=dict(c,chunk_cells=65536)
  with self.assertRaises(ValueError):check(changed,raw)
 def test_batch_schema_types_dimensions_dtype_order_scope_owner(self):
  check=self.helper('_batch_start');c,start,raw=self.batch()
  mutations=[('schema_version',True),('rows',True),('motifs',32.0),('chunk_cells',True),('dtype','<f4'),('order','column-major'),('owner',h('wrong')),('rows',2),('extra',0)]
  for key,value in mutations:
   bad=dict(start,**{key:value});body=tail.encode(bad);contract=dict(c,batch_start_sha256=tail.digest(body))
   with self.assertRaises(ValueError):check(contract,body)
  for field in tail.SCOPE:
   bad=copy.deepcopy(start);bad['scope'][field]=h('wrong');body=tail.encode(bad)
   with self.assertRaises(ValueError):check(dict(c,batch_start_sha256=tail.digest(body)),body)
 def test_batch_body_hash_and_canonical_bytes(self):
  check=self.helper('_batch_start');c,start,raw=self.batch()
  with self.assertRaises(ValueError):check(dict(c,batch_start_sha256=h('different')),raw)
  for body in (raw+b' ',b'[]',b'x'*8193):
   with self.assertRaises((ValueError,json.JSONDecodeError)):check(dict(c,batch_start_sha256=tail.digest(body)),body)
 def test_real_adapter_routes_new_checks_and_refuses_transport(self):
  tree=ast.parse(SOURCE.read_text());classes=[x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='HeldSource'];self.assertEqual(len(classes),1)
  methods={x.name:x for x in classes[0].body if isinstance(x,ast.FunctionDef)}
  self.assertIn('target',[x.arg for x in methods['__init__'].args.args])
  check_calls=[n.func.id for n in ast.walk(methods['check']) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
  self.assertGreaterEqual(check_calls.count('_scientific_joins'),2)
  calls=[n.func.id for n in ast.walk(methods['original_parts']) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
  self.assertEqual(calls.count('_batch_start'),2)
  transport=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='bind_transport')
  self.assertTrue(any(isinstance(x,ast.Raise) for x in ast.walk(transport)))
if __name__=='__main__':unittest.main(verbosity=2)
