"""Exact phase module AST with mocked authority; no real Scope or numerical imports."""
import ast,copy,hashlib,json,math,os,re,time,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[4]
SOURCE=ROOT/'tradingagents/research/onchain_replication/neural_phases.py'
def encoded(value,maximum=65536):
 raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
 if len(raw)>maximum:raise ValueError('bound')
 return raw

def identity():
 return {'plan_sha256':'a'*64,'claim_sha256':'b'*64,'source_commit':'c'*40,'model_config_sha256':'d'*64,'cell_id':'neural_checkpoint-2022-01-03','graph_manifest_sha256':'e'*64}

def selected():
 policy={'schema_version':1,'backend':'streamed-gat-mulsum-v1','block_edges':65536}
 sha='e8355dc4443dc40b64fe2fd0d22f764d47280c655f921e9f1705042e348ec21f'
 return {'policy':policy,'policy_sha256':hashlib.sha256(encoded(policy)).hexdigest(),'source_path':'tradingagents/research/onchain_replication/streamed_gat.py','source_sha256':sha,'candidate_sha256':sha}

class Checks(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  producer=Path(self.tmp.name);self.cell=producer/'cell-00';self.cell.mkdir();self.writes=[]
  self.scope=SimpleNamespace(roots={'producer':producer},anchor={'source':'c'*40},anchor_hash='f'*64,policy={'max_json_bytes':65536},check=lambda:{'claim_sha256':'b'*64})
  self.scope.atomic=lambda path,value:self.writes.append(copy.deepcopy(value))
  self.scope.read_metadata=lambda path:self.writes[-1]
  ns={'hashlib':hashlib,'json':json,'math':math,'os':os,'Path':Path,'re':re,'time':time,'current_metadata_scope':lambda:self.scope,'_bounded_encode':encoded,'_close':lambda *a:None}
  tree=ast.parse(SOURCE.read_text());tree.body=[n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom))]
  exec(compile(tree,str(SOURCE),'exec'),ns);ns['_sample']=lambda path:{'qualification':'mocked metadata'};self.cls=ns['PhaseJournal']
 def make(self,value):return self.cls(self.scope,self.cell,value,'/sys/fs/cgroup/mock')
 def test_legacy_receipt_unchanged(self):
  value=identity();journal=self.make(value);journal.record('graph_validation_before');self.assertEqual(self.writes[0]['schema_version'],1);self.assertEqual(self.writes[0]['identity'],value)
 def test_selected_receipt_detached_and_schema2(self):
  value=identity();value['model_execution']=selected();expected=copy.deepcopy(value);journal=self.make(value)
  value['model_execution']['policy']['block_edges']=1;value['model_execution']['source_sha256']='0'*64
  journal.record('graph_validation_before');journal.record('graph_validation_after')
  self.assertEqual(self.writes[-1]['schema_version'],2);self.assertEqual(self.writes[-1]['identity'],expected)
 def test_malformed_selected_refused_before_write(self):
  changes=[('policy_sha256','0'*64),('source_path','other.py'),('source_sha256','0'*64),('candidate_sha256','0'*64),('extra',1)]
  for key,val in changes:
   value=identity();value['model_execution']=selected();value['model_execution'][key]=val
   with self.subTest(key=key),self.assertRaises(ValueError):self.make(value)
  for key,val in [('schema_version',True),('block_edges',True),('schema_version',2),('block_edges',65535),('backend','eager'),('extra',0)]:
   value=identity();value['model_execution']=selected();value['model_execution']['policy'][key]=val
   value['model_execution']['policy_sha256']=hashlib.sha256(encoded(value['model_execution']['policy'])).hexdigest()
   with self.subTest(policy=key,val=val),self.assertRaises(ValueError):self.make(value)
  self.assertEqual(self.writes,[])
 def test_legacy_refusals_and_authority_unchanged(self):
  for change in [{'unknown':1},{'claim_sha256':'bad'},{'source_commit':'0'*40},{'cell_id':'other'}]:
   value=identity();value.update(change)
   with self.assertRaises(ValueError):self.make(value)
  journal=self.make(identity());self.scope.anchor_hash='0'*64
  with self.assertRaises(ValueError):journal.record('graph_validation_before')
  self.assertEqual(self.writes,[])
  with self.assertRaises(ValueError):journal.record('graph_validation_before')

if __name__=='__main__':unittest.main()
