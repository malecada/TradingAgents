"""Offline engineering checks; no Run/Owner/native/transport authority fixtures."""
import ast,hashlib,importlib.util,json,os,struct,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('history',P/'candidate/archive_control_history.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
POLICY={'schema_version':1,'format':h.FORMAT,'assumption':h.ASSUMPTION,'success_control_bytes':1024,'success_diagnostic_bytes':2048,'shard_bytes':4*1024**2,'full_interval_ms':1000,'max_stale_ms':5000,'max_callbacks_between_full':100}
def definitions(path,names,namespace):
 tree=ast.parse(path.read_text());selected=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
 exec(compile(ast.Module(body=selected,type_ignores=[]),str(path),'exec'),namespace);return namespace
class Checks(unittest.TestCase):
 def test_exact_shards_and_corruption(self):
  with tempfile.TemporaryDirectory(dir=P/'tests') as d:
   j=h.Journal(Path(d)/'journal',record_bytes=1024,total_bytes=20000,records=100,shard_bytes=1500)
   originals=[]
   for i in range(20):
    name=f'command-{i}.json';raw=(b'  exact JSON whitespace '+bytes([i])*93+b'\n');j.append(name,raw);originals.append((name,raw))
   j.audit();actual=[]
   for path in sorted(j.root.iterdir()):
    raw=path.read_bytes();at=0
    while at<len(raw):
     nl,rl=struct.unpack_from('<II',raw,at);at+=8;name=raw[at:at+nl].decode();at+=nl;body=raw[at:at+rl];at+=rl+32;actual.append((name,body))
   self.assertEqual(actual,originals)
   first=sorted(j.root.iterdir())[0];raw=first.read_bytes();first.write_bytes(raw[:50]+bytes([raw[50]^1])+raw[51:])
   with self.assertRaises(ValueError):j.audit()
 def test_limit_and_failed_fsync_no_ack(self):
  with tempfile.TemporaryDirectory(dir=P/'tests') as d:
   j=h.Journal(Path(d)/'j',record_bytes=20,total_bytes=1000,records=2,shard_bytes=400)
   fatal=KeyboardInterrupt('fsync fatal')
   with patch.object(h.os,'fsync',side_effect=fatal):
    with self.assertRaises(KeyboardInterrupt) as e:j.append('one',b'original')
   self.assertIs(e.exception,fatal);self.assertEqual((j.count,j.bytes),(0,0));self.assertTrue(j.failed)
   self.assertIn(b'original',(j.root/'control-00000000.bin').read_bytes())
   with self.assertRaises(ValueError):j.append('two',b'not a retry')
   k=h.Journal(Path(d)/'k',record_bytes=20,total_bytes=1000,records=2,shard_bytes=400)
   with self.assertRaises(ValueError):k.append('oversize',b'x'*21)
   self.assertEqual(k.count,0)
 def test_finite_audit_age_failure_and_boundary(self):
  now=[0.];audit=[];s=h.Interval(POLICY,clock=lambda:now[0]);s.check(lambda:audit.append(1))
  for i in range(20):now[0]+=.001;s.check(lambda:audit.append(1))
  self.assertEqual(len(audit),1)
  s.check(lambda:audit.append(1),force=True);self.assertEqual(len(audit),2)
  old=s.last
  def slow():now[0]+=5
  with self.assertRaises(ValueError):s.check(slow,force=True)
  self.assertEqual(s.last,old);self.assertTrue(s.failed)
  now=[10.];s=h.Interval(POLICY,clock=lambda:now[0]);s.check(lambda:None);now[0]=9
  with self.assertRaises(ValueError):s.check(lambda:None)
  self.assertTrue(s.failed)
 def test_capacity_and_invalid_policy(self):
  b=h.capacity(POLICY,472000)
  self.assertLess(b['control_bytes']+b['diagnostic_bytes'],4*1024**3)
  self.assertLess(b['control_files']+b['diagnostic_files'],2000)
  for key,value in [('full_interval_ms',5000),('success_control_bytes',True),('shard_bytes',2**30)]:
   with self.assertRaises(ValueError):h.validate({**POLICY,key:value})
 def test_legacy_policy_exact_answers(self):
  common={'require':h.need,'Path':Path,'re':__import__('re'),'hashlib':hashlib,'json':json,'FORMAT':'archive-dispatch-v1'}
  old=definitions(P/'baseline/archive_dispatch.py',{'_connection','policy'},dict(common))['policy']
  new=definitions(P/'candidate/archive_dispatch.py',{'_connection','policy'},dict(common))['policy']
  value={'schema_version':1,'format':'archive-dispatch-v1','connection':{'host':'fixture','user':'fixture','port':22,'identity_file':'/never-opened/identity','known_hosts_file':'/never-opened/hosts'},'rate_kbit':1,'max_seconds':1,'max_payload_bytes':1,'max_commands':1,'max_diagnostic_bytes':1,'max_control_bytes':1,'namespace':'test','receipt_output':'one','terminal_output':'two'}
  self.assertEqual(old(value.copy()),new(value.copy()))
  for delta in [{'schema_version':2,'typed_payload_input':'typed'},{'max_commands':0},{'unexpected':1},{'schema_version':3}]:
   answers=[]
   for fn in (old,new):
    try:answers.append(('ok',fn(value|delta)))
    except Exception as e:answers.append(('error',type(e),str(e)))
   self.assertEqual(*answers)
 def test_low_receipt_original_bytes_and_fatal(self):
  # Execute exact low receiver with bounded OS pipes and mocked subprocess.
  # No actual child or transport is created, and no authority object is forged.
  import select,signal,time,subprocess
  ns={'Path':Path,'os':os,'select':select,'signal':signal,'time':time,'subprocess':subprocess,'_positive_finite':lambda x:type(x) in (float,int) and x>0,'STDERR_TAIL_BYTES':16384,'_encode':lambda x:(json.dumps(x,sort_keys=True,indent=2)+'\n').encode()}
  def cleanup(actions):
   for a in actions:a()
  ns['archive']=types.SimpleNamespace(MAX_BYTES=8*1024**2,io=types.SimpleNamespace(_cleanup=cleanup))
  ns['_immutable']=lambda path,record:path.write_bytes(ns['_encode'](record))
  fn=definitions(P/'candidate/archive_transport.py',{'receive_diagnostic'},ns)['receive_diagnostic']
  with tempfile.TemporaryDirectory(dir=P/'tests') as d:
   r,w=os.pipe();os.write(w,b'x');os.close(w);er,ew=os.pipe();os.close(ew)
   proc=types.SimpleNamespace(stdout=os.fdopen(r,'rb'),stderr=os.fdopen(er,'rb'),pid=123,returncode=0,wait=lambda **kwargs:0)
   received=[]
   with patch.object(subprocess,'Popen',return_value=proc),patch.object(os,'killpg',return_value=None):
    fn(['never-run'],Path(d)/'get',expected_bytes=1,max_seconds=2,bytes_per_second=1e9,lease_callback=lambda:None,receipt_sink=lambda path,raw,success:received.append((path,raw,success)))
   path,raw,ok=received[0];self.assertTrue(ok);record=json.loads(raw);self.assertEqual(raw,ns['_encode'](record));self.assertEqual(record['returncode'],0);self.assertEqual((Path(d)/'get').read_bytes(),b'x');self.assertFalse(path.exists())
   fatal=KeyboardInterrupt('original')
   def fail():raise fatal
   def bad_sink(*args):raise ValueError('secondary publication error')
   with self.assertRaises(KeyboardInterrupt) as e:fn(['never-run'],Path(d)/'failed',expected_bytes=0,max_seconds=2,bytes_per_second=1e9,lease_callback=fail,receipt_sink=bad_sink)
   self.assertIs(e.exception,fatal);self.assertIn('receipt publication failed',fatal.__notes__[0])
 def test_changed_boundary_routing(self):
  for name in ('archive_dispatch.py','archive_owner_operations.py','archive_transport.py','controls01.py','build_inputs03.py'):
   compile((P/'candidate'/name).read_bytes(),name,'exec')
  tree=ast.parse((P/'candidate/archive_dispatch.py').read_text());ctx=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Context');methods={n.name:n for n in ctx.body if isinstance(n,ast.FunctionDef)}
  live=ast.unparse(methods['_live']);full=ast.unparse(methods['_full_history'])
  self.assertEqual(live.count('_outer(sampled=True)'),2);self.assertIn('_control_journal.audit()',full);self.assertIn('_diagnostic_journal.audit()',full)
  self.assertIn('force=not sampled',ast.unparse(methods['_outer']))
  call=ast.unparse(methods['_call']);self.assertLess(call.index("self._publish('result-"),call.index('empty.unlink()'))
  ledger=(P/'candidate/archive_owner_operations.py').read_text();self.assertIn('self._evidence(sampled=not full)',ledger);self.assertIn("io._read(fd,'intent.json'",ledger)
if __name__=='__main__':unittest.main(verbosity=2)
