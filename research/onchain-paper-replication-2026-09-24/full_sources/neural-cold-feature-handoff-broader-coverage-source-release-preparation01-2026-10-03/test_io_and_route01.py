import ast, hashlib, importlib.util, json, os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import acquisition_preparation as a
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
class Cases(unittest.TestCase):
 def test_actual_read_firstfatal_close_once(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'x').write_bytes(b'abc');original=os.close;closed=[];fatal=MemoryError('read sentinel')
   def close(fd):closed.append(fd);original(fd);raise OSError('close sentinel')
   with patch.object(a.os,'read',side_effect=fatal),patch.object(a.os,'close',side_effect=close):
    with self.assertRaises(MemoryError) as error:a.read_pinned(root,{'path':'x','bytes':3,'sha256':hashlib.sha256(b'abc').hexdigest()})
   self.assertIs(error.exception,fatal);self.assertEqual(len(closed),2);self.assertEqual(len(set(closed)),2)
 def test_actual_source_policy_inverse_ast_and_download_untouched(self):
  refs=json.loads((HERE/'source-pins01.json').read_bytes())['files']
  for ref in refs:
   if ref['path'].startswith('tradingagents/'):
    self.assertEqual(hashlib.sha256((ROOT/ref['path']).read_bytes()).hexdigest(),ref['sha256'])
  source=ast.parse((ROOT/'tradingagents/research/onchain_replication/range_source.py').read_text());copy=ast.parse((HERE/'range_policy_source.py').read_text())
  one=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='range_policy');two=next(n for n in copy.body if isinstance(n,ast.FunctionDef) and n.name=='range_policy')
  self.assertEqual(ast.dump(one,include_attributes=False),ast.dump(two,include_attributes=False))
 def test_actual_job_schema_accepts_only_real_ranges_payload(self):
  tree=ast.parse((ROOT/'tradingagents/research/onchain_replication/job.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='job_schema');ns={};exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual-job-schema','exec'),ns)
  job={'schema_version':1,'kind':'ranges','resources':{},'environment_input':'environment','payload':{}}
  ns['job_schema'](job)
  for change in ({'payload':{'dates':['2016-01-01']}},{'resources':{'physical_policy':{}}}):
   with self.assertRaises(ValueError):ns['job_schema']({**job,**change})
 def test_actual_frozen_drafts_full_population_and_null_release(self):
  d=json.loads((HERE/'drafts02.json').read_bytes());self.assertEqual(len(d['asset_years']),15);self.assertIsNone(d['cumulative_ceiling']);self.assertIsNone(d['identity_allocation']);self.assertFalse(d['transaction_data_admitted'])
  first=d['asset_years'][0];self.assertEqual(first['scope']['listed_complete_object_bytes'],150432044588);self.assertEqual(first['scope']['objects'],366);self.assertEqual(first['catalogue_input']['path'].split('/')[-2:],['BTC-2016','catalogue.json']);self.assertIsNone(first['range_policy'])
  self.assertEqual(d['asset_years'][-1]['asset_year'],'ETH-2021');self.assertEqual(len(first['required_physical_leaves']),16);self.assertIn('index',first['required_physical_leaves']);self.assertEqual(len(d['asset_years'][-1]['required_physical_leaves']),9)
if __name__=='__main__':unittest.main(verbosity=2)
