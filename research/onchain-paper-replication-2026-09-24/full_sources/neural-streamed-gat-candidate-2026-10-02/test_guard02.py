"""Stdlib-only old/new launcher regression; no unit, subprocess or guard run."""
import ast
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
SOURCE=sys.argv.pop(1) if len(sys.argv)>1 and sys.argv[1].endswith('.py') else 'guard_launcher02.py'
spec=importlib.util.spec_from_file_location('tested_guard',HERE/SOURCE);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
if not hasattr(m,'validate_result'):
    # Exact old acceptance predicates, with only external verification/report
    # reading removed. No legacy launch body or numerical import is executed.
    tree=ast.parse((HERE/SOURCE).read_text());launch=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='launch')
    outer=next(x for x in launch.body if isinstance(x,ast.Try) and any(isinstance(y,ast.Assign) and isinstance(y.value,ast.Call) and isinstance(y.value.func,ast.Attribute) and y.value.func.attr=='guarded_run' for y in x.body))
    body=[x for x in outer.body if isinstance(x,ast.If)]
    fn=ast.parse('def legacy(mode,result,report,proof):\n spec={"mode":mode}\n').body[0];fn.body+=body
    ns={};exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(HERE/SOURCE),'exec'),ns);m.validate_result=ns['legacy']


def fixture(mode='red'):
    native={'memory.max':str(1024**3),'memory.high':str(1024**3),'memory.swap.max':'0'}
    props={'Result':'exit-code' if mode=='red' else 'success','ExecMainStatus':'1' if mode=='red' else '0','ActiveState':'failed' if mode=='red' else 'inactive','SubState':'failed' if mode=='red' else 'dead','ControlGroup':'/unit'}
    events={k:0 for k in ('high','max','oom','oom_kill','oom_group_kill')}
    terminal={'memory_events':events,'memory_current_bytes':1000}
    result={'cleanup_verified':True,'cleanup_stop_returncode':0,'cleanup_unit_properties':props.copy(),'unit_properties':props,'memory_events':events.copy(),'initial_memory_events':events.copy(),'terminal_memory_snapshot':terminal,'kernel_controls':native,'cpus':[0,1],'cpu_thread_readback':{'12':[0,1]},'cpu_enforcement':'inherited two-CPU affinity with per-thread cgroup readback','child_exit_code':1 if mode=='red' else 0,'phase':'failed' if mode=='red' else 'complete','limit_reason':'RuntimeError: child or unit failed: '+str(props) if mode=='red' else None,'elapsed_time_kill':False,'retry':False,'elapsed_seconds':2.,'cgroup':'/sys/fs/cgroup/unit','disk_free_bytes':{'/owned':11*1024**3},'memory_current_bytes':1000,'peak_sampled_memory_current_bytes':1000,'storage_budget':{'root':'/owned','limits':{'max_allocated_bytes':64*1024**2,'max_logical_bytes':64*1024**2,'max_entries':12000,'max_depth':32,'max_scan_seconds':2}},'storage_observation':{'allocated_bytes':4096,'logical_file_bytes':1000,'entries':5},**{k:v for k,v in m.LIMITS.items() if k not in ('file_limit_bytes','allocated_stop_bytes','logical_stop_bytes')}}
    for key,value in result['storage_observation'].items():result['storage_peak_'+key]=value
    checks=['layer_mixed_self_isolated','layer_zero_edges','layer_masked','layer_float64','dropout_rng','duplicate_refusal','full_model_16x28_all_gradients_Adam_RNG_reload','aggregation_output_all_gradients','independent_gradcheck','independent_central_difference','invalid_block_refusal']
    if mode=='green':checks+=['bounded_blocks_first_order_contract','RESOURCE_EDGE_WIDE_SAVED_TENSORS_removed']
    report={'schema_version':1,'mode':mode,'status':'failed' if mode=='red' else 'passed','error':{'type':'AssertionError','message':'RESOURCE_EDGE_WIDE_SAVED_TENSORS'} if mode=='red' else None,'passed_checks':checks,'native':{'controls':native,'cpus':[0,1],'cgroup':'/sys/fs/cgroup/unit','rlimit_fsize':[4194304,4194304]}}
    proof={'native_controls':{'LimitFSIZE':'4194304','LimitFSIZESoft':'4194304','RuntimeMaxUSec':'2min','ControlGroup':'/unit','MainPID':'12'},'cpu_ready':{'cpus':[0,1],'pid':12},'child_exit':{'exit_code':1 if mode=='red' else 0,'reason':'workload exited','workload_pid':13,'terminal_memory_snapshot':terminal,'snapshot_error':None},'child_log_bytes':100,'owned_root':'/owned'}
    return result,report,proof

class Tests(unittest.TestCase):
    def test_expected_red_cannot_hide_final_storage_breach(self):
        result,report,proof=fixture();result['storage_breach']={'allocated_bytes':999999999};result['storage_last_error']='StorageLimitExceeded'
        with self.assertRaises((RuntimeError,ValueError)):m.validate_result('red',result,report,proof)
    def test_valid_red_and_green(self):
        for mode in ('red','green'):m.validate_result(mode,*fixture(mode))
    def test_missing_controls_events_or_cpu_rejected(self):
        for key in ('kernel_controls','memory_events','cpu_thread_readback','terminal_memory_snapshot','cleanup_verified'):
            result,report,proof=fixture();del result[key]
            with self.assertRaises((RuntimeError,ValueError,KeyError)):m.validate_result('red',result,report,proof)
    def test_terminal_and_truncation_rejected(self):
        for key,value in [('elapsed_time_kill',True),('cleanup_error','uncertain'),('child_log_limit_reached',True),('storage_last_error','scan failed')]:
            result,report,proof=fixture();result[key]=value
            with self.assertRaises((RuntimeError,ValueError)):m.validate_result('red',result,report,proof)
        result,report,proof=fixture();proof['child_log_bytes']=4194304
        with self.assertRaises((RuntimeError,ValueError)):m.validate_result('red',result,report,proof)
    def test_immutable_first_fatal_survives_close(self):
        fatal=MemoryError('write first');closed=[]
        with tempfile.TemporaryDirectory(prefix='guard-receipt-') as temp:
            path=Path(temp)/'receipt.json'
            if SOURCE=='guard_launcher01.py':
                class Stream:
                    def __enter__(self):return self
                    def __exit__(self,*args):raise OSError('close later')
                    def write(self,raw):raise fatal
                with patch.object(Path,'open',return_value=Stream()):
                    try:m.immutable(path,{'x':1})
                    except BaseException as error:caught=error
            else:
                real_close=os.close
                def close(fd):closed.append(fd);real_close(fd);raise OSError('close later')
                with patch.object(os,'write',side_effect=fatal),patch.object(os,'close',close):
                    try:m.immutable(path,{'x':1})
                    except BaseException as error:caught=error
                self.assertEqual(len(closed),2);self.assertEqual(len(set(closed)),2)
            self.assertIs(caught,fatal)
    def test_immutable_file_and_parent_synced_and_no_overwrite(self):
        with tempfile.TemporaryDirectory(prefix='guard-receipt-') as temp:
            path=Path(temp)/'receipt.json';calls=[];real=os.fsync
            def sync(fd):calls.append(fd);real(fd)
            with patch.object(os,'fsync',sync):m.immutable(path,{'x':1})
            self.assertEqual(json.loads(path.read_bytes()),{'x':1});self.assertEqual(len(calls),2)
            with self.assertRaises(FileExistsError):m.immutable(path,{'x':2})
    def test_later_actual_fatal_beats_earlier_close_uncertainty(self):
        if not hasattr(m,'_close_owned'):self.skipTest('new explicit reducer not present in legacy source')
        first=OSError('first ordinary close');fatal=SystemExit('second actual fatal');calls=[]
        def close(fd):calls.append(fd);raise first if fd==1 else fatal
        with patch.object(os,'close',close):
            with self.assertRaises(SystemExit) as caught:m._close_owned((1,2),m)
        self.assertIs(caught.exception,fatal);self.assertIs(caught.exception.__cause__,first);self.assertEqual(calls,[1,2])

if __name__=='__main__':unittest.main()
