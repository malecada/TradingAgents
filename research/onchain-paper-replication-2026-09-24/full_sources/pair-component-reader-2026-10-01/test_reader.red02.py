"""Small real NPY components; no empirical inputs or allocation guard claim."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from tradingagents.research.onchain_replication.component_store import save_component
from tradingagents.research.onchain_replication.provenance import canonical_bytes,file_hash

HERE=Path(__file__).resolve().parent
def api():
    assert (HERE/'reader.py').is_file(),'strict numeric component reader missing'
    spec=importlib.util.spec_from_file_location('strict_component_candidate',HERE/'reader.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class Tests(unittest.TestCase):
    def setUp(self):
        self.m=api();t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);self.root=Path(t.name)
        self.context={'owner':'synthetic','stage':'samples_complete'}
        self.payload={'a':np.arange(6,dtype=np.float64).reshape(2,3),
            'b':np.asfortranarray(np.arange(6,dtype=np.int64).reshape(3,2)),
            'nested':('text',[],{'ok':True,'empty':np.zeros((0,2),dtype=np.float32)})}
        self.path=save_component(self.root/'artifact',self.payload,self.context)
    def read(self,**kw):
        args=dict(root=self.root,max_manifest_bytes=65536,max_artifact_bytes=1000000,
            max_array_bytes=100000,lease=lambda:None);args.update(kw)
        return self.m.read_component(self.path,file_hash(self.path),self.context,**args)
    def manifest(self,mutate):
        value=json.loads(self.path.read_bytes());mutate(value);self.path.write_bytes(canonical_bytes(value))
    def refuse_before_allocation(self,**kw):
        with patch.object(self.m.np,'empty',side_effect=AssertionError('allocated before admission')):
            with self.assertRaises((ValueError,OSError)):self.read(**kw)
    def test_roundtrip_numeric_bytes_shapes_and_fortran_order_without_np_load(self):
        with patch.object(self.m.np,'load',side_effect=AssertionError('opened mapping/archive')):got=self.read()
        np.testing.assert_array_equal(got['a'],self.payload['a']);np.testing.assert_array_equal(got['b'],self.payload['b'])
        self.assertTrue(got['b'].flags.f_contiguous)
        self.assertEqual(got['nested'][:2],('text',[]));self.assertEqual(got['nested'][2]['empty'].shape,(0,2))
    def test_aggregate_array_and_file_bounds_refuse_before_allocation(self):
        self.refuse_before_allocation(max_array_bytes=80)
        self.refuse_before_allocation(max_artifact_bytes=self.path.stat().st_size)
        self.refuse_before_allocation(max_manifest_bytes=16)
    def test_late_member_header_or_extent_failure_precedes_first_allocation(self):
        p=self.path.parent/'array-000001.npy';p.write_bytes(p.read_bytes()[:-1])
        self.manifest(lambda v:v['arrays'][p.name].update(bytes=p.stat().st_size,sha256=file_hash(p)))
        self.refuse_before_allocation()
    def test_rehashed_disguised_npz_is_rejected_without_np_load(self):
        p=self.path.parent/'array-000001.npy'
        with p.open('wb') as f:np.savez(f,x=np.arange(6,dtype=np.int64))
        self.manifest(lambda v:v['arrays'][p.name].update(bytes=p.stat().st_size,sha256=file_hash(p)))
        with patch.object(self.m.np,'load',side_effect=AssertionError('archive opened')):self.refuse_before_allocation()
    def test_member_links_and_unpublished_inventory_refuse(self):
        p=self.path.parent/'array-000001.npy';alias=self.root/'alias.npy';os.link(p,alias)
        self.refuse_before_allocation();alias.unlink()
        p.rename(alias);p.symlink_to(alias)
        self.refuse_before_allocation();p.unlink();alias.rename(p)
        (self.path.parent/'unpublished').write_text('x');self.refuse_before_allocation()
    def test_tree_member_reuse_or_unreferenced_array_refuses(self):
        value=json.loads(self.path.read_bytes());old=canonical_bytes(value)
        self.manifest(lambda v:v['tree']['items'][1][1].update(member='array-000000.npy'))
        self.refuse_before_allocation();self.path.write_bytes(old)
        self.manifest(lambda v:v['tree']['items'].pop(1));self.refuse_before_allocation()
    def test_guard_loss_before_allocation_and_after_load_closes_every_handle(self):
        real=self.m.os.fdopen;opened=[]
        def fdopen(*a,**kw):
            f=real(*a,**kw);opened.append(f);return f
        with patch.object(self.m.os,'fdopen',fdopen):
            with patch.object(self.m.np,'empty',side_effect=AssertionError('allocated')):
                with self.assertRaisesRegex(ValueError,'guard'):self.read(lease=lambda:(_ for _ in ()).throw(ValueError('guard expired')))
            calls=[0]
            def lease():
                calls[0]+=1
                if calls[0]==5:raise ValueError('guard expired after load')
            with self.assertRaisesRegex(ValueError,'guard'):self.read(lease=lease)
        self.assertTrue(opened);self.assertTrue(all(f.closed for f in opened))
    def test_changed_late_file_during_load_refuses_and_closes_handles(self):
        real_empty=self.m.np.empty;real_fdopen=self.m.os.fdopen;opened=[];changed=[False]
        def fdopen(*a,**kw):
            f=real_fdopen(*a,**kw);opened.append(f);return f
        def allocate(*a,**kw):
            result=real_empty(*a,**kw)
            if not changed[0]:
                changed[0]=True;p=self.path.parent/'array-000001.npy';raw=bytearray(p.read_bytes());raw[-1]^=1;p.write_bytes(raw)
            return result
        with patch.object(self.m.np,'empty',allocate),patch.object(self.m.os,'fdopen',fdopen):
            with self.assertRaises(ValueError):self.read()
        self.assertTrue(opened);self.assertTrue(all(f.closed for f in opened))

    def test_growth_during_hash_is_bounded_to_admitted_extent_plus_one(self):
        p=self.path.parent/'array-000000.npy';size=p.stat().st_size
        real=self.m.digest_stream;observed=[0];injected=[False]
        class Tracked:
            def __init__(self,stream):self.stream=stream
            def seek(self,*args):return self.stream.seek(*args)
            def read(self,n=-1):
                data=self.stream.read(n);observed[0]+=len(data);return data
        def hashing(stream,*args,**kw):
            if not injected[0]:
                injected[0]=True
                with p.open('ab') as f:f.write(b'x'*1000000)
                return real(Tracked(stream),*args,**kw)
            return real(stream,*args,**kw)
        with patch.object(self.m,'digest_stream',hashing):
            with self.assertRaises(ValueError):self.read()
        self.assertLessEqual(observed[0],size+1)
    def test_non_native_endian_values_preserve_declared_bytes(self):
        p=self.root/'endian';payload={'values':np.asarray([1.25,-2.5,3.0],dtype='>f8')}
        path=save_component(p,payload,self.context)
        got=self.m.read_component(path,file_hash(path),self.context,root=self.root,
            max_manifest_bytes=65536,max_artifact_bytes=1000000,max_array_bytes=1000,lease=lambda:None)
        self.assertEqual(got['values'].dtype.str,'>f8');self.assertEqual(got['values'].tobytes(),payload['values'].tobytes())
    def test_oversized_header_length_refuses_before_header_body_or_array_allocation(self):
        import struct
        p=self.path.parent/'array-000001.npy'
        p.write_bytes(b'\x93NUMPY'+bytes([2,0])+struct.pack('<I',1000000)+b'x'*1000000)
        self.manifest(lambda v:v['arrays'][p.name].update(bytes=p.stat().st_size,sha256=file_hash(p)))
        self.refuse_before_allocation(max_artifact_bytes=2000000)

if __name__=='__main__':unittest.main(verbosity=2)
