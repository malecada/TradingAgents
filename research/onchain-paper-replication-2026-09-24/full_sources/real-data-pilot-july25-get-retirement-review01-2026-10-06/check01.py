"""Independent bounded review: exact source, invented metadata and tiny local bodies only."""
from pathlib import Path
import ast,copy,hashlib,json,os,tempfile,types,unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;C=HERE.with_name('real-data-pilot-july25-get-retirement-preparation01-2026-10-06');ROOT=HERE.parents[3]
def load(p):
 m=types.ModuleType('review_fixture');m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),vars(m));return m
fixture=load(C/'check01.py');r=fixture.r;m=fixture.m
WITNESSES={}
class Review(unittest.TestCase):
 def test_exact_pins_inverse_and_null_refusal(self):
  manifest=json.loads((C/'MANIFEST01.json').read_text())
  for p,d in manifest['files'].items():self.assertEqual(hashlib.sha256((C/p).read_bytes()).hexdigest(),d['sha256'])
  self.assertEqual(hashlib.sha256((C/'SOURCE_PINS01.json').read_bytes()).hexdigest(),r.PINS_SHA)
  delta=json.loads((C/'SOURCE_DELTA01.json').read_text());new=(C/'recovery01.py').read_text();old=(ROOT/delta['recovery_parent']).read_text();inverse=new.replace(delta['sole_replacement']['after'],delta['sole_replacement']['before']);self.assertEqual(inverse,old);self.assertEqual(ast.dump(ast.parse(inverse)),ast.dump(ast.parse(old)))
  with patch.object(m,'recovery',side_effect=AssertionError('unknown draft passed')),self.assertRaises(ValueError):r.validate(m,json.loads((C/'SELECTION_TEMPLATE01.json').read_text()))
 def test_exact_boundary_omission_witnesses(self):
  c,docs=fixture.Check().gate_fixture()
  def invoke(d):
   with patch.object(m,'recovery'),patch.object(m,'current'),patch.object(m,'metadata',side_effect=lambda root,p,pin:json.dumps(d[p]).encode()),patch.object(r,'retained'),patch.object(r.os.path,'lexists',return_value=False),patch.object(Path,'exists',return_value=False):return r.validate(m,c)
  invoke(docs)
  for name,role,key,value in [('ordinary_retire_fabricated_native_cleanup','retire_outer','cleanup_verified',True),('wrong_relocation_identity','relocation_receipt','identity','unrelated-maintenance')]:
   changed=copy.deepcopy(docs);changed[c['relocation'][role]['path']][key]=value
   invoke(changed);WITNESSES[name]={'candidate_accepts':True,'expected':'refusal','field':role+'.'+key,'invented_value':value}
  for role,key,value in [('retire_outer','guard_child_exit_code',0),('retire_root','actual_root_tool_exit_code',1),('copy_native','cleanup_verified',False),('retire_receipt','original_retired',None)]:
   changed=copy.deepcopy(docs);changed[c['relocation'][role]['path']][key]=value
   with self.assertRaises(ValueError):invoke(changed)
 def test_fatal_sync_with_close_errors_exact_get_only(self):
  for kind in (KeyboardInterrupt,SystemExit,MemoryError):
   with self.subTest(kind=kind.__name__),tempfile.TemporaryDirectory(dir=HERE) as directory:
    base=Path(directory);target=base/'data/events.sqlite';target.parent.mkdir();target.write_bytes(b'kept');get=base/'get.bin';get.write_bytes(b'copy');out=base/'out';out.mkdir()
    row={'recovered':{'path':'get.bin','stat_identity':m.identity(get.stat())}};target_record={'stat_identity':r.sig(target.stat())};receipts={};primary=kind('injected fatal sync');closed=[];realclose=os.close
    def close(fd):realclose(fd);closed.append(fd);raise OSError('injected late close')
    def sync(p):raise primary
    mm=types.SimpleNamespace(ORIGINAL='absent-original',identity=m.identity,current=lambda root,row:get)
    cold=types.SimpleNamespace(publish=lambda p,v:receipts.update({p.name:v}),sync_directory=sync)
    with patch.object(r,'ROOT',base),patch.object(r,'HERE',out),patch.object(r,'TARGET',target),patch.object(r,'inactive'),patch.object(r,'retained'),patch.object(r.os,'close',side_effect=close):
     with self.assertRaises(kind) as caught:r.retire(mm,cold,row,target_record,{'selection_sha256':'a'*64})
    self.assertIs(caught.exception,primary);self.assertEqual(len(closed),2)
    for fd in closed:
     with self.assertRaises(OSError):os.fstat(fd)
    self.assertEqual(target.read_bytes(),b'kept');self.assertFalse(get.exists());record=receipts['failed01.json'];self.assertEqual(record['removed'],['get.bin']);self.assertEqual(record['ambiguous_attempts'],[]);self.assertIs(record['get_retired'],True);self.assertEqual(record['stage'],'sync-get-parent');self.assertEqual(record['error_type'],kind.__name__)
if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(Review);result=unittest.TextTestRunner(verbosity=2).run(suite)
 (HERE/'CHECK01.json').write_text(json.dumps({'tests_passed':result.wasSuccessful(),'groups':3,'fatal_primary_cases':3,'witnesses':WITNESSES,'qualification':'Source review checks; RED acceptance witnesses are findings, not release.'},indent=2)+'\n')
 raise SystemExit(0 if result.wasSuccessful() else 1)
