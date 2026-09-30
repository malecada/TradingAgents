"""Real synthetic ResearchRun ancestry; only OS death predicates are mocked."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tests.research.test_lifecycle import registered, commit, git
from tradingagents.research.lifecycle import ResearchRun, _immutable
from tradingagents.research.onchain_replication.cache import cache_key
from tradingagents.research.onchain_replication.feature_journal import FeatureJournal
from tradingagents.research.onchain_replication.provenance import canonical_bytes, file_hash

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
SELF=str((HERE/'ancestry.py').relative_to(ROOT))
DEATH=str((HERE.parent/'pair-death-2026-09-30/death.py').relative_to(ROOT))


def api():
    assert (HERE/'ancestry.py').is_file(), 'registered failed ancestry component missing'
    spec=importlib.util.spec_from_file_location('candidate_ancestry',HERE/'ancestry.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def input_fault(name,transform):
    def decorate(function):
        function.input_fault=(name,transform);return function
    return decorate


class AncestryTests(unittest.TestCase):
    def setUp(self):
        self.m=api(); self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root,self.spec,_=registered.__wrapped__(Path(self.tmp.name))
        self.spec['families']['family-a']['attempt_budget']=3
        self.template=copy.deepcopy(self.spec['experiments']['example-a'])
        for name in (SELF,DEATH):
            target=self.root/name;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/name,target)
            self.template['source_files'][name]=file_hash(target)
        git(self.root,'add','--',SELF,DEATH)
        self.descriptor={'arm':'proposed','required_graphs':['a'*64],
                         'pair_execution':{'backend':'synthetic-fixed-backend','policy_sha256':'b'*64}}
        self.identity=cache_key(self.descriptor)
        self.work=self.root/'research_artifacts/onchain_representations'/self.identity
        self.proofs={};self.journals={};self.owners={};self.runs={}
        self.new_run('example-a',None,None)
        self.fail('example-a',None)
        self.new_run('example-b','example-a','example-a')
        self.fail('example-b','example-a')
        if self._testMethodName=='test_foreign_parent_path_refused_before_read':
            self.foreign=self.root/'unrelated/example-a/failed.json'
            self.foreign.parent.mkdir(parents=True)
            self.foreign.write_bytes(self.journals['example-a'].read_bytes())
            for path in [self.journals['example-b'],self.work/'example-b/start.json']:
                value=json.loads(path.read_bytes());value['parent']['path']=str(self.foreign)
                path.write_bytes(canonical_bytes(value))
        if self._testMethodName=='test_registered_historical_parent_cannot_be_erased':
            for path in [self.journals['example-b'],self.work/'example-b/start.json']:
                self.rewrite(path,parent=None)
            (self.work/'example-a').rename(self.root/'retained-a')
        self.new_run('example-c','example-b','example-b')
        self.current=self.runs['example-c']
        self.os_patches=[patch.object(self.m.death,'boot_id',return_value='synthetic-boot'),
                         patch.object(self.m.death,'same_process_alive',return_value=False),
                         patch.object(self.m.death,'pid_exists',return_value=False),
                         patch.object(self.m.death,'group_populated',return_value=False)]
        self.os_mocks=[p.start() for p in self.os_patches]
        self.addCleanup(patch.stopall)

    def input(self,exp,name,value=None,path=None):
        fault=getattr(getattr(self,self._testMethodName),'input_fault',None)
        if self.name=='example-c' and fault is not None and fault[0]==name:
            value=fault[1](copy.deepcopy(value))
        if path is None:
            path=self.root/(self.name+'-'+name+'.json');path.write_bytes(canonical_bytes(value))
        exp['inputs'][name]={'path':str(path.relative_to(self.root)),'sha256':file_hash(path),'dataset':'sample'}

    def new_run(self,name,parent,ancestor):
        self.name=name;exp=copy.deepcopy(self.template);exp['parent']=parent
        continuation='continuation' if ancestor else None;proof='death_evidence' if ancestor else None
        selected={'operation':'produce','plan_input':'plan','producer':'p','pair_checkpoint_input':'pair_policy',
                  'continuation_input':continuation,'death_input':proof,'descriptor':self.descriptor}
        item={k:v for k,v in selected.items() if k not in ('operation','plan_input','producer')}
        item.update(binding_output='binding.json',journal_output='journal.json')
        self.input(exp,'plan',{'schema_version':2,'producers':{'p':item}})
        self.input(exp,'execution_job',{'schema_version':1,'kind':'fit','payload':{'representation_jobs':{'r':selected}}})
        self.input(exp,'pair_policy',{'synthetic':True})
        # The checker establishes descriptor/ancestry joins, not numerical policy admission.
        if ancestor:
            self.input(exp,'continuation',path=self.journals[ancestor])
            names=[ancestor]+(['example-a'] if ancestor=='example-b' else [])
            self.input(exp,'death_evidence',{'schema_version':1,'ancestors':[{'experiment':n,'proof':self.proofs[n]} for n in names]})
        exp['outputs']+=['binding.json','journal.json']
        self.spec['experiments'][name]=exp
        source=commit(self.root,self.spec)
        self.runs[name]=ResearchRun.start(root=self.root,registration='registration.json',experiment=name,source=source)

    def fail(self,name,ancestor):
        run=self.runs[name]
        owner={'experiment':name,'source_commit':run.admission.source,'producer':'p','workflow_identity':self.identity}
        self.owners[name]=owner
        parent=None if ancestor is None else {'path':str(self.journals[ancestor]),'sha256':file_hash(self.journals[ancestor]),'owner':self.owners[ancestor]}
        journal=FeatureJournal(self.work/name,owner,required_graphs=self.descriptor['required_graphs'],parent=parent)
        _immutable(journal.directory/'claim.json',{'owner':owner,'descriptor':self.descriptor,'plan_input':'plan',
            'binding_output':'binding.json','registration_sha256':run.admission.registration_sha256,
            'pair_checkpoint_input':'pair_policy','pair_checkpoint_policy_sha256':run.admission.inputs['pair_policy']['sha256']})
        self.journals[name]=journal.seal('failed',reason='synthetic interruption')
        run.fail('synthetic interruption')
        base=self.root/self.m.death.PREFIX/name;(base/'guard').mkdir(parents=True)
        files={}
        def put(key,path,value=None):
            if value is not None:path.write_bytes(canonical_bytes(value))
            files[key]={'path':str(path.relative_to(self.root)),'sha256':file_hash(path)}
        put('claim',run.directory/'claim.json');put('failed',run.directory/'failed.json')
        guard_owner={'experiment':name,'source_commit':run.admission.source,'supervisor_pid':101,'nonce':name,'monitor_pid':102,'monitor_start_ticks':'123'}
        put('owner',base/'owner.json',guard_owner)
        put('launch',base/'launch.json',{k:v for k,v in guard_owner.items() if k not in ('monitor_pid','monitor_start_ticks')})
        live={'owner_identity':guard_owner,'monitor_pid':102,'boot_id':'synthetic-boot',
            'command':[str(self.root/'.venv/bin/python'),'-B','-m',self.m.death.MODULE,'--mode','worker','--root',str(self.root),'--registration','registration.json','--experiment',name,'--source',run.admission.source],
            'cgroup':'/sys/fs/cgroup/user.slice/onchain-replication-synthetic.service','unit':'onchain-replication-synthetic.service','phase':'running'}
        put('live',base/'guard/live.json',live)
        put('death',base/'guard/observer-death.json',{**live,'phase':'failed','cleanup_verified':True,'live_sha256':files['live']['sha256']})
        put('cells',base/'postmortem-cells.json',[]);put('journals',base/'unsealed-journals.json',[])
        put('observer',base/'observer.json',{'status':'failed','owner_sha256':files['owner']['sha256'],
            'terminal_sha256':files['failed']['sha256'],'cgroup_empty':True,'cell_ledger_sha256':files['cells']['sha256'],
            'unsealed_journals':0,'evidence_sha256':{str((self.root/v['path']).relative_to(base)):v['sha256'] for k,v in files.items() if k in ('launch','live','death','cells','journals')}})
        self.proofs[name]=files

    def verify(self,**kwargs):
        args=dict(representation='r',plan_input='plan',producer='p',policy_input='pair_policy',
                  continuation_input='continuation',death_input='death_evidence')
        args.update(kwargs);return self.m.verify(self.current,**args)

    def rewrite(self,path,**changes):
        value=json.loads(path.read_bytes());value.update(changes);path.write_bytes(canonical_bytes(value))

    def test_real_failed_chain_joins_current_admitted_successor_without_writes(self):
        before={str(p):file_hash(p) for p in self.root.rglob('*') if p.is_file() and '.git' not in p.parts}
        result=self.verify()
        self.assertEqual([x['experiment'] for x in result['ancestors']],['example-b','example-a'])
        self.assertEqual(result['experiment'],'example-c')
        self.assertFalse(result['continuation_admitted']);self.assertFalse(result['arrays_read'])
        self.assertFalse(result['numerical_compatibility_verified'])
        self.assertFalse((self.work/'example-c').exists())
        self.assertEqual(before,{str(p):file_hash(p) for p in self.root.rglob('*') if p.is_file() and '.git' not in p.parts})

    def test_fake_run_refused(self):
        self.current=object()
        with self.assertRaises(ValueError):self.verify()

    def test_terminal_current_run_refused(self):
        self.current.fail('synthetic')
        with self.assertRaises(ValueError):self.verify()

    def test_unregistered_routing_refused(self):
        for key in ['representation','plan_input','producer','policy_input','continuation_input','death_input']:
            with self.subTest(key=key),self.assertRaises(ValueError):self.verify(**{key:'foreign'})

    def test_live_ancestor_monitor_refused(self):
        self.os_mocks[1].return_value=True
        with self.assertRaises(ValueError):self.verify()

    def test_older_ancestor_live_cannot_hide_behind_dead_parent(self):
        self.os_mocks[1].side_effect=[False,False,True]
        with self.assertRaises(ValueError):self.verify()

    def test_current_journal_must_not_exist_before_ancestry_check(self):
        (self.work/'example-c').mkdir()
        with self.assertRaises(ValueError):self.verify()

    def test_foreign_sibling_refused(self):
        (self.work/'omitted-attempt').mkdir()
        with self.assertRaises(ValueError):self.verify()

    def test_completed_representation_refused(self):
        (self.work/'example-a/complete.json').write_text('{}')
        with self.assertRaises(ValueError):self.verify()

    def test_changed_parent_journal_refused(self):
        self.rewrite(self.journals['example-a'],reason='changed')
        with self.assertRaises(ValueError):self.verify()

    def test_changed_historical_representation_claim_refused(self):
        self.rewrite(self.work/'example-a/claim.json',descriptor={'foreign':True})
        with self.assertRaises(ValueError):self.verify()

    def test_changed_historical_lifecycle_claim_refused(self):
        self.rewrite(self.runs['example-a'].directory/'claim.json',source='f'*40)
        with self.assertRaises(ValueError):self.verify()

    def test_historical_symlink_refused(self):
        path=self.work/'example-a/owner.json';other=self.root/'foreign-owner.json'
        path.rename(other);path.symlink_to(other)
        with self.assertRaises(ValueError):self.verify()

    def test_bound_death_input_drift_refused(self):
        path=self.root/self.current.admission.inputs['death_evidence']['path'];path.write_text('{}')
        with self.assertRaises(ValueError):self.verify()

    def test_source_drift_refused(self):
        (self.root/SELF).write_text('# drift\n')
        with self.assertRaises(ValueError):self.verify()

    def test_sibling_appearing_during_death_check_refused(self):
        def mutation(*args):
            (self.work/'late-sibling').mkdir(exist_ok=True);return False
        self.os_mocks[1].side_effect=mutation
        with self.assertRaises(ValueError):self.verify()

    def test_historical_claim_changing_during_death_check_refused(self):
        def mutation(*args):
            self.rewrite(self.work/'example-b/claim.json',descriptor={'foreign':True});return False
        self.os_mocks[1].side_effect=mutation
        with self.assertRaises(ValueError):self.verify()

    @input_fault('death_evidence',lambda d:{**d,'ancestors':d['ancestors'][:1]})
    def test_registered_omitted_older_proof_refused(self):
        with self.assertRaises(ValueError):self.verify()

    @input_fault('death_evidence',lambda d:{**d,'ancestors':list(reversed(d['ancestors']))})
    def test_registered_reversed_ancestry_refused(self):
        with self.assertRaises(ValueError):self.verify()

    @input_fault('death_evidence',lambda d:{**d,'ancestors':[d['ancestors'][0]]*2})
    def test_registered_duplicate_ancestry_refused(self):
        with self.assertRaises(ValueError):self.verify()

    @input_fault('death_evidence',lambda d:{**d,'schema_version':True})
    def test_registered_boolean_schema_refused(self):
        with self.assertRaises(ValueError):self.verify()

    @input_fault('death_evidence',lambda d:{**d,'ancestors':d['ancestors']*5})
    def test_registered_excessive_depth_refused(self):
        with self.assertRaises(ValueError):self.verify()

    @input_fault('pair_policy',lambda d:{'synthetic':'changed-successor-policy'})
    def test_registered_policy_change_refused(self):
        with self.assertRaises(ValueError):self.verify()

    def test_foreign_parent_path_refused_before_read(self):
        original=self.m._read
        def guarded(root,path,*args):
            self.assertNotEqual(path,self.foreign,'foreign parent metadata was opened')
            return original(root,path,*args)
        with patch.object(self.m,'_read',side_effect=guarded),self.assertRaises(ValueError):self.verify()

    def test_earlier_parent_completing_during_later_death_check_refused(self):
        calls=0
        def mutation(*args):
            nonlocal calls
            calls+=1
            if calls==3:(self.runs['example-b'].directory/'complete.json').write_text('{}')
            return False
        self.os_mocks[1].side_effect=mutation
        with self.assertRaises(ValueError):self.verify()

    def test_earlier_final_appearing_during_later_death_check_refused(self):
        calls=0
        def mutation(*args):
            nonlocal calls
            calls+=1
            if calls==3:
                path=self.root/self.m.death.PREFIX/'example-b/guard/final.json';path.write_text('{}')
            return False
        self.os_mocks[1].side_effect=mutation
        with self.assertRaises(ValueError):self.verify()

    def test_liveness_is_rechecked_for_entire_chain(self):
        self.os_mocks[1].side_effect=[False]*4+[True]
        with self.assertRaises(ValueError):self.verify()

    @input_fault('death_evidence',lambda d:{**d,'ancestors':d['ancestors'][:1]})
    def test_registered_historical_parent_cannot_be_erased(self):
        with self.assertRaises(ValueError):self.verify()

if __name__=='__main__':unittest.main()
