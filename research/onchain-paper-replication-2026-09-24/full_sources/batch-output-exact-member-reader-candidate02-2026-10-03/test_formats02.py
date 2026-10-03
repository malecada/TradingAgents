import ast,hashlib,json,os,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import exact_members02 as m
ROOT=Path(__file__).resolve().parents[4]
P=ROOT/'tradingagents/research/onchain_replication'
def h(b):return hashlib.sha256(b).hexdigest()
def encode(v):
 tree=ast.parse((P/'score_batches.py').read_bytes());f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_json')
 ns={'json':json,'META_LIMIT':8192,'_require':m.require};exec(compile(ast.Module(body=[f],type_ignores=[]),'actual-score-json','exec'),ns);return ns['_json'](v)
def save(root,name,v):
 b=encode(v);(root/name).write_bytes(b);return h(b)
def batches(root,*,bad=False):
 start={'schema_version':1,'scope':{k:'12'*32 for k in m.SCOPES},'owner':'ab'*32,'rows':1,'motifs':32,'chunk_cells':32,'dtype':'<f8','order':'row-major'}
 initial=save(root,'start.json',start);payload=b'\x00'*256;(root/'chunk-000000000000.bin').write_bytes(payload)
 header={'schema_version':1,'start_sha256':initial,'previous':initial,'index':0,'start_cell':1 if bad else 0,'cells':32,'payload_sha256':h(payload)}
 head=save(root,'chunk-000000000000.json',header)
 return save(root,'terminal.json',{'schema_version':1,'start_sha256':initial,'head':head,'status':'complete','cells':32,'chunks':1,'reason':'','pending':[]})
def npy(dtype,shape):
 header=(repr({'descr':dtype,'fortran_order':False,'shape':shape})+'\n').encode('latin1')
 count=1
 for x in shape:count*=x
 return b'\x93NUMPY\x01\x00'+struct.pack('<H',len(header))+header+b'\0'*(count*(4 if dtype=='<f4' else 8))
def graph(root,*,wrong_header=False):
 arrays={}
 for name,dtype,shape in [('array-000000.npy','float32',(1,32)),('array-000001.npy','int64',(2,1))]:
  descriptor='<f4' if dtype=='float32' else '<i8';body=npy('<i8' if wrong_header and dtype=='float32' else descriptor,shape)
  (root/name).write_bytes(body);arrays[name]={'sha256':h(body),'bytes':len(body),'shape':list(shape),'dtype':dtype}
 def sc(v):return {'kind':'scalar','value':v}
 tree={'kind':'dict','items':[[sc('feature'),{'kind':'dict','items':[[sc('mcm'),{'kind':'array','member':'array-000000.npy'}],[sc('edge_index'),{'kind':'array','member':'array-000001.npy'}]]}],[sc('aligned_vectors'),sc(None)]]}
 value={'schema_version':1,'context':{'qualification':'synthetic byte fixture, no Owner'},'tree':tree,'arrays':arrays}
 b=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode();(root/'manifest.json').write_bytes(b);return h(b)
class Tests(unittest.TestCase):
 def test_actual_score_encoder_and_terminal(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);sha=batches(root)
   with m.open_local(root,kind='score-batches',document_sha256=sha) as r:self.assertEqual(r.read_part(r.members[0],0,256),b'\0'*256)
 def test_resealed_wrong_header_refuses(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);sha=batches(root,bad=True)
   with self.assertRaises(ValueError):
    with m.open_local(root,kind='score-batches',document_sha256=sha):pass
 def test_npy_header_and_full_members(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);sha=graph(root)
   with m.open_local(root,kind='graph-artifact',document_sha256=sha) as r:
    self.assertEqual(set(r.members),{'array-000000.npy','array-000001.npy'})
    with self.assertRaises(AttributeError):r.reference='ab'*32
    with self.assertRaises(ValueError):r.read_part('.',0,1)
 def test_header_disagrees_with_hash_valid_manifest(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);sha=graph(root,wrong_header=True)
   with self.assertRaisesRegex(ValueError,'NPY shape/dtype'):
    with m.open_local(root,kind='graph-artifact',document_sha256=sha):pass
 def test_first_fatal_during_read_and_both_fds_close_once(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);sha=batches(root);fatal=SystemExit('first');real=m.os.close;closed=[]
   def close(fd):closed.append(fd);real(fd);raise OSError('uncertain')
   with patch.object(m.os,'read',side_effect=fatal),patch.object(m.os,'close',side_effect=close):
    with self.assertRaises(SystemExit) as got:
     with m.open_local(root,kind='score-batches',document_sha256=sha):pass
   self.assertIs(got.exception,fatal);self.assertEqual(len(closed),2);self.assertEqual(len(set(closed)),2)
 def test_original_parent_replacement(self):
  with tempfile.TemporaryDirectory() as d:
   base=Path(d);root=base/'original';root.mkdir();sha=batches(root)
   with self.assertRaises(ValueError):
    with m.open_local(root,kind='score-batches',document_sha256=sha) as r:
     root.rename(base/'old');root.mkdir();batches(root);r.read_part(r.members[0],0,8)
if __name__=='__main__':unittest.main(verbosity=2)
