"""Actual terminal parser coherent-resealing regressions; stdlib fixtures only."""
import importlib.util,hashlib,json,os,struct,sys,tempfile,unittest
from pathlib import Path
D=Path(__file__).resolve().parent;S=Path(os.environ.get('FIXTURE_DIR',D.parent/'original-import-native-refusal-candidate03-2026-10-03'));sys.path.insert(0,str(S))
sys.path.append(str(D.parent/'original-import-fixture-native-preparation03-2026-10-03'))
if os.environ.get('PARSER_DIR'):
 for name in ('refusal_evidence','refusal_stage'):
  sp=importlib.util.spec_from_file_location(name,Path(os.environ['PARSER_DIR'])/(name+'.py'));mod=importlib.util.module_from_spec(sp);sys.modules[name]=mod;sp.loader.exec_module(mod)
from evidence_fixture03 import fixture,caller
from stage_fixture03 import populate
FRAME=struct.Struct('<QB7xQdQ32s32s32s')
def reseal(stage,write,change):
 path=stage/'matching/events-000000000000.bin';original=path.read_bytes();head=hashlib.sha256((stage/'matching/start.json').read_bytes()).digest();payload=b''
 for offset in range(0,len(original),168):
  v=list(FRAME.unpack(original[offset:offset+136]))
  if change in ('purpose','both'):v[5]=b'\x98'*32
  if change in ('pair','both'):v[6]=b'\x76'*32
  if change=='swapped':v[5],v[6]=v[6],v[5]
  frame=FRAME.pack(*v);head=hashlib.sha256(head+frame).digest();payload+=frame+head
 write(path,payload);terminal=stage/'matching/terminal.json';v=json.loads(terminal.read_bytes());v['head']=head.hex();v['payload_sha256']=hashlib.sha256(payload).hexdigest();write(terminal,v)
class Resealed(unittest.TestCase):
 def test_resealed_purpose_and_ordered_pair_refuse(self):
  for change in ('purpose','pair','both','swapped'):
   with self.subTest(change=change),tempfile.TemporaryDirectory() as temp:
    root=Path(temp);j,w=fixture(root,'wrong-ack');stage=populate(root,j,'wrong-ack',w);self.assertTrue(caller.terminal(root=root,variant='wrong-ack')['observed']);reseal(stage,w,change)
    with self.assertRaises(ValueError):caller.terminal(root=root,variant='wrong-ack')
 def test_coherent_other_center_or_motif_refuses(self):
  from refusal_pair_identity import expected_pairs
  for index in (1,32):
   with self.subTest(expected_other_index=index),tempfile.TemporaryDirectory() as temp:
    root=Path(temp);j,w=fixture(root,'wrong-ack');stage=populate(root,j,'wrong-ack',w);read=lambda p:json.loads(p.read_bytes());claim=read(root/'research_runs'/j.name/'claim.json');job=read(root/claim['inputs']['execution_job']['path']);selection=next(iter(job['payload']['representation_jobs'].values()));receipt=read(j/'compact/dictionary-import/import-complete.json');owner=read(j/'compact/owner.json');producer=read(next((root/'research_artifacts/onchain_compact_mcm').glob('*/*/*/start.json')));manifest_path=claim['inputs']['target0']['path'];dictionary=read(root/claim['inputs']['dictionary']['path'])
    values=expected_pairs(root,manifest_path,read(root/manifest_path),claim['inputs'],numeric=receipt['numeric'],dictionary_config=dictionary['config'],matching=selection['descriptor']['configs']['matching'],context=owner['context'],backend=receipt['execution']['backend'],workload=producer['scope']['workflow'],source_files=claim['experiment']['source_files'])
    path=stage/'matching/events-000000000000.bin';original=path.read_bytes();head=hashlib.sha256((stage/'matching/start.json').read_bytes()).digest();payload=b''
    for offset in range(0,len(original),168):
     event=list(FRAME.unpack(original[offset:offset+136]));event[5]=bytes.fromhex(values[index][0]);event[6]=bytes.fromhex(values[index][1]);frame=FRAME.pack(*event);head=hashlib.sha256(head+frame).digest();payload+=frame+head
    w(path,payload);terminal=stage/'matching/terminal.json';v=read(terminal);v['head']=head.hex();v['payload_sha256']=hashlib.sha256(payload).hexdigest();w(terminal,v)
    with self.assertRaises(ValueError):caller.terminal(root=root,variant='wrong-ack')
if __name__=='__main__':unittest.main()
