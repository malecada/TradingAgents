"""Actual parser; tiny fabricated retained bytes, never genuine authority."""
import json,tempfile,unittest,sys,shutil
from pathlib import Path
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D))
from evidence_fixture03 import fixture,caller
from stage_fixture03 import populate
class Evidence(unittest.TestCase):
 def test_valid_qualified_stage_counts(self):
  for v,p,a in [('wrong-purpose',0,0),('wrong-ack',1,0),('wrong-matrix',64,64),('wrong-count',64,64)]:
   with self.subTest(variant=v),tempfile.TemporaryDirectory() as temp:
    root=Path(temp);j,w=fixture(root,v);populate(root,j,v,w);r=caller.terminal(root=root,variant=v)['evidence']['numerical_stage'];self.assertEqual((r['started_pairs'],r['completed_pairs'],r['matching_events'],r['acknowledged_cells']),(p,p,2*p,a))
 def test_all_semantic_numeric_fields_and_schema_are_authenticated(self):
  mutations={'ordered_motifs':['9'*64]*32,'representative_sample_indices':[999999]*32,'bundle_sha256':'8'*64,'numeric_bytes':-1,'original_dictionary':'7'*64,'original_matching':'6'*64,'owner_stage_completed':True,'mcm_execution_admitted':True,'extra':False}
  for field,value in mutations.items():
   with self.subTest(field=field),tempfile.TemporaryDirectory() as temp:
    root=Path(temp);j,w=fixture(root,'lease-terminal');p=j/'compact/dictionary-import/import-complete.json';record=json.loads(p.read_bytes());record['numeric'][field]=value;w(p,record)
    with self.assertRaises(ValueError):caller.terminal(root=root,variant='lease-terminal')
 def test_semantic_extent_type_missing_fields_and_order_refuse(self):
  for change in ('bool_extent','missing_bundle','indices_order','motifs_order'):
   with self.subTest(change=change),tempfile.TemporaryDirectory() as temp:
    root=Path(temp);j,w=fixture(root,'lease-terminal');p=j/'compact/dictionary-import/import-complete.json';record=json.loads(p.read_bytes());numeric=record['numeric']
    if change=='bool_extent':numeric['numeric_bytes']=True
    elif change=='missing_bundle':del numeric['bundle_sha256']
    elif change=='indices_order':numeric['representative_sample_indices'].reverse()
    else:numeric['ordered_motifs'].reverse()
    w(p,record)
    with self.assertRaises(ValueError):caller.terminal(root=root,variant='lease-terminal')
 def test_original_node_order_and_stage_scope_refuse(self):
  for change in ('scope','node-body','terminal-state','event-byte','extra-file'):
   with self.subTest(change=change),tempfile.TemporaryDirectory() as temp:
    root=Path(temp);j,w=fixture(root,'wrong-count');stage=populate(root,j,'wrong-count',w)
    if change=='scope':
     p=stage/'intent.json';v=json.loads(p.read_bytes());v['scope']['workflow']='f'*64;w(p,v)
    elif change=='terminal-state':
     p=stage/'matching/terminal.json';v=json.loads(p.read_bytes());v['state']['completed_pairs']=63;w(p,v)
    elif change=='node-body':
     p=root/'inputs/nodes.npy';p.write_bytes(p.read_bytes()[:-8]+'ba'.encode('utf-32-le'))
    elif change=='event-byte':
     p=stage/'matching/events-000000000000.bin';v=bytearray(p.read_bytes());v[32]^=1;p.write_bytes(v)
    else:w(stage/'matching/unexpected.json',{})
    with self.assertRaises(ValueError):caller.terminal(root=root,variant='wrong-count')
 def test_original_sample_body_cannot_rebind_import(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);j,w=fixture(root,'lease-terminal');p=root/'inputs/samples.json';v=json.loads(p.read_bytes());v['identity']='0'*64;w(p,v)
   with self.assertRaises(ValueError):caller.terminal(root=root,variant='lease-terminal')
 def test_missing_or_truncated_required_stage_members_refuse(self):
  for relative in ('intent.json','matching/start.json','matching/terminal.json','matching/events-000000000000.bin','stream/start.json','stream/batches/start.json','stream/tails/tail-000000000000/records.bin','stream/tails/tail-000000000000/terminal.json','stream/seal-000000000000.json','stream/batches/chunk-000000000000.bin','stream/batches/terminal.json','stream/complete.json'):
   for action in ('remove','truncate'):
    with self.subTest(path=relative,action=action),tempfile.TemporaryDirectory() as temp:
     root=Path(temp);j,w=fixture(root,'wrong-count');stage=populate(root,j,'wrong-count',w);p=stage/relative
     if action=='remove':p.unlink()
     else:p.write_bytes(p.read_bytes()[:-1])
     with self.assertRaises((ValueError,FileNotFoundError,KeyError)):caller.terminal(root=root,variant='wrong-count')
 def test_empty_stage_and_wrong_phase_counts_refuse(self):
  for variant in ('wrong-purpose','wrong-ack','wrong-matrix','wrong-count'):
   with self.subTest(variant=variant),tempfile.TemporaryDirectory() as temp:
    root=Path(temp);j,w=fixture(root,variant)
    with self.assertRaises(ValueError):caller.terminal(root=root,variant=variant)
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);j,w=fixture(root,'wrong-purpose');populate(root,j,'wrong-count',w)
   with self.assertRaises(ValueError):caller.terminal(root=root,variant='wrong-purpose')
 def test_positive_non_numeric_boundaries(self):
  for v in ('policy-bool','job-input','lease-terminal'):
   with self.subTest(variant=v),tempfile.TemporaryDirectory() as temp:
    root=Path(temp);fixture(root,v);self.assertTrue(caller.terminal(root=root,variant=v)['observed'])
if __name__=='__main__':unittest.main()
