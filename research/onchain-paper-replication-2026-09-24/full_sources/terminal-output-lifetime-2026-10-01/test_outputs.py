"""Actual ResearchRun output publication with bounded append-only observation."""
import importlib.util
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from tests.research.test_lifecycle import registered,commit,start
from tradingagents.research import lifecycle
from tradingagents.research.onchain_replication.provenance import file_hash

HERE=Path(__file__).resolve().parent

def api():
    assert (HERE/'outputs.py').exists(),'post-terminal output tracker missing'
    spec=importlib.util.spec_from_file_location('output_lifetime_candidate',HERE/'outputs.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class Tests(unittest.TestCase):
    def fixture(self):
        m=api();tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        root,spec,_=registered.__wrapped__(Path(tmp.name))
        spec['experiments']['example-a']['outputs']=['binding.json','journal.json','controls.json','ledger.json']
        run=start((root,spec,commit(root,spec)));self.addCleanup(lambda:run.fail('synthetic test closure'))
        run.write_json('binding.json',{'fixed':1});run.write_json('journal.json',{'fixed':2})
        tracker=m.Outputs(run,dict(run._published_outputs),max_bytes=1024)
        return m,run,tracker
    def test_real_registered_additions_are_accepted_and_pinned(self):
        _,run,t=self.fixture();before=dict(run._published_outputs)
        for name in ('controls.json','ledger.json'):
            run.write_json(name,{'status':'complete'});t.check()
        self.assertEqual({k:run._published_outputs[k] for k in before},before)
        for name,sha in run._published_outputs.items():self.assertEqual(file_hash(run.directory/'outputs'/name),sha)
    def test_original_and_new_outputs_cannot_mutate_disappear_or_change_registry(self):
        for name in ('binding.json','journal.json','controls.json'):
            for mode in ('bytes','delete','registry','registry_delete','same_bytes_replace'):
                with self.subTest(name=name,mode=mode):
                    _,run,t=self.fixture()
                    if name=='controls.json':run.write_json(name,{'v':3});t.check()
                    target=run.directory/'outputs'/name
                    if mode=='bytes':target.write_text('{}')
                    elif mode=='delete':target.unlink()
                    elif mode=='registry':run._published_outputs[name]='0'*64
                    elif mode=='registry_delete':del run._published_outputs[name]
                    else:
                        raw=target.read_bytes();replacement=target.with_name('replacement');replacement.write_bytes(raw);replacement.replace(target)
                    with self.assertRaises((ValueError,OSError)):t.check()
    def test_partial_unknown_link_and_oversized_outputs_refuse(self):
        for mode in ('disk_only','registry_only','foreign','broken_link','pending','oversized'):
            with self.subTest(mode=mode):
                _,run,t=self.fixture();out=run.directory/'outputs'
                if mode=='disk_only':(out/'controls.json').write_text('{}')
                elif mode=='registry_only':run._published_outputs['controls.json']='0'*64
                elif mode=='foreign':(out/'foreign.json').write_text('{}');run._published_outputs['foreign.json']=file_hash(out/'foreign.json')
                elif mode=='broken_link':(out/'controls.json').symlink_to('missing');run._published_outputs['controls.json']='0'*64
                elif mode=='pending':(out/'.pending-controls').write_text('{}')
                else:run.write_json('controls.json',{'v':'x'*2048})
                with self.assertRaises((ValueError,OSError)):t.check()
    def test_unadmitted_object_and_invalid_cap_refuse(self):
        m=api()
        with self.assertRaises(ValueError):m.Outputs(object(),{},max_bytes=1024)
        _,run,_=self.fixture()
        for cap in (0,True,-1):
            with self.assertRaises(ValueError):m.Outputs(run,dict(run._published_outputs),max_bytes=cap)
    def test_baseline_cannot_be_omitted_or_rebound(self):
        m,run,_=self.fixture()
        for baseline in ({},{'binding.json':'0'*64}):
            with self.assertRaises(ValueError):m.Outputs(run,baseline,max_bytes=1024)
    def test_observer_waits_for_actual_writer_registry_publication(self):
        _,run,t=self.fixture();entered=threading.Event();release=threading.Event();attempted=threading.Event();done=threading.Event();errors=[]
        original_write=lifecycle._immutable;original_lock=lifecycle._lock
        def paused(path,value):
            result=original_write(path,value)
            if path.name=='controls.json':entered.set();self.assertTrue(release.wait(5))
            return result
        def locked(root):
            if threading.current_thread().name=='observer':attempted.set()
            return original_lock(root)
        def writer():
            try:run.write_json('controls.json',{'v':1})
            except BaseException as e:errors.append(e)
        def observer():
            try:t.check()
            except BaseException as e:errors.append(e)
            finally:done.set()
        with patch.object(lifecycle,'_immutable',side_effect=paused),patch.object(lifecycle,'_lock',side_effect=locked):
            w=threading.Thread(target=writer,name='writer');r=threading.Thread(target=observer,name='observer')
            w.start()
            try:
                self.assertTrue(entered.wait(5));r.start();self.assertTrue(attempted.wait(5));self.assertFalse(done.wait(.05))
            finally:
                release.set();w.join(5)
                if r.ident is not None:r.join(5)
            self.assertFalse(w.is_alive());self.assertFalse(r.is_alive());self.assertEqual(errors,[])
        t.check()

if __name__=='__main__':unittest.main(verbosity=2)
