"""Synthetic receipt/opaque-byte tests only; no authority or original arrays."""
import copy,hashlib,importlib.util,json,os,unittest
from pathlib import Path
P=Path(__file__).parent
spec=importlib.util.spec_from_file_location('held_outcome_under_test',P/'held_outcome01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class FakeReader:
 def __init__(self,files):self.files=files
 def body(self,name,limit=m.MAX):
  value=self.files[name];m.require(len(value)<=limit,'bound');return value
 def exact_members(self,path,names):m.require({p[len(path)+1:] for p in self.files if p.startswith(path+'/')}==set(names),'exact members')
def fixture(nodes):
 scope={k:'a'*64 for k in ('graph','node_order','dictionary','ordered_motifs','matching','workflow')};owner='b'*64;p='compact/mcm-'+scope['graph'];files={}
 def put(path,value):raw=m.canonical(value)+b'\n';files[path]=raw;return m.sha(raw)
 cells=nodes*32;count=(cells+63)//64
 batch=p+'/stream/batches';batchhead=start=put(batch+'/start.json',dict(schema_version=1,scope=scope,owner=owner,rows=nodes,motifs=32,chunk_cells=64,dtype='<f8',order='row-major'))
 streamhead=streamstart=put(p+'/stream/start.json',dict(schema_version=1,kind='mcm-score-stream',scope=scope,owner=owner,rows=nodes,motifs=32,chunk_cells=64,batch_start_sha256=start))
 h=hashlib.sha256()
 for i in range(count):
  n=min(64,cells-i*64);raw=bytes([i+1])*(n*8);stem='chunk-%012d'%i;files[batch+'/'+stem+'.bin']=raw;h.update(raw)
  batchhead=put(batch+'/'+stem+'.json',dict(schema_version=1,start_sha256=start,previous=batchhead,index=i,start_cell=i*64,cells=n,payload_sha256=m.sha(raw)))
  tail=put(p+'/stream/tails/tail-%012d/terminal.json'%i,{'synthetic_fixture_only':True})
  streamhead=put(p+'/stream/seal-%012d.json'%i,dict(schema_version=1,start_sha256=streamstart,previous=streamhead,index=i,start_cell=i*64,cells=n,tail_terminal_sha256=tail,batch_header_sha256=batchhead))
 end=put(batch+'/terminal.json',dict(schema_version=1,start_sha256=start,head=batchhead,status='complete',cells=cells,chunks=count,reason='',pending=[]))
 put(p+'/stream/complete.json',dict(schema_version=1,start_sha256=streamstart,head=streamhead,cells=cells,chunks=count,batch_terminal_sha256=end))
 policy=dict(part_bytes=1048576,max_read_bytes=768,max_members=32767);policyraw=m.canonical(policy)
 output=dict(schema_version=1,kind='original-import-held-score-readback-v1',status='local-byte-readback',target=scope['graph'],owner=owner,stage='mcm-'+scope['graph'],policy_input='held_score_policy',policy_sha256=m.sha(policyraw),readback=dict(members=count,parts=count,bytes=cells*8,sha256=h.hexdigest()),scientific_publication=False,transport_authority=False,local_bytes_retired=0)
 return files,p,scope,owner,policy,policyraw,output
class Checks(unittest.TestCase):
 def check(self,f):
  files,p,scope,owner,policy,raw,out=f
  return m.held_target(FakeReader(files),p,scope,owner,len(files[next(n for n in files if n.endswith('/chunk-000000000000.bin'))])//256 if False else self.nodes,'held_score_policy',raw,policy,m.canonical(out))
 def test_fixed512_768_positive(self):
  for self.nodes in (2,3):
   result=self.check(fixture(self.nodes));self.assertEqual(result['readback']['bytes'],512 if self.nodes==2 else 768);self.assertEqual(result['readback']['members'],1 if self.nodes==2 else 2)
 def test_semantic_mutations(self):
  self.nodes=3
  for key,value in [('owner','c'*64),('target','d'*64),('stage','mcm-other'),('policy_sha256','0'*64),('scientific_publication',True),('transport_authority',True),('local_bytes_retired',1),('schema_version',True),('status','complete')]:
   f=fixture(3);f[-1][key]=value
   with self.assertRaises(ValueError,msg=key):self.check(f)
  for key,value in [('members',1),('parts',1),('bytes',512),('sha256','0'*64)]:
   f=fixture(3);f[-1]['readback'][key]=value
   with self.assertRaises(ValueError,msg=key):self.check(f)
 def test_missing_mutated_order_and_extra(self):
  self.nodes=3
  for mode in ('missing','payload','header','extra','stream'):
   f=fixture(3);files=f[0];path=f[1]+'/stream/batches/chunk-000000000001.bin'
   if mode=='missing':del files[path]
   elif mode=='payload':files[path]=b'X'*256
   elif mode=='header':
    key=path[:-4]+'.json';d=m.parse(files[key]);d['index']=0;files[key]=m.canonical(d)
   elif mode=='extra':files[f[1]+'/stream/batches/unexpected']=b'X'
   else:files[f[1]+'/stream/complete.json']=b'{}'
   with self.assertRaises((ValueError,KeyError)):self.check(f)
 def test_unreleased_and_absent_original_held_output(self):
  template=P.parent/'held-consumer-native-release-prerequisite-investigation01-2026-10-03/RELEASE_TEMPLATE01.json';raw=template.read_bytes();root=m.parse(raw)['capsule_root']
  with self.assertRaisesRegex(ValueError,'unreleased'):m.authenticate(root,template.resolve(),m.sha(raw))
  with self.assertRaises(FileNotFoundError):m.Reader(root).body('research_runs/'+m.IDENTITY+'/outputs/held-target-01.json')
 def test_fd_reader_symlink_hardlink_and_growth(self):
  root=P/'owned-io-fixtures';root.mkdir();(root/'good').write_bytes(b'bytes')
  self.assertEqual(m.Reader(root.resolve()).body('good',5),b'bytes')
  (root/'link').symlink_to('good')
  with self.assertRaises((ValueError,OSError)):m.Reader(root.resolve()).body('link')
  os.link(root/'good',root/'hard')
  with self.assertRaises(ValueError):m.Reader(root.resolve()).body('good')
  with self.assertRaises(ValueError):m.Reader(root.resolve()).body('keys/never-opened')
 def test_cleanup_firstfatal(self):
  first=MemoryError('first');calls=[]
  def close():calls.append(1);raise OSError('later')
  with self.assertRaises(MemoryError) as found:m.cleanup([close,close],first)
  self.assertIs(found.exception,first);self.assertEqual(calls,[1,1])
if __name__=='__main__':unittest.main()
