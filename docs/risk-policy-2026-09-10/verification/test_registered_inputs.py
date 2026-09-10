"""Synthetic admission checks; no existing market values are loaded."""
import copy
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

import pandas as pd


def implementation():
    path = Path(__file__).with_name('verify_registered_inputs.py')
    if not path.exists(): raise AssertionError('risk-policy admission checker is not implemented')
    sys.path.insert(0, str(path.parent))
    try:
        spec = importlib.util.spec_from_file_location('risk_policy_admission_test', path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


class AdmissionTests(unittest.TestCase):
    def test_exact_timestamp_clock_and_schema_are_required(self):
        m = implementation()
        expected = pd.date_range('2021-11-07', periods=4, tz='UTC')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'synthetic.parquet'
            pd.DataFrame({'Date': expected, 'Close': [100., 101., 102., 103.]}).to_parquet(path)
            result = m.check_clock(path, 'Date', expected)
            self.assertEqual(result['rows'], 4)
            for clock in (expected[:-1], expected.insert(1, expected[0]), expected[::-1],
                          expected.append(pd.date_range('2025-04-01', periods=1, tz='UTC')),
                          expected.insert(1, pd.NaT)):
                pd.DataFrame({'Date': clock}).to_parquet(path)
                with self.subTest(clock=repr(clock)), self.assertRaises(ValueError):
                    m.check_clock(path, 'Date', expected)

    def test_clock_read_materializes_only_declared_timestamp_column(self):
        from unittest.mock import patch
        import pyarrow as pa
        m = implementation(); expected = pd.date_range('2021-11-07', periods=3, tz='UTC')
        class TimestampOnly:
            def read(self, *, columns):
                self.columns = columns
                if columns != ['Date']: raise AssertionError('forbidden financial-value read')
                return pa.table({'Date': expected})
        fake = TimestampOnly()
        with patch.object(m.pq, 'ParquetFile', return_value=fake):
            m.check_clock(Path('synthetic.parquet'), 'Date', expected)
        self.assertEqual(fake.columns, ['Date'])

    def test_gate_cells_must_equal_config_major_fixed_four_arms(self):
        m = implementation()
        configurations = [{'name': f'config{i}'} for i in range(18)]
        gate = {'configurations': configurations, 'arms': copy.deepcopy(m.ARMS),
                'coins': ['bitcoin','ethereum'], 'variants': list(m.VARIANTS),
                'expected_configurations':18, 'expected_identities':72,
                'expected_index_evaluations':288, 'expected_sleeve_books':576,
                'expected_shadows':72, 'expected_direct_contrasts':54,
                'expected_target_dates':1241, 'expected_trace_dates':1240,
                'development_window':['2021-11-07','2025-03-31'],
                'return_window':['2021-11-08','2025-03-31'],
                'allow_holdout':False, 'models_refit':False, 'network_allowed':False}
        gate['cells'] = [{'id':f'{config["name"]}|{arm["id"]}', 'configuration':config,
                          'arm':arm['id'], 'sizing':arm['sizing'], 'reentry':arm['reentry']}
                         for config in configurations for arm in m.ARMS]
        m.check_gate_schema(gate)
        for field in ('cells','arms','allow_holdout','expected_sleeve_books','development_window'):
            bad = copy.deepcopy(gate)
            if field == 'cells': bad[field][0],bad[field][1] = bad[field][1],bad[field][0]
            if field == 'arms': bad[field][0]['sizing'] = 'daily'
            if field == 'allow_holdout': bad[field] = True
            if field == 'expected_sleeve_books': bad[field] = 575
            if field == 'development_window': bad[field][1] = '2025-04-01'
            with self.subTest(field=field), self.assertRaises(ValueError): m.check_gate_schema(bad)


if __name__ == '__main__': unittest.main()
