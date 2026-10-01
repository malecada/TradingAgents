"""New admitted synthetic consumer; prior producer remains read-only and closed."""
import copy
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from tests.research.test_lifecycle import registered,commit,git
from tradingagents.research.lifecycle import ResearchRun,_immutable
from tradingagents.research.onchain_replication import native_reuse as reuse,native_producer,job,job_payload,resources,registered_features
from tradingagents.research.onchain_replication.environment import inventory
from tradingagents.research.onchain_replication.provenance import canonical_bytes,file_hash

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
OLD=ROOT/'research_artifacts/native-guarded-synthetic/attempt01'

def prepare(root):
    root,spec,_=registered.__wrapped__(Path(root));exp=spec['experiments']['example-a']
    claim=json.loads((OLD/'research_runs/example-a/claim.json').read_text());oldfiles=claim['experiment']['source_files']
    sources=reuse.required_sources()|(set(oldfiles)-{'engine.py'})
    for name in sorted(sources|{'uv.lock'}):
        p=root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,p)
        if name!='uv.lock':exp['source_files'][name]=file_hash(p)
    git(root,'add','--','tradingagents','research','uv.lock')
    def inp(name,value):
        path=root/(name+'.json');path.write_bytes(canonical_bytes(value))
        exp['inputs'][name]={'path':path.name,'sha256':file_hash(path),'dataset':'sample'}
    base=OLD/job.PREFIX/'runs/example-a';seal=next((OLD/'research_artifacts/onchain_representation_seals').glob('*/*/complete.json'))
    history={'experiment':'example-a','source':claim['source'],'claim_sha256':file_hash(OLD/'research_runs/example-a/claim.json'),
        'terminal_sha256':file_hash(OLD/'research_runs/example-a/complete.json'),'guard_sha256':file_hash(base/'guard/final.json'),'observer_sha256':file_hash(base/'observer.json')}
    limits={'max_metadata_bytes':2097152,'max_total_bytes':33554432,'max_records':256,'max_dictionary_bytes':2097152,
        'max_source_files':512,'max_source_file_bytes':2097152,'max_source_bytes':33554432,'max_inventory_entries':2000}
    inp('reuse_reference',{'schema_version':1,'historical_root':str(OLD),'history':history,'seal':{'path':str(seal),'sha256':file_hash(seal)},'limits':limits})
    oldlibs=set(oldfiles)-{'engine.py'}
    inp('source_transition',{'schema_version':1,'replacements':{n:{'before':oldfiles[n],'after':exp['source_files'][n]} for n in oldlibs if oldfiles[n]!=exp['source_files'][n]},
        'additions':{n:exp['source_files'][n] for n in sources-oldlibs}})
    for name in ('population','example_binding','batch_plan','native_batch'):inp(name,json.loads((OLD/(name+'.json')).read_text()))
    descriptor=json.loads((OLD/'plan.json').read_text())['producers']['p']['descriptor']
    route={'operation':'reuse','native_backend':reuse.BACKEND,'reuse_input':'reuse_reference','source_transition_input':'source_transition',
        'native_feature_batch_input':'native_batch','population':'whole','descriptor':descriptor,'binding_output':'binding.json'}
    policy={'memory_max_bytes':3*resources.GIB,'memory_high_bytes':2*resources.GIB,'reserve_bytes':3*resources.GIB,
        'start_reserve_bytes':6*resources.GIB,'disk_floor_bytes':10*resources.GIB,'disk_paths':[str(root),str(OLD)],'wall_seconds':900}
    execution={'schema_version':1,'kind':'fit','environment_input':'environment','resources':policy,
        'payload':{'batch_plan_input':'batch_plan','population_inputs':{'whole':'population'},'representation_jobs':{'r':route}}}
    inp('execution_job',execution);inp('environment',inventory(root,include_torch=True))
    exp['cells']=['sum','count'];exp['outputs']=['binding.json','feature_failure.json','ledger.json','controls.json']
    exp['question']='Synthetic guarded consumer of closed native features, no producer replay or financial outcomes.'
    source=commit(root,spec)
    return root,spec,source,execution

class Tests(unittest.TestCase):
    def fixture(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        root,spec,source,execution=prepare(temp.name)
        run=ResearchRun.start(root=root,registration='registration.json',experiment='example-a',source=source)
        self.addCleanup(lambda:run.fail('synthetic consumer fixture closed') if not any((run.directory/n).exists() for n in ('complete.json','failed.json')) else None)
        base=root/job.PREFIX/'runs/example-a';base.mkdir(parents=True)
        owner={'experiment':'example-a','source_commit':source,'supervisor_pid':os.getpid(),'nonce':'reuse-synthetic',
            'monitor_pid':os.getpid(),'monitor_start_ticks':Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19]}
        _immutable(base/'owner.json',owner)
        guard=patch.object(resources,'assert_guarded_worker',return_value={**execution['resources'],'owner_identity':owner,'monitor_pid':os.getpid()})
        mock=guard.start();self.addCleanup(guard.stop)
        examples,scaler=job_payload.population_from_record(json.loads(run.read_input('population')))
        return run,execution,examples,scaler,mock
    def test_actual_consumer_repeated_batches_and_guard_loss(self):
        run,execution,examples,scaler,guard=self.fixture();route=execution['payload']['representation_jobs']['r']
        with patch.object(native_producer,'produce',side_effect=AssertionError('old producer called')):
            prepared=reuse.prepare(run,'r',route,examples,scaler)
        self.assertEqual(prepared.features.verified_hashes(),prepared.binding['feature_hashes'])
        import gc
        for _ in range(2):
            batch=prepared.features.load_batch(prepared.features)
            self.assertEqual(len(batch),2);self.assertTrue(all(tuple(v['mcm'].shape)==(2,2) for v in batch.values()))
            del batch;gc.collect()
        guard.side_effect=ValueError('guard lost')
        with self.assertRaisesRegex(ValueError,'guard lost'):prepared.features.load_batch(prepared.features)
    def test_source_transition_cannot_waive_numerical_changes(self):
        run,execution,examples,scaler,_=self.fixture()
        oldclaim=json.loads((OLD/'research_runs/example-a/claim.json').read_text())
        transition=json.loads(run.read_input('source_transition'));transition['replacements']['tradingagents/research/onchain_replication/dictionary.py']={'before':'0'*64,'after':'1'*64}
        limits=json.loads(run.read_input('reuse_reference'))['limits']
        with self.assertRaisesRegex(ValueError,'unapproved numerical source'):reuse._sources(run,OLD,oldclaim,transition,limits)
    def test_declared_inventory_and_broken_failure_marker(self):
        # Isolated counterexamples; the actual historical producer stays immutable.
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);artifacts=root/'research_artifacts';journal=artifacts/'journal'
            owner={'experiment':'x','workflow_identity':'w','journal_directory':str(journal)}
            seal={'owner':owner,'feature_terminal':'feature','publication':'publication'}
            values={'feature':{'events':[]},'publication':{'closure':{'graphs':{}}}}
            directories=[root/'research_runs/x/outputs',journal]+[artifacts/k/'w/x' for k in
                ('onchain_representation_seals','onchain_representation_publications','onchain_dictionary_workflows')]
            for d in directories:d.mkdir(parents=True)
            for name in ('owner.json','start.json','claim.json','complete.json'):(journal/name).touch()
            for d in directories[2:]:
                for name in ('start.json','complete.json'):(d/name).touch()
            previous={'terminal':{'output_sha256':{}}}
            foreign=journal/'foreign.json';foreign.touch()
            with self.assertRaisesRegex(ValueError,'foreign historical output'):
                reuse._historical_lease(root,previous,seal,values.__getitem__,{},100)
            foreign.unlink()
            lease=reuse._historical_lease(root,previous,seal,values.__getitem__,{},100)
            marker=root/'research_runs/x/failed.json';marker.symlink_to('missing-target')
            with self.assertRaisesRegex(ValueError,'historical lifecycle conflict'):lease()
    def test_normal_executor_reuses_features_for_both_fits(self):
        run,execution,examples,scaler,_=self.fixture()
        with (patch.object(native_producer,'produce',side_effect=AssertionError('producer replay')),
              patch.object(registered_features,'reuse_registered_features',side_effect=AssertionError('generic reconstruction'))):
            rows,controls=job_payload.execute_fit_payload(run,execution['payload'])
        self.assertEqual([row['status'] for row in rows],['complete','complete'],rows)
        self.assertEqual(set(run._published_outputs),set(run.admission.experiment['outputs']))
        result=run.finish([{'id':r['id'],'status':'complete'} for r in rows]);self.assertEqual(result['status'],'complete')
        print('NATIVE REUSE BOTH FITS COMPLETE',flush=True)
if __name__=='__main__':unittest.main(verbosity=2)
