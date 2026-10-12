import importlib.util,json,hashlib,sys,tempfile,subprocess,types,unittest,os
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent;R=P.parents[3]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
pkg=types.ModuleType('proofcandidate');pkg.__path__=[str(P)];sys.modules['proofcandidate']=pkg
v=load('proofcandidate.verify',P/'verify.py');a=load('proofcandidate.admission',P/'admission.py');old=load('proofbaseline',R/'tradingagents/research/verify.py')
class ProofTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(dir=P);cls.root=Path(cls.tmp.name)
  def git(*args):return subprocess.check_output(['git',*args],cwd=cls.root,stderr=subprocess.PIPE)
  cls.git=staticmethod(git);git('init','-q');git('config','user.name','Synthetic');git('config','user.email','synthetic@invalid');cls.pins={}
  for i in range(12):
   body=(str(i)+'x'*32767).encode();name=f'source{i:02}.txt';(cls.root/name).write_bytes(body);cls.pins[name]=hashlib.sha256(body).hexdigest()
  family={'attempt_budget':20};exps={f'case{i}':{'source_files':cls.pins,'family':'f','inputs':{},'windows':[],'stage':'engineering'} for i in range(6)}
  reg={'program_id':'synthetic','experiments':exps,'families':{'f':family},'datasets':{}};raw=json.dumps(reg).encode();(cls.root/'gate.json').write_bytes(raw);git('add','.');git('commit','-qm','synthetic metadata');cls.commit=git('rev-parse','HEAD').decode().strip()
  for name,exp in exps.items():
   d=cls.root/'research_runs'/name;d.mkdir(parents=True);claim={'experiment_id':name,'source':cls.commit,'design_source':cls.commit,'registration':'gate.json','registration_sha256':hashlib.sha256(raw).hexdigest(),'program_id':'synthetic','experiment':exp,'family':family,'windows':[],'prior_exposures':[],'bindings':None,'bindings_sha256':None,'inputs':{}};(d/'claim.json').write_text(json.dumps(claim))
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_duplicate_history_exact_fewer_processes_same_bytes(self):
  def measured(module,operation):
   original=module._git_transport;popen=subprocess.Popen;exchange=getattr(module,'_SweepGitReader',None);calls=[];sizes=[]
   def child(*args,**kwargs):p=popen(*args,**kwargs);calls.append(p);return p
   def wrapped(*args,**kwargs):raw=original(*args,**kwargs);sizes.append(len(raw));return raw
   with patch.object(subprocess,'Popen',child),patch.object(module,'_git_transport',wrapped):
    if exchange:
     original_exchange=exchange.exchange
     def get(reader,*args,**kwargs):raw=original_exchange(reader,*args,**kwargs);sizes.append(len(raw));return raw
     with patch.object(exchange,'exchange',get):result=operation()
    else:result=operation()
   self.assertTrue(all(p.poll() is not None for p in calls))
   return result,{'processes':len(calls),'returned_bytes':sum(sizes)}
  baseline,b=measured(old,lambda:[old.verify_claim(p) for p in sorted((self.root/'research_runs').iterdir())]);actual,c=measured(v,lambda:a.claims(self.root))
  self.assertEqual(actual,baseline);self.assertLess(c['processes'],b['processes']);self.assertEqual(c['returned_bytes'],b['returned_bytes'])
  (P/'SYNTHETIC_METRICS03.json').write_text(json.dumps({'baseline':b,'candidate':c,'claims':6,'equal':True,'body_byte_reduction':False},indent=2)+'\n')
 def test_unique_mismatch_missing_and_order(self):
  cases=[self.pins,{'source00.txt':'0'*64},{'source00.txt':'0'*64,'missing.txt':'0'*64},{'missing.txt':'0'*64}]
  for pins in cases:
   def result(fn):
    try:fn();return 'ok'
    except ValueError as e:return str(e)
   expected=result(lambda:old._verify_sources(self.root,pins,{self.commit}))
   with v._SweepGitReader(self.root) as reader:
    actual=result(lambda:v._verify_sources(self.root,pins,{self.commit},_source_reader=reader))
   self.assertEqual(actual,expected)
 def test_fresh_mutation_claim_checked(self):
  p=self.root/'research_runs/case0/claim.json';raw=p.read_bytes();value=json.loads(raw);value['inputs']={'forged':{}};p.write_text(json.dumps(value))
  try:
   with self.assertRaisesRegex(ValueError,'claim input identities'):a.claims(self.root)
  finally:p.write_bytes(raw)
 def test_scope_and_closed_reader(self):
  with v._SweepGitReader(self.root) as reader:
   with self.assertRaisesRegex(ValueError,'sweep root'):v._verify_sources(self.root.parent,self.pins,{self.commit},_source_reader=reader)
  with self.assertRaisesRegex(ValueError,'already closed'):reader.exchange((self.commit+':source00.txt\n').encode())
 def test_consumer_abort_reaps_and_closes(self):
  reader=v._SweepGitReader(self.root)
  with self.assertRaisesRegex(RuntimeError,'consumer'):
   with reader:
    v._verify_sources(self.root,self.pins,{self.commit},_source_reader=reader);raise RuntimeError('consumer')
  self.assertIsNotNone(reader.process.poll());self.assertTrue(all(s.closed for s in (reader.process.stdin,reader.process.stdout,reader.process.stderr)))
 def test_frame_bounds_truncation(self):
  self.assertIsNone(v._SweepGitReader._end(b'a'*40+b' blob 4\nab',1,False))
  self.assertIsNone(v._SweepGitReader._end(b'a'*40+b' blob 999999999\n',1,False))
  self.assertEqual(v._SweepGitReader._end(b'a'*40+b' blob 1\nxy',1,False),50)
  with v._SweepGitReader(self.root) as reader:
   with self.assertRaisesRegex(ValueError,'count'):reader.exchange(b'x\n'*129)
 def test_real_child_timeout_and_truncation_retired(self):
  popen=subprocess.Popen
  cases=[("import time;time.sleep(10)",subprocess.TimeoutExpired),
         ("import sys;sys.stdout.buffer.write(b'a'*40+b' blob 4\\nab');sys.stdout.flush()",ValueError)]
  for code,error in cases:
   reader=v._SweepGitReader(self.root)
   def child(*args,**kwargs):return popen([sys.executable,'-c',code],**kwargs)
   with patch.object(subprocess,'Popen',child),patch.object(v,'_GIT_SECONDS',.1):
    with self.assertRaises(error):
     with reader:reader.exchange((self.commit+':source00.txt\n').encode())
   self.assertIsNotNone(reader.process.poll());self.assertTrue(all(s.closed for s in (reader.process.stdin,reader.process.stdout,reader.process.stderr)))
 def test_body_extent_limit_keeps_semantic_order(self):
  raw=b'a'*40+b' blob 1\nx\n'+b'b'*40+b' blob '+str(v._GIT_BODY+1).encode()+b'\n'+b'z'*(v._GIT_BODY+1)+b'\n'
  self.assertEqual(v._SweepGitReader._end(raw,2,False),len(raw))
  with self.assertRaisesRegex(ValueError,'hash mismatch'):v._verify_batch(raw,[('x','c','0'*64),('z','c','0'*64)])
 def test_fatal_cleanup_priority(self):
  def fatal():raise KeyboardInterrupt('fatal')
  with self.assertRaises(KeyboardInterrupt):v._git_cleanup((fatal,),ValueError('ordinary'))
if __name__=='__main__':unittest.main()
