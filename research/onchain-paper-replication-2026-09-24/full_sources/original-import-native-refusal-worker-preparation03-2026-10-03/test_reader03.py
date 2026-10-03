"""Actual complete-inventory reader, tiny synthetic files only."""
import ast,copy,hashlib,importlib.util,json,pathlib,stat,sys,tempfile,time,unittest
D=pathlib.Path(__file__).resolve().parent;ROOT=D.parents[3];OLD=D.parent/'original-import-native-refusal-worker-preparation02-2026-10-03';sys.path.insert(0,str(D));import refusal_inventory03 as inv
row=next(r for r in json.loads((OLD/'source_inventory02.json').read_text())['source_inventory'] if r['target']=='fixture_tools/raw_receipts01.py');path=ROOT/row['origin'];assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'];spec=importlib.util.spec_from_file_location('raw_receipts01',path);raw=importlib.util.module_from_spec(spec);sys.modules['raw_receipts01']=raw;spec.loader.exec_module(raw)
node=next(n for n in ast.parse((OLD/'refusal_outer01.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='inventory');env={'Path':pathlib.Path,'time':time,'stat':stat,'hashlib':hashlib,'body':raw.body,'require':raw.require,'FILE':inv.FILE,'GIB':inv.GIB};exec(compile(ast.Module(body=[node],type_ignores=[]),'actual retained inventory scan','exec'),env)
class Tests(unittest.TestCase):
 def setup_tree(self,root):
  outer=root/'fixture_outer'/'synthetic-case';outer.mkdir(parents=True);(root/'payload.txt').write_text('synthetic source fixture only\n');return outer
 def save(self,outer):
  def write(name,value):
   data=inv.encode(value);self.assertLessEqual(len(data),8192)
   with (outer/name).open('xb') as f:f.write(data)
  return write
 def test_actual_reader_full_original_members_and_tail(self):
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);outer=self.setup_tree(root);idx=env['inventory'](root);ref=inv.publish(root,outer,idx,'synthetic-case',self.save(outer));self.assertEqual(inv.authenticate(root,outer,'synthetic-case',ref),ref)
   (outer/'terminal.json').write_text('{"status":"synthetic"}');self.assertEqual(inv.authenticate(root,outer,'synthetic-case',ref),ref)
 def test_changed_body_unknown_member_and_root_ref_refused(self):
  for mode in ('body','extra','reference','page'):
   with self.subTest(mode=mode),tempfile.TemporaryDirectory() as td:
    root=pathlib.Path(td);outer=self.setup_tree(root);ref=inv.publish(root,outer,env['inventory'](root),'synthetic-case',self.save(outer))
    if mode=='body':(root/'payload.txt').write_text('changed')
    if mode=='extra':(root/'unlisted.txt').write_text('added')
    if mode=='reference':ref['sha256']='0'*64
    if mode=='page':next(outer.glob('inventory-page-*')).write_text('{}')
    with self.assertRaises(ValueError):inv.authenticate(root,outer,'synthetic-case',ref)
 def test_coherently_rebuilt_missing_original_member_refused(self):
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);outer=self.setup_tree(root);index=env['inventory'](root);index['members']=[r for r in index['members'] if r['path']!='payload.txt']
   with self.assertRaisesRegex(ValueError,'member set differs'):inv.publish(root,outer,index,'synthetic-case',self.save(outer))
 def test_unsupported_escaped_row_publishes_nothing(self):
  index={'schema_version':1,'root':'/synthetic-fixture','members':[{'path':'/'.join(['😀'*55]*16),'bytes':0,'allocated':0,'kind':'directory'}],'root_allocated':0,'tail_exclusion':'fixture'};writes=[]
  with self.assertRaisesRegex(ValueError,'encoded inventory row'):inv.publish(None,None,index,'synthetic-case',lambda n,v:writes.append(n))
  self.assertEqual(writes,[])
 def test_entry_headroom_refuses_before_publication(self):
  index={'schema_version':1,'root':'/synthetic-fixture','members':[{'path':str(i).zfill(5),'bytes':0,'allocated':0,'kind':'directory'} for i in range(32768)],'root_allocated':0,'tail_exclusion':'fixture'};writes=[]
  with self.assertRaisesRegex(ValueError,'entry headroom'):inv.publish(None,None,index,'synthetic-case',lambda n,v:writes.append(n))
  self.assertEqual(writes,[])
if __name__=='__main__':unittest.main(verbosity=2)
