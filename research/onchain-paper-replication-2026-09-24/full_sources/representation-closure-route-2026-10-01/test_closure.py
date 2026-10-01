"""Actual two-graph registered closure, complete calendar, no financial fitting."""
import importlib.util
from datetime import timedelta
from pathlib import Path
import unittest
from unittest.mock import patch
import weakref
from tradingagents.research.onchain_replication.contracts import GraphSnapshot
from tradingagents.research.onchain_replication.calendar import build_folds,stamp
from tradingagents.research.onchain_replication.dataset import build_examples
from tradingagents.research.onchain_replication.provenance import utc,file_hash,thaw
from tradingagents.research.onchain_replication.neighborhoods import graph_hash
from tests.research.onchain_replication import test_matching_owner as first

HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
base=load('closure_graph_fixture',HERE.parent/'graph-feature-artifact-route-2026-10-01/test_route.py')
calendar_fixture=load('closure_calendar_fixture',HERE.parent/'representation-denominator-route-2026-10-01/test_route.py')
CALENDAR=calendar_fixture.CALENDAR|{'folds':[calendar_fixture.CALENDAR['folds'][0]|{'train_start':'2024-01-08T00:00:00Z'}]}
COVERAGE=calendar_fixture.COVERAGE

def population():
    g,_,e=calendar_fixture.population();original=g[0]
    extra=GraphSnapshot(original.asset,'2024-01-08T00:00:00Z','2024-01-15T00:00:00Z','2024-01-16T00:00:00Z',
        original.source_hashes,original.graph_config_hash,original.node_ids,original.node_features,original.edge_index,original.edge_features,1,1,{})
    # The earlier training graph is deliberately not used by any included price row.
    from tradingagents.research.onchain_replication.contracts import PricePanel
    dates=('2024-01-28','2024-01-29','2024-01-30','2024-01-31','2024-02-01','2024-02-02','2024-02-03')
    prices=PricePanel('ETH-USD',dates,tuple(100.+i for i in range(7)),(),'b'*64,'2026-01-01T00:00:00Z')
    graphs=[extra,*g];fold=build_folds(CALENDAR,COVERAGE)[0]
    return graphs,fold,build_examples(graphs,prices,fold,CALENDAR)

def api():
    assert (HERE/'closure.py').exists(),'registered representation closure missing'
    return load('representation_closure_candidate',HERE/'closure.py')

class Tests(unittest.TestCase):
    def fixture(self):
        self.m=api();m=self.m
        f=base.Tests('test_exact_saved_reuse_and_output_lease_without_numeric_reentry');self.addCleanup(f.doCleanups)
        original=first.OwnershipTests.input
        def configured(instance,name,value):
            if name=='pair_workload':
                instance.graphs,instance.fold,instance.examples=population()
                value=value|{'example_manifest_sha256':calendar_fixture.full_hash(instance.examples)}
                instance.control=value
            if name=='plan':
                original(instance,'calendar',CALENDAR);original(instance,'coverage',COVERAGE)
                original(instance,'denominator',{'schema_version':1,'calendar_input':'calendar','coverage_input':'coverage','max_calendar_days':30})
                original(instance,'closure',{'schema_version':1,'max_graphs':3,'max_record_bytes':1048576,'max_sequential_numeric_bytes':1000,
                    'graph_admission':{'mcm_input':'mcm_execution','mcm_output_input':'mcm_output','mcm_read_input':'mcm_read',
                        'feature_input':'feature_tensor','output_input':'graph_output','read_input':'graph_read'}})
                value['producers']['p'].update(denominator_input='denominator',representation_closure_input='closure')
            if name=='execution_job':value['payload']['representation_jobs']['r'].update(denominator_input='denominator',representation_closure_input='closure')
            return original(instance,name,value)
        with patch.object(base,'api',return_value=m.graphs),patch.object(m.graphs,'SOURCES',m.SOURCES),patch.object(first.OwnershipTests,'input',new=configured):owner=f.fixture()
        self.f=f;self.owner=owner;self.ticket=f.f.f.f.ticket
        return owner
    def admit(self,**kw):
        f=self.owner;args=dict(examples=f.examples,fold=f.fold,denominator_input='denominator',dictionary_ticket=self.ticket,policy_input='closure');args.update(kw)
        return self.m.admit(f.owned,f.journal,**args)
    def test_all_required_graphs_and_training_only_lineage_close_without_retaining_tensors(self):
        f=self.fixture();m=self.m;g=m.graphs;saved=g.saved
        with patch.object(g,'admit',side_effect=AssertionError('graph array before full membership')):
            with self.assertRaisesRegex(ValueError,'completion membership'):self.admit()
        completed={e['context']['graph_hash'] for e in f.journal.records if e['stage']=='graph_complete'}
        dictionary_proof=saved._issued[self.ticket]['record']['dictionary_proof']['sha256']
        for h in sorted(set(f.workload.descriptor['required_graphs'])-completed):
            proof=saved.publication.produce(f.owned,f.journal,graph_hash=h,sampler_input='sampler_execution',artifact_input='artifact_read',
                dictionary_output_input='dictionary_output',dictionary_proof_sha256=dictionary_proof,mcm_input='mcm_execution',output_input='mcm_output')
            g.publication.produce(f.owned,f.journal,dictionary_ticket=self.ticket,graph_hash=h,mcm_input='mcm_execution',mcm_output_input='mcm_output',
                read_input='mcm_read',mcm_proof_sha256=proof['sha256'],feature_input='feature_tensor',output_input='graph_output')
        f.journal.records.append(f.journal.records[-1])
        with patch.object(g,'admit',side_effect=AssertionError('array before duplicate refusal')):
            with self.assertRaisesRegex(ValueError,'completion membership'):self.admit()
        f.journal.records.pop()
        real=g.admit;refs=[];calls=[]
        def checked(*args,**kwargs):
            self.assertTrue(all(ref() is None for ref in refs),'previous tensors retained at next admission')
            result=real(*args,**kwargs);refs.extend(weakref.ref(v) for v in result.feature.values());calls.append(kwargs['graph_hash']);return result
        before=f.owned.journal.reservations
        with patch.object(g,'admit',side_effect=checked),patch.object(saved.artifacts,'admit',side_effect=AssertionError('dictionary reentry')):
            receipt=self.admit();receipt.lease()
        self.assertTrue(all(ref() is None for ref in refs))
        record=thaw(receipt.record);binding=record['binding'];required=sorted(f.workload.descriptor['required_graphs'])
        self.assertEqual(calls,required);self.assertEqual(set(binding['feature_hashes']),set(required))
        self.assertEqual(len(binding['dictionary_training_graph_hashes']),3)
        self.assertEqual(set(binding['lineage']),{graph_hash(x) for x in f.graphs})
        self.assertEqual(record['denominator']['denominator']['calendar_days'],27)
        self.assertFalse(record['empirical_admission_verified']);self.assertEqual(before,f.owned.journal.reservations)
        first_graph=record['graphs'][required[0]];p=Path(first_graph['component']['path']).parent/'array-000000.npy'
        raw=bytearray(p.read_bytes());raw[-1]^=1;p.write_bytes(raw)
        with self.assertRaises(ValueError):receipt.lease()
    def test_unadmitted_owner_refuses(self):
        m=api()
        with self.assertRaises(ValueError):m.admit(object(),None,examples=None,fold=None,denominator_input='x',dictionary_ticket=None,policy_input='x')

if __name__=='__main__':unittest.main(verbosity=2)
