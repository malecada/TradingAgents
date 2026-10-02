"""Pure stdlib/byte fixtures; no ResearchRun, numerical imports or transport."""
import hashlib, importlib.util, json, os, pathlib, struct, sys, unittest
from unittest.mock import patch
HERE=pathlib.Path(__file__).resolve().parent
P=HERE/'score_tail_archive.py'
def h(b): return hashlib.sha256(b).hexdigest()
def j(v): return (json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def fixture(rows=1,chunk=32,index=0):
    scope={k:h(k.encode()) for k in ('graph','node_order','dictionary','ordered_motifs','matching','workflow')}
    motifs=[h(str(x).encode()) for x in range(32)]
    scope['ordered_motifs']=h(json.dumps(motifs,separators=(',',':')).encode())
    start=index*chunk;count=min(chunk,rows*32-start)
    c=dict(schema_version=1,format='score-tail-archive-v1',owner=h(b'owner'),stage='mcm-'+scope['graph'],
        stage_intent_sha256=h(b'stage'),source_commit='1'*40,job_input='execution_job',job_sha256=h(b'job'),
        binding_sha256=h(b'binding'),scope=scope,original_matching_sha256=h(b'original'),
        ordered_motifs=motifs,rows=rows,motifs=32,chunk_cells=chunk,index=index,previous_mapping_sha256=h(b'previous'),
        batch_directory=str(HERE/'not-opened-batches'),batch_start_sha256=h(b'batchstart'),
        batch_previous_sha256=h(b'batchprevious'),transport_identity=h(b'endpoint'),remote='tail-0000')
    dest=h(j(dict(directory=c['batch_directory'],start_sha256=c['batch_start_sha256'],index=index,start_cell=start,cells=count)))
    ts=j(dict(schema_version=1,kind='mcm-score-tail',scope=scope,owner=c['owner'],start_cell=start,cells=count,
        destination=dest,record_format='<Qd32s32s',record_bytes=80))
    head=h(ts);records=bytearray();values=bytearray()
    for ordinal in range(start,start+count):
        value=(ordinal%4)/4;purpose=h(('purpose'+str(ordinal)).encode())
        frame=struct.pack('<Qd32s',ordinal,value,bytes.fromhex(purpose));head=h(bytes.fromhex(head)+frame)
        records+=frame+bytes.fromhex(head);values+=frame[8:16]
    tt=j(dict(schema_version=1,start_sha256=h(ts),status='complete',reason='',acknowledged_cells=count,
        head=head,records_bytes=len(records),records_sha256=h(records)))
    bh=j(dict(schema_version=1,start_sha256=c['batch_start_sha256'],previous=c['batch_previous_sha256'],index=index,
        start_cell=start,cells=count,payload_sha256=h(values)))
    c.update(tail_start_sha256=h(ts),tail_terminal_sha256=h(tt),batch_header_sha256=h(bh),batch_payload_sha256=h(values))
    return c,ts,tt,bytes(records),bh,bytes(values)
class Candidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if P.exists():
            spec=importlib.util.spec_from_file_location('tail_candidate',P);cls.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.m)
    def module(self):
        self.assertTrue(P.exists(),'bounded score-tail archive implementation is missing')
        return self.m
    def test_exact_original_format_and_partial_final_chunk(self):
        m=self.module()
        for args in ((1,32,0),(2,40,1)):
            c,*parts=fixture(*args);result=m.verify_bytes(c,*parts)
            self.assertEqual(result['cells'],len(parts[2])//80)
            self.assertEqual(result['payload_sha256'],h(parts[2]))
            self.assertEqual(result['score_sha256'],h(b''.join(parts[2][n:n+48] for n in range(0,len(parts[2]),80))))
    def test_schema_denominator_identity_and_reordered_bytes_refused(self):
        m=self.module();c,*parts=fixture()
        for key,value in [('motifs',31),('rows',True),('chunk_cells',65537),('extra',1),('tail_start_sha256','0'*64)]:
            bad=dict(c,**{key:value})
            with self.assertRaises(ValueError):m.verify_bytes(bad,*parts)
        for i in (0,1,2,3,4):
            bad=list(parts);bad[i]=bad[i]+b' '
            with self.assertRaises(ValueError):m.verify_bytes(c,*bad)
        bad=list(parts);bad[2]=parts[2][80:160]+parts[2][:80]+parts[2][160:]
        with self.assertRaises(ValueError):m.verify_bytes(c,*bad)
    def test_bound_65536_cells_is_five_mib(self):
        m=self.module();c,*parts=fixture(2048,65536,0)
        self.assertEqual(len(parts[2]),5242880);self.assertEqual(m.verify_bytes(c,*parts)['cells'],65536)
    def test_writer_reader_atomic_seal_and_no_deletion(self):
        m=self.module();root=HERE/'fixture-green02';root.mkdir()
        c,*parts=fixture();writer=m.LocalChunk(root/'chunk',c,lease=lambda:None)
        ref=writer.seal(*parts)
        got=m.read_local(root/'chunk',contract=c,receipt_sha256=ref,lease=lambda:None)
        self.assertEqual(got['payload_sha256'],h(parts[2]));self.assertTrue((root/'chunk'/'records.bin').is_file())
        with self.assertRaises(FileExistsError):m.LocalChunk(root/'chunk',c,lease=lambda:None)
        with self.assertRaises(ValueError):m.read_local(root/'chunk',contract=dict(c,stage='mcm-other'),receipt_sha256=ref,lease=lambda:None)
    def test_revocation_before_success_preserves_bytes_and_poison(self):
        m=self.module();root=HERE/'fixture-revoked02';c,*parts=fixture();state={'fail':False}
        def lease():
            if state['fail']:raise RuntimeError('revoked')
        writer=m.LocalChunk(root,c,lease=lease);state['fail']=True
        with self.assertRaisesRegex(RuntimeError,'revoked'):writer.seal(*parts)
        self.assertFalse((root/'complete.json').exists());self.assertTrue(writer.closed)
    def test_alias_and_first_fatal_close_once(self):
        m=self.module();root=HERE/'fixture-alias02';root.mkdir();(root/'a').write_bytes(b'x');os.link(root/'a',root/'b')
        fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY)
        try:
            with self.assertRaises(ValueError):m.read_member(fd,'a',1)
        finally:os.close(fd)
        first=KeyboardInterrupt('first');calls=[]
        def one():calls.append(1);raise first
        def two():calls.append(2);raise OSError('second')
        with self.assertRaises(KeyboardInterrupt) as caught:m.cleanup((one,two))
        self.assertIs(caught.exception,first);self.assertEqual(calls,[1,2])
    def test_callback_mutates_contract_is_refused(self):
        m=self.module();c,*parts=fixture();writer=m.LocalChunk(HERE/'fixture-mutate02',c,lease=lambda:None)
        writer.contract['rows']=2
        with self.assertRaises(ValueError):writer.seal(*parts)
        self.assertTrue(writer.closed)
if __name__=='__main__':unittest.main(verbosity=2)
