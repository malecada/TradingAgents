"""Actual orchestration with owned opaque bytes and synthetic capability stand-ins.
No scientific f64 container or remote service is constructed or claimed.
"""
import hashlib,os,pathlib,tempfile,time,types,unittest
from test_transport01 import P,ns,Session
class RoundtripTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=P,prefix='roundtrip-test-');self.root=pathlib.Path(self.tmp.name);self.addCleanup(self.tmp.cleanup)
 def session(self,corrupt=False):
  original={'header.json':b'{"synthetic":true}\n','opaque.bin':b'abcdefghijk'};s=object.__new__(Session);s.root=self.root;s.fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY);s.closed=False;s.recovered=False;s.files={};s.pending_files={};s.directories={};s.deadline=time.monotonic()+10;s.inventory=tuple((n,hashlib.sha256(b).hexdigest(),len(b)) for n,b in sorted(original.items()));s._inventory_pin=ns['encoded']([{'name':n,'sha256':h,'bytes':z} for n,h,z in s.inventory]);s.parts=sum((len(b)+7)//8 for b in original.values());s.p={'part_bytes':8,'remote_namespace':'synthetic','max_files':100,'max_local_bytes':10000};s.output='summary.json';outputs=[];failures=[];steps=[]
  for name in ('parts','recovery','diagnostics'):
   p=self.root/name;p.mkdir();st=p.stat();s.directories[name]=(st.st_dev,st.st_ino)
  c=types.SimpleNamespace(failed=False,_transfer_spent={'commands':0},_transfer_observed={'commands_started':0},publish=lambda n,v:failures.append((n,v)))
  def write_json(name,value):
   self.assertTrue(s.closed);self.assertIsNone(s.fd);outputs.append((name,value))
  c.run=types.SimpleNamespace(write_json=write_json);s.c=c
  ledger=types.SimpleNamespace(identity='a'*64,context=c);op=types.SimpleNamespace(ledger=ledger,index=0,offset=0)
  def reserve(count):
   _,_,size=s.inventory[op.index];self.assertEqual(count,min(8,size-op.offset));op.offset+=count
   if op.offset==size:op.index+=1;op.offset=0
  op.reserve_next=reserve
  def verify(root):
   self.assertEqual(set(p.name for p in root.iterdir()),set(original))
   for name,body in original.items():self.assertEqual((root/name).read_bytes(),body)
   self.assertEqual(op.index,len(original));steps.append('whole-original-members-checked')
  op.verify_local_recovery=verify
  def fail(error):c.failed=True;raise error
  op.fail=fail;s.op=op
  reader=types.SimpleNamespace(reference='b'*64,members={'opaque.bin'},_files={n:(None,hashlib.sha256(v).hexdigest(),len(v)) for n,v in original.items()},_read=lambda n,*a,**kw:(None,original[n]))
  s.source=types.SimpleNamespace(_reader=reader,read_part=lambda n,o,z:original[n][o:o+z]);s.check=lambda:s.check_files();remote={};serial=0
  def command(kind,path,data,count):
   nonlocal serial
   steps.append(kind);serial+=1
   if kind=='upload':remote[path]=data
   raw=remote[path] if kind=='download' else b''
   if corrupt and kind=='download':raw=b'!'+raw[1:]
   dest=self.root/'parts'/str(serial);fd=s.create_owned(dest,max(1,len(raw)))
   try:os.write(fd,raw)
   finally:os.close(fd)
   s.seal_file(dest);return dest
  s._command=command
  return s,outputs,failures,steps
 def test_complete_ordered_roundtrip_preserves_original_members(self):
  s,outputs,failures,steps=self.session();result=s.run();self.assertEqual(steps[:-1],['mkdir','upload','download']*s.parts);self.assertEqual(steps[-1],'whole-original-members-checked');self.assertTrue(result['remote_body_roundtrip_verified']);self.assertEqual(result['local_bytes_retired'],0);self.assertFalse(result['disposition_authority']);self.assertEqual(len(outputs),1)
 def test_corrupt_part_no_final_output_partial_files_retained(self):
  s,outputs,failures,steps=self.session(True)
  with self.assertRaises(ValueError):s.run()
  self.assertEqual(outputs,[]);self.assertTrue(failures);self.assertTrue(list((self.root/'parts').iterdir()));self.assertTrue(list((self.root/'recovery').iterdir()));self.assertTrue(s.closed)
if __name__=='__main__':unittest.main(verbosity=2)
