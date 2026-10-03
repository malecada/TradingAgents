"""Finite actual source controls with explicitly synthetic metadata/owned bytes."""
import ast,hashlib,json,os,pathlib,tempfile,time,types,unittest
from unittest.mock import patch
from test_transport01 import P,ns,durable,io,Session
class ControlTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=P,prefix='control-test-');self.root=pathlib.Path(self.tmp.name);self.addCleanup(self.tmp.cleanup)
 def policy(self):
  c=dict(part_bytes=8,deadline_seconds=20,max_commands=8,max_control_bytes=8192*100,slots=[dict(graph='a'*64,role='score-batches')])
  p=dict(schema_version=1,kind='selected-non-tail-ssh-plaintext-channel-v1',connection=dict(host='fixture.invalid',user='fixture',port=23,identity_file='/not-opened/key',known_hosts_file='/not-opened/known'),remote_namespace='fixture',part_bytes=8,command_seconds=2,cleanup_seconds=1,stderr_bytes=64,max_commands=8,max_parts=4,max_rounded_bytes=2**20,max_channel_bytes=2**20,max_local_bytes=2**20,max_files=100,outputs={'a'*64:'roundtrip.json'})
  return p,c
 def test_policy_strict(self):
  p,c=self.policy();self.assertEqual(ns['policy'](p,c),p)
  for key,value in [('schema_version',True),('physical_wire_bound',100),('part_bytes',9),('max_commands',True),('kind','generic-ssh')]:
   q=dict(p);q[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):ns['policy'](q,c)
 def test_canonical_transport_policy_refuses_duplicates_and_extra_space(self):
  p,c=self.policy();raw=ns['encoded'](p);self.assertEqual(ns['parse_policy'](raw,c),p)
  with self.assertRaises(ValueError):ns['parse_policy'](b' '+raw,c)
  duplicate=raw.replace(b'{',b'{"schema_version":1,',1)
  with self.assertRaises(ValueError):ns['parse_policy'](duplicate,c)
 def test_connection_metadata_only_and_injection_refusal(self):
  p,c=self.policy()
  for field,value in [('host','a;echo'),('port',True),('identity_file','relative'),('known_hosts_file','/a\n')]:
   q={**p,'connection':{**p['connection'],field:value}}
   with self.subTest(field=field),self.assertRaises(ValueError):ns['policy'](q,c)
 def test_fixed_command_counts_and_no_scp_or_legacy(self):
  s=object.__new__(Session);s.p=self.policy()[0];s.op=types.SimpleNamespace(ledger=types.SimpleNamespace(identity='b'*64));remote=s._remote(1,2)
  self.assertIn('b'*64,remote)
  for kind in ('mkdir','upload','download'):
   argv,control=s._argv(kind,remote,32768);self.assertEqual(argv[0],'ssh');self.assertGreater(control,0);self.assertIn('StrictHostKeyChecking=yes',argv)
  self.assertIn('count=2',s._argv('download',remote,32768)[0])
  with self.assertRaises(ValueError):s._argv('mkdir','unsafe/../../a',0)
 def test_no_refund_reservation(self):
  s=object.__new__(Session);s.p=self.policy()[0];s.p['max_commands']=1;s.check=lambda:None;s.deadline=time.monotonic()+10;s.op=types.SimpleNamespace(ledger=types.SimpleNamespace(identity='a'*64));records={}
  c=types.SimpleNamespace(_transfer_active=None,_transfer_spent=dict(commands=0,parts=0,rounded_bytes=0,channel_bound=0),publish=lambda k,v:records.update({k:v}));s.c=c
  s._reserve('mkdir',10,0,0);self.assertEqual(c._transfer_spent['commands'],1)
  with self.assertRaises(ValueError):s._reserve('mkdir',10,0,0)
  c._transfer_active=None
  with self.assertRaises(ValueError):s._reserve('mkdir',10,0,0)
  self.assertEqual(len(records),1);self.assertIsNone(next(iter(records.values()))['physical_wire_bound'])
 def tree_session(self):
  s=object.__new__(Session);s.root=self.root;s.fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY);self.addCleanup(os.close,s.fd);s.p=self.policy()[0];s.deadline=time.monotonic()+10;s.files={};s.pending_files={};s.directories={};s.check=lambda:s.check_files()
  for name in ('parts','recovery','diagnostics'):
   p=self.root/name;p.mkdir();st=p.stat();s.directories[name]=(st.st_dev,st.st_ino)
  return s
 def test_owned_members_extra_mutation_and_caps(self):
  s=self.tree_session();p=self.root/'parts'/'one';fd=s.create_owned(p,4)
  try:ns['_write_all'](fd,b'abcd')
  finally:os.close(fd)
  s.seal_file(p);s.check_files();self.assertEqual(s.local_bytes,4)
  p.write_bytes(b'abce')
  with self.assertRaises(ValueError):s.check_files()
 def test_extra_file_refusal(self):
  s=self.tree_session();(self.root/'parts'/'rogue').write_bytes(b'a')
  with self.assertRaises(ValueError):s.check_files()
 def test_directory_redirect_refusal(self):
  s=self.tree_session();(self.root/'parts').rename(self.root/'old');(self.root/'parts').symlink_to('old')
  with self.assertRaises(ValueError):s.check_files()
 def test_file_hardlink_and_bound_refusal(self):
  s=self.tree_session();p=self.root/'parts'/'one';fd=s.create_owned(p,2)
  try:os.write(fd,b'abc')
  finally:os.close(fd)
  with self.assertRaises(ValueError):s.check_files()
 def test_registration_schema_default_and_selected(self):
  t=ast.parse((P/'archive_non_tail.py').read_text());f=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='validate_policy');g={**ns,**durable.__dict__,'encode':durable.encode,'META':8192};exec(compile(ast.Module([f],[]),'actual-policy','exec'),g)
  p=dict(schema_version=1,kind='non-tail-durable-population-v1',category='non-tail-original-members',namespace='test',deadline_seconds=20,max_rounded_bytes=2**20,max_commands=8,max_parts=8,max_control_bytes=8192*100,part_bytes=8,receipt_output='receipt.json',terminal_output='terminal.json',slots=[dict(graph='a'*64,role='score-batches',max_bytes=100,max_members=10)])
  self.assertEqual(g['validate_policy'](p),p)
  selected={**p,'schema_version':2,'kind':'non-tail-durable-selected-population-v2','transport_input':'selected_transport'};self.assertEqual(g['validate_policy'](selected),selected)
  for altered in ({**selected,'transport_input':False},{**selected,'unsafe':True},{**selected,'schema_version':True}):
   with self.assertRaises(ValueError):g['validate_policy'](altered)
 def context_standin(self):
  C=type('SyntheticContext',(),{});durable.Context=C;c=C();c.root=self.root;c.fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY);st=os.fstat(c.fd);c.inode=(st.st_dev,st.st_ino);c.policy={'schema_version':2,'terminal_output':'terminal.json'};c.check=lambda:None;c.active=None;c._transfer_active=None;c._transfer_spent={'commands':1,'parts':1,'rounded_bytes':32768,'channel_bound':4};c._transfer_observed={'commands_started':0,'stdin_bytes':0,'stdout_bytes':0,'stderr_bytes':0,'command_argument_bytes_started':0};c.failed=False;c.closed=False;c.operations={};c.publish=lambda name,value:None;c.outputs=[]
  def output(name,value):
   with self.assertRaises(OSError):os.fstat(c.fd)
   c.outputs.append((name,value))
  c.run=types.SimpleNamespace(write_json=output);return c
 def test_context_terminal_only_after_successful_close(self):
  c=self.context_standin();result=ns['close_context'](c);self.assertTrue(c.closed);self.assertEqual(len(c.outputs),1);self.assertFalse(result['physical_encrypted_wire_metered'])
 def test_late_close_failure_additive_and_no_success_output(self):
  c=self.context_standin();realclose=os.close;first=True
  def bad_close(fd):
   nonlocal first
   realclose(fd)
   if first:first=False;raise OSError('owned close uncertain')
  with patch.object(ns['os'],'close',side_effect=bad_close),self.assertRaises(io.CleanupFailure):ns['close_context'](c)
  self.assertTrue(c.closed and c.failed);self.assertEqual(c.outputs,[]);marker=json.loads((self.root/'selected-close-failed.json').read_text());self.assertEqual(marker['status'],'failed')
 def test_prior_fatal_retained_across_close_and_late_receipt(self):
  c=self.context_standin();fatal=MemoryError('original');realclose=os.close
  def bad_close(fd):realclose(fd);raise OSError('close uncertain')
  with patch.object(ns['os'],'close',side_effect=bad_close),self.assertRaises(MemoryError) as got:ns['close_context'](c,fatal)
  self.assertIs(got.exception,fatal);self.assertEqual(c.outputs,[]);self.assertTrue(c.closed and c.failed)
 def test_full_inverse_legacy_bytes_ast(self):
  current=(P/'archive_non_tail.py').read_text();original=(P/'archive_non_tail.baseline03.txt').read_text();t=ast.parse(current);rem=[]
  def visit(nodes,parent=''):
   for n in nodes:
    if isinstance(n,ast.FunctionDef) and n.name=='validate_policy':rem.append((n.body[0].lineno,n.body[0].end_lineno))
    if isinstance(n,ast.ClassDef):visit(n.body,n.name)
    if isinstance(n,ast.FunctionDef) and (parent,n.name) in [('Context','__init__'),('Context','check'),('Context','close'),('Operation','dispatch')]:
     rem.extend((x.lineno,x.end_lineno) for x in n.body if isinstance(x,ast.If) and 'schema_version' in ast.unparse(x.test) and '== 2' in ast.unparse(x.test))
  visit(t.body);lines=current.splitlines(keepends=True)
  for start,end in sorted(rem,reverse=True):del lines[start-1:end]
  self.assertEqual(len(rem),5);self.assertEqual(''.join(lines),original);self.assertEqual(ast.dump(ast.parse(''.join(lines))),ast.dump(ast.parse(original)))
if __name__=='__main__':unittest.main(verbosity=2)
