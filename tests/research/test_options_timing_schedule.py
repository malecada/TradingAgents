"""Invented timing boundaries only; transport children cannot start."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tradingagents.research_options_timing import schedule as s, transport
from tradingagents.research_options_timing.journal import Journal, digest

T=20000*s.DAY


class TimingScheduleTests(unittest.TestCase):
    def test_all_hourly_clocks_and_unchanged_other_calendars(self):
        from tradingagents.research_options_capture.schedule import calendar as historical
        selection={a:{'call':a+'-synthetic-C','put':a+'-synthetic-P','expiry_ms':T+7*s.DAY} for a in s.ASSETS}
        old=historical(T,selection);new=s.calendar(T,selection)
        for group in ('bootstrap','daily','final'):
            self.assertEqual(new[group],old[group])
        for group in ('known','selected'):
            for previous,current in zip(old[group],new[group],strict=True):
                expected=dict(previous,scheduled_ms=previous['scheduled_ms']+2000)
                self.assertEqual(current,expected)
                self.assertEqual(s.nominal_ms(T,current),previous['scheduled_ms'])
        self.assertEqual(sum(map(len,new.values())),17144)

    def test_nominal_identity_and_deadline_forgeries_refused(self):
        original=s.calendar(T)['known'][0]
        for replacement in ({'id':'h1057-options-time'},{'id':'h0000-other'},
                            {'scheduled_ms':T},{'deadline_ms':T+7000},
                            {'id':'h0001-options-time'}):
            with self.subTest(replacement=replacement),self.assertRaises(ValueError):
                s.nominal_ms(T,dict(original,**replacement))

    def test_own_exit_is_nominal_and_benchmark_retains_longer_asset(self):
        chosen={'BTC':{'call':'B-C','put':'B-P','expiry_ms':T+7*s.DAY},
                'ETH':{'call':'E-C','put':'E-P','expiry_ms':T+8*s.DAY}}
        rows=s.calendar(T,chosen)
        for group in ('known','selected'):
            for item in rows[group]:
                at=s.nominal_ms(T,item)
                if at==T+6*s.DAY:
                    self.assertFalse(s.post_exit(item['id'],at,chosen))
                if at==T+6*s.DAY+s.HOUR and item['id'].endswith('-btc-index'):
                    self.assertFalse(s.post_exit(item['id'],at,chosen))
                if at==T+6*s.DAY+s.HOUR and '-btc-call-' in item['id']:
                    self.assertTrue(s.post_exit(item['id'],at,chosen))

    def test_transport_release_and_absolute_deadline_before_any_child(self):
        item=s.calendar(T)['known'][0]
        for offset,deadline,error in [(1999,T+5000,'before scheduled'),(2000,T+7000,'matching durable'),
                                      (2000,T+5000,'synthetic child boundary')]:
            with self.subTest(offset=offset,deadline=deadline),tempfile.TemporaryDirectory() as td:
                root=Path(td);claim=root/'claim.json';claim.write_bytes(b'{}')
                with Journal(root/'raw',claim_path=claim,claim_sha256=digest(b'{}'),slots=[item],
                             total_cap=1024**2,terminal_reserve=4096,check_source=lambda:None) as journal:
                    journal.begin_group([item['id']],now_ms=T+2000)
                    with patch.object(transport.time,'time_ns',return_value=(T+offset)*1000000),\
                         patch.object(transport.time,'monotonic_ns',return_value=10**9),\
                         patch.object(transport.subprocess,'Popen',side_effect=RuntimeError('synthetic child boundary')) as spawn:
                        with self.assertRaisesRegex((ValueError,RuntimeError),error):
                            transport.collect(journal,[item['id']],deadline_ms=deadline)
                        self.assertEqual(spawn.call_count,1 if error=='synthetic child boundary' else 0)

    def test_elapsed_absolute_deadline_records_no_child_and_no_extension(self):
        item=s.calendar(T)['known'][0]
        for offset in (5000,5001,7000):
            with self.subTest(offset=offset),tempfile.TemporaryDirectory() as td:
                root=Path(td);claim=root/'claim.json';claim.write_bytes(b'{}')
                with Journal(root/'raw',claim_path=claim,claim_sha256=digest(b'{}'),slots=[item],
                             total_cap=1024**2,terminal_reserve=4096,check_source=lambda:None) as journal:
                    journal.begin_group([item['id']],now_ms=T+2000)
                    with patch.object(transport.time,'time_ns',return_value=(T+offset)*1000000),\
                         patch.object(transport.time,'monotonic_ns',return_value=10**9),\
                         patch.object(transport.subprocess,'Popen') as spawn:
                        result=transport.collect(journal,[item['id']],deadline_ms=T+5000)
                        spawn.assert_not_called()
                        metadata=result['sources'][item['id']]
                        self.assertFalse(metadata['attempted'])
                        self.assertEqual(metadata['controller_deadline_ms'],T+5000)
                        self.assertFalse(metadata['body_complete'])
