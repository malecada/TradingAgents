"""Independent stdlib retained-format counterexample; no genuine authority."""
import hashlib,json,os,struct,sys,tempfile
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));os.environ['REFUSAL_PARSER_DIR']=str(P)
from evidence_fixture03 import fixture,caller
from stage_fixture03 import populate
FRAME=struct.Struct('<QB7xQdQ32s32s32s')
with tempfile.TemporaryDirectory(prefix='refusal03-review-') as temp:
 root=Path(temp);journal,write=fixture(root,'wrong-ack');stage=populate(root,journal,'wrong-ack',write)
 assert caller.terminal(root=root,variant='wrong-ack')['observed']
 path=stage/'matching/events-000000000000.bin';original=path.read_bytes();head=hashlib.sha256((stage/'matching/start.json').read_bytes()).digest();payload=b''
 for offset in range(0,len(original),168):
  v=list(FRAME.unpack(original[offset:offset+136]));v[5]=b'\x98'*32;v[6]=b'\x76'*32
  frame=FRAME.pack(*v);head=hashlib.sha256(head+frame).digest();payload+=frame+head
 write(path,payload)
 terminal=stage/'matching/terminal.json';v=json.loads(terminal.read_bytes());v['head']=head.hex();v['payload_sha256']=hashlib.sha256(payload).hexdigest();write(terminal,v)
 result=caller.terminal(root=root,variant='wrong-ack')
 assert result['observed'] and result['evidence']['numerical_stage']['completed_pairs']==1
 print('CONFIRMED: actual parser accepts arbitrary replacement purpose 98*32 and ordered-pair identity 76*32 after resealing only matching event chain and terminal digest.')
 print('Original registered inputs, import receipt, workflow, graph and motif identities were unchanged. This is fabricated retained-format evidence only, not a real job.')
assert not any(k.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for k in sys.modules)
print('No numerical/package imports, lifecycle, Owner, guard or claim executed.')
