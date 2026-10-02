"""Stdlib counterexamples calling the actual native launcher validate entrypoint.

Fake inactive native metadata only. No guard, claim, subprocess or numerics.
All generated receipts are synthetic test fixtures, never operational evidence.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

HEAD='a'*40
MANIFEST='b'*64
PID=2000000100


def encoded(value):return (json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def phases(protocol,mode):
    names=['numerical_import']
    if mode=='correctness':
        suffixes=['construct','forward','backward','optimizer','save','reload',
            'continue-original.forward','continue-original.backward','continue-original.optimizer',
            'continue-restored.forward','continue-restored.backward','continue-restored.optimizer','eval','no_grad']
        for case in protocol['cases']:
            for enabled in (False,True):
                label=case['name']+('.true' if enabled else '.false')
                names.extend(label+'.'+suffix for suffix in suffixes)
            names.append(case['name']+'.comparison_complete')
    else:
        for case in protocol['profile_cases']:
            names.extend(case+'.'+suffix for suffix in ['construct','forward','backward','optimizer','save','reload','continuation-forward','continuation-backward','continuation-optimizer','complete'])
    return names+['complete']


def fixture(launcher,root):
    protocol=json.loads((launcher.HERE/'protocol01.json').read_bytes())
    modes=protocol['modes'];identity=launcher.IDENTITY
    group='/synthetic-counterexample-no-unit';cgroup='/sys/fs/cgroup'+group
    assert not Path(cgroup).exists() and all(not Path('/proc',str(PID+i)).exists() for i in range(8))
    controls={'memory.max':'1073741824','memory.high':'1073741824','memory.swap.max':'0'}
    native={'cgroup':cgroup,'controls':controls,'cpus':[0,1],'file_limit_bytes':4194304}
    snapshot={'memory_current_bytes':0,'memory_peak_bytes':1024}
    records={
      'guard/cpu_ready.json':{'pid':PID,'cpus':[0,1],'file_size_limit':[4194304,4194304]},
      'guard/child_exit.json':{'exit_code':0,'workload_pid':PID+1,'snapshot_error':None,'reason':'workload exited','terminal_memory_snapshot':snapshot},
      'native-unit-controls.json':{'LimitFSIZE':'4194304','LimitFSIZESoft':'4194304','RuntimeMaxUSec':'2min','ControlGroup':group,'MainPID':str(PID)},
      'workload/intent.json':{'run_id':identity,'source_commit':HEAD,'manifest_sha256':MANIFEST,'native':native},
    }
    arms=[]
    core=json.loads((launcher.ROOT/protocol['model_input']).read_bytes())
    for index,mode in enumerate(modes):
        arm={'mode':mode,'pid':PID+2+index,'returncode':0,'status':'exited','started_monotonic_ns':1,'ended_monotonic_ns':2};arms.append(arm)
        cases=[]
        for case in protocol['cases']:
            if mode!='correctness' and case['name'] not in protocol['profile_cases']:continue
            for enabled in ((False,True) if mode=='correctness' else (mode=='profile_true',)):
                config=copy.deepcopy(core);config['graph_activation_checkpointing']=enabled
                if mode=='correctness':config['gat_dropout']=case['dropout']
                cases.append({'case':case['name'],'checkpoint':enabled,'config_sha256':hashlib.sha256(encoded(config)).hexdigest(),'checkpoint_directory':case['name']+'.checkpoint'})
        names=phases(protocol,mode)
        assert len(names)==(147 if mode=='correctness' else 22)
        terminal={'schema_version':1,'status':'passed','mode':mode,'run_id':identity,'source_commit':HEAD,'manifest_sha256':MANIFEST,'error':None,
                  'result':{'cases':cases,'comparisons':[{'path':'synthetic-only','bitwise_equal':True}],'bitwise_different_tensors':0},
                  'phases':{'phase_markers':len(names),'sample_count':1,'samples':{'complete':{'samples':1,'max_memory_current_bytes':1024}}}}
        records['workload/'+mode+'/terminal.json']=terminal
        records['workload/'+mode+'/intent.json']={'mode':mode,'run_id':identity,'source_commit':HEAD,'manifest_sha256':MANIFEST,'protocol_sha256':digest(launcher.HERE/'protocol01.json'),'native':copy.deepcopy(native)}
        records['workload/'+mode+'.started.json']={k:v for k,v in arm.items() if k not in ('returncode','ended_monotonic_ns')}
        records['workload/'+mode+'.started.json']['status']='running'
        records['workload/'+mode+'.exited.json']=copy.deepcopy(arm)
        for n,name in enumerate(names):
            records['workload/'+mode+f'/phase-{n:04d}.json']={'schema_version':1,'index':n,'phase':name,'mode':mode,'monotonic_ns':n+1,'memory_current_bytes':1024,'cumulative_cgroup_memory_peak_bytes':2048}
    records['workload/terminal.json']={'schema_version':1,'status':'passed','run_id':identity,'source_commit':HEAD,'manifest_sha256':MANIFEST,'error':None,'active_child_pid':None,'cleanup_owner':'outer-native-guard','arms':arms}
    events={key:0 for key in ('low','high','max','oom','oom_kill','oom_group_kill')}
    result={'phase':'complete','child_exit_code':0,'limit_reason':None,'retry':False,'elapsed_time_kill':False,'elapsed_seconds':1,
      'kernel_controls':controls,'initial_memory_events':events,'memory_events':events,'terminal_memory_snapshot':snapshot,'cgroup':cgroup,
      'cpus':[0,1],'cpu_enforcement':'inherited two-CPU affinity with per-thread cgroup readback','cpu_thread_readback':{str(PID):[0,1]},
      'storage_budget':{'root':str(root),'limits':{'max_allocated_bytes':67108864,'max_logical_bytes':67108864,'max_entries':12000,'max_depth':32,'max_scan_seconds':2}},
      'disk_free_bytes':{str(root):10737418240},'cleanup_verified':True}
    for key in ('memory_max_bytes','memory_high_bytes','memory_swap_max_bytes','reserve_bytes','start_reserve_bytes','wall_seconds','disk_floor_bytes'):result[key]=launcher.LIMITS[key]
    return records,result,{'proof_manifest_sha256':MANIFEST}


def cases(modes):
    yield 'valid_control',None
    for mode in modes:
        prefix='workload/'+mode+'/'
        yield mode+'_missing_cases',lambda r,p=prefix:r[p+'terminal.json']['result'].pop('cases')
        def wrong_cases(r,p=prefix):r[p+'terminal.json']['result']['cases'][0]['case']='wrong-case'
        yield mode+'_wrong_cases',wrong_cases
        yield mode+'_missing_phase_count',lambda r,p=prefix:r[p+'terminal.json']['phases'].pop('phase_markers')
        def wrong_count(r,p=prefix):r[p+'terminal.json']['phases']['phase_markers']-=1
        yield mode+'_wrong_phase_count',wrong_count
        yield mode+'_missing_phase_file',lambda r,p=prefix:r.pop(p+'phase-0000.json')
        for field,value in [('index',1),('mode','wrong-mode'),('phase','wrong-phase')]:
            def mutation(r,p=prefix,k=field,v=value):r[p+'phase-0000.json'][k]=v
            yield mode+'_wrong_phase_'+field,mutation
        for field,value in [('mode','wrong-mode'),('run_id','wrong-run'),('source_commit','c'*40),('manifest_sha256','d'*64)]:
            def mutation(r,p=prefix,k=field,v=value):r[p+'intent.json'][k]=v
            yield mode+'_wrong_intent_'+field,mutation
    for file in ('intent.json','terminal.json'):
        for field,value in [('source_commit','c'*40),('manifest_sha256','d'*64)]:
            def mutation(r,f=file,k=field,v=value):r['workload/'+f][k]=v
            yield 'coordinator_'+file.split('.')[0]+'_wrong_'+field,mutation


def run(launcher_path,fixtures):
    assert 'torch' not in sys.modules and 'numpy' not in sys.modules
    spec=importlib.util.spec_from_file_location('actual_native_caller_under_test',launcher_path)
    launcher=importlib.util.module_from_spec(spec);spec.loader.exec_module(launcher)
    assert 'torch' not in sys.modules and 'numpy' not in sys.modules
    fixtures=fixtures.absolute();fixtures.mkdir(exist_ok=False)
    protocol=json.loads((launcher.HERE/'protocol01.json').read_bytes());results=[]
    # This stub concerns only the separately tested native cleanup predicate.
    # Actual validate(), metadata(), require() and sha() remain unmodified.
    helper=SimpleNamespace(_cleanup_complete=lambda result,proof:True)
    for name,mutate in cases(protocol['modes']):
        root=fixtures/name;records,result,release=fixture(launcher,root)
        if mutate is not None:mutate(records)
        for path,value in records.items():
            target=root/path;target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as out:out.write(encoded(value))
        for mode in protocol['modes']:(root/'workload'/(mode+'.log')).write_bytes(b'synthetic validator test only\n')
        error=None
        try:launcher.validate(result,root,release,HEAD,helper)
        except (RuntimeError,ValueError,KeyError,FileNotFoundError,TypeError,AssertionError) as exception:error=type(exception).__name__+': '+str(exception)
        accepted=error is None;expected=mutate is None;passed=accepted==expected
        row={'case':name,'expected_accept':expected,'actual_accept':accepted,'check_passed':passed,'error':error};results.append(row)
        with (root/'validation-call.json').open('xb') as out:out.write(encoded({'synthetic':True,'result':result,'spec':release,'head':HEAD,'outcome':row}))
        print(('PASS' if passed else 'UNEXPECTED_ACCEPT' if accepted else 'UNEXPECTED_REJECTION')+' '+name+(' '+error if error else ''))
    summary={'schema_version':1,'synthetic_only':True,'launcher_path':str(launcher_path),'launcher_sha256':digest(launcher_path),'test_source_sha256':digest(__file__),'numerical_imports':False,'guard_executed':False,'checks':results,'passed':all(x['check_passed'] for x in results)}
    with (fixtures/'summary.json').open('xb') as out:out.write(encoded(summary))
    print(json.dumps({'cases':len(results),'unexpected_accepts':sum(not r['check_passed'] and r['actual_accept'] for r in results),'unexpected_rejections':sum(not r['check_passed'] and not r['actual_accept'] for r in results),'passed':summary['passed']}))
    return 0 if summary['passed'] else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--launcher',type=Path,required=True);parser.add_argument('--fixtures',type=Path,required=True);args=parser.parse_args()
    raise SystemExit(run(args.launcher.absolute(),args.fixtures))
