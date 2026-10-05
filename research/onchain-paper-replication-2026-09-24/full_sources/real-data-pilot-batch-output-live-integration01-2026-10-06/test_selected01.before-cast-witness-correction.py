"""Synthetic byte/content controls only, no Run/Owner/transport construction.

Original pure file helpers are AST-extracted to avoid numerical module imports.
Stage authority is deliberately outside this isolated content-reader witness.
"""
import ast,hashlib,importlib,importlib.util,json,os,re,stat,struct,sys,tempfile,types,unittest
from pathlib import Path
D=Path(__file__).resolve().parent;ROOT=D.parents[3];P=Path('tradingagents/research/onchain_replication');C=D/'candidate'/P
PEER=D.parent/'real-data-pilot-typed-score-tail-live-integration01-2026-10-06'
pkg=types.ModuleType('storage_content_probe');pkg.__path__=[str(C),str(PEER),str(ROOT/P)];sys.modules[pkg.__name__]=pkg
io=types.ModuleType(pkg.__name__+'.score_batches');io.__package__=pkg.__name__;io.__dict__.update(os=os,re=re,stat=stat,json=json,hashlib=hashlib,Path=Path)
owned=importlib.import_module(pkg.__name__+'.owned_io');io.__dict__.update({n:getattr(owned,n) for n in ('_cleanup','_release','_close_after_failure')});io.META_LIMIT=8192;io.MAX_CHUNK_BYTES=8*1024**2
names={'_require','_hash','_identity','_scope','_json','_write','_signature','_stamp','_read','_open','_root'}
io.SCOPE_FIELDS={'graph','node_order','dictionary','ordered_motifs','matching','workflow'}
tree=ast.parse((ROOT/P/'score_batches.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'original-pure-score-io','exec'),io.__dict__);sys.modules[io.__name__]=io
stages=types.ModuleType(pkg.__name__+'.compact_stage');stages.__dict__.update(io=io,require=io._require,os=os,re=re,Path=Path)
tree=ast.parse((ROOT/P/'compact_stage.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='inventory'],type_ignores=[]),'original-pure-inventory','exec'),stages.__dict__);sys.modules[stages.__name__]=stages
out=types.ModuleType(pkg.__name__+'.compact_mcm_output');out.__package__=pkg.__name__;out.__dict__.update(io=io,stages=stages,require=io._require,os=os,stat=stat,json=json,hashlib=hashlib,Path=Path,cache_key=importlib.import_module(pkg.__name__+'.cache').cache_key)
tree=ast.parse((C/'compact_mcm_output.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'_manifest','_file'}],type_ignores=[]),'actual-output-pure-methods','exec'),out.__dict__);sys.modules[out.__name__]=out
m=importlib.import_module(pkg.__name__+'.mcm_raw_parts');typed=importlib.import_module(pkg.__name__+'.typed_payload_operations');pol=importlib.import_module(pkg.__name__+'.typed_payload_policy')
class Selected(unittest.TestCase):
 def fixture(self,directory):
  root=Path(directory)/'artifact';root.mkdir();(root/'transport').mkdir();ledger=Path(directory)/'synthetic-history';ledger.mkdir()
  values=[0.,-0.,0.5,1.];raw=b''.join(struct.pack('<f',v) for v in values);(root/'matrix.f32').write_bytes(raw)
  cfg={'schema_version':1,'kind':'mcm-output-f32-archive','input':'synthetic-policy','input_sha256':'a'*64,'part_bytes':8,'closed_check_assumption':m.ASSUMPTION}
  args={'stage_root':Path(directory)/'mcm-synthetic','stage_sha256':'b'*64,'contract':{'owner':'c'*64},'expected_scope':{k:'d'*64 for k in io.SCOPE_FIELDS},'max_output_bytes':8192+16,'storage_policy':cfg};start={'rows':1,'motifs':4};out._source=lambda _:start
  binding=m.output_binding(args,start);intent={'format':'typed-payload-operation-v1','kind':'mcm-output-f32','binding':binding,'reserved_chunks':2,'reserved_payload_bytes':16};ih=pol.sha(pol.raw(intent));iname='typed-'+ih+'.json';(ledger/iname).write_bytes(pol.raw(intent));chain=hashlib.sha256()
  for i in range(2):
   body=raw[8*i:8*i+8];h=pol.sha(body);receipt={'schema_version':1,'format':'archive-chunk-v1','transport_identity':'e'*64,'remote':'synthetic-'+str(i),'member':'synthetic-'+str(i)+'/payload.bin','scope':pol.sha(pol.raw({'operation':ih,'index':i,'bytes':8,'sha256':h})),'source_sha256':h,'bytes':8}
   part={'index':i,'operation_sha256':ih,'fresh_full_recovery':True,'receipt':receipt,'receipt_sha256':pol.sha(pol.raw(receipt))};pr=pol.raw(part);chain.update(bytes.fromhex(pol.sha(pr)));(ledger/('typed-part-'+ih+f'-{i:012d}.json')).write_bytes(pr)
  complete={'operation_sha256':ih,'assumption':pol.ASSUMPTION,'parts':2,'preserved_bytes':16,'parts_sha256':chain.hexdigest()};cr=pol.raw(complete);cname='typed-complete-'+ih+'.json';(ledger/cname).write_bytes(cr)
  history={'directory':str(ledger),'intent':iname,'intent_sha256':ih,'complete':cname,'complete_sha256':pol.sha(cr)}
  proof={'schema_version':1,'format':'mcm-output-recovery-proof-v1','binding':binding,'history':history,'cells':4,'f64_bytes':32,'f64_sha256':pol.sha(b''.join(struct.pack('<d',v) for v in values)),'f32_bytes':16,'f32_sha256':pol.sha(raw),'parts':2,'assumption':m.ASSUMPTION};pr=io._json(proof);(root/'storage.json').write_bytes(pr)
  value=out._manifest(args,start,pol.sha(raw))|{'schema_version':2,'storage_sha256':pol.sha(pr)};vr=io._json(value);(root/'manifest.json').write_bytes(vr)
  return root,pol.sha(vr),args,raw,ledger,ih
 def test_selected_current_bytes_and_missing_or_changed_parts(self):
  with tempfile.TemporaryDirectory(dir=D) as d:
   root,ref,args,raw,ledger,ih=self.fixture(d);value,_=m.inspect_output(root,ref,args);self.assertEqual(value['array_sha256'],pol.sha(raw))
   (root/'matrix.f32').write_bytes(raw[:-1]+bytes([raw[-1]^1]))
   with self.assertRaisesRegex(ValueError,'local f32 bytes'):m.inspect_output(root,ref,args)
   (root/'matrix.f32').write_bytes(raw)
   p=ledger/('typed-part-'+ih+'-000000000001.json');p.unlink()
   with self.assertRaises(FileNotFoundError):m.inspect_output(root,ref,args)
 def test_selected_rejects_partial_matrix_and_foreign_member(self):
  with tempfile.TemporaryDirectory(dir=D) as d:
   root,ref,args,raw,ledger,ih=self.fixture(d);(root/'matrix.f32').write_bytes(raw[:-1])
   with self.assertRaisesRegex(ValueError,'extent'):m.inspect_output(root,ref,args)
   (root/'matrix.f32').write_bytes(raw);(root/'unexpected').write_bytes(b'x')
   with self.assertRaises(ValueError):m.inspect_output(root,ref,args)
 def test_known_large_matrix_finite_limit_and_unchanged_cast_source(self):
  size,count=m.layout('mcm-output-f32',1768268*32,4*1024**2);self.assertEqual(size,226338304);self.assertEqual(count,54)
  old=sys.modules.get('resource');fake=types.SimpleNamespace(RLIMIT_FSIZE=1,getrlimit=lambda _: (4*1024**2,4*1024**2));sys.modules['resource']=fake
  try:
   with self.assertRaisesRegex(ValueError,'finite native'):m._native_limit(size)
   fake.getrlimit=lambda _:(size,size);m._native_limit(size)
   fake.getrlimit=lambda _:(-1,-1)
   with self.assertRaises(ValueError):m._native_limit(size)
  finally:
   if old is None:del sys.modules['resource']
   else:sys.modules['resource']=old
  t=ast.parse((C/'compact_mcm_output.py').read_text());f={n.name:n for n in t.body if isinstance(n,ast.FunctionDef)}
  def cast(node):return ast.dump(next(n for n in ast.walk(node) if isinstance(n,ast.With) and 'np.errstate' in ast.unparse(n)),include_attributes=False)
  self.assertEqual(cast(f['_chunks']),cast(f['_archived_chunks']))
  self.assertFalse({'numpy','torch','scipy','networkx'}&set(sys.modules))
if __name__=='__main__':unittest.main(verbosity=2)
