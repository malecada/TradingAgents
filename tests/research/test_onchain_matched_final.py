"""Synthetic checker regressions: all prices/counts are invented."""
import importlib.util
from pathlib import Path
import unittest
import pandas as pd
import numpy as np

PATH = Path(__file__).resolve().parents[2]/'research/onchain-graph-2026-09-16/comparison/evaluation-20260924/check_final.py'

class IndependentFinalTests(unittest.TestCase):
    def checker(self):
        self.assertTrue(PATH.exists(), 'independent checker not implemented')
        spec = importlib.util.spec_from_file_location('independent_matched_final', PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def fixture(self):
        days = pd.date_range('2023-11-01', '2024-01-04', tz='UTC')
        market = [dict(day=d, open=100+i%3, close=100+i, quote_volume=10+i,
                       available_at=d+pd.Timedelta(days=1, minutes=5)) for i,d in enumerate(days)]
        graph = [dict(day=d, available_at=d+pd.Timedelta(days=2), events=12,
                      nodes=4, directed_pairs=6, stars=3, dyads=2, triangles=1,
                      overlap_nodes=5, nonzero_nodes=2) for d in days]
        return market, graph

    def test_rebuild_lag_label_clock_and_missing_window(self):
        c = self.checker(); market,graph=self.fixture()
        rows=c.rebuild_panel(market,graph,'2024-01-01','2024-01-03')
        self.assertEqual(rows[0]['y'], 1)
        self.assertAlmostEqual(rows[0]['return_1'], np.log(159/158))
        self.assertEqual(rows[0]['nonzero_fraction'], .4)
        graph[-6]['available_at']=pd.Timestamp('2024-01-02',tz='UTC')
        rows=c.rebuild_panel(market,graph,'2024-01-01','2024-01-03')
        self.assertIn('late:events_relative_7', c.admission(rows)[0]['exclusion_reasons'])
        del market[45]
        rows=c.rebuild_panel(market,graph,'2024-01-01','2024-01-03')
        self.assertIsNone(rows[0]['return_30'])

    def test_metrics_missing_class_and_invalid_probability(self):
        c=self.checker()
        self.assertIsNone(c.metrics([1,1],[.8,.9])['balanced_accuracy'])
        self.assertAlmostEqual(c.metrics([0,1],[.2,.8])['brier'], .04)
        with self.assertRaises(ValueError): c.metrics([1],[1.01])

    def test_comparison_rejects_tamper(self):
        c=self.checker()
        c.same({'x':1.0},{'x':1.0+1e-12})
        with self.assertRaises(ValueError): c.same({'x':1.0},{'x':1.1})
        with self.assertRaises(ValueError): c.same([1,2],[2,1])

    def test_guard_requires_exact_command_and_clean_exit(self):
        c=self.checker()
        guard=dict(command=['python','-B','run.py','--source','abc'],cwd='/tmp',
                   phase='complete',child_exit_code=0,limit_reason=None,cleanup_verified=True,
                   memory_events=dict(oom=0,oom_kill=0,oom_group_kill=0))
        c.guard_check(guard,guard['command'],'/tmp')
        with self.assertRaises(ValueError): c.guard_check(guard,['other'],'/tmp')
        guard['child_exit_code']=1
        with self.assertRaises(ValueError): c.guard_check(guard,guard['command'],'/tmp')

    def test_bootstrap_fixed_constant_contrasts(self):
        c=self.checker()
        rows=[dict(decision_at=d.isoformat(),fold='2024-01',y=1,M0_probability=.5,M1_probability=.6,M2_probability=.8) for d in pd.date_range('2024-01-01',periods=28,tz='UTC')]
        result=c.bootstrap(rows,14,2000,42)
        expected=np.log(.6/.8)
        self.assertAlmostEqual(result['summaries']['M2-M1:log_loss']['mean'],expected)
        np.testing.assert_allclose(result['summaries']['M2-M1:log_loss']['ci95'],[expected,expected])
        rows.pop(4)
        with self.assertRaises(ValueError): c.bootstrap(rows,14,2000,42)

    def test_decode_month_checks_checksum_and_2025_units(self):
        import io, zipfile, hashlib, calendar
        c=self.checker(); data=[]
        for d in pd.date_range('2025-01-01',periods=31,tz='UTC'):
            t=int(d.timestamp())*1000000
            data.append(','.join(map(str,[t,100,102,99,101,4,t+86400000000-1,402,3,2,201,0])))
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w') as z: z.writestr('ETHUSDT-1d-2025-01.csv','\n'.join(data))
        raw=buf.getvalue(); checksum=(hashlib.sha256(raw).hexdigest()+'  ETHUSDT-1d-2025-01.zip').encode()
        rows=c.decode_month('2025-01',raw,checksum)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['open'],100)
        with self.assertRaises(ValueError): c.decode_month('2025-01',raw,checksum.replace(b'zip',b'bad'))

    def test_saved_replay_and_unavailable_inference(self):
        import lightgbm as lgb
        c=self.checker(); market,graph=self.fixture()
        panel=c.rebuild_panel(market,graph,'2023-12-05','2024-01-03')
        sets={'M0':['return_1'],'M1':['return_1','events_log_count'],'M2':['return_1','events_log_count','stars_log_count']}
        params=dict(n_estimators=2,num_leaves=2,min_child_samples=2,n_jobs=1,verbosity=-1)
        config=dict(feature_sets=sets,model=dict(params=params),purge_gap='1D',folds=[dict(id='2024-01',start='2024-01-01T00:00:00Z',end='2024-01-03T00:00:00Z')],bootstrap=dict(required_start='2024-01-01T00:00:00Z',required_end_exclusive='2025-01-01T00:00:00Z',block_days=14,resamples=2000,seed=42))
        train=[r for r in panel if pd.Timestamp(r['label_end'])<=pd.Timestamp('2023-12-31',tz='UTC')]
        test=panel[-2:]; fits=[]; predictions=[{k:r[k] for k in ('decision_at','label_start','label_end','y')} for r in test]
        for r in predictions: r.update(fold='2024-01',majority_probability=float(np.mean([x['y'] for x in train])>.5))
        for arm,features in sets.items():
            model=lgb.LGBMClassifier(**params).fit(pd.DataFrame(train)[features],[r['y'] for r in train])
            fits.append(dict(fold='2024-01',arm=arm,params=params,train_days=[r['decision_at'] for r in train],test_days=[r['decision_at'] for r in test],model_text=model.booster_.model_to_string()))
            for r,p in zip(predictions,model.predict_proba(pd.DataFrame(test)[features])[:,1]): r[arm+'_probability']=float(p)
        result=c.verify_predictions(panel,config,fits,predictions,[dict(fold='2024-01',status='complete',error=None)])
        self.assertEqual(result['screening']['status'],'unavailable')
        predictions[0]['M2_probability']+=.01
        with self.assertRaises(ValueError): c.verify_predictions(panel,config,fits,predictions,[dict(fold='2024-01',status='complete',error=None)])

    def test_storage_rejects_trailing_zstd_and_false_size(self):
        import zstandard,hashlib
        c=self.checker(); raw=b'invented bytes'; stored=zstandard.ZstdCompressor().compress(raw)
        meta=dict(codec='zstd',raw_bytes=len(raw),raw_sha256=hashlib.sha256(raw).hexdigest(),stored_bytes=len(stored),stored_sha256=hashlib.sha256(stored).hexdigest())
        self.assertEqual(c.unpack(stored,meta),raw)
        stored+=b'trailing';meta.update(stored_bytes=len(stored),stored_sha256=hashlib.sha256(stored).hexdigest())
        with self.assertRaises((ValueError,zstandard.ZstdError)): c.unpack(stored,meta)

    def test_graph_role_conservation_and_empty_denominator(self):
        c=self.checker()
        roles=[0]*40;roles[0]=3;roles[24]=4;roles[32]=3
        day=dict(day='2024-01-01',source_admitted=True,graph_admitted=True,source_status='complete',graph_status='complete',events=12,nodes=4,directed_pairs=6,stars=3,dyads=2,triangles=1,overlap_nodes=5,nonzero_nodes=2,available_at=None,local40=dict(local40_sums=roles,unique_occurrences=6,overlap_node_count=5,nonzero_nodes=2))
        panel=dict(global_uniqueness_admitted=True,days=[day])
        rows,excluded=c.graph_rows(panel,full=False)
        self.assertEqual(rows[0]['available_at'],'2024-01-03T00:00:00+00:00')
        self.assertIsNone(day['available_at'])
        roles[24]=3
        with self.assertRaises(ValueError): c.graph_rows(panel,full=False)

    def test_full_synthetic_evaluator_archive_matches_independent_checker(self):
        import json
        c=self.checker()
        def module(name,path):
            spec=importlib.util.spec_from_file_location(name,path);result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
        parent=PATH.parent.parent
        production_features=module('synthetic_final_features',parent/'features.py')
        production_model=module('synthetic_final_model',parent/'model.py')
        config=json.loads((parent/'config.json').read_text())
        days=pd.date_range('2021-12-01','2025-01-01',tz='UTC')
        market=[dict(day=d,open=100+(i%7),close=100+(i%11),quote_volume=10+i%5,available_at=d+pd.Timedelta(days=1,minutes=5)) for i,d in enumerate(days)]
        graph=[dict(day=d,available_at=d+pd.Timedelta(days=2),events=12+i%9,nodes=4,directed_pairs=6,stars=i%3,dyads=i%4,triangles=i%2,overlap_nodes=5,nonzero_nodes=2) for i,d in enumerate(days)]
        panel,sets=production_features.build_panel(pd.DataFrame(market),pd.DataFrame(graph),start=config['decisions']['start'],end=config['decisions']['end_exclusive'])
        rebuilt=c.rebuild_panel(market,graph,config['decisions']['start'],config['decisions']['end_exclusive'])
        c.same(panel.to_dict('records'),rebuilt)
        fits=[]
        def audit(fold,arm,learner,train,test):
            fits.append(dict(fold=fold,arm=arm,params=config['model']['params'],model_text=learner.booster_.model_to_string(),train_days=train.decision_at.tolist(),test_days=test.decision_at.tolist()))
        result=production_model.evaluate(panel,audit_fit=audit)
        def records(value):
            if isinstance(value,pd.DataFrame):return c.clean(value.to_dict('records'))
            if isinstance(value,dict):return {k:records(v) for k,v in value.items()}
            return c.clean(value)
        result=records(result);predictions=result.pop('predictions')
        checked=c.verify_predictions(rebuilt,config,c.clean(fits),predictions,result['attempts'])
        c.same(result,checked)
        self.assertEqual(checked['inference']['status'],'available')
        self.assertEqual(len(predictions),366)
        partial=[r for r in predictions if r['fold']!='2024-01']
        attempts=[dict(a) for a in result['attempts']]; attempts[0].update(status='failed',error='invented inference failure')
        unavailable=c.verify_predictions(rebuilt,config,c.clean(fits),partial,attempts)
        self.assertEqual(unavailable['inference']['status'],'unavailable')
        self.assertEqual(len(unavailable['inference']['missing_dates']),31)
        fits[0]['train_days']=fits[0]['train_days'][:-1]
        with self.assertRaises(ValueError): c.verify_predictions(rebuilt,config,c.clean(fits),predictions,result['attempts'])

    def test_unclean_compute_guard_is_failure_evidence_not_admission(self):
        c=self.checker(); command=['python','-B','run.py','--source','invented']
        guard=dict(command=command,cwd='/invented',phase='complete',child_exit_code=-9,limit_reason='memory',cleanup_verified=True,memory_events=dict(oom=1,oom_kill=1,oom_group_kill=0))
        result=c.compute_evidence(guard,command,'/invented')
        self.assertFalse(result['clean'])
        self.assertIn('guard unclean exit',result['reason'])
        self.assertFalse(c.compute_evidence(None,command,'/invented')['clean'])
        with self.assertRaises(ValueError): c.compute_evidence(guard,['other'],'/invented')

    def test_checkpoint_chain_binds_claim_and_final_fits(self):
        import json,tempfile
        c=self.checker()
        fit=dict(fold='2024-01',arm='M0',train_days=['invented train day'],test_days=['invented test day'],params={},model_text='invented model text')
        envelope=dict(schema_version=1,experiment_id=c.EXPERIMENT,source='synthetic-source',claim_sha256='a'*64,sequence=0,fit=fit)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'fit-checkpoints';path.mkdir()
            file=path/'2024-01-M0.json';file.write_text(json.dumps(envelope))
            checked=c.checkpoint_evidence(path,'synthetic-source','a'*64,final_fits=[fit])
            self.assertEqual(checked['count'],1)
            self.assertFalse(checked['saved_models_replayed'])
            with self.assertRaises(ValueError): c.checkpoint_evidence(path,'other-source','a'*64)
            with self.assertRaises(ValueError): c.checkpoint_evidence(path,'synthetic-source','a'*64,final_fits=[])
            envelope['sequence']=1;file.write_text(json.dumps(envelope))
            with self.assertRaises(ValueError): c.checkpoint_evidence(path,'synthetic-source','a'*64)

    def test_missing_checkpoints_only_allowed_before_any_fit(self):
        import tempfile
        c=self.checker()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'missing'
            self.assertEqual(c.checkpoint_evidence(path,'s','h')['count'],0)
            with self.assertRaises(ValueError): c.checkpoint_evidence(path,'s','h',final_fits=[{}])

    def test_pending_checkpoint_is_partial_evidence_only(self):
        import tempfile
        c=self.checker()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory); (path/('.pending-'+'a'*32)).write_bytes(b'{interrupted invented bytes')
            checked=c.checkpoint_evidence(path,'s','h',allow_pending=True)
            self.assertEqual(checked['count'],0)
            self.assertEqual(len(checked['pending_files']),1)
            with self.assertRaises(ValueError): c.checkpoint_evidence(path,'s','h')

    def test_inference_exception_remains_unavailable_after_independent_validation(self):
        c=self.checker()
        computed=dict(inference=dict(status='available',result={'invented':1},missing_dates=[]),screening=dict(status='available',supported=True),counts=[{'n':366}])
        saved=dict(inference=dict(status='unavailable',reason='RuntimeError: invented failure',missing_dates=[],error_type='inference_failed'),screening=dict(status='unavailable',supported=None),counts=[{'n':366}])
        checked=c.check_saved_evaluation(computed,saved)
        self.assertTrue(checked)
        self.assertEqual(saved['screening']['status'],'unavailable')
        saved['counts'][0]['n']=365
        with self.assertRaises(ValueError): c.check_saved_evaluation(computed,saved)

if __name__ == '__main__': unittest.main()
