"""Synthetic native terminal map through actual registered fitting and prediction."""
import importlib.util
import json
import io
import torch
from pathlib import Path
from contextlib import ExitStack
import unittest
from unittest.mock import patch
import numpy as np
from tests.research.onchain_replication import test_matching_owner as first
from tests.research.onchain_replication.test_evaluation import CONFIG
from tests.research.onchain_replication.test_training import CFG
from tradingagents.research.onchain_replication import run as batch, registered_features
from tradingagents.research.onchain_replication.contracts import PricePanel
from tradingagents.research.onchain_replication.dataset import fit_scaler
from tradingagents.research.onchain_replication.evaluation import example_binding
from tradingagents.research.onchain_replication.provenance import file_hash,digest
from tradingagents.research.onchain_replication.cache import read_artifact
from tradingagents.research.onchain_replication.model_registry import build_model
from tradingagents.research.onchain_replication.training import predict_cell
from tradingagents.research.onchain_replication.evaluation import batch_factory
from tradingagents.research.onchain_replication.verification import independent_classification,independent_regression,compare_summary

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('native_batch_fixture',HERE.parent/'terminal-native-map-2026-10-01/test_prepare.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

class Tests(unittest.TestCase):
    def test_native_terminal_features_fit_checkpoint_predict_and_refuse_duplicate_batch(self):
        fixture=base.Tests('test_actual_terminal_transition_and_native_batches_without_producer_reentry')
        self.addCleanup(fixture.doCleanups)
        original=first.OwnershipTests.input
        def configured(instance,name,value):
            if name=='execution_job' and hasattr(instance,'examples'):
                e=instance.examples;fold=instance.fold
                dates=tuple('2024-01-'+str(d) for d in range(28,32))+tuple('2024-02-0'+str(d) for d in range(1,4))
                prices=PricePanel('ETH-USD',dates,tuple(100.+i for i in range(7)),(),'b'*64,'2026-01-01T00:00:00Z')
                instance.batch_scaler=fit_scaler(e,prices,fold)
                binding=example_binding(e,instance.batch_scaler)
                common={'asset':'ETH','fold':fold.id,'seed':11,'variant':'whole','lane':'algorithm','arm':'proposed'}
                cells=[{'cell':dict(common,id=i,task=t),'status':'ready','population':'whole','representation':'r'}
                       for i,t in [('sum','direction'),('count','regression')]]
                plan={'schema_version':1,'cells':cells,'populations':{'whole':{'input':'example_binding','binding':binding,
                    'train_examples':len(e.train),'test_examples':len(e.test),'asset':'ETH','fold':fold.id,'variant':'whole'}},
                    'representations':{'r':{'output':'binding.json','failure_output':'feature_failure.json'}},
                    'model':dict(CONFIG,mcm_input=instance.configs['dictionary']['size']),
                    'training':dict(CFG,epochs=1,batch_size=1),'ledger_output':'ledger.json','controls_output':'controls.json'}
                original(instance,'batch_plan',plan);original(instance,'example_binding',binding)
                instance.exp['cells']=['sum','count']
                for output in ('ledger.json','controls.json','feature_failure.json'):
                    if output not in instance.exp['outputs']:instance.exp['outputs'].append(output)
                value['payload']['batch_plan_input']='batch_plan'
            return original(instance,name,value)
        with patch.object(first.OwnershipTests,'input',new=configured):
            m,owner,args=fixture.fixture()
        run=owner.run;populations={'whole':(owner.examples,owner.batch_scaler)}
        batch.preflight_batch(run,populations)
        prepared,terminal=m.prepare(owner.owned,owner.journal,**args)
        reservations=owner.owned.journal.reservations
        with ExitStack() as stack:
            for module,name in ((m.seal,'finish'),(m.seal.publication,'produce'),(m.seal.publication.closure,'admit'),
                    (m.seal.saved,'prepare_dictionary'),(registered_features,'prepare_registered_features'),
                    (registered_features,'reuse_registered_features')):
                stack.enter_context(patch.object(module,name,side_effect=AssertionError('completed producer replayed by fitting')))
            stack.enter_context(patch.object(np,'load',side_effect=AssertionError('generic NumPy loader used')))
            rows,controls=batch.execute_batch(run,populations,{'r':prepared})
            self.assertEqual([r['status'] for r in rows],['complete','complete'],rows)
            self.assertEqual(controls['whole']['fit_count'],0)
            for row in rows:
                path=run.admission.root/row['cell_record'];record=json.loads(path.read_bytes())
                predictions=json.loads((path.parent/'predictions.json').read_bytes())
                self.assertEqual(len(predictions),len(owner.examples.test))
                direction=row['id']=='sum';task='direction' if direction else 'regression'
                for prediction,expected in zip(predictions,owner.examples.test,strict=True):
                    for field in ('decision_at','label_start','label_end','max_input_available_at'):
                        self.assertEqual(prediction[field],getattr(expected,field))
                    self.assertEqual(prediction['y_true'],float(expected.up if direction else expected.target_price))
                    self.assertEqual((prediction['lane'],prediction['asset'],prediction['arm'],prediction['fold_id'],prediction['seed']),
                                     ('algorithm','ETH','proposed',owner.fold.id,11))
                truths=[e.up if direction else e.target_price for e in owner.examples.test]
                actual=independent_classification(truths,[r['probability_up'] for r in predictions]) if direction else independent_regression(truths,[r['predicted_price'] for r in predictions])
                completion_path=run.admission.root/'research_artifacts/onchain_fit_cells'/digest(row['id'].encode())/run.admission.experiment_id/'complete.json'
                completion=json.loads(completion_path.read_bytes());checkpoint=Path(completion['checkpoint'])
                self.assertEqual(completion['epochs'],1)
                self.assertEqual(file_hash(checkpoint),completion['sha256'])
                self.assertEqual(completion['sha256'],record['checkpoint_hash'])
                for prediction in predictions:self.assertEqual(prediction['checkpoint_hash'],record['checkpoint_hash'])
                artifact=read_artifact(checkpoint,record['provenance'])
                state=torch.load(io.BytesIO(artifact['state.pt']),map_location='cpu',weights_only=True)
                self.assertEqual((state['epoch'],state['batch']),(1,0))
                self.assertTrue(state['optimizer']['state'])
                plan=json.loads(run.read_input('batch_plan'));model=build_model('proposed',task,plan['model'])
                model.load_state_dict(state['model'],strict=True)
                factory=batch_factory('proposed',task,owner.examples.test,owner.batch_scaler,prepared.features)
                output=predict_cell(model,factory,len(owner.examples.test),plan['training']['batch_size'])
                values=torch.softmax(output,1)[:,1].numpy() if direction else owner.batch_scaler.inverse(output[:,0].numpy())
                self.assertEqual([float(v) for v in values],[r['probability_up'] if direction else r['predicted_price'] for r in predictions])
                del output,model,state,artifact,factory

                self.assertTrue(compare_summary(record['metrics'],actual)['passed'])
                self.assertEqual(record['provenance']['dictionary_hash'],prepared.binding['dictionary_hash'])
                self.assertEqual(record['test_mask_hash'],owner.examples.test_mask_hash)
                self.assertEqual(file_hash(path.parent/'predictions.json'),record['prediction_hash'])
                print('VERIFIED SYNTHETIC CELL',row['id'],'predictions',len(predictions),'checkpoint',record['checkpoint_hash'],flush=True)
            self.assertEqual(prepared.features.live_tensor_bytes(),0)
            self.assertEqual(owner.owned.journal.reservations,reservations)
            ledger=run.directory/'outputs/ledger.json';before=file_hash(ledger)
            with self.assertRaises(FileExistsError):batch.execute_batch(run,populations,{'r':prepared})
            self.assertEqual(file_hash(ledger),before)
        terminal.lease()

if __name__=='__main__':unittest.main(verbosity=2)
