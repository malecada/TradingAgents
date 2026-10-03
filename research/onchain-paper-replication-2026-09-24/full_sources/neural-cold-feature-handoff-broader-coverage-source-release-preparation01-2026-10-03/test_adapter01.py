"""Tiny metadata only: never call capture/admit/network or numerical modules."""
import copy, importlib.util, json, tempfile, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('adapter',HERE/'acquisition_preparation.py')
module=None
if spec and spec.loader and (HERE/'acquisition_preparation.py').exists():
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class Cases(unittest.TestCase):
 def setUp(self):self.assertIsNotNone(module,'bounded acquisition preparation implementation absent')
 def cat(self):
  days=module.year_dates(2016)
  return {'asset':'BTC','year':2016,'listing_complete':True,'required_dates':366,'listed_dates':366,'listed_object_bytes':3660,'transaction_data_admitted':False,'dates':{d:{'objects':[{'date':d,'bytes':12,'key':f'v1.0/btc/transactions/date={d}/part.parquet','etag':'"abc"'}]} for d in days}}
 def test_exact_fifteen_and_leap_boundaries(self):
  self.assertEqual(len(module.POPULATION),15);self.assertEqual(module.POPULATION[0],('BTC',2016));self.assertEqual(module.POPULATION[-1],('ETH',2021));self.assertEqual(len(module.year_dates(2016)),366);self.assertEqual(len(module.year_dates(2017)),365)
 def test_full_year_and_original_object_byte_scope(self):
  c=self.cat();c['listed_object_bytes']=4392
  x=module.catalogue_scope(c,'BTC',2016);self.assertEqual(x['objects'],366);self.assertEqual(x['listed_complete_object_bytes'],4392);self.assertIsNone(x['selected_column_bytes'])
 def test_cell_receipt_is_not_catalogue(self):
  with self.assertRaises(ValueError):module.catalogue_scope({'id':'BTC-2016-catalogue','status':'complete','catalogue_sha256':'a'*64},'BTC',2016)
 def test_gap_wrong_date_etag_boolean_and_total_refusal(self):
  c=self.cat();c['listed_object_bytes']=4392
  for mutation in ('gap','date','etag','bool','total'):
   d=copy.deepcopy(c);first=d['dates']['2016-01-01']['objects'][0]
   if mutation=='gap':d['dates'].pop('2016-01-02')
   elif mutation=='date':first['date']='2016-01-02'
   elif mutation=='etag':first['etag']='abc'
   elif mutation=='bool':first['bytes']=True
   else:d['listed_object_bytes']=1
   with self.assertRaises(ValueError,msg=mutation):module.catalogue_scope(d,'BTC',2016)
 def test_policy_real_function_and_strict_caps(self):
  caps=dict(maximum_span_bytes=1024,max_requests=2000,max_received_bytes=10000000,max_blob_bytes=20000000)
  p=module.policy_draft('BTC',2016,'catalogue_BTC_2016',caps)
  self.assertEqual(p['retries'],0);self.assertEqual(len(p['dates']),366);self.assertEqual(p['catalogue_inputs'],{'2016':'catalogue_BTC_2016'})
  for key in caps:
   bad=dict(caps);bad[key]=True
   with self.assertRaises(ValueError):module.policy_draft('BTC',2016,'catalogue_BTC_2016',bad)
 def test_no_daily_new_identity_or_outside_population(self):
  with self.assertRaises(ValueError):module.policy_draft('ETH',2024,'x',{})
 def test_missing_release_not_promoted_by_caller_booleans(self):
  for x in ({},{'approved':True,'budget':65,'preserved':True}):
   with self.assertRaises(module.ReleaseUnavailable):module.require_execution_release(x)
 def test_unknown_caps_not_inferred_from_object_bytes(self):
  self.assertIsNone(module.policy_draft('BTC',2016,'catalogue_BTC_2016',None))
 def test_bounded_read_mutation_hash_link_secret_refuse(self):
  import hashlib,os
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'x').write_bytes(b'abc');h=hashlib.sha256(b'abc').hexdigest()
   self.assertEqual(module.read_pinned(root,{'path':'x','bytes':3,'sha256':h}),b'abc')
   for ref in ({'path':'x','bytes':3,'sha256':'0'*64},{'path':'../x','bytes':3,'sha256':h},{'path':'keys/x','bytes':3,'sha256':h}):
    with self.assertRaises(ValueError):module.read_pinned(root,ref)
   os.link(root/'x',root/'y')
   with self.assertRaises(ValueError):module.read_pinned(root,{'path':'x','bytes':3,'sha256':h})
 def test_body_limits_before_open(self):
  with self.assertRaises(ValueError):module.read_pinned(Path('/not-real'),{'path':'x','bytes':9000000,'sha256':'0'*64})
if __name__=='__main__':unittest.main(verbosity=2)
