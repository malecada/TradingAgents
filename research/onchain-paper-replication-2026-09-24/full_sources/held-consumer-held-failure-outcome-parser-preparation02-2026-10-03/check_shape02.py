import ast,copy,importlib.util,sys,types,unittest,hashlib
from pathlib import Path
P=Path(__file__).parent
source=Path(sys.argv.pop(1)) if len(sys.argv)>1 else P/'held_failure01.py'
s=importlib.util.spec_from_file_location('failure',source);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
JP=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source/tradingagents/research/onchain_replication/feature_journal.py')
tree=ast.parse(JP.read_bytes());cl=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='FeatureJournal');seal=next(n for n in cl.body if isinstance(n,ast.FunctionDef) and n.name=='seal');ns={};exec(compile(ast.Module([seal],[]),str(JP),'exec'),ns)
REASON='FixturePublicationFailure: registered second-target publication boundary; retain first output; no retry'
def witness():
 workflow='a'*64;captured=[]
 obj=types.SimpleNamespace(directory=P/'never-created-journal',sealed=False,records=[],identity=None,parent=None,owner={'workflow_identity':workflow},required=list(m.TARGETS),_publish=lambda p,v:captured.append(v))
 ns['seal'](obj,'failed',reason=REASON)
 cells=[dict(id='import-target-01',status='complete',resource_only=True),dict(id='import-target-02',status='failed',reason=REASON,resource_only=True)]
 resource=dict(schema_version=2,kind='original-import-resource-terminal',status='failed',resource_only=True,financial_representation_admitted=False,reason=REASON)
 return [cells,resource,captured[0],workflow]
class Checks(unittest.TestCase):
 def test_actual_source_seal_record(self):
  a=witness();self.assertIsNone(a[2]['workflow_identity']);self.assertIsNone(a[2]['parent']);self.assertEqual(a[2]['events'],[]);self.assertEqual(m.failure_shape(*a),REASON)
 def test_top_level_and_parent_refuse(self):
  for key,value in [('workflow_identity','a'*64),('workflow_identity',False),('parent',{}),('parent','a'*64),('events',[{}]),('events',None)]:
   a=witness();a[2][key]=value
   with self.assertRaises((ValueError,TypeError,KeyError)):m.failure_shape(*a)
 def test_owner_workflow_refuse(self):
  for value in (None,'b'*64,False):
   a=witness();a[2]['owner']['workflow_identity']=value
   with self.assertRaises(ValueError):m.failure_shape(*a)
 def test_missing_fields_refuse(self):
  for key in ('owner','workflow_identity','parent','events'):
   a=witness();a[2].pop(key)
   with self.assertRaises((ValueError,KeyError,TypeError)):m.failure_shape(*a)
 def test_existing_shape_refusals(self):
  for key,value in [('schema_version',True),('status','complete'),('reason','wrong'),('required_graphs',[])]:
   a=witness();a[2][key]=value
   with self.assertRaises(ValueError):m.failure_shape(*a)
 def test_cell_dispositions_unchanged(self):
  for index in (0,1):
   a=witness();a[0][index]['status']='unavailable'
   with self.assertRaises(ValueError):m.failure_shape(*a)
if __name__=='__main__':unittest.main()
