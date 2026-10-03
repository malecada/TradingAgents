"""Tiny metadata fixtures; never interpreted as genuine registration authority."""
import hashlib,json,os,runpy,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent
B=runpy.run_path(str(P/'capsule_builder01.py'));B=B['held_document'].__globals__
G=runpy.run_path(str(P/'generate_inputs01.py'))
IO=runpy.run_path(str(P.parent/'neural-cold-feature-handoff-held-score-reader-preparation01-2026-10-03/owned_io.py'))
class Tests(unittest.TestCase):
 def source(self):return {'source_count':199,'package_count':148,'execution_admitted':False,'source':'1'*40,'anchor':'2'*40,'root':'/synthetic','source_files':{'uv.lock':'a'*64}}
 def ref(self,p):return {'path':p,'sha256':'a'*64,'bytes':1}
 def role(self,name,document):return {'reference':self.ref(name+'.json'),'document':document}
 def test_missing_roles_explicit_not_authority(self):
  x=G['held_input_plan']({},self.source());self.assertEqual(x['remaining_roles'],list(G['HELD_ROLES']));self.assertFalse(x['execution_admitted']);self.assertFalse(x['arrays_generated']);self.assertIsNone(x['experiment_id'])
 def test_complete_catalog_policy_metadata_without_arrays(self):
  targets=[]
  for i,(h,n) in enumerate([('a'*64,2),('b'*64,3)]):targets.append({'graph_hash':h,'nodes':n,'input_name':'graph'+str(i),'manifest':self.ref('g'+str(i)+'/manifest.json'),'components':{k:self.ref('g'+str(i)+'/'+k+'.npy') for k in ('node_ids','node_features','edge_index','edge_features')}})
  case={'schema_version':1,'kind':'root-selected-imported-held-resource-v1','program_id':'future-root-synthetic','experiment_id':'future-held-exp','job_input':'job','plan_input':'plan','representation':'rep','producer':'producer','held_policy_input':'held_policy','readback_outputs':{t['graph_hash']:'read'+str(i)+'.json' for i,t in enumerate(targets)},'additional_inputs':{}}
  roles={'target_catalog':self.role('targets',{'schema_version':1,'kind':'registered-imported-held-targets-v1','targets':targets}),'case_contract':self.role('case',case)}
  x=G['held_input_plan'](roles,self.source());self.assertEqual(len(x['input_rows']),10);v=x['rendered_metadata']['held_policy'];self.assertEqual(hashlib.sha256(v['raw_utf8'].encode()).hexdigest(),v['sha256']);self.assertEqual(json.loads(v['raw_utf8'])['max_read_bytes'],768);self.assertFalse(x['execution_admitted'])
  case['experiment_id']='compact-cold-comparison-20261003-01'
  with self.assertRaisesRegex(ValueError,'closed/cold'):G['held_input_plan'](roles,self.source())
 def test_original_counts_refuse_resampling(self):
  e={'sample_count':512,'motif_count':32,'resample':False,'recluster':False};self.assertFalse(G['held_input_plan']({'original_evidence':self.role('original',e)},self.source())['original_sampling_rerun'])
  e['resample']=True
  with self.assertRaises(ValueError):G['held_input_plan']({'original_evidence':self.role('original',e)},self.source())
 def test_actual_metadata_fd_growth_and_firstfatal(self):
  with tempfile.TemporaryDirectory(dir=P) as d:
   root=Path(d);f=root/'meta.json';f.write_bytes(b'{}');ref={'path':'meta.json','bytes':2,'sha256':hashlib.sha256(b'{}').hexdigest()}
   with patch.dict(B,{'_held_io':lambda root:IO['_cleanup']}):
    self.assertEqual(B['held_document'](root,ref),b'{}')
    fatal=MemoryError('read');realclose=os.close;closes=[]
    def close(fd):closes.append(fd);realclose(fd);raise OSError('close')
    with patch.object(os,'read',side_effect=fatal),patch.object(os,'close',side_effect=close):
     with self.assertRaises(MemoryError) as e:B['held_document'](root,ref)
    self.assertIs(e.exception,fatal);self.assertEqual(len(closes),2)
    realread=os.read;sizes=[]
    def grow(fd,n):
     sizes.append(n)
     if len(sizes)==1:
      with f.open('ab') as s:s.write(b'xxxx')
     return realread(fd,n)
    with patch.object(os,'read',side_effect=grow):
     with self.assertRaisesRegex(ValueError,'grew'):B['held_document'](root,ref)
    self.assertEqual(sizes,[3])
 def test_declared_numerical_reference_refusal(self):
  with self.assertRaisesRegex(ValueError,'numerical body'):B['held_document'](Path('/synthetic'),self.ref('array.npy'))
if __name__=='__main__':unittest.main(verbosity=2)
