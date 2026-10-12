import importlib.util,json,hashlib,sys,tempfile,subprocess,types,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
R=P.parents[3]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
pkg=types.ModuleType('proofcandidate');pkg.__path__=[str(P)];sys.modules['proofcandidate']=pkg
v=load('proofcandidate.verify',P/'verify.py');a=load('proofcandidate.admission',P/'admission.py')
old=load('proofbaseline',R/'tradingagents/research/verify.py')
class ProofTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(dir=P);cls.root=Path(cls.tmp.name)
  def git(*args):return subprocess.check_output(['git',*args],cwd=cls.root,stderr=subprocess.PIPE)
  cls.git=staticmethod(git);git('init','-q');git('config','user.name','Synthetic');git('config','user.email','synthetic@invalid')
  cls.pins={}
  for i in range(12):
   body=(str(i)+'x'*32767).encode();name=f'source{i:02}.txt';(cls.root/name).write_bytes(body);cls.pins[name]=hashlib.sha256(body).hexdigest()
  family={'attempt_budget':20};exps={f'case{i}':{'source_files':cls.pins,'family':'f','inputs':{},'windows':[],'stage':'engineering'} for i in range(6)}
  reg={'program_id':'synthetic','experiments':exps,'families':{'f':family},'datasets':{}}
  raw=json.dumps(reg).encode();(cls.root/'gate.json').write_bytes(raw);git('add','.');git('commit','-qm','synthetic metadata');cls.commit=git('rev-parse','HEAD').decode().strip()
  for name,exp in exps.items():
   d=cls.root/'research_runs'/name;d.mkdir(parents=True)
   claim={'experiment_id':name,'source':cls.commit,'design_source':cls.commit,'registration':'gate.json','registration_sha256':hashlib.sha256(raw).hexdigest(),'program_id':'synthetic','experiment':exp,'family':family,'windows':[],'prior_exposures':[],'bindings':None,'bindings_sha256':None,'inputs':{}}
   (d/'claim.json').write_text(json.dumps(claim))
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_duplicate_history_exact_and_fewer_body_bytes(self):
  metrics={}
  def measured(module,operation):
   original=module._git_transport;calls=[]
   def wrapped(*args,**kwargs):
    raw=original(*args,**kwargs);calls.append((len(raw),kwargs.get('headers',False)));return raw
   module._git_transport=wrapped
   try:result=operation()
   finally:module._git_transport=original
   return result,{'processes':len(calls),'returned_bytes':sum(x[0] for x in calls),'header_processes':sum(x[1] for x in calls)}
  baseline,b=measured(old,lambda:[old.verify_claim(p) for p in sorted((self.root/'research_runs').iterdir())])
  actual,c=measured(v,lambda:a.claims(self.root))
  self.assertEqual(actual,baseline);self.assertLess(c['returned_bytes'],b['returned_bytes']/2)
  (P/'SYNTHETIC_METRICS01.json').write_text(json.dumps({'baseline':b,'candidate':c,'claims':6,'equal':True},indent=2)+'\n')
 def test_unique_and_warm_hash_mismatch(self):
  cache=v._source_body_cache(self.root);v._verify_sources(self.root,self.pins,{self.commit},_body_cache=cache)
  bad=dict(self.pins);bad['source00.txt']='0'*64
  for module,kw in [(old,{}),(v,{'_body_cache':cache})]:
   with self.assertRaisesRegex(ValueError,'registered source/charter/selection hash mismatch'):module._verify_sources(self.root,bad,{self.commit},**kw)
 def test_missing_and_error_priority(self):
  bad={'source00.txt':'0'*64,'missing.txt':'0'*64}
  for module,kw in [(old,{}),(v,{'_body_cache':v._source_body_cache(self.root)})]:
   with self.assertRaisesRegex(ValueError,'hash mismatch'):module._verify_sources(self.root,bad,{self.commit},**kw)
  with self.assertRaisesRegex(ValueError,'missing, malformed'):v._verify_sources(self.root,{'missing.txt':'0'*64},{self.commit},_body_cache=v._source_body_cache(self.root))
 def test_scope_and_budget(self):
  cache=v._source_body_cache(self.root);v._verify_sources(self.root,self.pins,{self.commit},_body_cache=cache)
  self.assertLessEqual(cache['bytes'],v._GIT_BODY);self.assertLessEqual(len(cache['bodies']),v._GIT_PARTS)
  with self.assertRaisesRegex(ValueError,'sweep root'):v._verify_sources(self.root.parent,self.pins,{self.commit},_body_cache=cache)
if __name__=='__main__':unittest.main()
