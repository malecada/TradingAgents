"""Pure offline protocol controls; no Owner/Run/arrays or transport execution."""
import ast
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import types
import unittest
D=Path(__file__).resolve().parent
P=D.parents[3]/'tradingagents/research/onchain_replication'
pkg=types.ModuleType('typed_offline');pkg.__path__=[str(D),str(P)];sys.modules[pkg.__name__]=pkg
from typed_offline import typed_payload_policy as p, score_tail_semantics as s, typed_payload_operations as o

def pure_read(path,limit=131072):
    path=Path(path);raw=path.read_bytes()
    if len(raw)>limit:raise ValueError('bounded offline metadata')
    return raw
# The test substitutes ONLY metadata file I/O to avoid numerical imports. No
# scientific object/capability or successful actual operation is constructed.
o._read=pure_read

class Controls(unittest.TestCase):
    def test_unchanged_original_semantics_and_corruption(self):
        scope={k:'a'*64 for k in s.SCOPE_FIELDS}
        start=dict(schema_version=1,kind='mcm-score-tail',scope=scope,owner='b'*64,start_cell=7,cells=3,destination='c'*64,record_format='<Qd32s32s',record_bytes=80)
        sr=p.raw(start);head=bytes.fromhex(p.sha(sr));records=[]
        for i,value in enumerate((0.,.25,1.)):
            frame=struct.pack('<Qd32s',7+i,value,bytes([i])*32);head=hashlib.sha256(head+frame).digest();records.append(frame+head)
        raw=b''.join(records);terminal=dict(schema_version=1,start_sha256=p.sha(sr),status='complete',reason='',acknowledged_cells=3,head=head.hex(),records_bytes=len(raw),records_sha256=p.sha(raw));tr=p.raw(terminal)
        def verify(body):
            source=io.BytesIO(body)
            return s.verify_complete(lambda n:source.read(min(n,7)),start_raw=sr,terminal_raw=tr,start_sha256=p.sha(sr),terminal_sha256=p.sha(tr),scope=scope,owner='b'*64)
        self.assertEqual(verify(raw)['cells_verified'],3)
        for bad in (raw[:-1],raw+b'x',raw[80:]+raw[:80],raw[:8]+bytes([raw[8]^1])+raw[9:]):
            with self.assertRaises(ValueError):verify(bad)
        with self.assertRaises(MemoryError):s.verify_complete(lambda n:(_ for _ in ()).throw(MemoryError()),start_raw=sr,terminal_raw=tr,start_sha256=p.sha(sr),terminal_sha256=p.sha(tr),scope=scope,owner='b'*64)

    def test_explicit_budget_and_original_population(self):
        kinds={k:dict(max_operations=5,max_preserved_bytes=32*v,max_recovered_bytes=64*v,max_chunks=8,chunk_bytes=80*8192 if k=='score-tail-f64' else 524288) for k,v in p.KINDS.items()}
        value=dict(schema_version=1,format='typed-payload-budget-v1',assumption=p.ASSUMPTION,graphs={'a'*64:dict(rows=1,chunk_cells=32,kinds=kinds)},local_free_floor_bytes=10*1024**3,max_control_bytes=1024**2)
        bound=p.capacity(value);self.assertEqual(bound['logical_bytes'],32*(80+8+4)*4)
        for change in ('assumption','rows','bytes','partial'):
            bad=copy.deepcopy(value)
            if change=='assumption':bad['assumption']='current remote verified'
            elif change=='rows':bad['graphs']['a'*64]['rows']=True
            elif change=='bytes':bad['graphs']['a'*64]['kinds']['score-tail-f64']['chunk_bytes']=4*1024**2+80
            else:bad['graphs']['a'*64]['kinds']['score-batch-f64']['max_preserved_bytes']=8
            with self.assertRaises(ValueError):p.validate(bad)

    def test_historical_proof_chain_and_mutation(self):
        with tempfile.TemporaryDirectory(dir=D,prefix='offline-') as tmp:
            root=Path(tmp);binding={'schema_version':1,'owner':'a'*64};intent={'format':'typed-payload-operation-v1','kind':'score-tail-f64','binding':binding,'reserved_chunks':2,'reserved_payload_bytes':160};ir=p.raw(intent);key=p.sha(ir);parts=[]
            for i in range(2):
                receipt=dict(schema_version=1,format='archive-chunk-v1',transport_identity='b'*64,remote=f'original-p000-{i:012d}',member=f'original-p000-{i:012d}/payload.bin',scope=p.sha(p.raw(dict(operation=key,index=i,bytes=80,sha256='c'*64))),source_sha256='c'*64,bytes=80)
                part=dict(index=i,operation_sha256=key,fresh_full_recovery=True,receipt=receipt,receipt_sha256=p.sha(p.raw(receipt)));parts.append(part)
                (root/f'typed-part-{key}-{i:012d}.json').write_bytes(p.raw(part))
            complete=dict(operation_sha256=key,assumption=p.ASSUMPTION,parts=2,preserved_bytes=160,parts_sha256=p.sha(b''.join(bytes.fromhex(p.sha(p.raw(v))) for v in parts)))
            record=dict(directory=str(root),intent=f'typed-{key}.json',intent_sha256=key,complete=f'typed-complete-{key}.json',complete_sha256=p.sha(p.raw(complete)))
            (root/record['intent']).write_bytes(ir);(root/record['complete']).write_bytes(p.raw(complete))
            self.assertEqual(len(list(o.iter_history_parts(record,binding=binding,kind='score-tail-f64'))),2)
            with self.assertRaises(ValueError):list(o.iter_history_parts(record,binding={'owner':'wrong'},kind='score-tail-f64'))
            path=root/f'typed-part-{key}-000000000001.json';saved=path.read_bytes();bad=copy.deepcopy(parts[1]);bad['index']=0;path.write_bytes(p.raw(bad))
            with self.assertRaises(ValueError):list(o.iter_history_parts(record,binding=binding,kind='score-tail-f64'))
            path.write_bytes(saved);path.unlink()
            with self.assertRaises(FileNotFoundError):list(o.iter_history_parts(record,binding=binding,kind='score-tail-f64'))

    def test_actual_changed_source_order_and_default_inverse(self):
        for name in ('typed_payload_operations.py','typed_score_store.py','archive_dispatch.py','archive_owner_operations.py','archive_owner_seal.py','mcm_score_stream.py','compact_stage.py','archived_stage.py','typed_tail_binding.py'):ast.parse((D/name).read_bytes())
        source=(D/'typed_score_store.py').read_text()
        self.assertLess(source.index('semantic=semantics.verify_complete'),source.index("operations.dispose(tr/'records.bin'"))
        ops=(D/'typed_payload_operations.py').read_text()
        self.assertLess(ops.index('ref=a.preserve('),ops.index("for name in ('snapshot.bin','readback.bin')"))
        self.assertIn('type(owner) is a.owners.Owner',ops);self.assertIn('self.held.check(owner)',ops)
        self.assertIn("self.parent['lease']()",ops);self.assertIn('self.context._cap=op.parent',ops)
        self.assertNotIn('numpy',sys.modules)

if __name__=='__main__':unittest.main(verbosity=2)
