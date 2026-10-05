"""Metadata-only candidate tests: no imported Owner/claim or numerical pilot."""
import copy
import importlib.util
from pathlib import Path
import unittest
import sys
from unittest.mock import patch

HERE=Path(__file__).resolve().parent

def module():
    path=HERE/'real_pilot_import_caller.py'
    assert path.exists(), 'functional import caller not implemented'
    spec=importlib.util.spec_from_file_location('tradingagents.research.onchain_replication._candidate_import_caller',path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def plan():
    graphs={format(i,'064x'):'graph_'+str(i) for i in range(7)}
    keys=list(graphs)
    return {'schema_version':1,'kind':'real-data-import-training-pilot-v1','asset':'ETH','seed':11,
      'batch_size':16,'lookback_days':28,'cell_id':'real-eth-one-update','graph_inputs':graphs,
      'indices':list(range(16)),'decisions':['2020-01-%02dT00:00:00Z'%(i+1) for i in range(16)],
      'graph_sequences':[[keys[(i+j)//7%7] for j in range(28)] for i in range(16)],
      'population_plan_input':'population_plan','model_input':'model','training_input':'training',
      'model_execution':None,'max_checkpoint_bytes':4*1024**2,
      'outputs':{'summary':'pilot-summary.json','ledger':'cell-ledger.json','binding':'resource-binding.json','journal':'resource-journal.json'}}


class Checks(unittest.TestCase):
    def test_exact_real_batch_plan_and_unambiguous_route(self):
        m=module();p=plan();self.assertEqual(m.validate_plan(p),p)
        job={'payload':{'representation_jobs':{'rep':{'real_pilot_input':'pilot'}}}}
        self.assertTrue(m.selected(job))
        job['payload']['representation_jobs']['extra']={}
        with self.assertRaises(ValueError):m.selected(job)

    def test_refuses_incomplete_or_ambiguous_plan(self):
        changes=[lambda p:p['indices'].__setitem__(15,16),lambda p:p['graph_sequences'][0].__setitem__(0,'f'*64),lambda p:p['graph_inputs'].pop(next(iter(p['graph_inputs']))),lambda p:p['outputs'].__setitem__('summary','cell-ledger.json')]
        for i,change in enumerate(changes):
            with self.subTest(i=i):
                m=module();p=plan();change(p)
                with self.assertRaises(ValueError):m.validate_plan(p)

    def test_legacy_route_and_same_resource_ceilings(self):
        # Only the real, stdlib-only canonical validator is loaded. No guard,
        # Binding, Owner, arrays, claims or completed evidence are synthesized.
        import tradingagents.research.onchain_replication
        base=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-canonical-native-20261005-01/source/tradingagents/research/onchain_replication')
        name='tradingagents.research.onchain_replication.resource_binding'
        spec=importlib.util.spec_from_file_location(name,base/'resource_binding.py')
        binding=importlib.util.module_from_spec(spec);spec.loader.exec_module(binding)
        m=module()
        self.assertFalse(m.selected({'payload':{'representation_jobs':{'legacy':{}}}}))
        selection={key:key for key in m.KEYS}
        selection.update(operation='produce',descriptor={'arm':'proposed','dictionary_origin':'imported-original-v1'})
        limits={'max_allocated_bytes':m.GIB,'max_logical_bytes':m.GIB,'max_entries':32768,'max_depth':32,'max_scan_seconds':5}
        job={'schema_version':1,'kind':'compact_resource','environment_input':'environment',
             'payload':{'representation_jobs':{'pilot':selection}},
             'resources':{'wall_seconds':1800,'memory_max_bytes':3*m.GIB,
                          'native_unit_limits':{'file_size_bytes':m.FILE_MAX},
                          'storage_budget':{'root':'/unused','limits':limits}}}
        with patch.dict(sys.modules,{name:binding}):
            m.schema(job)
            for key,bad in [('wall_seconds',1801),('memory_max_bytes',3*m.GIB+1),('native_unit_limits',{'file_size_bytes':m.FILE_MAX+1})]:
                changed=copy.deepcopy(job);changed['resources'][key]=bad
                with self.subTest(key=key), self.assertRaises(ValueError):m.schema(changed)
            changed=copy.deepcopy(job);changed['resources']['storage_budget']['limits']['max_logical_bytes']+=1
            with self.assertRaises(ValueError):m.schema(changed)
            changed=copy.deepcopy(job);changed['payload']['representation_jobs']['pilot']['held_score_consumer_input']='old-tiny-policy'
            with self.assertRaises(ValueError):m.schema(changed)

    def test_no_duck_typed_run_or_implicit_launch(self):
        with self.assertRaisesRegex(ValueError,'ResearchRun'):module().execute(object(),{})

if __name__=='__main__':unittest.main()
