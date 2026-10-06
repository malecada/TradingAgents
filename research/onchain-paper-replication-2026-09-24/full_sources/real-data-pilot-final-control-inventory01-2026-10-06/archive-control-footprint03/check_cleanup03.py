"""Actual packed audit RED/GREEN fault injection, stdlib and synthetic bytes."""
import argparse,importlib,json,os,sys,tempfile,types
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];SRC=ROOT/'tradingagents/research/onchain_replication'
a=argparse.ArgumentParser();a.add_argument('--candidate',type=Path,required=True);a.add_argument('--output',type=Path,required=True);args=a.parse_args()
def guard(event,details):
    if event.startswith(('socket.','subprocess.')):raise RuntimeError('offline checks forbid network/subprocess')
    if event=='import' and details[0].split('.')[0] in {'numpy','torch','pandas','scipy'}:raise RuntimeError('numerical imports forbidden')
sys.addaudithook(guard)
pkg=types.ModuleType('selected_cleanup');pkg.__path__=[str(args.candidate.resolve()),str(SRC)];sys.modules[pkg.__name__]=pkg
name=pkg.__name__+'.score_batches';m=types.ModuleType(name);m.__file__=str(SRC/'score_batches.py');m.__package__=pkg.__name__;sys.modules[name]=m
source=Path(m.__file__).read_text();assert source.count('import numpy as np\n')==1
exec(compile(source.replace('import numpy as np\n',''),m.__file__,'exec'),m.__dict__)
rc=importlib.import_module(pkg.__name__+'.archive_read_controls');io=rc.io

def capture(call):
    try:call()
    except BaseException as error:return error
    return None

def scenario(root,primary=None):
    root.mkdir();j=rc.history.Journal(root/'controls',record_bytes=8192,total_bytes=10000,records=4,shard_bytes=4194304)
    name=rc.record_name(0,'intent.json');body=b'original synthetic receipt';j.append(name,body)
    def expected():
        if primary is not None:raise primary
        yield name,b'mutated expectation'
    real_open=os.open;real_close=os.close;opened=[];closed=[];cleanup=[]
    def tracked_open(*a,**k):
        fd=real_open(*a,**k);opened.append(fd);return fd
    def fault_close(fd):
        real_close(fd);closed.append(fd)
        error=OSError('injected close failure after actual reap '+str(len(closed)));cleanup.append(error);raise error
    with patch.object(rc.os,'open',tracked_open),patch.object(rc.os,'close',fault_close):
        error=capture(lambda:rc.audit(root,expected(),rc.POLICY,max_chunks=1))
    reaped=all(capture(lambda fd=fd:os.fstat(fd)) is not None for fd in opened)
    # Observational postcondition only: never retry an ambiguous descriptor.
    if primary is not None:passed=error is primary
    else:
        failures=getattr(error,'failures',())
        passed=isinstance(error,io.CleanupFailure) and len(failures)==3 and isinstance(failures[0],ValueError) and 'original receipt differs' in str(failures[0]) and failures[1] is cleanup[0] and failures[2] is cleanup[1]
    return {'passed':passed and len(opened)==2 and len(closed)==2 and set(opened)==set(closed) and reaped,'actual_error_type':type(error).__name__,'original_fatal_preserved':error is primary if primary is not None else None,'cleanup_failure_count':len(getattr(error,'failures',())),'opened_descriptor_count':len(opened),'closed_once_count':len(closed),'all_real_descriptors_reaped':reaped,'no_close_retry':len(set(closed))==len(closed)}

results={}
with tempfile.TemporaryDirectory(dir=HERE) as tmp:
    root=Path(tmp)
    results['fatal_primary_plus_two_close_errors']={}
    for klass in (KeyboardInterrupt,SystemExit,MemoryError):
        results['fatal_primary_plus_two_close_errors'][klass.__name__]=scenario(root/klass.__name__,klass('original fatal'))
    results['ordinary_mutation_plus_two_close_errors']=scenario(root/'mutation')
    birth=root/'float-writer';birth.mkdir();before=set(birth.iterdir());bad=dict(rc.POLICY,shard_bytes=4194304.0)
    direct=capture(lambda:rc.policy(bad));error=capture(lambda:rc.Writer(birth,1,bad))
    results['float_policy_refused_before_writer_birth']={'passed':isinstance(direct,ValueError) and isinstance(error,ValueError) and not (birth/'controls').exists() and set(birth.iterdir())==before,'direct_error_type':type(direct).__name__,'writer_error_type':type(error).__name__,'controls_root_absent':not (birth/'controls').exists()}
checks=list(results['fatal_primary_plus_two_close_errors'].values())+[results['ordinary_mutation_plus_two_close_errors'],results['float_policy_refused_before_writer_birth']]
report={'status':'PASS' if all(c['passed'] for c in checks) else 'FAIL_EXPECTED_ON_PREDECESSOR','regression_groups':3,'fatal_subcases':3,'candidate':str(args.candidate),'results':results}
args.output.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps(report,sort_keys=True,indent=2));sys.exit(0 if report['status']=='PASS' else 1)
