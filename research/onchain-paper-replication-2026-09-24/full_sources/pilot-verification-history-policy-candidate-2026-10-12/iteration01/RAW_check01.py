"""Isolated AST engineering fixtures; no genuine claim/Run or Git execution."""
import ast,copy,hashlib,json,math,os,re,stat,tempfile,threading,time,types,unittest,hmac
from pathlib import Path
from weakref import WeakKeyDictionary
from datetime import datetime,timezone
from dataclasses import dataclass
P=Path(__file__).resolve().parent
N=types.SimpleNamespace
class ResearchRun:
 def _active(self):
  if hashlib.sha256((self.directory/'claim.json').read_bytes()).hexdigest()!=self._claim_sha256:raise ValueError('own changed')
  if any((self.directory/x).exists() for x in ('complete.json','failed.json')):raise ValueError('terminal')
def load(path,env):
 tree=ast.parse(path.read_text())
 tree.body=[x for x in tree.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))]
 for f in ast.walk(tree):
  if isinstance(f,ast.FunctionDef):f.body=[x for x in f.body if not isinstance(x,ast.ImportFrom)]
 exec(compile(tree,str(path),'exec'),env)
class Fixture:
 def __init__(self,count=5):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);(self.root/'research_runs').mkdir()
  self.events=[];self.clock=10.;self.verify_error=None;self.git_error=False
  self.policy={'format':'bounded-claims-v2','workers':1,'max_audit_seconds':300}
  family={'mechanism_id':'mechanism','attempt_budget':1000,'prior_attempts':0,'history_reference':'fixture'}
  window={'start':'2020-01-01T00:00:00Z','end':'2020-01-02T00:00:00Z','dataset':'data','availability':'existing'}
  exp={'family':'family','parent':None,'question':'fixture','stage':'development','reuse':'exploratory','charter':{'path':'charter','sha256':'pin'},'source_files':{'code':'pin'},'runtime_hashes':{},'cells':['cell'],'outputs':['out.json'],'windows':[window],'inputs':{'input':{'path':'input','sha256':'a'*64,'dataset':'data'}}}
  self.spec={'schema_version':1,'program_id':'program','historical_claim_verification':self.policy,'experiments':{'own':exp},'families':{'family':family},'datasets':{'data':{'identity':'data','history_reference':'fixture','exposures':[]}}}
  self.raw=json.dumps(self.spec).encode()
  for i in range(count):self.add(f'old{i:03}',family,exp,terminal=True)
  self.add('own',family,exp,terminal=False)
  self.env=dict(Path=Path,ResearchRun=ResearchRun,datetime=datetime,timezone=timezone,dataclass=dataclass,hashlib=hashlib,json=json,re=re,os=os,stat=stat,threading=threading,time=N(monotonic=lambda:self.clock),math=math,hmac=hmac,_HISTORY=WeakKeyDictionary(),_HISTORY_BUSY=WeakKeyDictionary(),_HISTORY_MUTEX=threading.Lock(),_HISTORY_SEAL_KEY=b'x'*32,_HISTORY_MAX_RUNS=512,_HISTORY_MAX_BODY=8*1024**2,_HISTORY_MAX_BYTES=64*1024**2)
  load(P/'admission.py',self.env)
  def verify(path):
   self.events.append(('verify',path.name))
   if self.verify_error is not None:raise self.verify_error
   return json.loads((path/'claim.json').read_bytes())
  self.env['verify_claim']=verify
  def git(root,*args):
   self.events.append(('git',args))
   if self.git_error:raise ValueError('current Git mutation')
   if args==('rev-parse','HEAD'):return b'source'
   if args[0]=='merge-base':return b''
   if args[0]=='show' and args[-1]=='source:gate':return self.raw
   if args[-1]=='source:charter':return b'charter'
   if '--format=%cI' in args:return b'2019-01-01T00:00:00+00:00'
   raise AssertionError(args)
  self.env['_git']=git;self.env['_committed']=lambda root,source,name,expected=None:self.raw if name=='gate' else b'charter'
  realdigest=self.env['digest'];self.env['digest']=lambda x:'pin' if x==b'charter' else realdigest(x)
  self.env['runtime_hashes']=lambda:{};self.env['_source_files']=lambda *a:self.events.append(('source',None));self.env['effective_budget']=lambda *a:1000
  self.ad=self.env['Admission'](self.root,'gate','own','source',realdigest(self.raw),self.spec,exp,family,[],True,'source',None,None,exp['inputs'],1000)
  self.run=ResearchRun();self.run.admission=self.ad;self.run.directory=self.root/'research_runs/own';self.run._claim_sha256=realdigest((self.run.directory/'claim.json').read_bytes())
 def add(self,name,family=None,exp=None,terminal=True):
  if family is None:family=self.ad.family;exp=self.ad.experiment
  d=self.root/'research_runs'/name;d.mkdir();(d/'claim.json').write_text(json.dumps({'experiment_id':name,'family':family,'experiment':exp,'prior_exposures':[],'windows':[]}))
  if terminal:(d/'failed.json').write_text('{}')
 def admit(self,force=False):
  return self.env['admit'](root=self.root,registration='gate',experiment='own',source='source',_own_claim='own',_history_run=self.run,_force_history=force)
 def prior(self,force=False):return self.env['_history_prior'](self.run,self.root,'gate','own','source','source',self.raw,self.policy,force)
 def close(self):self.temp.cleanup()
class Tests(unittest.TestCase):
 def setUp(self):self.f=Fixture()
 def tearDown(self):self.f.close()
 def test_cost_and_full_force_expiry(self):
  f=self.f;f.admit();self.assertEqual(sum(k=='verify' for k,v in f.events),6)
  f.events.clear();f.admit();self.assertEqual(sum(k=='verify' for k,v in f.events),1);self.assertIn(('source',None),f.events)
  f.events.clear();f.admit(True);self.assertEqual(sum(k=='verify' for k,v in f.events),6)
  f.events.clear();f.clock+=300;f.admit();self.assertEqual(sum(k=='verify' for k,v in f.events),6)
 def test_claim_terminal_frontier_changes(self):
  f=self.f
  for change in ('claim','terminal','new'):
   f.admit();f.events.clear()
   if change=='claim':p=f.root/'research_runs/old000/claim.json';p.write_text(p.read_text()+' ')
   if change=='terminal':(f.root/'research_runs/old000/failed.json').write_text('{"changed":true}')
   if change=='new':f.add('new')
   f.admit();self.assertGreater(sum(k=='verify' for k,v in f.events),1)
 def test_tamper_authority_clock(self):
  for change in ('seal','root','policy','clock','own'):
   f=Fixture();f.admit()
   if change=='seal':state,seal=f.env['_HISTORY'][f.run];f.env['_HISTORY'][f.run]=(state,b'x'*32)
   if change=='root':f.run.directory=f.root/'research_runs/wrong'
   if change=='policy':f.policy['workers']=2
   if change=='clock':f.clock-=1
   if change=='own':(f.run.directory/'claim.json').write_text('{}')
   with self.subTest(change=change),self.assertRaises(ValueError):f.admit()
   f.close()
 def test_full_failure_fatal_clears(self):
  f=self.f;f.admit();fatal=KeyboardInterrupt('original');f.verify_error=fatal
  with self.assertRaises(KeyboardInterrupt) as c:f.admit(True)
  self.assertIs(c.exception,fatal);self.assertNotIn(f.run,f.env['_HISTORY']);self.assertNotIn(f.run,f.env['_HISTORY_BUSY'])
 def test_current_git_and_thread_isolation(self):
  f=self.f;f.admit();f.git_error=True
  with self.assertRaisesRegex(ValueError,'current Git'):f.admit()
  f.git_error=False;errors=[]
  def work():
   try:f.admit()
   except BaseException as e:errors.append(e)
  t=threading.Thread(target=work);t.start();t.join();self.assertEqual(len(errors),1);self.assertIn('thread',str(errors[0]))
 def test_policy_bounds_active_and_fresh_run(self):
  f=self.f
  for value in ({'format':'bounded-claims-v2','workers':True,'max_audit_seconds':300},{'format':'bounded-claims-v2','workers':2,'max_audit_seconds':300.0},{'format':'bounded-claims-v2','workers':2,'max_audit_seconds':301}):
   with self.assertRaises(ValueError):f.env['_history_policy'](value)
  f.env['_HISTORY_MAX_BODY']=10
  with self.assertRaisesRegex(ValueError,'bounded'):f.admit()
  f.env['_HISTORY_MAX_BODY']=8*1024**2;f.add('foreign',terminal=False)
  with self.assertRaisesRegex(ValueError,'another active'):f.admit()
 def test_default_source_parity(self):
  a=ast.parse((P/'BASELINE_admission.py').read_text());b=ast.parse((P/'admission.py').read_text())
  old={x.name:ast.dump(x) for x in a.body if isinstance(x,ast.FunctionDef)};new={x.name:ast.dump(x) for x in b.body if isinstance(x,ast.FunctionDef)}
  for name in old.keys()-{'admit'}:self.assertEqual(old[name],new[name],name)
  # In unselected mode the original claims expression remains verbatim.
  self.assertIn('prior = claims(root) if claim_workers == 1 else claims(root, workers=claim_workers)',(P/'admission.py').read_text())
  self.assertIn('history_run._check_source(force_history=True)',(P/'compact_mcm_batched.py').read_text())
if __name__=='__main__':unittest.main(verbosity=2)
