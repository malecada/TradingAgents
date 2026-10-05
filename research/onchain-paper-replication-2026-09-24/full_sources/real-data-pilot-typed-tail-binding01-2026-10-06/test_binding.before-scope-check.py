"""Tiny original-append bytes and metadata only; never genuine scientific authority."""
from pathlib import Path
import ast,hashlib,io,json,math,os,struct,sys,tempfile,types,unittest
import typed_tail_binding as a
D=Path(__file__).resolve().parent;M=D.parents[3];P=M/'tradingagents/research/onchain_replication'
sha=a.bank.digest;encode=a.bank.encode
# Only the original unchanged append AST executes; its local file harness is not Owner.
tree=ast.parse((P/'score_tail.py').read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ScoreTail');append=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='append')
g={'batch':types.SimpleNamespace(_identity=a.bank.identity,_hash=sha),'require':a.require,'FRAME':struct.Struct('<Qd32s'),'RECORD_BYTES':80,'os':os,'math':math}
exec(compile(ast.Module(body=[append],type_ignores=[]),'original-append-AST','exec'),g)
class Writer:
 append=g['append']
 def _check(self,expected_size=None):
  assert os.fstat(self.record_fd).st_size==(self.acknowledged*80 if expected_size is None else expected_size)

def fixture(root):
 motifs=[sha(('motif'+str(i)).encode()) for i in range(32)];scope={k:sha(k.encode()) for k in a.bank.SCOPE};scope['ordered_motifs']=sha(json.dumps(motifs,separators=(',',':')).encode());stage_name='mcm-'+scope['graph'];stage_root=root/stage_name
 c={k:sha(k.encode()) for k in a.bank.HASHES};c.update(schema_version=1,format='score-tail-archive-v1',stage=stage_name,source_commit='a'*40,job_input='execution_job',scope=scope,ordered_motifs=motifs,rows=17,motifs=32,chunk_cells=544,index=0,batch_directory=str(stage_root/'stream/batches'),remote='synthetic-original-tail')
 meta={};meta['batch_start']=encode(dict(schema_version=1,scope=scope,owner=c['owner'],rows=17,motifs=32,chunk_cells=544,dtype='<f8',order='row-major'));c['batch_start_sha256']=sha(meta['batch_start']);c['batch_previous_sha256']=c['batch_start_sha256']
 destination=sha(encode(dict(directory=c['batch_directory'],start_sha256=c['batch_start_sha256'],index=0,start_cell=0,cells=544)))
 start=dict(schema_version=1,kind='mcm-score-tail',scope=scope,owner=c['owner'],start_cell=0,cells=544,destination=destination,record_format='<Qd32s32s',record_bytes=80);meta['tail_start']=encode(start);c['tail_start_sha256']=sha(meta['tail_start'])
 w=Writer();w.start=start;w.acknowledged=0;w.head=c['tail_start_sha256'];payload=b''
 with tempfile.TemporaryFile(dir=root) as f:
  w.record_fd=f.fileno()
  for n in range(544):
   value=-0.0 if n==0 else .1234567890123456
   w.append(n,sha(str(n).encode()),value);payload+=struct.pack('<d',value)
  f.seek(0);body=f.read()
 c['batch_payload_sha256']=sha(payload)
 meta['tail_terminal']=encode(dict(schema_version=1,start_sha256=c['tail_start_sha256'],status='complete',reason='',acknowledged_cells=544,head=w.head,records_bytes=len(body),records_sha256=sha(body)));c['tail_terminal_sha256']=sha(meta['tail_terminal'])
 meta['batch_header']=encode(dict(schema_version=1,start_sha256=c['batch_start_sha256'],previous=c['batch_previous_sha256'],index=0,start_cell=0,cells=544,payload_sha256=c['batch_payload_sha256']));c['batch_header_sha256']=sha(meta['batch_header'])
 meta['stream_start']=encode(dict(schema_version=1,kind='mcm-score-stream',scope=scope,owner=c['owner'],rows=17,motifs=32,chunk_cells=544,batch_start_sha256=c['batch_start_sha256']))
 previous=sha(meta['stream_start']);meta['seal']=encode(dict(schema_version=1,start_sha256=previous,previous=previous,index=0,start_cell=0,cells=544,tail_terminal_sha256=c['tail_terminal_sha256'],batch_header_sha256=c['batch_header_sha256']))
 meta['stream_complete']=encode(dict(schema_version=1,start_sha256=previous,head=sha(meta['seal']),cells=544,chunks=1,batch_terminal_sha256=sha(b'batch terminal')))
 event_scope={'workflow':scope['workflow'],'policy':sha(b'policy')}
 meta['intent']=encode(dict(schema_version=1,owner=c['owner'],stage=stage_name,kind='mcm',scope=event_scope,pairs=544,logical_reservation_bytes=1000000,policy_sha256=sha(b'policy')));c['stage_intent_sha256']=sha(meta['intent'])
 meta['stage']=encode(dict(schema_version=1,kind='mcm',owner=c['owner'],scope=event_scope,policy_sha256=sha(b'policy'),completed_pairs=544,log_terminal_sha256=sha(b'logterminal'),stream_terminal_sha256=sha(meta['stream_complete']),stream_start_sha256=previous,log_start_sha256=sha(b'logstart'),matching_scores_sha256=sha(b'not independently checked'),checkpoints=0,checkpoint_logical_bytes=0,checkpoints_sha256=sha(b''),execution_admitted=False))
 pins={k:sha(v) for k,v in meta.items()};binding=a.bind(c,meta,pins,previous_seal=previous)
 return binding,body,payload,stage_root

class Checks(unittest.TestCase):
 def test_original_f64_stream_and_chunk_recovery(self):
  with tempfile.TemporaryDirectory(dir=D) as tmp:
   b,body,payload,root=fixture(Path(tmp));chunks=[];source=io.BytesIO(body)
   result=a.verify(b,lambda n:source.read(min(n,7)),io.BytesIO(payload).read,lease=lambda:None,max_seconds=5,emit=chunks.append)
   self.assertEqual([len(x.raw) for x in chunks],[40960,2560]);self.assertEqual(b''.join(x.raw for x in chunks),body)
   self.assertEqual(a.verify_recovery(b,iter(chunks),io.BytesIO(payload).read,lease=lambda:None,max_seconds=5),result)
   self.assertEqual(chunks[0].raw[8:16],struct.pack('<d',-0.0));self.assertIsNone(result['authority'])
 def test_corrupt_partial_and_float32_substitution_refuse(self):
  with tempfile.TemporaryDirectory(dir=D) as tmp:
   b,body,payload,root=fixture(Path(tmp));bad=bytearray(body);bad[25]^=1
   for raw in (bytes(bad),body[:-1],body+b'!'):
    with self.assertRaises(ValueError):a.verify(b,io.BytesIO(raw).read,io.BytesIO(payload).read,lease=lambda:None,max_seconds=5)
   converted=b''.join(struct.pack('<d',struct.unpack('<f',struct.pack('<f',struct.unpack('<d',payload[i:i+8])[0]))[0]) for i in range(0,len(payload),8))
   with self.assertRaisesRegex(ValueError,'float64 batch bits'):a.verify(b,io.BytesIO(body).read,io.BytesIO(converted).read,lease=lambda:None,max_seconds=5)
 def test_identity_and_lease_refusals(self):
  with tempfile.TemporaryDirectory(dir=D) as tmp:
   b,body,payload,root=fixture(Path(tmp));m=dict(b.metadata);v=a.bank.decode(m['stage']);v['owner']='0'*64;m['stage']=encode(v);pins=dict(b.pins);pins['stage']=sha(m['stage'])
   with self.assertRaisesRegex(ValueError,'stage receipt'):a.bind(a.bank.decode(b.contract_raw),m,pins,previous_seal=b.previous_seal)
   chunks=[];a.verify(b,io.BytesIO(body).read,io.BytesIO(payload).read,lease=lambda:None,max_seconds=5,emit=chunks.append)
   wrong=a.Chunk('0'*64,0,0,chunks[0].raw)
   with self.assertRaises(ValueError):a.verify_recovery(b,[wrong],io.BytesIO(payload).read,lease=lambda:None,max_seconds=5)
   with self.assertRaises(ValueError):a.verify_recovery(b,reversed(chunks),io.BytesIO(payload).read,lease=lambda:None,max_seconds=5)
   def expired():raise RuntimeError('expired original caller lease')
   with self.assertRaisesRegex(RuntimeError,'expired'):a.verify(b,io.BytesIO(body).read,io.BytesIO(payload).read,lease=expired,max_seconds=5)
   with self.assertRaisesRegex(ValueError,'selected transport'):a.preserve_chunk(b,chunks[0],source='unused',attempt='unused',remote='unused',transport=types.SimpleNamespace(identity='0'*64),lease=lambda:None,free_floor_bytes=0)
   with self.assertRaises(ValueError):a.activate(b)
 def test_original_fd_metadata_mutation_refuses(self):
  with tempfile.TemporaryDirectory(dir=D) as tmp:
   b,body,payload,root=fixture(Path(tmp));tail=root/'stream/tails/tail-000000000000';batch=root/'stream/batches';tail.mkdir(parents=True);batch.mkdir()
   paths={'intent':root/'intent.json','stage':root/'stage-complete.json','stream_start':root/'stream/start.json','stream_complete':root/'stream/complete.json','seal':root/'stream/seal-000000000000.json','batch_start':batch/'start.json','batch_header':batch/'chunk-000000000000.json','tail_start':tail/'start.json','tail_terminal':tail/'terminal.json'}
   for name,raw in b.metadata:paths[name].write_bytes(raw)
   (tail/'records.bin').write_bytes(body);(batch/'chunk-000000000000.bin').write_bytes(payload)
   with a.original_readers(b,root,lease=lambda:None) as readers:a.verify(b,*readers,lease=lambda:None,max_seconds=5)
   with self.assertRaisesRegex(ValueError,'member changed'):
    with a.original_readers(b,root,lease=lambda:None) as readers:
     a.verify(b,*readers,lease=lambda:None,max_seconds=5);paths['stage'].write_bytes(paths['stage'].read_bytes()+b' ')
   self.assertFalse({'numpy','torch','scipy','networkx'}&set(sys.modules))

if __name__=='__main__':unittest.main(verbosity=2)
