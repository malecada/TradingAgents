"""Actual stdlib validator; finite synthetic JSON only, no original graph loads."""
import ast,copy,dataclasses,hashlib,importlib.util,json,os,sys,unittest
from pathlib import Path
HERE=Path(__file__).parent
SOURCE=Path(os.environ.get('VALIDATOR_SOURCE',HERE/'candidate01.py'))
GRAPH_KEYS={'node_ids','node_features','edge_index','edge_features','edge_width','parent_hash','center_id'}
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def fixture(n=6,m=2,mutation=None):
 cfg={'size':m,'sample_count':n,'hop_depth':1,'maximum_neighborhood_nodes':10};gh='a'*64;matching={'alpha':0.5}
 graphs=[{'node_ids':['n'+str(i)],'node_features':[[i*1.0,0,0,0]],'edge_index':[[],[]],'edge_features':[],'edge_width':2,'center_id':'n'+str(i),'parent_hash':gh} for i in range(n)]
 indices=list(range(n-1,n-1-m,-1));groups=[[j] for j in indices];groups[0]+=list(range(n-m))
 reps=[copy.deepcopy(graphs[i]) for i in indices]
 if mutation:mutation(graphs,reps,groups)
 records=[{'graph_hash':gh,'center_id':g['center_id'],'center_index':i,'probability':1/(n-i),'node_count':len(g['node_ids']),'edge_count':len(g['edge_features'])} for i,g in enumerate(graphs)]
 rng={'bit_generator':'PCG64','state':{'state':123,'inc':5},'has_uint32':0,'uinteger':0};scfg=cfg|{'train_start':'2022-01-03T00:00:00Z','train_end':'2026-01-01T00:00:00Z'}
 sid=sha(canonical({'training_graphs':[gh],'config':scfg,'seed':11,'records':records,'rng_state':rng}))
 samples={'graphs':graphs,'records':records,'source_hashes':[gh],'rng_state':rng,'seed':11,'identity':sid}
 d={'representatives':reps,'memberships':groups,'sample_hash':sid,'training_graph_hashes':[gh],'config':cfg,'matching_config_hash':sha(canonical(matching)),'hierarchy':[]}
 science={'graphs':[{'nodes':g['node_ids'],**{k:g[k] for k in ('node_features','edge_index','edge_features','parent_hash','center_id')}} for g in reps],'sample_hash':sid,'training_graph_hashes':[gh],'config':cfg,'matching_hash':d['matching_config_hash'],'memberships':groups,'hierarchy':[]};d['identity']=sha(canonical(science))
 v={'dictionary':d,'samples':samples,'dictionary_config':cfg,'matching_config':matching,'graph_manifest':{'graph_hash':gh,'metadata':{'start_utc':scfg['train_start'],'available_at':'2022-01-11T00:00:00Z'}},'gate':{'experiments':{'old':{'parent':None}}}}
 paths={k:'/original/'+k+'.json' for k in v}
 v['claim']={'experiment_id':'old','source':'b'*40,'design_source':'b'*40,'registration_sha256':sha(canonical(v['gate'])),'experiment':{'parent':None}}
 v['terminal']={'experiment_id':'old','status':'failed','claim_sha256':sha(canonical(v['claim']))}
 v['dictionary_intent']={'source_commit':'b'*40,'phase':'dictionary','week':'2022-01-03','bindings':{paths[k]:sha(canonical(v[k])) for k in ('samples','dictionary_config','matching_config')}}
 v['sample_intent']={'source_commit':'b'*40,'phase':'neighborhoods','week':'2022-01-03','bindings':{paths[k]:sha(canonical(v[k])) for k in ('graph_manifest','dictionary_config')}}
 v['dictionary_result']={'phase':'dictionary','week':'2022-01-03','status':'complete','details':{'identity':d['identity'],'motifs':m,'resource_only':True}}
 for k in v:paths.setdefault(k,'/original/'+k+'.json')
 blobs={k:canonical(x) for k,x in v.items()}
 p={'schema_version':1,'kind':'original-dictionary-import-v1','original_claim':'old','original_source':'b'*40,'week':'2022-01-03','dictionary_identity':d['identity'],'sample_identity':sid,'sample_config':scfg,'seed':11,'sample_count':n,'motif_count':m,'required_graphs':[gh],'max_json_bytes':1048576,'max_total_json_bytes':4194304,'max_total_nodes':n*2,'max_total_edges':n*2,'refs':{k:{'input':k,'original_path':paths[k],'sha256':sha(raw)} for k,raw in blobs.items()}}
 return p,blobs
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.old=load(HERE/'baseline.py','baseline_validator');cls.new=load(SOURCE,'selected_validator')
 def outcome(self,module,p,b):
  try:return ('return',dataclasses.asdict(module.validate(p,b)))
  except ValueError as e:return ('refused',str(e))
 def test_valid_actual_evidence_order_equal(self):
  for n,m in ((1,1),(6,2),(32,32)):
   p,b=fixture(n,m);self.assertEqual(self.outcome(self.old,p,b),self.outcome(self.new,p,b));self.assertEqual(self.new.validate(p,b).representative_indices,tuple(range(n-1,n-1-m,-1)))
 def test_full512_32_multiplicity_requirement(self):
  p,b=fixture(512,32);counts={}
  for name,module in [('old',self.old),('new',self.new)]:
   original=module.canonical;calls=[]
   def observed(v):
    if type(v) is dict and set(v)==GRAPH_KEYS:calls.append(v['center_id'])
    return original(v)
   module.canonical=observed
   try:module.validate(p,b)
   finally:module.canonical=original
   counts[name]=len(calls)
  print('GRAPH_CANONICAL_COUNTS',json.dumps(counts,sort_keys=True));self.assertEqual(counts['old'],32768);self.assertEqual(counts['new'],544)
 def test_corrupt_duplicate_nomember_partition_and_order(self):
  changes=[lambda gs,rs,gp:gs.__setitem__(0,copy.deepcopy(gs[-1])),lambda gs,rs,gp:rs[0]['node_features'][0].__setitem__(0,999),lambda gs,rs,gp:rs.__setitem__(1,copy.deepcopy(rs[0])),lambda gs,rs,gp:gp.reverse(),lambda gs,rs,gp:gs[0]['node_features'][0].__setitem__(0,True)]
  for change in changes:
   p,b=fixture(mutation=change);before=self.outcome(self.old,p,b);self.assertEqual(before[0],'refused');self.assertEqual(before,self.outcome(self.new,p,b))
 def test_recomputed_between_validations_no_cache(self):
  p,b=fixture();before=self.new.validate(p,b);p2,b2=fixture(mutation=lambda gs,rs,gp:rs[0]['node_features'][0].__setitem__(0,444))
  with self.assertRaises(ValueError):self.new.validate(p2,b2)
  self.assertEqual(dataclasses.asdict(before),dataclasses.asdict(self.new.validate(p,b)))
 def test_canonical_fatal_identity_and_first_use_order(self):
  p,b=fixture();logs=[]
  for module in (self.old,self.new):
   for center in ('n5','n2'):
    original=module.canonical;fatal=MemoryError(center);calls=[]
    def observed(v):
     if type(v) is dict and set(v)==GRAPH_KEYS:
      calls.append(v['center_id'])
      if v['center_id']==center:raise fatal
     return original(v)
    module.canonical=observed
    try:
     with self.assertRaises(MemoryError) as caught:module.validate(p,b)
     self.assertIs(caught.exception,fatal)
    finally:module.canonical=original
    logs.append(list(dict.fromkeys(calls)))
  self.assertEqual(logs[:2],logs[2:])
 def test_later_representative_not_visited_after_first_refusal(self):
  p,b=fixture(mutation=lambda gs,rs,gp:rs[0]['node_features'][0].__setitem__(0,444))
  for module in (self.old,self.new):
   original=module.canonical;seen=[]
   def observed(v):
    if type(v) is dict and set(v)==GRAPH_KEYS and v['center_id']=='n4':seen.append(id(v))
    return original(v)
   module.canonical=observed
   try:self.assertEqual(self.outcome(module,p,b),('refused','representative is not unique original sample member'))
   finally:module.canonical=original
   self.assertEqual(len(seen),1) # sample visited; later representative never canonicalized
 def test_no_numerical_or_package_imports(self):self.assertFalse(any(n.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for n in sys.modules))
if __name__=='__main__':unittest.main(verbosity=2)
