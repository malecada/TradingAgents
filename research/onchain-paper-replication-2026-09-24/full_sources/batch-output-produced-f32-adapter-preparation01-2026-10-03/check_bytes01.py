"""Tiny opaque owned-byte content checks, not numerical/Produced authority."""
import ast,hashlib,importlib.util,json,sys,unittest
from pathlib import Path
P=Path(__file__).parent
EXTERNAL=P.parent/'neural-cold-feature-handoff-held-score-reader-preparation01-2026-10-03'
for name in ('owned_io','exact_members02'):
 path=EXTERNAL/(name+'.py');tree=ast.parse(path.read_text())
 assert not any(isinstance(n,ast.Import) and any(x.name.split('.')[0] in {'numpy','torch','pandas','pyarrow'} for x in n.names) for n in ast.walk(tree))
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m)
content=sys.modules['exact_members02']
def sha(b):return hashlib.sha256(b).hexdigest()
class Checks(unittest.TestCase):
 def make(self,name,change=None):
  root=P/'tiny-byte-fixtures02'/name;root.mkdir(parents=True,exist_ok=False)
  payload=b'\x00'*128
  manifest=dict(schema_version=1,kind='compact-mcm-output',stage_sha256='1'*64,contract_sha256='2'*64,stage_directory='/synthetic/unclaimed/stage',scope={k:'3'*64 for k in ('graph','node_order','dictionary','ordered_motifs','matching','workflow')},owner='4'*64,rows=1,motifs=32,dtype='<f4',order='row-major',array_bytes=128,array_sha256=sha(payload),execution_admitted=False)
  raw=(json.dumps(manifest,sort_keys=True,separators=(',',':'))+'\n').encode();(root/'manifest.json').write_bytes(raw)
  if change!='missing':(root/'matrix.f32').write_bytes((b'\x01'+payload[1:]) if change=='corrupt' else payload)
  if change=='extra':(root/'unexpected').write_bytes(b'never-admitted')
  return root,sha(raw),payload
 def test_whole_raw_read(self):
  root,pin,payload=self.make('complete')
  with content.open_local(root,kind='mcm-output',document_sha256=pin) as reader:
   self.assertEqual({n for n,_ in reader._pin},{'manifest.json','matrix.f32'});self.assertEqual(reader.read_part('matrix.f32',0,128),payload);reader.check()
 def test_corrupt(self):
  root,pin,_=self.make('corrupt','corrupt')
  with self.assertRaises(BaseException):
   with content.open_local(root,kind='mcm-output',document_sha256=pin):pass
 def test_missing(self):
  root,pin,_=self.make('missing','missing')
  with self.assertRaises(BaseException):
   with content.open_local(root,kind='mcm-output',document_sha256=pin):pass
 def test_extra(self):
  root,pin,_=self.make('extra','extra')
  with self.assertRaises(BaseException):
   with content.open_local(root,kind='mcm-output',document_sha256=pin):pass
if __name__=='__main__':unittest.main()
