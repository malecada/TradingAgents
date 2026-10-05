"""Offline native-control mocks only; systemd and subprocess never execute."""
import ast
from contextlib import ExitStack
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

D=Path(__file__).resolve().parent
PACKAGE='tradingagents.research.onchain_replication'

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

guard=load('native_candidate_resources',D/'resources.py')
legacy=load('native_baseline_resources',D/'resources.py.baseline') if False else None
# Extensionless original is deliberately compiled without invoking any entry.
legacy=SimpleNamespace()
exec(compile((D/'resources.py.baseline').read_text(),'resources.baseline','exec'),legacy.__dict__)
io=load(PACKAGE+'.owned_io',D.parent/'real-data-pilot-main-import-port01-2026-10-05/candidate/tradingagents/research/onchain_replication/owned_io.py')
POLICY={'file_size_bytes':4*1024**2}


def mock_run(root,module,policy,bad_soft=False):
    receipt=root/'r';calls=[];reads=[0]
    def run(args,**kwargs):
        calls.append(list(args))
        if args[0]=='systemd-run':
            ready={'pid':1,'cpus':[0,1]}
            if policy is not None:ready.update(native_unit_limits=policy,file_size_limit=[POLICY['file_size_bytes']]*2,native_environment=module._native_owned_env(root))
            (receipt/'cpu_ready.json').write_text(json.dumps(ready))
            (receipt/'child_exit.json').write_text(json.dumps({'exit_code':0,'terminal_memory_snapshot':{'memory_current_bytes':42,'memory_events':{'oom':0,'oom_kill':0}}}))
        if args[0]=='systemctl' and 'show' in args:
            return subprocess.CompletedProcess(args,0,'LimitFSIZE=4194304\nLimitFSIZESoft='+('1' if bad_soft else '4194304')+'\nRuntimeMaxUSec=30min\n','')
        return subprocess.CompletedProcess(args,0,'','')
    def props(unit):
        reads[0]+=1
        return {'ControlGroup':'/user.slice/nonexistent-offline-unit.service','ActiveState':'active' if reads[0]==1 else 'inactive','Result':'success'}
    with ExitStack() as stack:
        import tradingagents.research.onchain_replication
        stack.enter_context(patch.dict(sys.modules,{PACKAGE+'.owned_io':io}))
        stack.enter_context(patch.object(module.os,'sched_getaffinity',return_value={0,1}))
        stack.enter_context(patch.object(module,'mem_available',return_value=20*module.GIB))
        stack.enter_context(patch.object(module.subprocess,'run',side_effect=run))
        stack.enter_context(patch.object(module,'_properties',side_effect=props))
        stack.enter_context(patch.object(module,'_read_controls',return_value={'memory.max':str(3*module.GIB),'memory.high':str(3*module.GIB),'memory.swap.max':'0'}))
        stack.enter_context(patch.object(module,'verify_cpu_tree',return_value={'1':[0,1]}))
        stack.enter_context(patch.object(module,'_snapshot',return_value={'memory_current_bytes':42,'memory_events':{'oom':0,'oom_kill':0}}))
        stack.enter_context(patch.object(module.shutil,'disk_usage',return_value=SimpleNamespace(free=40*module.GIB)))
        stack.enter_context(patch.object(module.signal,'signal',return_value=None))
        options={} if module is legacy else {'native_unit_limits':policy}
        result=module.guarded_run(['never-executed'],cwd=root,receipt_dir=receipt,
            memory_max_bytes=3*module.GIB,memory_high_bytes=3*module.GIB,wall_seconds=1800,disk_paths=[root],**options)
    return result,calls,receipt


class Checks(unittest.TestCase):
    def test_policy_and_conflicting_authority_refuse_before_birth(self):
        self.assertIsNone(guard._native_policy(None))
        self.assertEqual(guard._native_policy(POLICY),POLICY)
        for p in ({},{'file_size_bytes':True},{'file_size_bytes':0},{'file_size_bytes':4194305},{'file_size_bytes':4096,'other':1}):
            with self.subTest(p=p), self.assertRaises(ValueError):guard._native_policy(p)
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'absent'
            with self.assertRaises(ValueError):guard.guarded_run(['never'],cwd=tmp,receipt_dir=out,native_unit_limits=POLICY,physical_policy={})
            self.assertFalse(out.exists())

    def test_selected_readback_rejects_soft_hard_wall_child_and_environment(self):
        root=Path('/fixed-unused')
        ready={'native_environment':guard._native_owned_env(root),'file_size_limit':[4194304]*2,'native_unit_limits':POLICY}
        props={'LimitFSIZE':'4194304','LimitFSIZESoft':'4194304','RuntimeMaxUSec':'30min'}
        guard._native_ready(POLICY,ready,props,1800,root)
        for key in props:
            wrong={**props,key:'1s' if key=='RuntimeMaxUSec' else '1'}
            with self.subTest(key=key),self.assertRaises(ValueError):guard._native_ready(POLICY,ready,wrong,1800,root)
        for key,bad in [('file_size_limit',[1,4194304]),('native_environment',{}),('native_unit_limits',{'file_size_bytes':1})]:
            with self.subTest(key=key),self.assertRaises(ValueError):guard._native_ready(POLICY,{**ready,key:bad},props,1800,root)

    def test_native_mock_command_release_and_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            result,calls,receipt=mock_run(Path(tmp),guard,POLICY)
            self.assertEqual(result['phase'],'complete');self.assertTrue(result['cleanup_verified'])
            launch=next(c for c in calls if c[0]=='systemd-run')
            self.assertIn('--property=LimitFSIZE=4194304',launch)
            self.assertIn('--property=RuntimeMaxSec=1800',launch)
            self.assertIn('--native-file-limit',launch)
            self.assertEqual(result['native_unit_properties']['LimitFSIZESoft'],'4194304')
            self.assertTrue((receipt/'release.json').exists())
            self.assertEqual(result['minimum_sampled_disk_free_bytes'][tmp],40*guard.GIB)
            self.assertTrue(any('stop' in c for c in calls))

    def test_bad_native_readback_never_releases_but_cleans(self):
        with tempfile.TemporaryDirectory() as tmp:
            result,calls,receipt=mock_run(Path(tmp),guard,POLICY,bad_soft=True)
            self.assertEqual(result['phase'],'failed');self.assertFalse((receipt/'release.json').exists())
            self.assertTrue(result['cleanup_verified']);self.assertTrue(any('stop' in c for c in calls))

    def test_legacy_none_mock_retains_original_command_controls(self):
        with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
            old,oldcalls,_=mock_run(Path(a),legacy,None)
            new,newcalls,_=mock_run(Path(b),guard,None)
            for name in ('phase','cleanup_verified','child_exit_code','memory_max_bytes','memory_high_bytes','reserve_bytes','wall_seconds','disk_floor_bytes','cpus'):
                self.assertEqual(old[name],new[name])
            for calls in (oldcalls,newcalls):
                launch=next(c for c in calls if c[0]=='systemd-run')
                self.assertFalse(any('LimitFSIZE' in c or 'RuntimeMaxSec' in c or 'native-file-limit' in c for c in launch))
            self.assertNotIn('native_unit_limits',new)

    def test_literal_inverse_and_unchanged_telemetry(self):
        records=json.loads((D/'INVERSE01.json').read_text())
        for name,record in records.items():
            raw=(D/name).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),record['candidate_sha256'])
            lines=raw.decode().splitlines(True)
            for e in reversed(record['changes']):
                self.assertEqual(''.join(lines[e['after_start']:e['after_end']]),e['after'])
                lines[e['after_start']:e['after_end']]=e['before'].splitlines(True)
            restored=''.join(lines).encode()
            self.assertEqual(restored,(D/(name+'.baseline')).read_bytes())
            self.assertEqual(hashlib.sha256(restored).hexdigest(),record['baseline_sha256'])
        def fn(text,name):
            tree=ast.parse(text);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
            return ''.join(text.splitlines(True)[node.lineno-1:node.end_lineno])
        old=(D/'resources.py.baseline').read_text();new=(D/'resources.py').read_text()
        self.assertEqual(fn(old,'_telemetry'),fn(new,'_telemetry'))
        job=(D/'job.py').read_text();base=(D/'job.py.baseline').read_text()
        for name in ('workspace_binding','_admitted','_command','launch','execute_source_job','reconcile'):
            self.assertEqual(fn(base,name),fn(job,name))

    def test_child_wrong_inherited_rlimit_never_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt=Path(tmp)
            with patch.object(guard.os,'sched_setaffinity'),patch.object(guard.os,'sched_getaffinity',return_value={0,1}),patch.object(resource,'getrlimit',return_value=(1,1)),patch.object(guard.subprocess,'Popen',side_effect=AssertionError('must not dispatch')),patch.object(guard,'_snapshot',side_effect=FileNotFoundError),patch.object(guard,'_own_cgroup',return_value=receipt):
                self.assertEqual(guard._child(receipt,[0,1],15,['never'],native_unit_limits=POLICY),125)
            result=json.loads((receipt/'child_exit.json').read_text())
            self.assertIn('inherited native file limit differs',result['reason'])
            self.assertIsNone(result['workload_pid'])

if __name__=='__main__':unittest.main()
