import ast,hashlib,json,types,unittest
from pathlib import Path
from types import SimpleNamespace as N
H=Path(__file__).resolve().parent

def require(x,m):
 if not x:raise ValueError(m)
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def function(path,name):return next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name)
class Checks(unittest.TestCase):
 def setUp(self):
  self.events=[];self.mutation=lambda:None;self.revoked=False;self.calls=0;self.present=set()
  root=H.resolve();key='abc';self.key=key
  self.policy={'schema_version':1,'max_entries':10,'max_workflow_metadata_bytes':10,'numeric':{'cap':10}}
  inputs={n:{'sha256':'a'*64} for n in ('mcm','out')}
  selected={'plan_input':'plan','compact_mcm_input':'mcm'}
  payload={'execution_job':{'payload':{'representation_jobs':{'rep':selected}}},'plan':{'producers':{'prod':{'compact_mcm_input':'mcm'}}},'mcm':self.policy}
  run=N(admission=N(root=root,inputs=inputs),read_input=lambda n:json.dumps(payload[n]))
  bound=N(_run=run,record={'workflow_identity':'wf','experiment':'exp','representation':'rep','producer':'prod'})
  owner=N(bound=bound,matching={},policy={},reserved=0,maximum=100,active=None,required=['dictionary-import','mcm-abc'],stages={},root=root,identity='owner')
  d=N(representatives=['motif'],identity='dict',matching_config_hash='match')
  graph=N(node_ids=[1,2]);scope={'graph':key,'node_order':'order','dictionary':'dict','ordered_motifs':'motifs','matching':'match','workflow':'wf'}
  def check():
   self.calls+=1;self.events.append('check')
   if self.calls==2:self.mutation()
   require(not self.revoked,'revoked')
  self.target=N(check=check,_prepare_sources=lambda:{'source':'a'*64},_prepare_graph=lambda k:graph,owner=owner,dictionary=d,graph=graph,key=key,scope=scope,derive_scope=lambda:dict(scope),_pins=lambda:None,receipt_sha256='b'*64)
  self.kernel=N(validate_policy=lambda p,n:None)
  self.ns=dict(require=require,_imported=lambda d:self.imported,_sources=lambda d:{'source':'a'*64},_owner=lambda d:owner,_graph=lambda d,k:graph,thaw=lambda x:x,graph_identity=lambda x:x,node_order_hash=lambda x:'order',cache_key=digest,BACKEND='backend',json=json,_kernel=lambda d:self.kernel,publication=N(_output_policy=lambda *a:({},1)),compact_policy=N(validate=lambda *a,**k:{'logical_reservation_bytes':1}),compact_owner=N(STAGE_BYTES=1,present=lambda p:str(p) in self.present),io=N(META_LIMIT=1,_json=lambda x:self.events.append('json')),_source_evidence=lambda d,s:s)
  self.imported=True
 def invoke(self,file='compact_mcm.py'):
  n=function(H/file,'_prepare');exec(compile(ast.Module([n],type_ignores=[]),str(H/file),'exec'),self.ns)
  return self.ns['_prepare'](self.target,self.key,'mcm','out')
 def test_success(self):
  result=self.invoke();self.assertEqual(self.calls,2);self.assertEqual(self.events,['check','json','check']);self.assertEqual(result[3]['cells'],2)
 def test_legacy_inverse(self):
  self.imported=False;a=self.invoke('baseline_compact_mcm.py');self.calls=0;self.events=[];b=self.invoke();self.assertEqual(a,b);self.assertEqual(self.calls,1)
 def test_final_mutations(self):
  for case in ('revoked','result','owner','graph','dimension','stage','reservation','output'):
   with self.subTest(case=case):
    self.setUp()
    def mutate():
     if case=='revoked':self.revoked=True
     if case=='result':self.policy['numeric']['cap']=999 # read_input copied; capture actual policy below
     if case=='owner':self.target.owner=N()
     if case=='graph':self.target.graph=N(node_ids=[1,2])
     if case=='dimension':self.target.graph.node_ids.append(3)
     if case=='stage':self.target.owner.active=object()
     if case=='reservation':self.target.owner.reserved=999
     if case=='output':self.present.add(str(H.resolve()/'research_artifacts/onchain_compact_outputs/wf/exp/mcm-abc'))
    if case=='result':
     self.kernel.validate_policy=lambda p,n:setattr(self,'seen_policy',p)
     self.mutation=lambda:self.seen_policy.update(cap=999)
    else:self.mutation=mutate
    with self.assertRaises(ValueError):self.invoke()
 def test_numeric_and_other_functions_unchanged(self):
  old=(H/'baseline_compact_mcm.py').read_text();new=(H/'compact_mcm.py').read_text()
  self.assertEqual(old[old.index('    rows = len(graph.node_ids)'):old.index('    io._json(start); return')],new[new.index('    rows = len(graph.node_ids)'):new.index('    io._json(start)\n')])
  for n in ast.parse(old).body:
   if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name!='_prepare':
    actual=next(x for x in ast.parse(new).body if isinstance(x,type(n)) and x.name==n.name)
    self.assertEqual(ast.dump(n),ast.dump(actual))
 def test_private_access_and_public_check(self):
  tree=ast.parse((H/'imported_mcm_identity.py').read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef));methods=[n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name in ('sources','_prepare_sources','_prepare_graph')]
  ns=dict(require=require,job=N(required_sources=lambda:{'x'}),KERNEL='k',HELPER='h',file_hash=lambda p:'a'*64)
  exec(compile(ast.Module(methods,type_ignores=[]),'target','exec'),ns)
  t=N(owner=N(bound=N(_run=N(admission=N(root=H,experiment={'source_files':dict.fromkeys(['x','k','h'],'a'*64)})))),check=lambda:self.events.append('checked'),_pins=lambda:None,key='abc',graph=object())
  t._prepare_sources=lambda:ns['_prepare_sources'](t)
  self.assertEqual(len(ns['sources'](t)),3);self.assertEqual(self.events,['checked']);self.events=[]
  self.assertEqual(len(t._prepare_sources()),3);self.assertEqual(self.events,[])
  self.assertIs(ns['_prepare_graph'](t,'abc'),t.graph)
  with self.assertRaises(ValueError):ns['_prepare_graph'](t,'wrong')
  ns['file_hash']=lambda p:'0'*64
  with self.assertRaises(ValueError):t._prepare_sources()
if __name__=='__main__':unittest.main(verbosity=2)
