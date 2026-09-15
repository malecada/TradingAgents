"""Invented values, witnesses and stage bytes only; no empirical data or I/O."""
from copy import deepcopy
import json
import unittest

from tradingagents import research_value_readiness as r

H='a'*64


def observation(protocol='p',metric='dailyFees',value='100',status='observed',start='2026-08-04T00:00:00Z',end='2026-08-05T00:00:00Z'):
    return {'protocol':protocol,'metric':metric,'start_utc':start,'end_utc':end,'status':status,'value':value,'member_sha256':H}


def snapshot(identity,day):
    return {'snapshot_id':identity,'label':day,'manifest_sha256':H,'inventory_sha256':'b'*64,
            'completion_evidence':{'upper_bound_utc':day+'T12:00:01Z','inventory_sha256':'b'*64,'witness_sha256':'c'*64},
            'request_intervals':[{'request_id':'p-fees','start_utc':day+'T12:00:00Z','end_utc':day+'T12:00:01Z','receipt_sha256':'d'*64}]}


def pair():
    first=snapshot('one','2026-09-04');first['completion_evidence']['upper_bound_utc']='2026-09-04T12:00:00Z';first['request_intervals']=[]
    return r.snapshot_pair(first,snapshot('two','2026-09-18'),registration_sha256=H,clarification_sha256='e'*64)


def stage(name,pair_bytes=None,**kwargs):
    raw=pair_bytes or pair()
    return r.stage_record(name,raw,expected_pair_sha256=r.sha(raw),source_code_sha256='f'*64,verdict=True,result={'invented':True},**kwargs)


class ComparisonTests(unittest.TestCase):
    def test_opposing_protocol_revisions_do_not_cancel(self):
        first=[observation('a'),observation('b')]
        second=[observation('a',value='120'),observation('b',value='80')]
        self.assertEqual(sum(int(v['value']) for v in first),sum(int(v['value']) for v in second))
        result=r.compare_protocol_days(first,second)
        fees=result['metrics']['dailyFees']
        self.assertEqual((fees['comparable_common'],fees['changed_gt_10pct']),(2,2))
        self.assertEqual(fees['changed_share'],{'numerator':1,'denominator':1})
        self.assertEqual(result['scope'],r.SCOPE);self.assertFalse(result['source_admission'])
        self.assertEqual(fees['cells'][0]['first_rows'][0]['member_sha256'],H)

    def test_metrics_not_pooled_and_exact_5pct_boundary(self):
        first=[];second=[]
        for metric in r.METRICS:
            for i in range(20):
                first.append(observation(str(i),metric))
                changed=i<(1 if metric=='dailyFees' else 2)
                second.append(observation(str(i),metric,'120' if changed else '100'))
        out=r.compare_protocol_days(first,second)['metrics']
        self.assertIs(out['dailyFees']['observed_subset_within_5pct'],True)
        self.assertIs(out['dailyRevenue']['observed_subset_within_5pct'],False)
        self.assertEqual(out['dailyFees']['comparable_common'],20)
        self.assertEqual(out['dailyRevenue']['comparable_common'],20)

    def test_strict_change_boundary_uses_exact_arithmetic(self):
        out=r.compare_protocol_days([observation('a'),observation('b')],
            [observation('a',value='110'),observation('b',value='110.0000000000000000000000000000000000000000000000000001')])['metrics']['dailyFees']
        self.assertEqual([c['changed_gt_10pct'] for c in out['cells']],[False,True])

    def test_zero_cases_distinct_from_missing_and_percentage_undefined(self):
        first=[observation('same',value='0'),observation('up',value='0'),observation('down',value='10'),observation('missing',value='0')]
        second=[observation('same',value='0'),observation('up',value='1'),observation('down',value='0'),observation('missing',value=None,status='missing')]
        out=r.compare_protocol_days(first,second)['metrics']['dailyFees'];cells={c['protocol']:c for c in out['cells']}
        self.assertEqual(out['comparable_common'],3);self.assertEqual(out['changed_gt_10pct'],2)
        self.assertEqual(cells['same']['classification'],'zero_to_zero')
        self.assertIsNone(cells['same']['relative_change']);self.assertIsNone(cells['up']['relative_change'])
        self.assertEqual(cells['missing']['classification'],'missing_or_failed_common')
        self.assertIn('missing_or_failed_common',out['proposed_completeness_blockers'])

    def test_missing_revenue_never_inherits_fee_screen(self):
        out=r.compare_protocol_days([observation()],[observation()])['metrics']
        self.assertIs(out['dailyFees']['observed_subset_within_5pct'],True)
        self.assertIsNone(out['dailyRevenue']['observed_subset_within_5pct'])
        self.assertIn('no_comparable_common_observations',out['dailyRevenue']['proposed_completeness_blockers'])

    def test_deletion_addition_and_recent_union_preserved(self):
        first=[observation('stable'),observation('deleted'),observation('recent',start='2026-08-05T00:00:00Z',end='2026-08-06T00:00:00Z')]
        second=[observation('stable'),observation('added')]
        out=r.compare_protocol_days(first,second)['metrics']['dailyFees']
        self.assertEqual(out['counts']['union_keys'],4)
        self.assertEqual(out['counts']['first_only_keys'],2)
        self.assertEqual(out['counts']['first_only_deletion'],1)
        self.assertEqual(out['counts']['second_only_addition'],1)
        self.assertEqual(out['counts']['excluded_recent'],1)
        self.assertIn('first_only_deletion',out['proposed_completeness_blockers'])

    def test_duplicate_rows_are_retained_not_overwritten(self):
        out=r.compare_protocol_days([observation(),observation(value='120')],[observation()])['metrics']['dailyFees']
        self.assertEqual(out['counts']['union_keys'],1)
        self.assertEqual(out['comparable_common'],0)
        self.assertEqual(len(out['cells'][0]['first_rows']),2)
        self.assertIn('duplicate_interval',out['proposed_completeness_blockers'])

    def test_conflicting_day_end_keeps_protocol_day_identity(self):
        out=r.compare_protocol_days([observation(),observation(end='2026-08-05T12:00:00Z')],[observation()])['metrics']['dailyFees']
        self.assertEqual(out['counts']['union_keys'],1)
        self.assertEqual(out['cells'][0]['classification'],'invalid_interval')

    def test_negative_nonfinite_or_float_values_stay_invalid(self):
        for value in ('-1','NaN','Infinity',1.0):
            with self.subTest(value=value):
                out=r.compare_protocol_days([observation()],[observation(value=value)])['metrics']['dailyFees']
                self.assertEqual(out['cells'][0]['classification'],'invalid_value')
                self.assertEqual(out['comparable_common'],0)

    def test_missing_cannot_carry_zero_and_unknown_metric_refused(self):
        for bad in (observation(status='missing',value='0'),observation(metric='token_total')):
            with self.assertRaises(ValueError):r.compare_protocol_days([bad],[])


class PairTests(unittest.TestCase):
    def test_exact_14day_boundary_and_immutable_snapshot_pair(self):
        raw=pair();value=r.verify_pair(raw,r.sha(raw))
        self.assertEqual(value['interval_readiness'],'supported_under_referenced_witnesses')
        self.assertFalse(value['source_admission'])
        value['first']['label']='forged'
        self.assertNotEqual(r.canonical(value),raw)
        self.assertEqual(r.verify_pair(raw,r.sha(raw))['first']['label'],'2026-09-04')

    def test_forged_date_label_does_not_prove_gap(self):
        first=snapshot('one','2026-09-04');second=snapshot('two','2026-09-05');second['label']='2026-10-18'
        value=json.loads(r.snapshot_pair(first,second,registration_sha256=H,clarification_sha256=H))
        self.assertEqual(value['interval_readiness'],'unavailable')

    def test_every_second_request_must_satisfy_gap(self):
        raw=pair();value=json.loads(raw);second=value['second']
        early=deepcopy(second['request_intervals'][0]);early.update(request_id='p-revenue',start_utc='2026-09-18T11:59:59.999999Z')
        second['request_intervals'].append(early)
        rebuilt=json.loads(r.snapshot_pair(value['first'],second,registration_sha256=H,clarification_sha256='e'*64))
        self.assertEqual(rebuilt['interval_readiness'],'unavailable')

    def test_start_only_first_vintage_stays_unavailable(self):
        value=json.loads(pair());value['first']['completion_evidence']=None
        rebuilt=json.loads(r.snapshot_pair(value['first'],value['second'],registration_sha256=H,clarification_sha256=H))
        self.assertIsNone(rebuilt['earliest_second_request_utc'])
        self.assertIn('first completion upper bound unavailable',rebuilt['reasons'])

    def test_wrong_inventory_and_non_utc_labels_refused(self):
        value=json.loads(pair());value['first']['completion_evidence']['inventory_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'another inventory'):r.snapshot_pair(value['first'],value['second'],registration_sha256=H,clarification_sha256=H)
        for bad in ('2026-09-04','2026-09-04T12:00:00+02:00'):
            value=json.loads(pair());value['first']['completion_evidence']['upper_bound_utc']=bad
            with self.assertRaisesRegex(ValueError,'explicit UTC'):r.snapshot_pair(value['first'],value['second'],registration_sha256=H,clarification_sha256=H)

    def test_external_pair_anchor_and_tampered_readiness_refused(self):
        raw=pair()
        with self.assertRaisesRegex(ValueError,'anchor mismatch'):r.verify_pair(raw,'0'*64)
        value=json.loads(raw);value['interval_readiness']='admitted';changed=r.canonical(value)
        with self.assertRaisesRegex(ValueError,'canonical bytes changed'):r.verify_pair(changed,r.sha(changed))


class StageTests(unittest.TestCase):
    def test_ordered_proposed_chain_is_not_actual_admission(self):
        p0=stage('P0');p1=stage('P1',predecessor=p0,predecessor_sha256=r.sha(p0));p2=stage('P2',predecessor=p1,predecessor_sha256=r.sha(p1))
        self.assertEqual(json.loads(p2)['predecessor_sha256'],r.sha(p1))
        self.assertFalse(json.loads(p2)['source_admission']);self.assertEqual(json.loads(p2)['scope'],r.SCOPE)
        self.assertNotIn('pass',json.loads(p0))

    def test_failed_or_unavailable_predecessor_blocks_next_probe(self):
        for verdict in (False,None):
            raw=pair();p0=r.stage_record('P0',raw,expected_pair_sha256=r.sha(raw),source_code_sha256='f'*64,verdict=verdict,result={})
            with self.assertRaisesRegex(ValueError,'predecessor blocks'):stage('P1',predecessor=p0,predecessor_sha256=r.sha(p0))

    def test_wrong_pair_predecessor_digest_and_skipped_stage_refused(self):
        p0=stage('P0');value=json.loads(pair());value['second']['label']='different-vintage-label'
        other=r.snapshot_pair(value['first'],value['second'],registration_sha256=H,clarification_sha256='e'*64)
        with self.assertRaisesRegex(ValueError,'pair/source mismatch'):stage('P1',other,predecessor=p0,predecessor_sha256=r.sha(p0))
        with self.assertRaisesRegex(ValueError,'bytes changed'):stage('P1',predecessor=p0,predecessor_sha256='0'*64)
        with self.assertRaisesRegex(ValueError,'stage/pair/source mismatch'):stage('P2',predecessor=p0,predecessor_sha256=r.sha(p0))

    def test_repeat_terminal_non_boolean_and_grid_refused(self):
        p0=stage('P0');identity=json.loads(p0)['stage_id']
        with self.assertRaisesRegex(ValueError,'already consumed'):stage('P0',occupied_stage_ids=[identity])
        with self.assertRaisesRegex(ValueError,'terminal'):stage('P0',terminal_seen=True)
        raw=pair()
        for verdict in (1,'yes'):
            with self.assertRaisesRegex(ValueError,'Boolean'):r.stage_record('P0',raw,expected_pair_sha256=r.sha(raw),source_code_sha256='f'*64,verdict=verdict,result={})
        with self.assertRaisesRegex(ValueError,'P0/P1/P2'):stage('grid')


if __name__=='__main__':unittest.main()
