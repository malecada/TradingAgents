"""Metadata-only full daily denominator and per-step graph clock fixtures."""
from dataclasses import asdict,replace
import importlib.util
from pathlib import Path
import unittest
from tradingagents.research.onchain_replication.contracts import Fold
from tradingagents.research.onchain_replication.dataset import Example,ExampleManifest,CalendarGraph
from tradingagents.research.onchain_replication.provenance import canonical_bytes,digest,freeze

HERE=Path(__file__).resolve().parent
def api():
    path=HERE/'denominator.py';assert path.exists(),'exact representation denominator missing'
    spec=importlib.util.spec_from_file_location('representation_denominator',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def stamp(date):return date+'T00:00:00Z'

def fixture():
    graphs=(CalendarGraph('ETH',stamp('2024-01-15'),stamp('2024-01-22'),stamp('2024-01-23'),('a'*64,),'1'*64),
        CalendarGraph('ETH',stamp('2024-01-22'),stamp('2024-01-29'),stamp('2024-01-30'),('a'*64,),'2'*64))
    fold=Fold('tiny',stamp('2024-01-30'),stamp('2024-02-01'),None,None,stamp('2024-02-02'),stamp('2024-02-04'),'f'*64)
    def row(day,end,dates,ids):
        return Example(stamp(day),stamp(day),stamp(end),stamp(day),dates,(1.,2.),tuple(graphs[i].identity for i in ids),
            tuple(graphs[i].available_at for i in ids),3.,1)
    train=(row('2024-01-30','2024-01-31',('2024-01-28','2024-01-29'),(0,1)),
        row('2024-01-31','2024-02-01',('2024-01-29','2024-01-30'),(1,1)))
    test=(row('2024-02-02','2024-02-03',('2024-01-31','2024-02-01'),(1,1)),
        row('2024-02-03','2024-02-04',('2024-02-01','2024-02-02'),(1,1)))
    examples=ExampleManifest(train,test,(freeze({'decision_at':stamp('2024-02-01'),'reason':'outside_fold','partition':'test'}),),
        '', '',('a'*64,'b'*64),fold.member_hash)
    return graphs,fold,rehash(examples)

def rehash(examples):
    return replace(examples,train_hash=digest(canonical_bytes([asdict(x) for x in examples.train])),
        test_mask_hash=digest(canonical_bytes([x.decision_at for x in examples.test])))

def manifest_hash(examples):
    return digest(canonical_bytes({**vars(examples),'train':[asdict(x) for x in examples.train],'test':[asdict(x) for x in examples.test]}))

class Tests(unittest.TestCase):
    def run_case(self,m,graphs,fold,examples,**kw):
        args=dict(lookback_days=2,max_calendar_days=20,expected_manifest_sha256=manifest_hash(examples),
            expected_population=['1'*64,'2'*64],expected_required=['1'*64,'2'*64])
        args.update(kw);return m.validate(graphs,examples,fold,**args)

    def test_complete_day_partition_and_graph_denominator(self):
        m=api();g,f,e=fixture();record=self.run_case(m,g,f,e)
        self.assertEqual(record['calendar_days'],5);self.assertEqual(record['train_rows'],2);self.assertEqual(record['test_rows'],2)
        self.assertEqual(record['excluded_by_reason'],{'outside_fold':1});self.assertEqual(record['test_calendar_days'],2)
        self.assertEqual(record['required_graphs'],['1'*64,'2'*64]);self.assertFalse(record['price_exclusions_revalidated'])

    def test_rehashed_missing_duplicate_or_reordered_dates_still_refuse(self):
        m=api();g,f,e=fixture()
        for bad in (replace(e,test=e.test[:1]),replace(e,test=tuple(reversed(e.test))),
            replace(e,train=(*e.train,e.train[0])),replace(e,exclusions=())):
            with self.subTest(train=len(bad.train),test=len(bad.test),excluded=len(bad.exclusions)),self.assertRaises(ValueError):
                self.run_case(m,g,f,rehash(bad))

    def test_graph_available_by_decision_but_future_at_input_step_refuses(self):
        m=api();g,f,e=fixture();row=replace(e.train[0],graph_hashes=('2'*64,'2'*64),graph_available_at=(g[1].available_at,)*2)
        bad=rehash(replace(e,train=(row,e.train[1])))
        with self.assertRaises(ValueError):self.run_case(m,g,f,bad,expected_required=['2'*64])

    def test_lookback_labels_exclusion_partition_and_population_refuse(self):
        m=api();g,f,e=fixture()
        badrows=(replace(e.train[0],input_dates=('2024-01-29',)),
            replace(e.train[0],label_end=stamp('2024-02-02')),replace(e.train[0],max_input_available_at=stamp('2024-01-31')))
        for row in badrows:
            with self.subTest(row=row),self.assertRaises(ValueError):self.run_case(m,g,f,rehash(replace(e,train=(row,e.train[1]))))
        bad=replace(e,exclusions=(freeze({'decision_at':stamp('2024-02-01'),'reason':'outside_fold','partition':'train'}),))
        with self.assertRaises(ValueError):self.run_case(m,g,f,rehash(bad))
        with self.assertRaises(ValueError):self.run_case(m,g,f,e,expected_required=['2'*64])
        with self.assertRaises(ValueError):self.run_case(m,(*g,g[0]),f,e)
        with self.assertRaises(ValueError):self.run_case(m,g,f,e,expected_manifest_sha256='0'*64)
        with self.assertRaises(ValueError):self.run_case(m,g,f,e,max_calendar_days=4)

    def test_recorded_price_exclusion_keeps_day_without_claiming_price_revalidation(self):
        m=api();g,f,e=fixture();excluded=freeze({'decision_at':e.test[1].decision_at,'reason':'warmup_or_missing_price','partition':'test'})
        bad=rehash(replace(e,test=e.test[:1],exclusions=(*e.exclusions,excluded)))
        record=self.run_case(m,g,f,bad)
        self.assertEqual(record['test_rows'],1);self.assertEqual(record['test_calendar_days'],2)
        self.assertEqual(record['excluded_by_reason'],{'outside_fold':1,'warmup_or_missing_price':1})
        self.assertFalse(record['price_exclusions_revalidated'])

    def test_missing_and_late_graph_exclusions_replay_actual_calendar(self):
        m=api();g,f,e=fixture()
        for reason,graphs in (('missing_expected_graph',g[1:]),
            ('late_expected_graph',(replace(g[0],available_at=stamp('2024-01-30')),g[1]))):
            bad=rehash(replace(e,train=e.train[1:],exclusions=(freeze({'decision_at':e.train[0].decision_at,
                'reason':reason,'partition':'train'}),*e.exclusions)))
            with self.subTest(reason=reason):
                record=self.run_case(m,graphs,f,bad,expected_population=sorted(x.identity for x in graphs),expected_required=['2'*64])
                self.assertEqual(record['excluded_by_reason'][reason],1)
                with self.assertRaises(ValueError):self.run_case(m,g,f,bad,expected_required=['2'*64])

    def test_purged_training_label_remains_in_complete_denominator(self):
        m=api();g,f,e=fixture();f=replace(f,test_start=stamp('2024-02-01'))
        excluded=(freeze({'decision_at':stamp('2024-01-31'),'reason':'purged_training_label','partition':'train'}),
            freeze({'decision_at':stamp('2024-02-01'),'reason':'warmup_or_missing_price','partition':'test'}))
        e=rehash(replace(e,train=e.train[:1],exclusions=excluded))
        record=self.run_case(m,g,f,e)
        self.assertEqual(record['calendar_days'],5);self.assertEqual(record['test_calendar_days'],3)
        self.assertEqual(record['excluded_by_reason']['purged_training_label'],1)

if __name__=='__main__':unittest.main(verbosity=2)
