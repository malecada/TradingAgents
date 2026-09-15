"""Invented clocks/transport only. No market or account requests."""
import json
import os
import base64
import subprocess
import sys
import time
from types import SimpleNamespace
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tradingagents.research_options_timing import schedule, worker
from tradingagents.research_options_timing.journal import encode, digest
from tradingagents.research_options_timing.transport import request_url

T=20000*schedule.DAY
CHOICES={a:{'status':'complete','selected':{'call':a+'-241101-100-C','put':a+'-241101-100-P',
                                        'expiry_ms':T+30*schedule.DAY}} for a in schedule.ASSETS}


class ScheduleTests(unittest.TestCase):
    def test_exact_denominator_windows_and_routes(self):
        slots=schedule.calendar(T,worker.selected_projection(CHOICES))
        self.assertEqual({k:len(v) for k,v in slots.items()},
                         {'bootstrap':3,'known':8456,'selected':8456,'daily':225,'final':4})
        self.assertEqual(sum(map(len,slots.values())),17144)
        for rows in slots.values():
            self.assertEqual(len({s['id'] for s in rows}),len(rows))
            for s in rows:
                self.assertEqual(s['deadline_ms']-s['scheduled_ms'],3000 if s['id'].startswith('h') else 5000)
                self.assertTrue(request_url(s['request']).startswith('https://'))
        self.assertEqual(slots['bootstrap'][0]['scheduled_ms'],T-60000)
        self.assertEqual(slots['known'][-1]['scheduled_ms'],T+44*schedule.DAY+2000)
        final=slots['final']
        self.assertEqual(final[0]['request']['parameters']['endTime']+1,final[1]['request']['parameters']['startTime'])
        self.assertEqual(final[1]['request']['parameters']['endTime'],T+44*schedule.DAY+5000)
        self.assertEqual(final[0]['scheduled_ms'],T+45*schedule.DAY)

    def test_minute_and_bool_entry_refused(self):
        for value in (True,T+1,0):
            with self.assertRaises(ValueError):schedule.calendar(value)

    def test_exit_included_post_exit_preserved(self):
        selection=worker.selected_projection(CHOICES)
        exit_ms=T+29*schedule.DAY
        self.assertFalse(schedule.post_exit('h0696-btc-call-depth',exit_ms,selection))
        self.assertTrue(schedule.post_exit('h0697-btc-call-depth',exit_ms+schedule.HOUR,selection))
        self.assertFalse(schedule.post_exit('h0697-options-time',exit_ms+schedule.HOUR,selection))
        selection['ETH']=dict(selection['ETH'],expiry_ms=T+40*schedule.DAY)
        self.assertFalse(schedule.post_exit('h0697-btc-index',exit_ms+schedule.HOUR,selection))
        self.assertTrue(schedule.post_exit('h0697-btc-perp-depth',exit_ms+schedule.HOUR,selection))
        self.assertTrue(schedule.post_exit('h1000-btc-index',T+40*schedule.DAY,selection))

    def test_unknown_selection_no_fallback(self):
        with self.assertRaises(ValueError):worker.selected_projection({'BTC':{'status':'unavailable'},'ETH':CHOICES['ETH']})


class WorkerTests(unittest.TestCase):
    def execute(self, *, deny=False, unavailable=False, start_offset=-60000, real_adapter=False, restart=False, known_elapsed=0, choose_elapsed=0, interrupt_before_selection=False, interrupt_after_selection=False):
        with tempfile.TemporaryDirectory() as td:
            package=Path(td)/'package';package.mkdir();data=Path(td)/'data'
            claim=encode({'synthetic':True});(package/'claim.json').write_bytes(claim)
            from tests.research import test_options_capture_adapter as fixture
            entry=fixture.T if real_adapter else T
            initial,known,_=fixture.initial()
            for row in known.values():
                meta=row['metadata']
                for key in ('request_ms','retrieval_ms','controller_retrieval_ms','controller_window_start_ms'):
                    if key in meta:meta[key]+=2000
                for key in ('request_monotonic_ns','retrieval_monotonic_ns','controller_retrieval_monotonic_ns','controller_window_start_monotonic_ns'):
                    if key in meta:meta[key]+=2000000000
                value=json.loads(base64.b64decode(row['body_base64']))
                for key in ('time','serverTime','T','E'):
                    if key in value:value[key]+=2000
                raw=json.dumps(value,separators=(',',':')).encode()
                row.update(body_base64=base64.b64encode(raw).decode(),body_bytes=len(raw),body_sha256=digest(raw))
                meta.update(body_bytes=len(raw),body_sha256=digest(raw))
            spec={'entry_ms':entry,'lease_not_before_ms':entry-120000,'lease_expires_ms':entry+45*schedule.DAY+60000,'data_root':str(data),
                  'claim_sha256':digest(claim)}
            clock=[entry+start_offset];attempts=[];crashed=[False]
            def sleep(seconds):clock[0]+=max(1,int(seconds*1000))
            def acquire(journal,names,*,deadline_ms):
                for name in names:
                    slot=journal.slots[name]
                    self.assertGreaterEqual(clock[0],slot['scheduled_ms'])
                    self.assertEqual(deadline_ms,slot['deadline_ms'])
                    if name.startswith('h'):
                        nominal=schedule.nominal_ms(entry,slot)
                        self.assertEqual(deadline_ms,nominal+5000)
                        self.assertGreaterEqual(clock[0],nominal+2000)
                self.assertTrue(all((journal.path/('intent-'+n+'.json')).exists() for n in names))
                attempts.extend(names)
                for n in names:
                    row=initial if n=='initial-options-rules' else known.get(n.removeprefix('h0000-'))
                    if real_adapter and row is not None:journal.record(n,base64.b64decode(row['body_base64']),metadata=row['metadata'])
                    else:journal.record(n,b'{}',metadata={'invented':True})
                if names[0]=='h0000-options-time':
                    clock[0]+=known_elapsed
                    if interrupt_before_selection and not crashed[0]:
                        crashed[0]=True
                        raise KeyboardInterrupt('invented interruption before selection')
                if '-call-' in names[0]:
                    if restart and not crashed[0]:
                        crashed[0]=True
                        raise KeyboardInterrupt('invented capture interruption')
                    (data/'STOP').write_text('synthetic stop')
                return {'halt_on_access_restriction':deny}
            def choose(*args,**kwargs):
                self.assertEqual(kwargs['entry_ms'],entry)
                clock[0]+=choose_elapsed
                self.assertNotIn('h0000-options-time',args[1])
                if real_adapter:
                    from tradingagents.research_options_timing.adapter import select_initial
                    return select_initial(*args,**kwargs)
                return {'BTC':{'status':'unavailable'},'ETH':CHOICES['ETH']} if unavailable else CHOICES
            original_publish=worker.publish
            def publish(path,value):
                original_publish(path,value)
                if interrupt_after_selection and path.name=='selection.json' and not crashed[0]:
                    crashed[0]=True
                    raise KeyboardInterrupt('invented interruption after immutable selection')
            with patch.object(worker,'assignment',return_value=spec),patch.object(worker,'publish',side_effect=publish):
                if restart:
                    with self.assertRaises(KeyboardInterrupt):worker.run(package,data,'a'*64,acquisition=acquire,choose=choose,now=lambda:clock[0],sleep=sleep)
                    clock[0]=entry+2500 if interrupt_before_selection or interrupt_after_selection else entry+schedule.HOUR
                result=worker.run(package,data,'a'*64,acquisition=acquire,choose=choose,now=lambda:clock[0],sleep=sleep)
                with self.assertRaisesRegex(ValueError,'sealed source'):
                    worker.run(package,data,'a'*64,acquisition=acquire,choose=choose,now=lambda:clock[0],sleep=sleep)
            retained=json.loads((data/'source-seal.json').read_text())
            self.assertEqual(retained,result)
            return result,attempts

    def test_durable_split_entry_then_stop(self):
        result,attempts=self.execute()
        self.assertEqual(len(attempts),19)
        self.assertEqual(len(set(attempts)),19)
        self.assertEqual(result['status'],'failed')
        self.assertIn('explicit stop',result['reason'])
        self.assertEqual(result['unresolved_selected_slots'],0)
        self.assertEqual(result['intended_slot_count'],17144)

    def test_actual_adapter_selects_before_option_requests(self):
        result,attempts=self.execute(real_adapter=True)
        self.assertEqual(len(attempts),19)
        self.assertIsNotNone(result['selection_sha256'])
        self.assertIn('explicit stop',result['reason'])

    def test_actual_adapter_recovery_binds_same_initial_receipts(self):
        result,attempts=self.execute(real_adapter=True,restart=True)
        self.assertEqual(len(attempts),35)
        self.assertEqual(len(set(attempts)),35)
        self.assertIn('explicit stop',result['reason'])

    def test_known_latency_uses_remaining_window_without_second_delay(self):
        result,attempts=self.execute(known_elapsed=2900)
        self.assertEqual(len(attempts),19)
        self.assertIn('explicit stop',result['reason'])

    def test_late_selection_cannot_extend_deadline(self):
        result,attempts=self.execute(choose_elapsed=3001)
        self.assertEqual(len(attempts),11)
        self.assertIn('selection missed entry deadline',result['reason'])

    def test_consumed_known_without_selection_cannot_restart_entry(self):
        result,attempts=self.execute(restart=True,interrupt_before_selection=True)
        self.assertEqual(len(attempts),11)
        self.assertEqual(len(set(attempts)),11)
        self.assertIn('consumed without immutable selection',result['reason'])
        self.assertEqual(result['unresolved_selected_slots'],8456)

    def test_restart_after_immutable_selection_uses_remaining_entry_window(self):
        result,attempts=self.execute(restart=True,interrupt_after_selection=True,real_adapter=True)
        self.assertEqual(len(attempts),19)
        self.assertEqual(len(set(attempts)),19)
        self.assertIn('explicit stop',result['reason'])
        self.assertIsNotNone(result['selection_sha256'])

    def test_access_denial_stops_later_groups(self):
        result,attempts=self.execute(deny=True)
        self.assertEqual(len(attempts),3)
        self.assertIn('access restriction',result['reason'])
        self.assertEqual(result['unresolved_selected_slots'],8456)

    def test_selection_failure_no_option_probe(self):
        result,attempts=self.execute(unavailable=True)
        self.assertEqual(len(attempts),11)
        self.assertIn('selection unavailable',result['reason'])
        self.assertEqual(result['unresolved_selected_slots'],8456)

    def test_restart_after_entry_never_replaces_entry(self):
        result,attempts=self.execute(start_offset=6000)
        self.assertEqual(attempts,[])
        self.assertIn('initial selection absent',result['reason'])

    def test_external_anchor_fails_before_parse(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);(p/'assignment.json').write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError,'external assignment hash'):
                worker.assignment(p,'0'*64)

    def test_frozen_package_and_claim_clock_binding(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            files={}
            for name in worker.PACKAGE_FILES:
                dest=p/name;dest.parent.mkdir(parents=True,exist_ok=True)
                dest.write_bytes(b'# invented frozen module\n');files[name]=digest(dest.read_bytes())
            def iso(ms):return datetime.fromtimestamp(ms/1000,timezone.utc).isoformat()
            claim={'source':'b'*40,'episode_protocol':{'schema_version':3,'hourly_acquisition_delay_ms':2000,'worker_lease':{'not_before':iso(T-120000),'expires_at':iso(T+45*schedule.DAY+60000)},
                  'observation_window':{'start':iso(T),'end':iso(T+44*schedule.DAY+5000)}}}
            (p/'claim.json').write_bytes(encode(claim))
            value={'schema_version':1,'entry_ms':T,'lease_not_before_ms':T-120000,'lease_expires_ms':T+45*schedule.DAY+60000,
                   'claim_path':'claim.json','claim_sha256':digest(encode(claim)),'package_files':files,
                   'journal_caps':worker.CAPS,'terminal_reserves':worker.RESERVES,'authority':'raw-worker-only',
                   'target':'options-timing-20260915','source_commit':'b'*40,'data_root':str(p/'data'),'host_identity':os.uname().nodename}
            raw=encode(value);(p/'assignment.json').write_bytes(raw)
            with patch.object(worker,'__file__',str(p/'tradingagents/research_options_timing/worker.py')):
                self.assertEqual(worker.assignment(p,digest(raw)),value)
                extra=p/'tradingagents/__init__.py';extra.write_text('# unregistered import')
                with self.assertRaisesRegex(ValueError,'unregistered package member'):worker.assignment(p,digest(raw))
                extra.unlink()
                dest=p/'tradingagents/research_options_timing/schedule.py';dest.write_bytes(b'# altered\n')
                with self.assertRaisesRegex(ValueError,'frozen source changed'):worker.assignment(p,digest(raw))
                dest.write_bytes(b'# invented frozen module\n')
                for version,delay in ((2,2000),(3,0),(3,3000)):
                    claim['episode_protocol'].update(schema_version=version,hourly_acquisition_delay_ms=delay)
                    (p/'claim.json').write_bytes(encode(claim));value['claim_sha256']=digest(encode(claim))
                    raw=encode(value);(p/'assignment.json').write_bytes(raw)
                    with self.subTest(version=version,delay=delay),self.assertRaisesRegex(ValueError,'fixed timing protocol'):
                        worker.assignment(p,digest(raw))
                claim['episode_protocol'].update(schema_version=3,hourly_acquisition_delay_ms=2000)
                (p/'claim.json').write_bytes(encode(claim));value['claim_sha256']=digest(encode(claim))
                value['target']='options-episode-20260911';raw=encode(value);(p/'assignment.json').write_bytes(raw)
                with self.assertRaisesRegex(ValueError,'raw worker authority'):worker.assignment(p,digest(raw))
                value['target']='options-timing-20260915'
                claim['episode_protocol']['worker_lease']['expires_at']=iso(T+46*schedule.DAY)
                (p/'claim.json').write_bytes(encode(claim))
                value['claim_sha256']=digest(encode(claim));raw=encode(value);(p/'assignment.json').write_bytes(raw)
                with self.assertRaisesRegex(ValueError,'claim worker lease mismatch'):worker.assignment(p,digest(raw))

    def test_alternate_data_root_refused_without_http_or_lock(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);wrong=p/'alternate'
            with patch.object(worker,'assignment',return_value={'data_root':str(p/'bound')}), patch.object(worker,'collect') as network:
                with self.assertRaisesRegex(ValueError,'data root mismatch'):worker.run(p,wrong,'a'*64)
                with self.assertRaisesRegex(ValueError,'data root mismatch'):worker.supervise(p,wrong,'a'*64)
                network.assert_not_called()
            self.assertFalse(wrong.exists())

    def test_same_root_supervisor_lock_prevents_duplicate_child(self):
        import fcntl
        with tempfile.TemporaryDirectory() as td:
            data=Path(td)
            with (data/'supervisor.lock').open('w') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                with patch.object(worker,'assignment',return_value={'data_root':str(data)}),patch.object(worker.subprocess,'Popen') as child:
                    with self.assertRaises(BlockingIOError):worker.supervise(data,data,'a'*64)
                    child.assert_not_called()

    def test_supervisor_retains_failure_and_kill_reason(self):
        original=subprocess.Popen
        for kill in (False,True):
            with self.subTest(kill=kill), tempfile.TemporaryDirectory() as td:
                p=Path(td);data=p/'data';wall=int(time.time()*1000)
                spec={'data_root':str(data),'lease_not_before_ms':wall-1000,'lease_expires_ms':wall+(300 if kill else 5000)}
                code="import time; time.sleep(10)" if kill else "import sys; sys.stderr.write('invented failure'); sys.exit(3)"
                def fake(command,**kwargs):
                    self.assertEqual(command[1:4],['-I','-B',str(p/'release_bootstrap.py')])
                    return original([sys.executable,'-B','-c',code],**kwargs)
                affinity=os.sched_getaffinity(0)
                try:
                    with patch.object(worker,'assignment',return_value=spec),patch.object(worker.subprocess,'Popen',side_effect=fake):
                        if kill:
                            with self.assertRaisesRegex(RuntimeError,'lease expired'):worker.supervise(p,data,'a'*64)
                        else:self.assertEqual(worker.supervise(p,data,'a'*64),3)
                finally:os.sched_setaffinity(0,affinity)
                record=json.loads((data/'supervisor-exit-000000.json').read_text())
                self.assertEqual(record['child_exit_code'],-9 if kill else 3)
                if kill:self.assertIn('lease expired',record['reason'])
                else:self.assertEqual(base64.b64decode(record['stderr_base64']),b'invented failure')

    def test_actual_bootstrap_forwards_isolated_child_arguments(self):
        with tempfile.TemporaryDirectory() as td:
            package=Path(td)/'package';package.mkdir();data=Path(td)/'data'
            files={}
            root=Path(__file__).resolve().parents[2]
            for name in worker.PACKAGE_FILES:
                p=package/name;p.parent.mkdir(parents=True,exist_ok=True)
                body=(root/'scripts/options_timing_release_bootstrap.py').read_bytes() if name=='release_bootstrap.py' else b'# invented module\n'
                if name=='tradingagents/research_options_timing/worker.py':
                    body=b'import json,sys; print(json.dumps({"isolated":sys.flags.isolated,"args":sys.argv[1:]}))\n'
                p.write_bytes(body);files[name]=digest(body)
            (package/'claim.json').write_bytes(b'{}')
            assignment={'package_files':files,'claim_sha256':digest(b'{}'),'data_root':str(data),'host_identity':os.uname().nodename}
            raw=encode(assignment);(package/'assignment.json').write_bytes(raw);expected=digest(raw)
            command=[sys.executable,'-I','-B',str(package/'release_bootstrap.py'),str(package),str(data),expected,'--child-fd','99']
            completed=subprocess.run(command,check=True,capture_output=True,text=True,timeout=10)
            value=json.loads(completed.stdout)
            self.assertEqual(value['isolated'],1)
            self.assertEqual(value['args'],[str(package),str(data),expected,'--child-fd','99'])

    def test_filesystem_reservation_and_inode_bounds(self):
        values=dict(f_frsize=4096,f_bsize=4096,f_bavail=8*1024**3//4096,f_favail=1200258)
        with patch.object(worker.os,'statvfs',return_value=SimpleNamespace(**values)):
            worker.disk_preflight(Path('/synthetic'))
        for key,value in [('f_frsize',8192),('f_bsize',8192),('f_bavail',values['f_bavail']-1),('f_favail',1200257)]:
            with self.subTest(key=key),patch.object(worker.os,'statvfs',return_value=SimpleNamespace(**dict(values,**{key:value}))):
                with self.assertRaises(ValueError):worker.disk_preflight(Path('/synthetic'))

    def test_watchdog_limits_and_boundaries(self):
        args=dict(aggregate_rss=512*worker.MIB,progress_age=120,clock_drift=.1,wall_ms=T,lease_end=T+1)
        self.assertIsNone(worker.resource_reason(**args))
        self.assertIn('monotonic',worker.resource_reason(**args,monotonic_now=5,monotonic_lease_end=5))
        for key,value,expected in [('aggregate_rss',512*worker.MIB+1,'RSS'),
                                   ('progress_age',120.001,'watchdog'),
                                   ('clock_drift',-.101,'discontinuity'),
                                   ('wall_ms',T+1,'lease')]:
            with self.subTest(key=key):
                self.assertIn(expected,worker.resource_reason(**dict(args,**{key:value})))

    def test_immutable_auxiliary_publish(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'selection.json';worker.publish(p,{'x':1})
            with self.assertRaises(FileExistsError):worker.publish(p,{'x':2})
            self.assertEqual(json.loads(p.read_text()),{'x':1})


if __name__=='__main__':unittest.main()
