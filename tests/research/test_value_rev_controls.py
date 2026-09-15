"""Invented declared scores/clocks only; no market reads, ranks or books."""
from copy import deepcopy
import json
import unittest

from tradingagents import research_value_controls as c

D=1000000
EXECUTION={'inputs_sha256':'a'*64,'policy_sha256':'b'*64,'lag_ms':172800000,'action_ms':D+5000}


def fixture():
    cells={}
    for identity in c.CELLS:
        metric,breadth=identity.split('_')
        cohort=['A','B','C'] if metric=='fees' else ['B','D']
        fields={'cohort':cohort,'breadth':breadth,'decision_ms':D,'execution_ref':deepcopy(EXECUTION)}
        roles={}
        for index,role in enumerate(c.ROLES):
            roles[role]={**deepcopy(fields),'orientation':'low_is_long','score_source_sha256':str(index+1)*64,
                         'scores':{symbol:{'value':str(i-index),'available_ms':D} for i,symbol in enumerate(cohort)}}
        cells[identity]={**deepcopy(fields),'signals':roles}
    return cells


def assemble(cells,**kwargs):
    return c.assemble(cells,decision_ms=kwargs.get('decision_ms',D),execution_ref=kwargs.get('execution_ref',EXECUTION))


class ControlAssemblyTests(unittest.TestCase):
    def assert_unavailable(self,result,identity='fees_tercile',role='C1'):
        self.assertEqual(result['status'],'unavailable')
        self.assertEqual(set(result['cells']),set(c.CELLS))
        cell=result['cells'][identity]
        self.assertEqual(cell['status'],'unavailable')
        self.assertEqual(set(cell['signals']),set(c.ROLES))
        self.assertEqual(cell['signals'][role]['status'],'unavailable')
        self.assertEqual(set(cell['signals'][role]['scores']),set(cell['cohort']))
        return cell['signals'][role]

    def test_four_frozen_identities_both_breadths_and_unequal_metric_cohorts(self):
        inputs=fixture();original=deepcopy(inputs);result=assemble(inputs)
        self.assertEqual(inputs,original)
        self.assertEqual(result['status'],'declared_aligned')
        self.assertEqual(result['registered_cell_count'],4)
        for identity,cell in result['cells'].items():
            metric,breadth=identity.split('_')
            self.assertEqual(cell['registered_metric'],'mcap_over_'+metric+'_90d')
            self.assertEqual(cell['breadth'],breadth)
            for role in cell['signals'].values():
                self.assertEqual(role['cohort'],cell['cohort'])
                self.assertEqual(role['breadth'],breadth)
                self.assertEqual(role['execution_ref'],EXECUTION)
                self.assertEqual(set(role['scores']),set(cell['cohort']))
        self.assertNotEqual(result['cells']['fees_decile']['cohort'],result['cells']['revenue_decile']['cohort'])

    def test_no_admission_at_any_result_level(self):
        result=assemble(fixture())
        for obj in [result,*result['cells'].values(),*[r for x in result['cells'].values() for r in x['signals'].values()]]:
            self.assertFalse(obj['source_admission']);self.assertFalse(obj['empirical_admission'])
            self.assertEqual(obj['scope'],c.SCOPE)

    def test_control_breadth_mismatch(self):
        x=fixture();x['fees_tercile']['signals']['C1']['breadth']='decile'
        self.assert_unavailable(assemble(x))

    def test_different_control_cohort_no_intersection_or_substitution(self):
        x=fixture();x['fees_tercile']['signals']['C1']['cohort']=['A','B','OTHER']
        role=self.assert_unavailable(assemble(x))
        self.assertEqual(role['cohort'],['A','B','C'])
        self.assertEqual(role['declared_cohort'],['A','B','OTHER'])

    def test_missing_extra_and_duplicate_coverage(self):
        for fault in ('missing','extra','duplicate'):
            x=fixture();role=x['fees_tercile']['signals']['C1']
            if fault=='missing':del role['scores']['C']
            if fault=='extra':role['scores']['OTHER']={'value':0,'available_ms':D}
            if fault=='duplicate':role['cohort']=['A','B','B']
            with self.subTest(fault=fault):self.assert_unavailable(assemble(x))

    def test_late_and_unknown_availability(self):
        for value in (D+1,None,True,'1000000',-1):
            x=fixture();x['fees_tercile']['signals']['C1']['scores']['A']['available_ms']=value
            with self.subTest(value=value):
                role=self.assert_unavailable(assemble(x));self.assertEqual(role['scores']['A']['status'],'unavailable')

    def test_nonfinite_missing_and_permuted_nan_scores_never_zero_filled(self):
        for value in (float('nan'),float('inf'),float('-inf'),'NaN','Infinity',None,True):
            x=fixture();x['fees_tercile']['signals']['C1']['scores']['B']['value']=value
            with self.subTest(value=value):
                result=assemble(x);role=self.assert_unavailable(result)
                self.assertIsNone(role['scores']['B']['value']);json.dumps(result,allow_nan=False)
        x=fixture();scores=x['fees_tercile']['signals']['C1']['scores']
        scores['A']['value']=float('nan');scores['C']['value']='1'
        self.assert_unavailable(assemble(x))

    def test_explicit_orientations_retained_without_sign_guess(self):
        x=fixture();x['fees_tercile']['signals']['C2']['orientation']='high_is_long'
        result=assemble(x)
        self.assertEqual(result['status'],'declared_aligned')
        self.assertEqual(result['cells']['fees_tercile']['signals']['C2']['orientation'],'high_is_long')
        for direction in (None,'reversal','negative',True):
            x=fixture();x['fees_tercile']['signals']['C2']['orientation']=direction
            with self.subTest(direction=direction):self.assert_unavailable(assemble(x),role='C2')

    def test_common_execution_input_policy_lag_and_action_mismatch(self):
        for key,value in (('inputs_sha256','c'*64),('policy_sha256','d'*64),('lag_ms',0),('action_ms',D+6000)):
            x=fixture();x['fees_tercile']['signals']['C1']['execution_ref'][key]=value
            with self.subTest(key=key):self.assert_unavailable(assemble(x))

    def test_explicit_common_lag_is_not_inferred_or_widened(self):
        x=fixture();execution=dict(EXECUTION,lag_ms=999)
        for cell in x.values():
            cell['execution_ref']=deepcopy(execution)
            for role in cell['signals'].values():role['execution_ref']=deepcopy(execution)
        result=assemble(x,execution_ref=execution)
        self.assertEqual(result['status'],'declared_aligned')
        self.assertTrue(all(r['execution_ref']['lag_ms']==999 for cell in result['cells'].values() for r in cell['signals'].values()))
        self.assertFalse(result['empirical_admission'])

    def test_decision_mismatch_and_invalid_common_reference(self):
        x=fixture();x['fees_tercile']['signals']['C1']['decision_ms']=D-1
        self.assert_unavailable(assemble(x))
        for decision,execution in ((None,EXECUTION),(D,dict(EXECUTION,action_ms=D-1)),(D,dict(EXECUTION,policy_sha256='unproved'))):
            result=assemble(fixture(),decision_ms=decision,execution_ref=execution)
            self.assertEqual(len(result['cells']),4)
            self.assertTrue(all(row['status']=='unavailable' for row in result['cells'].values()))

    def test_missing_cells_and_roles_preserve_full_denominator(self):
        x=fixture();del x['fees_tercile'];del x['revenue_decile']['signals']['C2']
        result=assemble(x)
        self.assertEqual(len(result['cells']),4)
        self.assertEqual(result['cells']['fees_tercile']['status'],'unavailable')
        self.assertEqual(len(result['cells']['fees_tercile']['signals']),3)
        self.assertEqual(result['cells']['revenue_decile']['status'],'unavailable')
        self.assertEqual(result['cells']['revenue_decile']['signals']['strategy']['status'],'declared_aligned')
        self.assertEqual(result['cells']['revenue_decile']['signals']['C1']['status'],'declared_aligned')
        self.assertEqual(result['cells']['fees_decile']['status'],'declared_aligned')

    def test_unknown_cell_rejects_bundle_without_losing_four_cells(self):
        x=fixture();x['extra']=deepcopy(x['fees_decile'])
        result=assemble(x)
        self.assertEqual(set(result['cells']),set(c.CELLS))
        self.assertEqual(result['status'],'unavailable')

    def test_deterministic_assembly_digest_changes_with_score_not_just_supplied_hash(self):
        x=fixture();first=assemble(x)
        permuted=dict(reversed(list(x.items())))
        for cell in permuted.values():
            cell['cohort'].reverse()
            for role in cell['signals'].values():role['cohort'].reverse()
        self.assertEqual(first,assemble(permuted))
        x['fees_decile']['signals']['strategy']['scores']['A']['value']='8'
        self.assertNotEqual(first['assembly_sha256'],assemble(x)['assembly_sha256'])
