"""Tiny actual registered owner joins; guard/death observations are synthetic."""
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

from tests.research.onchain_replication import test_matching_successor as successor
from tests.research.onchain_replication import test_matching_owner as first
from tradingagents.research.onchain_replication.provenance import canonical_bytes, file_hash, thaw
from tradingagents.research.onchain_replication.cache import cache_key

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
rf=load('route_fixture',HERE.parent/'pair-workload-route-2026-09-30/test_route.py')
def api():
    assert (HERE/'ownership.py').is_file(),'registered pair owner route missing'
    return load('pair_ownership_candidate',HERE/'ownership.py')

def admit(m,f,run=None,directory=None,**kw):
    return m.route.admit(run or f.run,representation='r',plan_input='plan',producer='p',policy_input='pair_policy',
        control_input='pair_workload',journal_directory=directory or f.directory,
        graphs=f.graphs,examples=f.examples,fold=f.fold,seed=11,configs=f.configs,**kw)

class Parent(rf.Fixture):
    __test__=False
    close_pair=True;pending=False;published=False
    def prepare(self):
        for path in (HERE/'ownership.py',HERE/'journal.py'):
            name=str(path.relative_to(ROOT));target=self.root/name;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(path,target);self.exp['source_files'][name]=file_hash(target);first.git(self.root,'add','--',name)
        self.item.update(continuation_input=None,death_input=None,pair_journal_parent_input=None)
        self.execution['payload']['representation_jobs']['r'].update(continuation_input=None,death_input=None,pair_journal_parent_input=None)
        super().prepare()
        self.workload=admit(self.bridge,self)
        self.owned=self.bridge.open_journal(self.workload)
        if self.pending:
            purpose={'kind':'synthetic-reservation','index':0};target=self.owned.journal.target(purpose)
            self.owned.journal.reserve(purpose,target['path'],'a'*64,1000)
        if self.published:
            # Compact metadata fixture only; deliberately no numerical arrays.
            purpose={'kind':'synthetic-publication','index':0};j=self.owned.journal
            target=j.target(purpose);identity={'fixture':'metadata-only'}
            j.reserve(purpose,target['path'],self.bridge.journal.digest(identity),1000)
            path=Path(target['path']);path.parent.mkdir(parents=True)
            ref=self.bridge.journal.write(path,{'owner':target['artifact_owner'],'identity':identity,
                'parent':target['session_parent'],'kind':'complete'})
            j.publish(ref);self.publication=path
        if self.close_pair:self.pair_terminal=self.owned.seal('failed')

class Child(successor.SuccessorTests):
    __test__=False
    def input(self,name,value):
        parent=self.parent.pair_terminal
        self.exp['inputs']['pair_parent']={'path':str(Path(parent['path']).relative_to(self.root)),
            'sha256':parent['sha256'],'dataset':'sample'}
        if name=='plan':value['producers']['p']['pair_journal_parent_input']='pair_parent'
        if name=='execution_job':value['payload']['representation_jobs']['r']['pair_journal_parent_input']='pair_parent'
        super().input(name,value)

def snapshot(path):return {str(p.relative_to(path)):file_hash(p) for p in path.rglob('*') if p.is_file()}

class Tests(unittest.TestCase):
    def fixture(self,*,child=False,pending=False,published=False):
        self.m=api()
        class Selected(Parent):pass
        Selected.bridge=self.m;Selected.close_pair=child;Selected.pending=pending;Selected.published=published
        if child:
            f=Child('test_actual_successor_binds_new_claim_and_original_numerical_context')
            self.addCleanup(f.doCleanups)
            with patch.object(successor,'_FirstOwner',Selected):f.setUp()
            self.child=f;self.parent=f.parent
        else:
            f=Selected('test_actual_claim_owner_and_old_numerical_anchor_are_distinct')
            self.addCleanup(f.doCleanups);f.setUp();self.parent=f
        return f
    def child_route(self):
        self.child.open()
        return admit(self.m,self.parent,run=self.child.run,directory=self.child.directory,
            continuation_input='continuation',death_input='death_evidence')
    def test_first_owner_is_real_claim_bound_exclusive_and_metadata_charged(self):
        p=self.fixture();owned=p.owned
        certificate=json.loads((owned.journal.directory/'binding.json').read_bytes())
        self.assertEqual(certificate['binding']['claim_sha256'],p.run._claim_sha256)
        self.assertEqual(certificate['binding']['source_commit'],p.source)
        self.assertEqual(owned.journal.owner,cache_key(certificate))
        self.assertGreater(owned.reserved_bytes,owned.journal.reserved_bytes)
        self.assertLessEqual(owned.reserved_bytes,p.control['journal_limits']['max_reserved_bytes'])
        before=snapshot(owned.journal.root)
        with self.assertRaises((ValueError,FileExistsError)):self.m.open_journal(p.workload)
        self.assertEqual(snapshot(owned.journal.root),before)
    def test_actual_failed_parent_child_retains_owner_charge_and_exact_reference(self):
        self.fixture(child=True);p=self.parent;before=snapshot(p.owned.journal.root)
        route=self.child_route();owned=self.m.open_journal(route,parent_input='pair_parent');owned.lease()
        self.assertEqual(owned.journal.start['path'],str(owned.journal.directory/'start.json'))
        start=json.loads(Path(owned.journal.start['path']).read_bytes())
        self.assertEqual(start['parent'],p.pair_terminal)
        self.assertNotEqual(owned.journal.owner,p.owned.journal.owner)
        self.assertGreater(owned.reserved_bytes,p.owned.reserved_bytes)
        self.assertEqual(owned.journal.reservations,p.owned.journal.reservations)
        for name,sha in before.items():self.assertEqual(file_hash(p.owned.journal.root/name),sha)
    def test_forged_historical_binding_refused_before_child_pair_directory(self):
        self.fixture(child=True);route=self.child_route();p=self.parent
        path=p.owned.journal.directory/'binding.json';value=json.loads(path.read_bytes())
        value['binding']['source_commit']='f'*40;path.write_bytes(canonical_bytes(value))
        with self.assertRaises(ValueError):self.m.open_journal(route,parent_input='pair_parent')
        self.assertFalse((p.owned.journal.root/'example-b').exists())
    def test_foreign_pair_owner_or_session_refused_before_child_allocation(self):
        for suffix in ('foreign-owner','pairs/foreign-session'):
            with self.subTest(suffix=suffix):
                f=self.fixture(child=True);route=self.child_route();p=self.parent
                (p.owned.journal.root/suffix).mkdir()
                with self.assertRaises(ValueError):self.m.open_journal(route,parent_input='pair_parent')
                self.assertFalse((p.owned.journal.root/'example-b').exists());f.doCleanups()
    def test_pending_parent_reservation_requires_reconciliation(self):
        self.fixture(child=True,pending=True);route=self.child_route();root=self.parent.owned.journal.root
        before=snapshot(root)
        with self.assertRaisesRegex(ValueError,'reconciliation'):self.m.open_journal(route,parent_input='pair_parent')
        self.assertFalse((root/'example-b').exists());self.assertEqual(before,snapshot(root))
    def test_changed_certificate_and_foreign_owner_refused_on_live_lease(self):
        p=self.fixture();certificate=p.owned.journal.directory/'binding.json'
        certificate.write_text('{}')
        with self.assertRaises(ValueError):p.owned.lease()
    def test_omitted_parent_route_refused_before_child_allocation(self):
        self.fixture(child=True);route=self.child_route()
        with self.assertRaises(ValueError):self.m.open_journal(route)
        self.assertFalse((self.parent.owned.journal.root/'example-b').exists())
    def test_parent_revives_after_child_open_and_blocks_further_work(self):
        self.fixture(child=True);route=self.child_route();owned=self.m.open_journal(route,parent_input='pair_parent')
        before=snapshot(owned.journal.root);self.child.mocks[3].return_value=True
        with self.assertRaises(ValueError):owned.lease()
        self.assertEqual(before,snapshot(owned.journal.root))

    def test_historical_inventory_changes_are_refused_on_lease(self):
        self.fixture(child=True);owned=self.m.open_journal(self.child_route(),parent_input='pair_parent')
        directory=self.parent.owned.journal.directory
        for name,symlink in [('complete.json',False),('complete.json',True),('event-999999.json',False)]:
            with self.subTest(name=name,symlink=symlink):
                path=directory/name
                if symlink:path.symlink_to(directory/'absent')
                else:path.write_text('{}')
                try:
                    with self.assertRaises(ValueError):owned.lease()
                finally:path.unlink()
    def test_inherited_publication_drift_and_session_loss_are_refused(self):
        self.fixture(child=True,published=True)
        owned=self.m.open_journal(self.child_route(),parent_input='pair_parent')
        path=self.parent.publication;raw=path.read_bytes();path.write_text('{}')
        try:
            with self.assertRaises(ValueError):owned.lease()
        finally:path.write_bytes(raw)
        session=path.parent.parent;away=session.parent.parent.parent/'temporarily-outside-pairs'
        session.rename(away)
        try:
            with self.assertRaises((ValueError,FileNotFoundError)):owned.lease()
        finally:away.rename(session)
    def test_guard_expiry_during_locked_reads_prevents_child_creation(self):
        self.fixture(child=True);route=self.child_route();real_lock=self.m._lock
        real_read=self.m.owner.ancestry._read;real_lease=route.lease;flags={'locked':False,'expired':False}
        @contextmanager
        def locked(root):
            with real_lock(root):
                flags['locked']=True
                try:yield
                finally:flags['locked']=False
        def read(*args,**kw):
            result=real_read(*args,**kw)
            if flags['locked']:flags['expired']=True
            return result
        def lease():
            if flags['expired']:raise ValueError('synthetic guard expired')
            return real_lease()
        with patch.object(self.m,'_lock',locked),patch.object(self.m.owner.ancestry,'_read',read),patch.object(route,'lease',lease):
            with self.assertRaises(ValueError):self.m.open_journal(route,parent_input='pair_parent')
        self.assertFalse((self.parent.owned.journal.root/'example-b').exists())
    def test_guard_expiry_during_constructor_replay_prevents_child_creation(self):
        self.fixture(child=True);route=self.child_route();real_init=self.m.journal.Journal.__init__
        real_load=self.m.journal.load;real_lease=route.lease;flags={'creating':False,'expired':False}
        def init(j,*args,**kw):
            flags['creating']=True
            try:return real_init(j,*args,**kw)
            finally:flags['creating']=False
        def load_parent(*args,**kw):
            result=real_load(*args,**kw)
            if flags['creating']:flags['expired']=True
            return result
        def lease():
            if flags['expired']:raise ValueError('synthetic guard expired')
            return real_lease()
        with patch.object(self.m.journal.Journal,'__init__',init),patch.object(self.m.journal,'load',load_parent),patch.object(route,'lease',lease):
            with self.assertRaises(ValueError):self.m.open_journal(route,parent_input='pair_parent')
        self.assertFalse((self.parent.owned.journal.root/'example-b').exists())

    def test_foreign_session_during_constructor_replay_prevents_creation(self):
        self.fixture(child=True);route=self.child_route();real_init=self.m.journal.Journal.__init__
        real_load=self.m.journal.load;flags={'creating':False,'inserted':False}
        def init(j,*args,**kw):
            flags['creating']=True
            try:return real_init(j,*args,**kw)
            finally:flags['creating']=False
        def load_parent(*args,**kw):
            result=real_load(*args,**kw)
            if flags['creating'] and not flags['inserted']:
                (self.parent.owned.journal.root/'pairs'/'foreign-session').mkdir()
                flags['inserted']=True
            return result
        with patch.object(self.m.journal.Journal,'__init__',init),patch.object(self.m.journal,'load',load_parent):
            with self.assertRaises(ValueError):self.m.open_journal(route,parent_input='pair_parent')
        self.assertFalse((self.parent.owned.journal.root/'example-b').exists())

def load_tests(loader,tests,pattern):return loader.loadTestsFromTestCase(Tests)
if __name__=='__main__':unittest.main(verbosity=2)
