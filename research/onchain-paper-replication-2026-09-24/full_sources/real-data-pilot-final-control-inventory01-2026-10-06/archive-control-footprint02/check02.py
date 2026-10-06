"""Focused source-loader checks: actual archive IO, synthetic bytes, stdlib only."""
import hashlib,importlib,json,os,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];SRC=ROOT/'tradingagents/research/onchain_replication'
def guard(event,args):
    if event.startswith(('socket.','subprocess.')):raise RuntimeError('offline only')
    if event=='import' and args[0].split('.')[0] in {'numpy','torch','pandas','scipy'}:raise RuntimeError('no numerical imports')
sys.addaudithook(guard)
package=types.ModuleType('selected_archive');package.__path__=[str(HERE/'candidate'),str(SRC)];sys.modules[package.__name__]=package
# Original scalar/descriptor IO with sole unused numerical import removed.
name='selected_archive.score_batches';m=types.ModuleType(name);m.__file__=str(SRC/'score_batches.py');m.__package__='selected_archive';sys.modules[name]=m
source=Path(m.__file__).read_text();assert source.count('import numpy as np\n')==1
exec(compile(source.replace('import numpy as np\n',''),m.__file__,'exec'),m.__dict__)
rc=importlib.import_module('selected_archive.archive_read_controls');w=importlib.import_module('selected_archive.archive_pair_writer');reader=importlib.import_module('selected_archive.archive_pair_reader');io=w.io
class Transport:
    identity='f'*64
    def __init__(self):self.data={};self.fail=False
    def mkdir(self,name):pass
    def put(self,path,member):self.data[member]=Path(path).read_bytes()
    def get(self,member,path,expected_bytes):
        Path(path).write_bytes(self.data[member])
        if self.fail:raise OSError('invented transport failure')

class Checks(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=HERE);self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.free=patch.object(w.archive.shutil,'disk_usage',return_value=types.SimpleNamespace(free=100*1024**3));self.free.start();self.addCleanup(self.free.stop)
        self.scope={k:'a'*64 for k in w.events.FIELDS};self.owner='b'*64;self.transport=Transport()
    def make(self,packed=True):
        limits={'max_events':4,'max_pairs':2,'chunk_events':2,'max_logical_bytes':4*168+2*8192}
        policy={'schema_version':1,'remote_prefix':'synthetic','transport_identity':self.transport.identity,'max_chunks':2,'max_metadata_bytes':(7*2+8)*8192,'local_free_floor_bytes':10*1024**3}
        if packed:policy['read_controls']=dict(rc.POLICY)
        writer=w.ArchivePairLog(self.root/'writer',owner=self.owner,scope=self.scope,limits=limits,max_iterations=10,lease=lambda:None,transport=self.transport,archive_policy=policy)
        for _ in range(2):writer.begin('c'*64,'d'*64);writer.complete(0.5,'temperature_complete',1)
        writer.finish();return policy,writer.archive_complete_sha
    def verify(self,policy,sha,ordinal=0,lease=lambda:None):
        return reader.verify(self.root/'writer',expected_sha256=sha,owner=self.owner,scope=self.scope,archive_policy=policy,attempt=self.root/('read'+str(ordinal)),transport=self.transport,lease=lease,max_read_metadata_bytes=reader._read_metadata_capacity(policy))
    def test_actual_packed_reader_sixteen_reads_and_exact_inverse(self):
        policy,sha=self.make()
        for index in range(16):
            result=self.verify(policy,sha,index);self.assertEqual(result['replay']['completed_pairs'],2)
            root=self.root/('read'+str(index));self.assertEqual({p.name for p in root.iterdir()},{'intent.json','complete.json','controls'})
            fd=os.open(self.root/'writer',os.O_RDONLY|os.O_DIRECTORY)
            try:
                snapshot=reader._Snapshot(self.root/'writer',fd,sha,self.owner,self.scope,policy,self.transport)
                reader._check_read_contents(root,snapshot)
            finally:os.close(fd)
    def test_packed_and_legacy_preserve_numerical_payload_and_replay(self):
        base=self.root;observed=[]
        for packed in (False,True):
            self.root=base/str(packed);self.root.mkdir();self.transport=Transport()
            policy,sha=self.make(packed);result=self.verify(policy,sha)
            observed.append((dict(self.transport.data),result['replay']))
        self.assertEqual(observed[0],observed[1])
    def test_candidate_admission_and_metadata_seams_compile(self):
        for source in (HERE/'candidate').glob('*.py'):compile(source.read_text(),str(source),'exec')
        dispatch=(HERE/'candidate/archive_dispatch.py').read_text()
        self.assertIn("set(archived)-{'read_controls'}==archive_owner_policy.FIELDS",dispatch)
        self.assertIn("archive_read_controls.policy(archived['read_controls'])",dispatch)
        scalar=(HERE/'candidate/controls01.py').read_text()
        self.assertIn("packed=read_capacity(Q,a['read_controls'])",scalar)
    def test_legacy_default_preserved(self):
        policy,sha=self.make(False);self.verify(policy,sha)
        self.assertEqual({p.name for p in (self.root/'read0').iterdir()},{'intent.json','complete.json','chunk-000000000000','chunk-000000000001'})
        self.assertEqual(reader._read_metadata_capacity(policy),(3*2+8)*8192)
    def test_worst_case_schema_bounds_exact(self):
        receipt={'schema_version':1,'format':'archive-chunk-v1','transport_identity':'f'*64,'remote':'z'*128,'member':'z'*128+'/payload.bin','scope':'f'*64,'source_sha256':'f'*64,'bytes':8388608}
        bodies=rc.bodies(receipt,'f'*64)
        self.assertEqual({k:len(v) for k,v in bodies.items()},rc.ROLE_BYTES)
        receipt['remote']+='z';receipt['member']='z'*129+'/payload.bin'
        with self.assertRaises(ValueError):rc.bodies(receipt,'f'*64)
    def test_closed_shard_mutation_refused(self):
        policy,sha=self.make();self.verify(policy,sha)
        root=self.root/'read0';path=root/'controls/control-00000000.bin';b=bytearray(path.read_bytes());b[60]^=1;path.write_bytes(b)
        fd=os.open(self.root/'writer',os.O_RDONLY|os.O_DIRECTORY)
        try:
            snapshot=reader._Snapshot(self.root/'writer',fd,sha,self.owner,self.scope,policy,self.transport)
            with self.assertRaises(ValueError):reader._check_read_contents(root,snapshot)
        finally:os.close(fd)
    def test_failure_receipts_and_payload_retained(self):
        policy,sha=self.make();self.transport.fail=True
        with self.assertRaises(OSError):self.verify(policy,sha)
        root=self.root/'read0';self.assertTrue((root/'failed.json').exists());self.assertFalse((root/'complete.json').exists());self.assertTrue((root/'payload-000000000000.bin').exists())
        b=(root/'controls/control-00000000.bin').read_bytes();self.assertIn(b'chunk-000000000000-intent.json',b);self.assertIn(b'chunk-000000000000-failed.json',b);self.assertIn(b'OSError',b)
    def test_policy_and_foreign_member_refusals(self):
        for bad in ({},dict(rc.POLICY,shard_bytes=8192),dict(rc.POLICY,schema_version=True)):
            with self.assertRaises(ValueError):rc.policy(bad)
        policy,sha=self.make();self.verify(policy,sha);root=self.root/'read0';(root/'controls/foreign').write_bytes(b'x')
        with self.assertRaises(ValueError):rc.audit(root,[],rc.POLICY,max_chunks=2)
    def test_source_policy_mutation_not_accepted(self):
        policy,sha=self.make();bad=dict(policy,read_controls=dict(rc.POLICY,shard_bytes=8192))
        with self.assertRaises(ValueError):self.verify(bad,sha)
    def test_partial_and_missing_records_refused(self):
        policy,sha=self.make();self.verify(policy,sha);root=self.root/'read0';p=root/'controls/control-00000000.bin';p.write_bytes(p.read_bytes()[:-1])
        with self.assertRaises(ValueError):rc.audit(root,[],rc.POLICY,max_chunks=2)
    def test_callback_mutation_refuses_before_payload_disposal(self):
        root=self.root/'mutation';root.mkdir();obj=rc.Writer(root,2,rc.POLICY)
        payload=b'invented payload';self.transport.data['remote/payload.bin']=payload
        receipt={'schema_version':1,'format':'archive-chunk-v1','transport_identity':self.transport.identity,'remote':'remote','member':'remote/payload.bin','scope':'c'*64,'source_sha256':io._hash(payload),'bytes':len(payload)}
        raw=io._json(receipt)
        def lease():
            if obj.journal.count==2:
                path=obj.journal._path(0);body=bytearray(path.read_bytes());body[60]^=1;path.write_bytes(body)
        with self.assertRaisesRegex(ValueError,'shard changed'):
            obj.consume(0,receipt_bytes=raw,receipt_sha256=io._hash(raw),expected_scope='c'*64,transport=self.transport,lease=lease,free_floor_bytes=0)
        self.assertEqual((root/'payload-000000000000.bin').read_bytes(),payload)
        self.assertFalse(obj.next)
    def test_selected_writer_binding_mutation_refused(self):
        root=self.root/'selected';root.mkdir();obj=rc.Writer(root,2,rc.POLICY)
        obj.journal.total_bytes+=1
        with self.assertRaisesRegex(ValueError,'binding changed'):obj._check()
    def test_existing_journal_multishard_exact_inverse(self):
        # Synthetic repeated metadata only; no transport/event numerical work.
        root=self.root/'many';root.mkdir();count=6000;bound=rc.capacity(count,rc.POLICY)
        journal=rc.history.Journal(root/'controls',record_bytes=8192,total_bytes=bound['journal_bytes'],records=3*count+4,shard_bytes=rc.POLICY['shard_bytes'])
        body=b'x'*748
        for i in range(count):journal.append(rc.record_name(i,'intent.json'),body)
        self.assertGreater(len(journal.pins),1)
        result=rc.audit(root,((rc.record_name(i,'intent.json'),body) for i in range(count)),rc.POLICY,max_chunks=count)
        self.assertEqual(result['records'],count)
        bad=root/'controls/control-00000000.bin';blob=bytearray(bad.read_bytes());blob[100]^=1;bad.write_bytes(blob)
        with self.assertRaises(ValueError):rc.audit(root,((rc.record_name(i,'intent.json'),body) for i in range(count)),rc.POLICY,max_chunks=count)
if __name__=='__main__':unittest.main(verbosity=2)
