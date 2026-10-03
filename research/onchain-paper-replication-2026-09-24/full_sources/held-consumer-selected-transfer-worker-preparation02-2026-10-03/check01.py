"""Offline extracted source tests; no genuine run or remote authority."""
import ast,hashlib,json,os,sys,threading,unittest
from pathlib import Path
ROOT=Path(__file__).parent
NAME=sys.argv.pop(1) if len(sys.argv)>1 else 'held_score_consumer.py'
def extract(names):
 tree=ast.parse((ROOT/NAME).read_text());nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
 ns=dict(Path=Path,json=json,hashlib=hashlib,os=os,threading=threading,KIND='original-import-held-score-readback-v1',TRANSFER_KIND='original-import-held-score-selected-transfer-v2')
 exec(compile(ast.Module(nodes,type_ignores=[]),str(ROOT/NAME),'exec'),ns);return ns
class Checks(unittest.TestCase):
 def setUp(self):
  self.ns=extract({'require','_policy','_transfer_outputs','_transfer_scope','_transfer_closure'});self.graphs=['a'*64,'b'*64]
  self.p=dict(schema_version=2,kind='original-import-held-score-selected-transfer-v2',targets={h:{'output':f'read{i}.json'} for i,h in enumerate(self.graphs)},part_bytes=8192,max_read_bytes=10000,max_members=32,population_input='population',network_release_input='release',source_closure_input='closure')
 def test_selected(self):self.assertEqual(self.ns['_policy'](self.p,self.graphs,['read0.json','read1.json']),self.p)
 def test_default(self):
  p={k:v for k,v in self.p.items() if k not in ('population_input','network_release_input','source_closure_input')};p.update(schema_version=1,kind=self.ns['KIND']);self.assertEqual(self.ns['_policy'](p,self.graphs,['read0.json','read1.json']),p)
 def test_unknown(self):
  for key in ('network_allowed','callback'):
   with self.assertRaises(ValueError):self.ns['_policy'](self.p|{key:True},self.graphs,['read0.json','read1.json'])
 def test_role_collision(self):
  with self.assertRaises(ValueError):self.ns['_policy'](self.p|{'network_release_input':'population'},self.graphs,['read0.json','read1.json'])
 def test_outputs(self):
  pop={'receipt_output':'context.json','terminal_output':'terminal.json'};tx={'outputs':dict(zip(self.graphs,['transfer0.json','transfer1.json']))}
  base={'binding.json','journal.json','cell-ledger.json','resource-summary.json'}
  out=base|{'read0.json','read1.json','context.json','terminal.json','transfer0.json','transfer1.json'}
  self.assertEqual(self.ns['_transfer_outputs'](self.p,pop,tx,base,out),out)
  for bad in (out|{'extra.json'},out-{'read0.json'}):
   with self.assertRaises(ValueError):self.ns['_transfer_outputs'](self.p,pop,tx,base,bad)
  with self.assertRaises(ValueError):self.ns['_transfer_outputs'](self.p,pop,{'outputs':dict(zip(self.graphs,['read0.json','transfer1.json']))},base,out)
 def test_scope(self):
  a={'descriptor':{'required_graphs':self.graphs},'held_score_consumer_input':'held','non_tail_transport_input':'population'};b=a|{'binding_output':'binding.json','journal_output':'journal.json'}
  self.ns['_transfer_scope'](a,b,self.p)
  for mutation in ({'descriptor':{}},{'non_tail_transport_input':'other'},{'extra':1}):
   with self.assertRaises(ValueError):self.ns['_transfer_scope'](a,b|mutation,self.p)
if __name__=='__main__':unittest.main()
