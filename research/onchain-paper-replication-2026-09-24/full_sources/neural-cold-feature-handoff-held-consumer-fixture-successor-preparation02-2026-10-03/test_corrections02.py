"""Actual helper/extracted draft, synthetic metadata stand-ins; no real authority."""
import ast,copy,hashlib,json,pathlib,runpy,types,unittest
P=pathlib.Path(__file__).parent;G=runpy.run_path(str(P/'generate_inputs01.py'));R=pathlib.Path('/synthetic-review-only')
def canon(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def ref(p,b=b'{}'):return {'path':p,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def role(n,v):return {'reference':ref(n+'.json',canon(v)),'document':v}
def fixture():
 source={'source_count':199,'package_count':148,'execution_admitted':False,'source':'1'*40,'anchor':'2'*40,'root':str(R),'source_files':{'uv.lock':'a'*64},'package_files':{'synthetic.py':'a'*64}}
 original={'inputs':[{'name':'original_node_ids' if i==0 else 'original_'+str(i),'reference':ref('old/'+str(i)+'.json'),'original_path':'original/'+str(i)} for i in range(11)],'original_source':'3'*40,'original_claim':'saved-original'}
 targets=[{'graph_hash':h*64,'nodes':n,'input_name':name,'manifest':ref(name+'/manifest.json'),'components':{k:ref(name+'/'+k+'.npy') for k in ('node_ids','node_features','edge_index','edge_features')}} for h,n,name in [('a',2,'graph0'),('b',3,'graph1')]]
 native={'memory_max_bytes':3*1024**3,'memory_high_bytes':3*1024**3,'reserve_bytes':3*1024**3,'start_reserve_bytes':6*1024**3,'disk_floor_bytes':10*1024**3,'wall_seconds':1800,'native_unit_limits':{'file_size_bytes':4194304},'disk_paths':[str(R)],'storage_budget':{'root':str(R)}}
 case={'schema_version':1,'kind':'root-selected-imported-held-resource-v1','program_id':'synthetic-program','experiment_id':'future-review-only','job_input':'job','plan_input':'plan','representation':'rep','producer':'prod','held_policy_input':'held','readback_outputs':{'a'*64:'a.json','b'*64:'b.json'},'additional_inputs':{}}
 selected={'operation':'produce','plan_input':'plan','producer':'prod','descriptor':{'dictionary_origin':'imported-original-v1','required_graphs':['a'*64,'b'*64]},'held_score_consumer_input':'held','pair_checkpoint_input':'pair','original_dictionary_input':'control'}
 policy={'schema_version':1,'kind':'original-import-held-score-readback-v1','targets':{h:{'output':v} for h,v in case['readback_outputs'].items()},'part_bytes':1048576,'max_read_bytes':768,'max_members':32767}
 docs={'job.json':{'schema_version':1,'kind':'compact_resource','resources':native,'environment_input':'env','payload':{'representation_jobs':{'rep':selected}}},'plan.json':{'schema_version':2,'producers':{'prod':selected|{'binding_output':'binding.json','journal_output':'journal.json'}}},'pair.json':{'numerical_source':{'commit':source['anchor'],'files':source['package_files']}},'control.json':{'kind':'original-dictionary-import-v1','sample_count':512,'motif_count':32,'original_source':'3'*40,'original_claim':'saved-original'},'env.json':{},'held.json':policy,'target-provenance.json':{'generator':'registered-explicit-arrays-v1','kind':'synthetic-original-import-targets','node_denominators':[2,3],'schema_version':1}}
 for name in ('job','plan','pair','control','env','held','target_provenance'):
  path='target-provenance.json' if name=='target_provenance' else name+'.json';case['additional_inputs'][name]={'reference':ref(path,canon(docs[path])),'dataset':'synthetic'}
 roles={'original_import_index':role('original',original),'original_evidence':role('evidence',{'sample_count':512,'motif_count':32,'resample':False,'recluster':False}),'target_catalog':role('targets',{'schema_version':1,'kind':'registered-imported-held-targets-v1','targets':targets}),'case_contract':role('case',case),'native_policy':role('native',native),'software_environment':role('env',{})}
 plan=G['held_input_plan'](roles,source)
 inputs={k:{key:v[key] for key in ('path','sha256','dataset')} for k,v in plan['input_rows'].items()}
 roles['registration']=role('registration',{'program_id':case['program_id'],'experiments':{case['experiment_id']:{'source_files':source['source_files'],'inputs':inputs,'outputs':['a.json','b.json','binding.json','journal.json'],'cumulative_budget_extension':{'synthetic':'not authority'}}}})
 return source,roles,docs

def draft(source,roles,docs):
 reads=[];documents={v['reference']['path']:canon(v['document']) for v in roles.values()};documents.update({k:canon(v) for k,v in docs.items()})
 def document(root,row):
  reads.append(row['path']);b=documents[row['path']];assert ref(row['path'],b)==row;return b
 builder=types.SimpleNamespace(__file__=str(R/'fixture_tools/capsule_builder01.py'),held_source_plan=lambda *a:source,held_document=document)
 generator=types.SimpleNamespace(__file__=str(R/'fixture_tools/generate_inputs01.py'),HELD_ROLES=G['HELD_ROLES'],held_input_plan=G['held_input_plan'])
 t=ast.parse((P/'build_release_draft01.py').read_text());f=next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name=='held_metadata_draft');f.body=[x for x in f.body if not isinstance(x,ast.ImportFrom)];ns={'builder':builder,'generator':generator,'Path':pathlib.Path,'require':G['require'],'json':json,'__file__':str(R/'proof_tools/build_release_draft01.py')};exec(compile(ast.Module(body=[f],type_ignores=[]),'actual-helper/synthetic-reader','exec'),ns)
 out=ns['held_metadata_draft'](R,source['source'],source['anchor'],[],{k:v['reference'] for k,v in roles.items()});return out,reads

def refresh(roles,docs):
 c=roles['case_contract']['document']
 for v in c['additional_inputs'].values():v['reference']=ref(v['reference']['path'],canon(docs[v['reference']['path']]))
 # Registration is also resealed to isolate inner coherence rather than hash failure.
 source=fixture()[0];plan=G['held_input_plan']({k:v for k,v in roles.items() if k!='registration'},source)
 roles['registration']['document']['experiments'][c['experiment_id']]['inputs']={k:{key:v[key] for key in ('path','sha256','dataset')} for k,v in plan['input_rows'].items()}
 for name,v in roles.items():v['reference']=ref(v['reference']['path'],canon(v['document']))

class Tests(unittest.TestCase):
 def test_complete_positive(self):
  s,r,d=fixture();o,reads=draft(s,r,d);self.assertIn('held.json',reads);self.assertFalse(o['execution_admitted']);self.assertEqual(len(o['input_plan']['input_rows']),28)
 def test_component_original_collision(self):
  s,r,d=fixture();r['target_catalog']['document']['targets'][0]['input_name']='original'
  with self.assertRaises(ValueError):G['held_input_plan'](r,s)
 def test_target_component_manifest_collision(self):
  s,r,d=fixture();r['target_catalog']['document']['targets'][1]['input_name']='graph0_node_ids'
  with self.assertRaises(ValueError):G['held_input_plan'](r,s)
 def test_additional_collision(self):
  s,r,d=fixture();r['case_contract']['document']['additional_inputs']['graph0_node_ids']={'reference':ref('other.json'),'dataset':'synthetic'}
  with self.assertRaises(ValueError):G['held_input_plan'](r,s)
 def test_missing_policy(self):
  s,r,d=fixture();del r['case_contract']['document']['additional_inputs']['held'];refresh(r,d)
  with self.assertRaises(ValueError):draft(s,r,d)
 def test_resealed_changed_policy(self):
  s,r,d=fixture();d['held.json']['max_read_bytes']=769;refresh(r,d)
  with self.assertRaises(ValueError):draft(s,r,d)
 def test_missing_provenance(self):
  s,r,d=fixture();del r['case_contract']['document']['additional_inputs']['target_provenance'];refresh(r,d)
  with self.assertRaises(ValueError):draft(s,r,d)
 def test_bad_dataset(self):
  s,r,d=fixture();r['case_contract']['document']['additional_inputs']['held']['dataset']='original_dictionary';refresh(r,d)
  with self.assertRaises(ValueError):draft(s,r,d)
 def test_plan_selection_drift(self):
  s,r,d=fixture();d['plan.json']['producers']['prod']['pair_checkpoint_input']='wrong';refresh(r,d)
  with self.assertRaises(ValueError):draft(s,r,d)
 def test_output_header_collision(self):
  s,r,d=fixture();d['plan.json']['producers']['prod']['binding_output']='a.json';refresh(r,d)
  with self.assertRaises(ValueError):draft(s,r,d)
 def test_absent_registration(self):
  s,r,d=fixture();del r['registration']
  with self.assertRaises(ValueError):draft(s,r,d)
 def test_inverse_seams_only(self):
  for name,seam in [('generate_inputs01.py','held_input_plan'),('build_release_draft01.py','held_metadata_draft')]:
   old=(P/(name+'.baseline01')).read_text();new=(P/name).read_text();a=next(x for x in ast.parse(old).body if isinstance(x,ast.FunctionDef) and x.name==seam);b=next(x for x in ast.parse(new).body if isinstance(x,ast.FunctionDef) and x.name==seam)
   lines=new.splitlines(keepends=True);lines[b.lineno-1:b.end_lineno]=old.splitlines(keepends=True)[a.lineno-1:a.end_lineno];self.assertEqual(''.join(lines),old)
  self.assertEqual((P/'capsule_builder01.py').read_bytes(),(P/'capsule_builder01.py.baseline01').read_bytes())
if __name__=='__main__':unittest.main(verbosity=2)
