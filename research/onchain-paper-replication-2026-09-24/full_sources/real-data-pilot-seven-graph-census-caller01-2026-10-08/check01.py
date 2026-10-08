"""Tiny synthetic caller checks. No retained scientific inputs are opened."""
from pathlib import Path
import hashlib, importlib.util, json, tempfile, unittest
import numpy as np
H=Path(__file__).resolve().parent;R=H.parents[3]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=str(p.relative_to(R)),sha256=digest(p),bytes=p.stat().st_size)
def save(p,v):p.write_text(json.dumps(v));return ref(p)
class CallerTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((H/'caller01.py').exists(),'seven-graph topology caller is not implemented')
        spec=importlib.util.spec_from_file_location('census_caller_test',H/'caller01.py');self.c=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.c)
        self.temp=tempfile.TemporaryDirectory(dir=H);self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.rows=[]
        for i in range(7):
            d=self.root/str(i);d.mkdir();edge=np.array([[0,1,1,2,3,3],[1,0,2,1,3,3]],dtype='<i8');ids=np.array(['a','b','c','d'],dtype='<U1')
            np.save(d/'edge_index.npy',edge);np.save(d/'node_ids.npy',ids)
            ar={k:ref(d/(k+'.npy'))|dict(dtype=v.dtype.str,shape=list(v.shape),fortran_order=False) for k,v in [('edge_index',edge),('node_ids',ids)]}
            manifest={'graph_hash':hashlib.sha256(str(i).encode()).hexdigest(),'metadata':{'start_utc':f'2022-01-{i+1:02d}T00:00:00Z'},'arrays':{k:{'path':k+'.npy','sha256':v['sha256'],'bytes':v['bytes']} for k,v in ar.items()}}
            manifest['arrays']['node_features']={'path':'MUST_NOT_OPEN.npy','sha256':'f'*64,'bytes':32}
            mr=save(d/'manifest.json',manifest)
            cr=save(d/'count.json',dict(schema_version=1,kind='graph-node-count-metadata-v1',rows=4,graph_manifest_sha256=mr['sha256'],node_features_sha256='f'*64))
            self.rows.append(dict(role=f'graph_{i}',week=f'2022-01-{i+1:02d}',graph_hash=manifest['graph_hash'],manifest=mr,node_count=4,node_count_reference=cr,**ar))
        self.settings=dict(schema_version=1,kind='topology-only-seven-graph-census-v1',inputs=save(self.root/'inputs.json',self.rows),caller_sha256=digest(H/'caller01.py'),helper_sha256=digest(R/'tradingagents/research/onchain_replication/weak_one_hop_census.py'),max_work_bytes=268435456,chunk_edges=65536,chunk_centers=262144)
    def run_call(self,name='out'):
        p=self.root/('settings-'+name+'.json');save(p,self.settings)
        return self.c.run(R,p,digest(p),self.root/name)
    def test_complete_seven_and_exact_unique_weak_counts(self):
        result=self.run_call();self.assertEqual([x['status'] for x in result['graphs']],['completed']*7)
        for row in result['graphs']:
            card=np.concatenate([np.load(self.root/'out'/x['path'],allow_pickle=False) for x in row['chunks']]);self.assertEqual(card.tolist(),[2,3,2,1])
            self.assertEqual(row['maximum_center_index'],1);self.assertLessEqual(max(x['bytes'] for x in row['chunks']),4194304)
        self.assertNotIn('torch',__import__('sys').modules)
    def test_bad_edge_pin_stops_and_retains_full_denominator(self):
        p=R/self.rows[2]['edge_index']['path'];b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(b)
        result=self.run_call();self.assertEqual([x['status'] for x in result['graphs']],['completed']*2+['failed']+['unattempted']*4)
        self.assertIn('hash',result['graphs'][2]['reason'])
        self.assertFalse(result['graphs'][2]['failure_rechecks']['edge_index']['matches_declared'])
    def test_count_manifest_mismatch_refused(self):
        p=R/self.rows[0]['node_count_reference']['path'];v=json.loads(p.read_text());v['graph_manifest_sha256']='0'*64;self.rows[0]['node_count_reference']=save(p,v);self.settings['inputs']=save(self.root/'inputs.json',self.rows)
        result=self.run_call();self.assertEqual(result['graphs'][0]['status'],'failed');self.assertEqual(result['graphs'][1]['status'],'unattempted')
    def test_only_seven_distinct_graphs_and_one_use_outputs(self):
        self.run_call()
        with self.assertRaises(FileExistsError):self.run_call()
        self.settings['inputs']=save(self.root/'inputs-short.json',self.rows[:6])
        with self.assertRaises(ValueError):self.run_call('short')
    def test_changed_edge_after_computation_is_not_published(self):
        actual=self.c.load_helper
        def changed(*args):
            module=actual(*args);original=module.census
            def compute(*a,**kw):
                result=original(*a,**kw);p=R/self.rows[0]['edge_index']['path'];b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(b);return result
            module.census=compute;return module
        self.c.load_helper=changed
        result=self.run_call();self.assertEqual(result['graphs'][0]['status'],'failed');self.assertFalse(result['graphs'][0].get('chunks'))
    def test_changed_declaration_keeps_terminal_summary(self):
        actual=self.c.load_helper
        def changed(*args):
            module=actual(*args);original=module.census
            def compute(*a,**kw):
                result=original(*a,**kw);p=R/self.settings['inputs']['path'];p.write_text(p.read_text()+' ');return result
            module.census=compute;return module
        self.c.load_helper=changed
        result=self.run_call();self.assertEqual(result['status'],'failed');self.assertEqual(len(result['graphs']),7)
        self.assertIn('integrity_failure',result);self.assertTrue((self.root/'out/SUMMARY01.json').exists())
    def test_independent_set_check_rejects_wrong_returned_count(self):
        edge=np.array([[0,1,1],[1,0,2]],dtype=np.int64)
        with self.assertRaisesRegex(ValueError,'independent per-center'):
            self.c.independent_counts(edge,np.array([2,2,2]),1,2)
    def test_chunk_boundary_keeps_all_center_counts(self):
        d=self.root/'chunks';d.mkdir();helper=self.c.load_helper(R,self.settings['helper_sha256'])
        row=self.c.graph(R,self.rows[0],d,helper,self.settings|{'chunk_centers':2})
        self.assertEqual(row['status'],'completed');self.assertEqual(len(row['chunks']),2)
        self.assertEqual(np.concatenate([np.load(self.root/x['path'],allow_pickle=False) for x in row['chunks']]).tolist(),[2,3,2,1])
    def test_mmap_cleanup_failure_keeps_original_failure(self):
        load=self.c.np.load;helper_load=self.c.load_helper
        class Wrapper:
            def __init__(self,m):self.m=m;self._mmap=self
            def view(self,*a):return self.m.view(*a)
            def close(self):self.m._mmap.close();raise RuntimeError('synthetic close failure')
        def failing_helper(*args):
            m=helper_load(*args)
            def fail(*a,**k):raise ValueError('synthetic primary failure')
            m.census=fail;return m
        self.c.load_helper=failing_helper;self.c.np.load=lambda *a,**k:Wrapper(load(*a,**k))
        try:result=self.run_call()
        finally:self.c.np.load=load
        self.assertEqual(result['graphs'][0]['reason'],'ValueError: synthetic primary failure')
        self.assertEqual(result['graphs'][0]['cleanup_error'],'RuntimeError: synthetic close failure')
if __name__=='__main__':unittest.main(verbosity=2)
