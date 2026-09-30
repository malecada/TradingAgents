"""Actual synthetic failed run -> guarded-owner successor, without pair arrays."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tests.research.onchain_replication import test_matching_owner as first
from tests.research.test_lifecycle import commit
from tradingagents.research.lifecycle import ResearchRun
from tradingagents.research.onchain_replication import matching_owner as owner
from tradingagents.research.onchain_replication import matching_death as death
from tradingagents.research.onchain_replication.provenance import canonical_bytes, file_hash


def fault(name,transform):
    def decorate(function):
        function.fault=(name,transform);return function
    return decorate


class _FirstOwner(first.OwnershipTests):
    # This fixture is invoked explicitly; hide it from pytest collection below.
    __test__=False
    def prepare(self):
        self.item.update(continuation_input=None,death_input=None)
        self.execution['payload']['representation_jobs']['r'].update(continuation_input=None,death_input=None)
        self.input('plan',self.plan);self.input('execution_job',self.execution)
        super().prepare()


class SuccessorTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(hasattr(owner,'open_successor'),'guarded successor constructor missing')
        self.parent=_FirstOwner('test_actual_claim_owner_and_old_numerical_anchor_are_distinct')
        self.parent.setUp();self.addCleanup(self.parent.doCleanups)
        p=self.parent;self.root=p.root
        p.bind().lease()
        self.parent_terminal=p.journal.seal('failed',reason='synthetic interruption')
        p.run.fail('synthetic interruption')
        self.proof=self.failed_executor()
        self.exp=copy.deepcopy(p.exp);self.exp['parent']='example-a'
        self.spec=p.spec;self.spec['experiments']['example-b']=self.exp
        self.item=copy.deepcopy(p.item);self.item.update(continuation_input='continuation',death_input='death_evidence')
        self.plan={'schema_version':2,'producers':{'p':self.item}}
        self.execution=copy.deepcopy(p.execution)
        self.execution['payload']['representation_jobs']['r'].update(continuation_input='continuation',death_input='death_evidence')
        self.input('plan',self.plan);self.input('execution_job',self.execution)
        self.input('death_evidence',{'schema_version':1,'ancestors':[{'experiment':'example-a','proof':self.proof}]})
        self.exp['inputs']['continuation']={'path':str(self.parent_terminal.relative_to(self.root)),
                                           'sha256':file_hash(self.parent_terminal),'dataset':'sample'}
        mutation=getattr(getattr(self,self._testMethodName),'fault',None)
        if mutation:
            name,transform=mutation
            old=json.loads((self.root/self.exp['inputs'][name]['path']).read_bytes())
            self.input(name,transform(old))
        self.source=commit(self.root,self.spec)
        self.run=ResearchRun.start(root=self.root,registration='registration.json',experiment='example-b',source=self.source)
        self.directory=p.directory.parent/'example-b'
        self.base=self.root/death.PREFIX/'example-b';self.base.mkdir(parents=True)
        self.launch={**p.launch,'experiment':'example-b','source_commit':self.source,'nonce':'successor'}
        self.guard_owner={**p.guard_owner,**self.launch}
        (self.base/'launch.json').write_bytes(canonical_bytes(self.launch))
        (self.base/'owner.json').write_bytes(canonical_bytes(self.guard_owner))
        self.live={**p.live,'owner_identity':self.guard_owner}
        p.mock.return_value=self.live
        self.mocks=[patch.object(death,'boot_id',return_value='synthetic-boot').start(),
                    patch.object(death,'same_process_alive',return_value=False).start(),
                    patch.object(death,'pid_exists',return_value=False).start(),
                    patch.object(death,'group_populated',return_value=False).start()]
        self.addCleanup(patch.stopall)

    def input(self,name,value):
        path=self.root/('child-'+name+'.json');path.write_bytes(canonical_bytes(value))
        self.exp['inputs'][name]={'path':path.name,'sha256':file_hash(path),'dataset':'sample'}

    def failed_executor(self):
        p=self.parent;base=p.base;(base/'guard').mkdir()
        proof={}
        def put(key,path,value=None):
            if value is not None:path.write_bytes(canonical_bytes(value))
            proof[key]={'path':str(path.relative_to(self.root)),'sha256':file_hash(path)}
        put('claim',p.run.directory/'claim.json');put('failed',p.run.directory/'failed.json')
        put('owner',base/'owner.json');put('launch',base/'launch.json')
        live={**p.live,'boot_id':'synthetic-boot','command':[str(self.root/'.venv/bin/python'),'-B','-m',death.MODULE,
            '--mode','worker','--root',str(self.root),'--registration','registration.json','--experiment','example-a','--source',p.source],
            'cgroup':'/sys/fs/cgroup/user.slice/onchain-replication-synthetic.service','unit':'onchain-replication-synthetic.service','phase':'running'}
        put('live',base/'guard/live.json',live)
        put('death',base/'guard/observer-death.json',{**live,'phase':'failed','cleanup_verified':True,'live_sha256':proof['live']['sha256']})
        put('cells',base/'postmortem-cells.json',[]);put('journals',base/'unsealed-journals.json',[])
        put('observer',base/'observer.json',{'status':'failed','owner_sha256':proof['owner']['sha256'],
            'terminal_sha256':proof['failed']['sha256'],'cgroup_empty':True,'cell_ledger_sha256':proof['cells']['sha256'],
            'unsealed_journals':0,'evidence_sha256':{str((self.root/v['path']).relative_to(base)):v['sha256'] for k,v in proof.items() if k in ('launch','live','death','cells','journals')}})
        return proof

    def open(self):
        return owner.open_successor(self.run,representation='r',plan_input='plan',producer='p',policy_input='pair_policy',
                                    continuation_input='continuation',death_input='death_evidence')

    def test_actual_successor_binds_new_claim_and_original_numerical_context(self):
        before={str(p):file_hash(p) for p in self.parent.directory.rglob('*') if p.is_file()}
        journal,bound=self.open();bound.lease();bound.check()
        self.assertEqual(journal.directory,self.directory)
        self.assertEqual(journal.parent['path'],str(self.parent_terminal))
        self.assertEqual(bound.record['source_commit'],self.source)
        self.assertNotEqual(self.source,self.parent.source)
        self.assertEqual(bound.context['source_commit'],self.parent.anchor)
        self.assertEqual(bound.record['claim_sha256'],self.run._claim_sha256)
        self.assertEqual(before,{str(p):file_hash(p) for p in self.parent.directory.rglob('*') if p.is_file()})
        self.assertFalse((self.directory/'pairs').exists())

    def test_duplicate_successor_cannot_recreate_journal(self):
        self.open();before={str(p):file_hash(p) for p in self.directory.iterdir()}
        with self.assertRaises((ValueError,FileExistsError)):self.open()
        self.assertEqual(before,{str(p):file_hash(p) for p in self.directory.iterdir()})

    def test_foreign_live_guard_refused_before_journal_creation(self):
        self.parent.mock.return_value={**self.live,'owner_identity':self.parent.guard_owner}
        with self.assertRaises(ValueError):self.open()
        self.assertFalse(self.directory.exists())

    def test_dead_current_monitor_refused_before_journal_creation(self):
        with patch.object(owner.job,'same_process_alive',return_value=False),self.assertRaises(ValueError):self.open()
        self.assertFalse(self.directory.exists())

    def test_live_parent_refused_before_journal_creation(self):
        self.mocks[1].return_value=True
        with self.assertRaises(ValueError):self.open()
        self.assertFalse(self.directory.exists())

    @fault('pair_policy',lambda d:{**d,'backend':{'foreign':True}})
    def test_registered_wrong_backend_refused_before_journal_creation(self):
        with self.assertRaises(ValueError):self.open()
        self.assertFalse(self.directory.exists())

    @fault('execution_job',lambda d:{**d,'resources':{**d['resources'],'memory_max_bytes':0}})
    def test_registered_invalid_resource_policy_refused_before_creation(self):
        with self.assertRaises(ValueError):self.open()
        self.assertFalse(self.directory.exists())

    def test_parent_evidence_change_refused_on_lease(self):
        _,bound=self.open();(self.parent.directory/'claim.json').write_text('{}')
        with self.assertRaises(ValueError):bound.lease()

    def test_parent_becoming_live_refused_on_lease(self):
        _,bound=self.open();self.mocks[3].return_value=True
        with self.assertRaises(ValueError):bound.lease()

    def test_current_guard_expiry_refused_on_lease(self):
        _,bound=self.open();self.parent.mock.side_effect=ValueError('expired lease')
        with self.assertRaises(ValueError):bound.lease()

    def test_foreign_sibling_refused_on_lease(self):
        _,bound=self.open();(self.directory.parent/'foreign').mkdir()
        with self.assertRaises(ValueError):bound.lease()

    def test_terminal_child_run_refused_on_lease(self):
        _,bound=self.open();self.run.fail('synthetic')
        with self.assertRaises(ValueError):bound.lease()

    def test_terminal_child_journal_refused_on_lease(self):
        journal,bound=self.open();journal.seal('failed',reason='synthetic')
        with self.assertRaises(ValueError):bound.lease()

    def test_current_source_drift_refused_on_full_check(self):
        _,bound=self.open();(self.root/'engine.py').write_text('# drift\n')
        with self.assertRaises(ValueError):bound.check()

    def test_claim_publication_failure_retains_partial_journal(self):
        real=owner._immutable
        def fail_claim(path,value):
            if path.name=='claim.json':raise OSError('synthetic publication failure')
            return real(path,value)
        with patch.object(owner,'_immutable',side_effect=fail_claim),self.assertRaises(OSError):self.open()
        self.assertTrue((self.directory/'start.json').is_file())
        with self.assertRaises((ValueError,FileExistsError)):self.open()

    def test_current_guard_lost_during_ancestry_refused_before_publication(self):
        real=owner.ancestry.verify
        def expire(*args,**kwargs):
            result=real(*args,**kwargs)
            self.parent.mock.side_effect=ValueError('lease expired during ancestry check')
            return result
        with patch.object(owner.ancestry,'verify',side_effect=expire),self.assertRaises(ValueError):self.open()
        self.assertFalse(self.directory.exists(),'journal published after current guard was lost')


def load_tests(loader,tests,pattern):
    # unittest otherwise discovers inherited tests on the explicitly used fixture.
    return loader.loadTestsFromTestCase(SuccessorTests)
