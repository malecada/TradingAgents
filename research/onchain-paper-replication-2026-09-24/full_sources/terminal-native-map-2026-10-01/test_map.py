"""Synthetic native batching and maintained consumer compatibility."""
import importlib.util
import gc
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
import weakref
import threading
import numpy as np
import torch
from tradingagents.research.onchain_replication.component_store import save_component
from tradingagents.research.onchain_replication.provenance import file_hash
from tradingagents.research.onchain_replication.evaluation import batch_factory
from tradingagents.research.onchain_replication.model import ReplicationModel
from tradingagents.research.onchain_replication.feature_residency import FixedFeatureMap

HERE=Path(__file__).resolve().parent
def api():
    assert (HERE/'native_map.py').exists(),'terminal native feature map missing'
    spec=importlib.util.spec_from_file_location('native_map_candidate',HERE/'native_map.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class Tests(unittest.TestCase):
    def fixture(self,**policy):
        self.m=m=api();tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);root=Path(tmp.name)
        refs={};hashes={};values={}
        for i in range(2):
            h=('a' if i==0 else 'b')*64;a=np.array([[0,.25],[.5,1],[.75,0]],dtype=np.float32)
            edges=np.array([[0,1],[1,2]],dtype=np.int64) if i==0 else np.empty((2,0),dtype=np.int64)
            context={'synthetic':i};path=save_component(root/str(i),{'feature':{'mcm':a,'edge_index':edges},'aligned_vectors':None},context)
            identity=m.boundary.identity(a,edges,2);hashes[h]=identity;values[h]={'mcm':torch.tensor(a),'edge_index':torch.tensor(edges)}
            refs[h]={'path':str(path),'sha256':file_hash(path),'context':context,'nodes':3,'motifs':2,'edge_shape':list(edges.shape),
                'feature_hash':identity,'max_manifest_bytes':1048576,'max_artifact_bytes':1048576}
        settings={'schema_version':1,'max_live_tensor_bytes':1000,'max_numeric_bytes':2000,'chunk_entries':2}|policy
        self.refs=refs;self.hashes=hashes;self.values=values
        return m._NativeMap(root,refs,settings,lease=lambda:None,read_lease=lambda:None)
    def test_accounting_query_cannot_race_with_batch_registration(self):
        features=self.fixture(max_live_tensor_bytes=56);entered=threading.Event();release=threading.Event();result=[];errors=[]
        def hold():
            entered.set()
            if not release.wait(5):raise RuntimeError('barrier timeout')
        features._lease=hold
        def worker():
            try:result.append(features.load_batch(['a'*64]))
            except BaseException as error:errors.append(error)
        thread=threading.Thread(target=worker);thread.start()
        try:
            self.assertTrue(entered.wait(5))
            with self.assertRaisesRegex(ValueError,'already active'):features.live_tensor_bytes()
        finally:release.set();thread.join(5)
        self.assertFalse(thread.is_alive());self.assertFalse(errors);self.assertEqual(features.live_tensor_bytes(),56)
        with self.assertRaises(ValueError):features.load_batch(['a'*64])
    def test_minimum_capacity_requires_each_graph_to_load_before_sealing(self):
        self.fixture();m=self.m
        graphs={'a':SimpleNamespace(node_ids=('x','y','z'),edge_index=np.array([[0,1],[1,2]],dtype=np.int64))}
        base={'schema_version':1,'max_live_tensor_bytes':56,'max_numeric_bytes':130,'chunk_entries':2}
        m.minimum_capacity(graphs,['a'],2,base)
        for settings in (base|{'max_live_tensor_bytes':55},base|{'max_numeric_bytes':129}):
            with self.assertRaisesRegex(ValueError,'capacity'):m.minimum_capacity(graphs,['a'],2,settings)
    def test_deduplicated_native_cpu_bytes_empty_edges_and_release(self):
        features=self.fixture();m=self.m
        self.assertIsInstance(features,FixedFeatureMap);self.assertEqual(features.verified_hashes(),self.hashes)
        with patch.object(np,'load',side_effect=AssertionError('generic loader used')):
            out=features.load_batch(['a'*64,'a'*64,'b'*64])
        self.assertEqual(set(out),set(self.hashes));self.assertEqual(features.live_tensor_bytes(),80)
        for h,value in out.items():
            for key in value:torch.testing.assert_close(value[key],self.values[h][key],rtol=0,atol=0)
        held=weakref.ref(out['a'*64]['mcm']);del value,out;gc.collect()
        self.assertIsNone(held());self.assertEqual(features.live_tensor_bytes(),0)
    def test_aggregate_budget_and_unknown_keys_refuse_before_reader_allocation(self):
        features=self.fixture(max_numeric_bytes=153);m=self.m
        with patch.object(m.reader,'read_component',side_effect=AssertionError('premature native allocation')):
            with self.assertRaises(ValueError):features.load_batch(['a'*64,'b'*64])
            with self.assertRaises(ValueError):features.load_batch(['z'*64])
        features=self.fixture(max_live_tensor_bytes=80,max_numeric_bytes=154);m=self.m
        out=features.load_batch(['a'*64,'b'*64]);self.assertEqual(features.verified_hashes(),self.hashes)
        with patch.object(m.reader,'read_component',side_effect=AssertionError('prior live tensors omitted')):
            with self.assertRaises(ValueError):features.load_batch(['a'*64])
        del out;gc.collect();self.assertEqual(features.live_tensor_bytes(),0)
    def test_storage_layout_mutation_and_file_drift_refuse(self):
        features=self.fixture();out=features.load_batch(['a'*64]);out['a'*64]['mcm'].resize_(1)
        with self.assertRaises(ValueError):features.live_tensor_bytes()
        features=self.fixture();manifest=Path(self.refs['a'*64]['path']);target=manifest.parent/'array-000000.npy'
        raw=bytearray(target.read_bytes());raw[-1]^=1;target.write_bytes(raw)
        with self.assertRaises(ValueError):features.verified_hashes()
    def test_wrong_manifest_shape_refuses_before_numeric_allocation(self):
        features=self.fixture();m=self.m;h='a'*64;ref=dict(self.refs[h]);ref['nodes']=4
        wrong=m._NativeMap(features.root,{h:ref},{'schema_version':1,'max_live_tensor_bytes':1000,'max_numeric_bytes':2000,'chunk_entries':2},lease=lambda:None,read_lease=lambda:None)
        with patch.object(m.reader,'read_component',side_effect=AssertionError('wrong schema loaded')):
            with self.assertRaises(ValueError):wrong.load_batch([h])
    def test_reentrancy_and_late_failure_do_not_retain_new_tensors(self):
        features=self.fixture();m=self.m
        def reenter():features.verified_hashes()
        features._lease=reenter
        with self.assertRaises(ValueError):features.load_batch(['a'*64])
        features=self.fixture();m=self.m;count=[];held=[];original=m.boundary.materialize
        def collect(*a,**k):
            result=original(*a,**k);held.extend(weakref.ref(t) for t in result.values());return result
        def final_failure():
            count.append(1)
            if len(count)==2:raise RuntimeError('late terminal drift')
        features._lease=final_failure
        with patch.object(m.boundary,'materialize',side_effect=collect),self.assertRaisesRegex(RuntimeError,'late terminal drift'):
            features.load_batch(['a'*64])
        gc.collect();self.assertTrue(held);self.assertTrue(all(r() is None for r in held));self.assertEqual(features.live_tensor_bytes(),0)
    def test_maintained_batch_factory_full_neural_path_and_gradients(self):
        features=self.fixture()
        examples=[SimpleNamespace(input_prices=(1.,2.),up=1,target_price=3.,graph_hashes=('a'*64,'a'*64)),
            SimpleNamespace(input_prices=(2.,3.),up=0,target_price=2.,graph_hashes=('b'*64,'a'*64))]
        factory=batch_factory('proposed','direction',examples,SimpleNamespace(transform=lambda x:np.asarray(x)),features)
        inputs,targets=factory([0,1]);rows=inputs['graph_sequences']
        self.assertIs(rows[0][0],rows[0][1]);self.assertIs(rows[0][0],rows[1][1])
        config=json.loads((HERE.parents[1]/'config/model.json').read_text());config['mcm_input']=2
        torch.manual_seed(11);model=ReplicationModel(config,'classification').eval()
        output=model(**inputs);self.assertEqual(tuple(output.shape),(2,2))
        torch.nn.functional.cross_entropy(output,targets).backward()
        for name,parameters in model.parameter_groups().items():
            self.assertTrue(any(p.grad is not None and torch.isfinite(p.grad).all() and p.grad.abs().sum()>0 for p in parameters),name)

if __name__=='__main__':unittest.main(verbosity=2)
