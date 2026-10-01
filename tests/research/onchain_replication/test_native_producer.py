"""Selectable native producer preflight; no data loading in these tests."""
import importlib
import importlib.util
import tempfile
from pathlib import Path
import unittest
from tests.research.test_lifecycle import registered,commit,start
from tradingagents.research.onchain_replication.provenance import canonical_bytes,file_hash

class Tests(unittest.TestCase):
    def api(self):
        name='tradingagents.research.onchain_replication.native_producer'
        self.assertIsNotNone(importlib.util.find_spec(name),'maintained native producer missing')
        return importlib.import_module(name)
    def run_fixture(self,item,job):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        root,spec,_=registered.__wrapped__(Path(tmp.name));exp=spec['experiments']['example-a']
        for name,value in [('plan',{'schema_version':2,'producers':{'p':item}}),('execution_job',{'payload':{'representation_jobs':{'r':job}}})]:
            path=root/(name+'.json');path.write_bytes(canonical_bytes(value));exp['inputs'][name]={'path':path.name,'sha256':file_hash(path),'dataset':'sample'}
        run=start((root,spec,commit(root,spec)));self.addCleanup(lambda:run.fail('synthetic closure'));return run
    def test_old_route_is_not_silently_changed(self):
        m=self.api();job={'operation':'produce','plan_input':'plan','producer':'p'}
        run=self.run_fixture({},job);self.assertFalse(m.selected(run,'r',job))
    def test_one_sided_or_unknown_engine_refuses_before_loading(self):
        m=self.api()
        for a,b in [(m.BACKEND,None),(None,m.BACKEND),('unknown','unknown')]:
            with self.subTest(a=a,b=b):
                job={'operation':'produce','plan_input':'plan','producer':'p','native_backend':b}
                run=self.run_fixture({'native_backend':a},job)
                with self.assertRaises(ValueError):m.selected(run,'r',job)
    def test_native_reuse_or_omitted_required_routes_refuse(self):
        m=self.api()
        for operation in ('reuse','produce'):
            job={'operation':operation,'plan_input':'plan','producer':'p','native_backend':m.BACKEND}
            run=self.run_fixture({'native_backend':m.BACKEND},job)
            with self.assertRaises(ValueError):m.selected(run,'r',job)
    def test_actual_run_is_required(self):
        m=self.api()
        with self.assertRaises(ValueError):m.selected(object(),'r',{})

if __name__=='__main__':unittest.main(verbosity=2)
