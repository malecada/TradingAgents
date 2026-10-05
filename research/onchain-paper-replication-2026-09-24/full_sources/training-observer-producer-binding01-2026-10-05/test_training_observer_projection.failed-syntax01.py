"""Scalar metadata checks; no neural fit or scientific capability construction."""
import copy
import json
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from tradingagents.research.onchain_replication import population_batch_projection as projection
from tradingagents.research.onchain_replication import training_batch_observer as observer


def fixture():
    def row(day):
        dates=[(day-timedelta(days=i)).date().isoformat() for i in range(28,0,-1)]
        return dict(decision_at=day.isoformat(),label_start=day.isoformat(),
            label_end=(day+timedelta(days=1)).isoformat(),max_input_available_at=day.isoformat(),
            input_dates=dates,input_prices=['private-price']*28,
            graph_hashes=['1'*64,'2'*64]*14,graph_available_at=['2023-12-01T00:00:00Z']*28,
            target_price='private-target',up='private-label')
    first=datetime(2024,2,1,tzinfo=timezone.utc)
    train=[row(first+timedelta(days=i+(i>=8))) for i in range(17)]
    test=[row(datetime(2024,3,1,tzinfo=timezone.utc))]
    exclusions=[dict(decision_at='2024-02-09T00:00:00+00:00',reason='missing_expected_graph',partition='train'),
        dict(decision_at='2024-03-02T00:00:00+00:00',reason='late_expected_graph',partition='test')]
    examples=dict(train=train,test=test,exclusions=exclusions,
        train_hash=projection.digest(projection.encode(train)),
        test_mask_hash=projection.digest(projection.encode([r['decision_at'] for r in test])),
        source_hashes=['3'*64],fold_hash='4'*64)
    scaler=dict(mean=1,std=1,dates=[],train_hash=examples['train_hash'])
    population=dict(schema_version=1,examples=examples,scaler=scaler)
    binding={k:examples[k] for k in ('train_hash','test_mask_hash','source_hashes','fold_hash')}
    binding.update(test_examples_hash=projection.digest(projection.encode(test)),scaler=scaler)
    admitted=dict(source_hashes=['3'*64],price_source_hash='3'*64)
    assembly=dict(schema_version=1,weeks={},decision_count=20,provenance=dict(
        source_admission=admitted,source_admission_hash=projection.digest(projection.encode(admitted)),
        calendar=dict(lookback_days=28),fold=dict(member_hash='4'*64)))
    return population,binding,assembly


class TrainingProjectionTests(unittest.TestCase):
    def test_exact_existing_observer_schema_with_all_training_rows_and_gaps(self):
        population,binding,assembly=fixture();examples=population['examples']
        actual=projection.training_metadata(population,binding,assembly,{})
        borrowed=SimpleNamespace(train=[SimpleNamespace(**r) for r in examples['train']],exclusions=examples['exclusions'])
        expected=dict(schema_version=1,train_hash=examples['train_hash'],fold_hash=examples['fold_hash'],
            source_hashes=examples['source_hashes'],rows=[observer.project(r) for r in borrowed.train],
            exclusions=observer.excluded(borrowed))
        self.assertEqual(actual,expected)
        self.assertEqual(len(actual['rows']),17)
        self.assertEqual(actual['rows'][8]['decision_at'],'2024-02-10T00:00:00+00:00')
        text=json.dumps(actual)
        for forbidden in ('private-price','private-target','private-label','label_start','input_prices','target_price','2024-03-01'):
            self.assertNotIn(forbidden,text)

    def test_full_projection_and_unavailable_components_are_preserved(self):
        population,binding,assembly=fixture();components={'1'*64:dict(status='unavailable',reason='original MCM absent',evidence_hashes=['9'*64])}
        full=projection.project(population,binding,assembly,components);before=copy.deepcopy(full)
        projection._training_metadata(full)
        self.assertEqual(full,before)
        self.assertEqual([len(b['ordinals']) for b in full['batches']],[16,1,1])
        self.assertEqual(full['components']['1'*64']['status'],'unavailable')
        self.assertEqual(full['components']['2'*64']['status'],'missing_registered_component')
        self.assertEqual(len(full['exclusions']),2)

    def test_changed_test_values_do_not_enter_training_output(self):
        population,binding,assembly=fixture();before=projection.training_metadata(population,binding,assembly,{})
        population['examples']['test'][0]['target_price']='changed-test-target'
        population['examples']['test'][0]['up']='changed-test-label'
        binding['test_examples_hash']=projection.digest(projection.encode(population['examples']['test']))
        self.assertEqual(before,projection.training_metadata(population,binding,assembly,{}))

    def test_binding_and_unknown_original_fields_are_refused(self):
        population,binding,assembly=fixture();binding['fold_hash']='e'*64
        with self.assertRaises(ValueError):projection.training_metadata(population,binding,assembly,{})
        population,binding,assembly=fixture();population['examples']['train'][0]['new_label']=1
        digest=projection.digest(projection.encode(population['examples']['train']))
        population['examples']['train_hash']=binding['train_hash']=population['scaler']['train_hash']=digest
        with self.assertRaises(ValueError):projection.training_metadata(population,binding,assembly,{})

    def test_observer_cardinality_and_output_extent_refuse_without_truncation(self):
        full=projection.project(*fixture(),{})
        full['rows']=[full['rows'][0]]*2049
        with self.assertRaisesRegex(ValueError,'population bound'):projection._training_metadata(full)
        full=projection.project(*fixture(),{})
        full['rows'][0]['input_dates']=['x'*(projection.OUTPUT_LIMIT+1)]
        with self.assertRaisesRegex(ValueError,'byte bound'):projection._training_metadata(full)


if __name__=='__main__':unittest.main()
