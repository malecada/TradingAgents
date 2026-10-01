"""Actual fresh-owner job dispatch, synthetic data and mocked kernel guard only."""
import importlib.util
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
from tests.research.onchain_replication import test_matching_owner as first
from tests.research.onchain_replication.test_evaluation import CONFIG
from tests.research.onchain_replication.test_training import CFG
from tests.research.test_lifecycle import commit
from tradingagents.research.lifecycle import ResearchRun,_immutable
from tradingagents.research.onchain_replication import native_producer as native,job,job_payload,resources,registered_features
from tradingagents.research.onchain_replication.contracts import PricePanel
from tradingagents.research.onchain_replication.dataset import fit_scaler
from tradingagents.research.onchain_replication.evaluation import example_binding
from tradingagents.research.onchain_replication.graph_store import save_graph
from tradingagents.research.onchain_replication.neighborhoods import graph_hash
from tradingagents.research.onchain_replication.provenance import file_hash

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('dispatch_configuration_fixture',HERE.parent/'terminal-native-map-2026-10-01/test_prepare.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
class Ready(Exception):
    def __init__(self,owner):self.owner=owner

class Tests(unittest.TestCase):
    def fixture(self):
        fixture=base.Tests('test_actual_terminal_transition_and_native_batches_without_producer_reentry')
        self.addCleanup(fixture.doCleanups)
        original=first.OwnershipTests.input
        def configured(f,name,value):
            if name=='execution_job' and hasattr(f,'examples'):
                e=f.examples;fold=f.fold
                dates=tuple('2024-01-'+str(d) for d in range(28,32))+tuple('2024-02-0'+str(d) for d in range(1,4))
                prices=PricePanel('ETH-USD',dates,tuple(100.+i for i in range(7)),(),'b'*64,'2026-01-01T00:00:00Z')
                f.batch_scaler=fit_scaler(e,prices,fold);binding=example_binding(e,f.batch_scaler)
                common={'asset':'ETH','fold':fold.id,'seed':11,'variant':'whole','lane':'algorithm','arm':'proposed'}
                cells=[{'cell':dict(common,id=i,task=t),'status':'ready','population':'whole','representation':'r'} for i,t in [('sum','direction'),('count','regression')]]
                plan={'schema_version':1,'cells':cells,'populations':{'whole':{'input':'example_binding','binding':binding,
                    'train_examples':len(e.train),'test_examples':len(e.test),'asset':'ETH','fold':fold.id,'variant':'whole'}},
                    'representations':{'r':{'output':'binding.json','failure_output':'feature_failure.json'}},
                    'model':dict(CONFIG,mcm_input=f.configs['dictionary']['size']),
                    'training':dict(CFG,epochs=1,batch_size=1),'ledger_output':'ledger.json','controls_output':'controls.json'}
                original(f,'batch_plan',plan);original(f,'example_binding',binding)
                original(f,'population',job_payload.population_record(e,f.batch_scaler))
                f.exp['cells']=['sum','count']
                for output in ('ledger.json','controls.json','feature_failure.json'):
                    if output not in f.exp['outputs']:f.exp['outputs'].append(output)
                value['payload'].update(batch_plan_input='batch_plan',population_inputs={'whole':'population'})
            return original(f,name,value)
        def ready(f):raise Ready(f)
        original_load=base.load
        def load(name,path):return native.api() if Path(path).name=='native_map.py' else original_load(name,path)
        # Only configuration is inherited: abort before old owner creation and all
        # old producers. Actual code below must create every journal and artifact.
        with patch.object(base,'load',side_effect=load),patch.object(first.OwnershipTests,'input',new=configured),patch.object(first.OwnershipTests,'prepare',new=ready):
            try:fixture.fixture()
            except Ready as result:f=result.owner
            else:self.fail('configuration fixture entered existing producer path')
        for g in f.graphs:
            h=graph_hash(g);name=f.item['graphs'][h]['input']
            path=save_graph(f.root/('graph-'+h),g)
            f.exp['inputs'][name]={'path':str(path.relative_to(f.root)),'sha256':file_hash(path),'dataset':'sample'}
        selected=f.execution['payload']['representation_jobs']['r']
        f.item['native_backend']=native.BACKEND
        selected.update(native_backend=native.BACKEND,binding_output='binding.json',journal_output='journal.json',population='whole',max_graph_payload_bytes=1048576)
        for key in native.ROUTES:selected[key]=f.item[key]
        selected['pair_journal_parent_input']=f.item['pair_journal_parent_input']=None
        f.input('plan',f.plan);f.input('execution_job',f.execution)
        f.source=commit(f.root,f.spec)
        f.run=ResearchRun.start(root=f.root,registration='registration.json',experiment='example-a',source=f.source)
        self.addCleanup(lambda:f.run.fail('synthetic dispatch fixture closed'))
        f.base=f.root/job.PREFIX/'runs/example-a';f.base.mkdir(parents=True)
        launch={'experiment':'example-a','source_commit':f.source,'supervisor_pid':os.getpid(),'nonce':'synthetic-dispatch'}
        owner={**launch,'monitor_pid':os.getpid(),'monitor_start_ticks':Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19]}
        _immutable(f.base/'launch.json',launch);_immutable(f.base/'owner.json',owner)
        self.guard=patch.object(resources,'assert_guarded_worker',return_value={**f.resources,'owner_identity':owner,'monitor_pid':os.getpid()})
        self.guard.start();self.addCleanup(self.guard.stop)
        return f

    def test_actual_job_creates_first_owner_and_completes_both_cells(self):
        f=self.fixture();self.assertFalse((f.root/'research_artifacts/onchain_representations').exists())
        from tradingagents.research.onchain_replication import graph_store
        original=graph_store.load_graph;loaded=[];prepared=[];produce=native.produce
        def resident(*args,**kwargs):
            self.assertIs(kwargs.get('resident'),True)
            g=original(*args,**kwargs)
            for key in ('node_features','edge_index','edge_features','edge_aggregates'):
                self.assertFalse(isinstance(getattr(g,key),np.memmap))
            loaded.append(graph_hash(g));return g
        def capture(*args,**kwargs):
            value=produce(*args,**kwargs);prepared.append(value);return value
        with patch.object(graph_store,'load_graph',side_effect=resident),patch.object(native,'produce',side_effect=capture),patch.object(registered_features,'prepare_registered_features',side_effect=AssertionError('legacy route selected')):
            rows,controls=job_payload.execute_fit_payload(f.run,f.execution['payload'])
        self.assertEqual([r['status'] for r in rows],['complete','complete'],rows)
        self.assertEqual(sorted(loaded),sorted(f.descriptor['graph_population']))
        self.assertEqual(len(prepared),1)
        features,terminal=prepared[0];terminal.lease()
        self.assertEqual(features.features.live_tensor_bytes(),0)
        for row in rows:
            record=json.loads((f.root/row['cell_record']).read_bytes())
            self.assertEqual(record['test_mask_hash'],f.examples.test_mask_hash)
            print('DISPATCH VERIFIED',row['id'],record['checkpoint_hash'],flush=True)
        self.assertEqual(controls['whole']['fit_count'],0)
        with patch.object(native,'produce',side_effect=AssertionError('duplicate producer reached')):
            with self.assertRaises((FileExistsError,ValueError)):job_payload.execute_fit_payload(f.run,f.execution['payload'])

if __name__=='__main__':unittest.main(verbosity=2)
