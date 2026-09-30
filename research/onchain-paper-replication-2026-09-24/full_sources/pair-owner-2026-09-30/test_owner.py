"""Synthetic real ResearchRun admission; only the kernel guard boundary is mocked."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from tests.research.test_lifecycle import registered, commit, git
from tradingagents.research.lifecycle import ResearchRun, _immutable
from tradingagents.research.onchain_replication import job, matching_pair, resources
from tradingagents.research.onchain_replication.environment import inventory
from tradingagents.research.onchain_replication.feature_journal import FeatureJournal
from tradingagents.research.onchain_replication.cache import cache_key
from tradingagents.research.onchain_replication.provenance import file_hash, canonical_bytes, digest

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
REL=str((HERE/'owner.py').relative_to(ROOT))

def api():
    assert (HERE/'owner.py').is_file(), 'admitted matching owner component missing'
    spec=importlib.util.spec_from_file_location('candidate_owner',HERE/'owner.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def contract_mutation(section,key,value):
    def decorate(function):
        function.contract_mutation=(section,key,value)
        return function
    return decorate

class OwnershipTests(unittest.TestCase):
    def setUp(self):
        self.module=api()
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root,self.spec,_=registered.__wrapped__(Path(self.temp.name))
        self.exp=self.spec['experiments']['example-a']
        for name in sorted(job.required_sources() | {REL,'uv.lock'}):
            target=self.root/name;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/name,target)
            if name!='uv.lock':self.exp['source_files'][name]=file_hash(target)
        git(self.root,'add','--','tradingagents',REL,'uv.lock')
        self.anchor=commit(self.root,self.spec)
        self.policy={'schema_version':1,'backend':matching_pair.BACKEND,
            'limits':{k:65536 for k in matching_pair.POLICY_FIELDS},
            'numerical_source':{'commit':self.anchor,'files':{n:file_hash(self.root/n) for n in sorted(job.required_sources())}}}
        self.environment=inventory(self.root,include_torch=True)
        self.input('pair_policy',self.policy);self.input('environment',self.environment)
        self.descriptor={'arm':'proposed','required_graphs':['a'*64],
            'pair_execution':{'backend':matching_pair.BACKEND,'policy_sha256':self.exp['inputs']['pair_policy']['sha256']}}
        self.item={'descriptor':self.descriptor,'pair_checkpoint_input':'pair_policy','binding_output':'binding.json','journal_output':'journal.json'}
        self.plan={'schema_version':2,'producers':{'p':self.item}}
        self.input('plan',self.plan)
        self.resources=dict(memory_max_bytes=3*resources.GIB,memory_high_bytes=2*resources.GIB,
            reserve_bytes=3*resources.GIB,start_reserve_bytes=6*resources.GIB,
            disk_floor_bytes=10*resources.GIB,disk_paths=[str(self.root)],wall_seconds=300)
        self.execution={'schema_version':1,'kind':'fit','environment_input':'environment','resources':self.resources,
            'payload':{'representation_jobs':{'r':{'operation':'produce','plan_input':'plan','producer':'p',
                'pair_checkpoint_input':'pair_policy','descriptor':self.descriptor}}}}
        self.input('execution_job',self.execution)
        self.exp['outputs']+=['binding.json','journal.json']
        mutation=getattr(getattr(self,self._testMethodName),'contract_mutation',None)
        if mutation is not None:
            section,key,value=mutation
            getattr(self,section)[key]=value
            self.input('pair_policy',self.policy)
            self.descriptor['pair_execution']['policy_sha256']=self.exp['inputs']['pair_policy']['sha256']
            self.input('plan',self.plan);self.input('execution_job',self.execution)
        self.prepare()

    def input(self,name,value):
        path=self.root/(name+'.json');path.write_bytes(canonical_bytes(value))
        self.exp['inputs'][name]={'path':path.name,'sha256':file_hash(path),'dataset':'sample'}

    def prepare(self):
        self.source=commit(self.root,self.spec)
        self.run=ResearchRun.start(root=self.root,registration='registration.json',experiment='example-a',source=self.source)
        self.identity=cache_key(self.descriptor)
        self.owner={'experiment':'example-a','source_commit':self.source,'producer':'p','workflow_identity':self.identity}
        self.directory=self.root/'research_artifacts/onchain_representations'/self.identity/'example-a'
        self.journal=FeatureJournal(self.directory,self.owner,required_graphs=self.descriptor['required_graphs'])
        self.claim={'owner':self.owner,'descriptor':self.descriptor,'plan_input':'plan','binding_output':'binding.json',
            'registration_sha256':self.run.admission.registration_sha256,
            'pair_checkpoint_input':'pair_policy','pair_checkpoint_policy_sha256':self.exp['inputs']['pair_policy']['sha256']}
        _immutable(self.directory/'claim.json',self.claim)
        self.base=self.root/job.PREFIX/'runs/example-a';self.base.mkdir(parents=True)
        self.launch={'experiment':'example-a','source_commit':self.source,'supervisor_pid':os.getpid(),'nonce':'synthetic'}
        self.guard_owner={**self.launch,'monitor_pid':os.getpid(),'monitor_start_ticks':Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19]}
        _immutable(self.base/'launch.json',self.launch);_immutable(self.base/'owner.json',self.guard_owner)
        self.live={**self.resources,'owner_identity':self.guard_owner,'monitor_pid':os.getpid()}
        self.mock=patch.object(resources,'assert_guarded_worker',return_value=self.live).start()
        self.addCleanup(patch.stopall)

    def bind(self,**kw):
        args=dict(representation='r',plan_input='plan',producer='p',policy_input='pair_policy',journal_directory=self.directory)
        args.update(kw);return self.module.bind(self.run,**args)

    def rewrite(self,path,value):path.write_bytes(canonical_bytes(value))

    def test_actual_claim_owner_and_old_numerical_anchor_are_distinct(self):
        bound=self.bind();bound.check()
        self.assertNotEqual(self.anchor,self.source)
        self.assertEqual(bound.record['source_commit'],self.source)
        self.assertEqual(bound.record['claim_sha256'],self.run._claim_sha256)
        self.assertEqual(bound.context['source_commit'],self.anchor)
        self.assertEqual(bound.context['namespace'],self.identity)
        self.assertEqual(bound.context['runtime_hash'],digest(canonical_bytes(self.environment)))
        self.assertIn(self.source,self.mock.call_args.args[1])
        with self.assertRaises(TypeError):bound.record['source_commit']='f'*40
        self.assertFalse((self.directory/'pairs').exists())

    def test_unadmitted_run_refused(self):
        with self.assertRaises(ValueError):self.module.bind(object(),representation='r',plan_input='plan',producer='p',policy_input='pair_policy',journal_directory=self.directory)

    def test_wrong_producer_policy_or_representation_refused(self):
        for kw in ({'producer':'other'},{'policy_input':'sample'},{'representation':'other'},{'plan_input':'sample'}):
            with self.subTest(kw=kw),self.assertRaises(ValueError):self.bind(**kw)

    def test_terminal_claim_refused_on_recheck(self):
        bound=self.bind();self.run.fail('synthetic closure')
        with self.assertRaises(ValueError):bound.check()

    def test_source_drift_refused(self):
        bound=self.bind();(self.root/'engine.py').write_text('# changed\n')
        with self.assertRaises(ValueError):bound.check()

    def test_input_drift_refused(self):
        bound=self.bind();(self.root/'pair_policy.json').write_text('{}')
        with self.assertRaises(ValueError):bound.check()

    def test_changed_journal_claim_refused(self):
        bound=self.bind();self.claim['owner']={**self.owner,'producer':'foreign'}
        self.rewrite(self.directory/'claim.json',self.claim)
        with self.assertRaises(ValueError):bound.check()

    def test_terminal_journal_refused(self):
        bound=self.bind();self.journal.seal('failed',reason='synthetic')
        with self.assertRaises(ValueError):bound.check()

    def test_wrong_directory_refused_before_guard(self):
        with self.assertRaises(ValueError):self.bind(journal_directory=self.root)
        self.mock.assert_not_called()

    def test_foreign_guard_owner_or_policy_refused(self):
        for key,value in [('owner_identity',{**self.guard_owner,'source_commit':'f'*40}),('wall_seconds',301)]:
            with self.subTest(key=key):
                self.mock.return_value={**self.live,key:value}
                with self.assertRaises(ValueError):self.bind()

    def test_guard_expiry_and_monitor_death_refused(self):
        bound=self.bind();self.mock.side_effect=ValueError('expired guard')
        with self.assertRaises(ValueError):bound.check()
        self.mock.side_effect=None
        with patch.object(job,'same_process_alive',return_value=False),self.assertRaises(ValueError):bound.check()

    def test_changed_guard_metadata_refused(self):
        bound=self.bind();self.rewrite(self.base/'owner.json',{**self.guard_owner,'nonce':'other'})
        with self.assertRaises(ValueError):bound.check()

    def test_symlink_journal_metadata_refused(self):
        raw=(self.directory/'owner.json').read_bytes();(self.root/'foreign.json').write_bytes(raw)
        (self.directory/'owner.json').unlink();(self.directory/'owner.json').symlink_to(self.root/'foreign.json')
        with self.assertRaises(ValueError):self.bind()

    def test_foreign_sibling_after_binding_refused(self):
        bound=self.bind();(self.directory.parent/'unadmitted-owner').mkdir()
        with self.assertRaises(ValueError):bound.lease()

    def test_failed_parent_not_silently_admitted(self):
        start=json.loads((self.directory/'start.json').read_bytes())
        start['parent']={'path':'unadmitted-parent','sha256':'f'*64}
        self.rewrite(self.directory/'start.json',start)
        with self.assertRaises(ValueError):self.bind()

    def test_numerical_anchor_drift_is_not_execution_commit_compatibility(self):
        prior=json.loads(json.dumps(self.policy['numerical_source']))
        prior['files']['tradingagents/__init__.py']='f'*64
        with self.assertRaises(ValueError):self.module._source(self.run,prior)

    def test_numerical_anchor_incomplete_closure_refused(self):
        prior=json.loads(json.dumps(self.policy['numerical_source']))
        prior['files'].pop('tradingagents/__init__.py')
        with self.assertRaises(ValueError):self.module._source(self.run,prior)

    def test_uncommitted_numerical_anchor_refused(self):
        prior=json.loads(json.dumps(self.policy['numerical_source']))
        prior['commit']='0'*40
        import subprocess
        with self.assertRaises((ValueError,subprocess.CalledProcessError)):
            self.module._source(self.run,prior)

    def test_live_monitor_must_equal_retained_owner_monitor(self):
        self.mock.return_value={**self.live,'monitor_pid':os.getpid()+1}
        with self.assertRaises(ValueError):self.bind()

    @contract_mutation('policy','schema_version',True)
    def test_boolean_policy_version_refused(self):
        with self.assertRaises(ValueError):self.bind()

    @contract_mutation('policy','schema_version',1.0)
    def test_float_policy_version_refused(self):
        with self.assertRaises(ValueError):self.bind()

    @contract_mutation('plan','schema_version',2.0)
    def test_float_plan_version_refused(self):
        with self.assertRaises(ValueError):self.bind()

    def test_boolean_journal_version_refused(self):
        start=json.loads((self.directory/'start.json').read_bytes());start['schema_version']=True
        self.rewrite(self.directory/'start.json',start)
        with self.assertRaises(ValueError):self.bind()

    @contract_mutation('execution','schema_version',True)
    def test_boolean_execution_version_refused(self):
        with self.assertRaises(ValueError):self.bind()

if __name__=='__main__':unittest.main()
