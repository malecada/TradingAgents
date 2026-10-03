"""Independent source/tiny opaque-byte checks; no actual CAP/Git/network invocation."""
import ast,gzip,hashlib,importlib.util,io,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
P=BASE/'neural-cold-feature-handoff-comparison-capsule-retention-preparation01-2026-10-03'
sys.path.insert(0,str(P));import retention01 as m
class Checks(unittest.TestCase):
 def test_actual_draft_interface_metadata_only(self):
  D=BASE/'neural-cold-feature-handoff-root-compare-request02-2026-10-03'
  draft=json.loads((D/'DRAFT_EXECUTION02.json').read_bytes());env=json.loads((D/'CANDIDATE_RELEASE_ENVELOPE02.json').read_bytes());roles={}
  for row in draft['exact_four_additions']:
   raw=(D/'draft-bodies02'/row['role']).read_bytes();self.assertEqual(len(raw),row['bytes']);self.assertEqual(m.digest(raw),row['sha256']);roles[row['role']]=row
  self.assertEqual(set(roles),{'registration','charter','phase_contract','evolution'});self.assertEqual(draft['source_at_generation'],m.A)
  reg=json.loads((D/'draft-bodies02/registration').read_bytes());first=reg['experiments'][m.FIRST];second=reg['experiments'][m.SECOND]
  self.assertEqual(second['parent'],m.FIRST);self.assertEqual(len(second['inputs']),44);self.assertEqual(len(first['inputs']),9);self.assertEqual(second['source_files'],first['source_files']);self.assertEqual(len(first['source_files']),195)
  self.assertEqual(sum(n.startswith('tradingagents/') for n in first['source_files']),147)
  family=reg['families'][first['family']];self.assertEqual((family['attempt_budget'],family['prior_attempts']),(2,0));self.assertEqual(env['source'],'361339125a3f1cd57e7ba8611f5a994ae649fa0b');self.assertEqual(env['registration']['sha256'],roles['registration']['sha256']);self.assertEqual(env['phase_contract']['sha256'],roles['phase_contract']['sha256'])
 def test_multiple_git_blob_order_and_extent(self):
  a=b'one';b=b'\x00two\xff';raw=b'a'*40+b' blob 3\n'+a+b'\n'+b'b'*40+b' blob 5\n'+b+b'\n'
  self.assertEqual(m.blobs(lambda *_a,**_k:raw,Path('/synthetic-not-opened'),'c'*40,['one','two']),{'one':a,'two':b})
  with self.assertRaises(ValueError):m.blobs(lambda *_a,**_k:raw+b'\n',Path('/synthetic-not-opened'),'c'*40,['one','two'])
 def test_concatenated_gzip_and_changed_mode_refuse(self):
  for change in ('gzip','mode'):
   with self.subTest(change=change),tempfile.TemporaryDirectory(dir=HERE/'tmp') as d:
    root=Path(d);source=root/'original';source.mkdir();(source/'opaque').write_bytes(b'tiny\x00opaque');rows=m.archive.snapshot(source,root/'copy',limit=65536);full=[{'path':'.','kind':'directory','mode':source.stat().st_mode&0o777,'bytes':0}]+rows;m.pack(source,root/'archive.gz',full)
    if change=='gzip':
     with (root/'archive.gz').open('ab') as f:f.write(gzip.compress(b'',mtime=0))
    else:full[0]['mode']^=0o010
    with self.assertRaises(ValueError):m.unpack(root/'archive.gz',root/'restored',full)
 def test_protected_reference_refuses_before_open(self):
  for component in ('keys','apis','.env','.env.local','hf_token.txt'):
   with self.subTest(component=component),patch.object(m.owned,'_opened',side_effect=AssertionError('must refuse before opening')):
    with self.assertRaises(ValueError):m.referenced({'path':'/synthetic/'+component+'/unused','sha256':'0'*64})
 def test_source_only_import_closure_and_bound_contract(self):
  allowed={'argparse','gzip','hashlib','io','json','os','resource','signal','stat','subprocess','tarfile','time','pathlib','archive01','owned_io','sys','contextlib'}
  for name in ('retention01.py','archive01.py','owned_io.py'):
   tree=ast.parse((P/name).read_text());imports=set()
   for n in ast.walk(tree):
    if isinstance(n,ast.Import):imports.update(x.name.split('.')[0] for x in n.names)
    elif isinstance(n,ast.ImportFrom):imports.add(n.module.split('.')[0])
   self.assertLessEqual(imports,allowed)
  self.assertEqual(m.MAX,4194304);self.assertEqual(m.GIB,1073741824)
  source=(P/'retention01.py').read_text();self.assertIn('child.wait(timeout=60)',source);self.assertIn('child.wait(timeout=5)',source);self.assertNotIn('extractall(',source)
if __name__=='__main__':unittest.main(verbosity=2)
