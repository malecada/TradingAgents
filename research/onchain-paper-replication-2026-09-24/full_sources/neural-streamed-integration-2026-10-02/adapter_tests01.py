"""One-use finite production adapter test; imports numerical modules only in native envelope."""
import argparse,json,os,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
TEST='tests/research/onchain_replication/test_streamed_execution_integration.py'
NAMES=['test_real_constructor_default_selected_initial_rng_and_detachment','test_schema2_real_admission_source_and_original_model','test_schema2_refuses_checkpoint_block_and_source_body','test_actual_selected_tiny_resource_checkpoint_identity']
def native_envelope(report):
    # Parent owns single-use identity, 120s systemd deadline and descendant cleanup.
    # This is actual inherited native readback before numerical imports.
    row=[x for x in Path('/proc/self/cgroup').read_text().splitlines() if x.startswith('0::')]
    if len(row)!=1:raise RuntimeError('unified cgroup required')
    suffix=row[0][3:];cg=Path('/sys/fs/cgroup')/suffix.lstrip('/')
    if '..' in Path(suffix).parts or cg.resolve()!=cg:raise RuntimeError('cgroup path redirected')
    expected={'memory.max':'1073741824','memory.high':'1073741824','memory.swap.max':'0'}
    actual={k:(cg/k).read_text().strip() for k in expected}
    if actual!=expected or len(os.sched_getaffinity(0))!=2:raise RuntimeError('unreleased native numerical envelope')
    import resource
    if resource.getrlimit(resource.RLIMIT_FSIZE)!=(4*1024**2,4*1024**2):raise RuntimeError('finite file cap required')
    if not report.parent.is_dir() or report.exists() or report.is_symlink():raise RuntimeError('new report under owned root required')
    if shutil.disk_usage(report.parent).free<10*1024**3:raise RuntimeError('disk floor')
    return {'cgroup':str(cg),'controls':actual,'cpus':sorted(os.sched_getaffinity(0)),'rlimit_fsize':list(resource.getrlimit(resource.RLIMIT_FSIZE))}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('green',),required=True);parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    native=native_envelope(args.report)
    if os.environ.get('PYTEST_DISABLE_PLUGIN_AUTOLOAD')!='1':raise RuntimeError('unreleased test plugin environment')
    import pytest
    class Observation:
        def __init__(self):self.collected=[];self.outcomes=[]
        def pytest_collection_finish(self,session):self.collected=[item.nodeid for item in session.items]
        def pytest_runtest_logreport(self,report):self.outcomes.append({'nodeid':report.nodeid,'when':report.when,'outcome':report.outcome})
    observer=Observation();primary=None;code=None
    try:
        code=int(pytest.main(['-q','-p','no:cacheprovider','--rootdir='+str(ROOT),'--basetemp='+str(args.report.parent/'tmp/pytest'),str(ROOT/TEST)],plugins=[observer]))
        expected=[TEST+'::'+name for name in NAMES]
        if code!=0 or observer.collected!=expected:raise RuntimeError('exact four adapter tests did not complete')
        for name in expected:
            if [x for x in observer.outcomes if x['nodeid']==name]!=[{'nodeid':name,'when':phase,'outcome':'passed'} for phase in ('setup','call','teardown')]:raise RuntimeError('adapter test phases differ')
    except BaseException as error:primary=error
    report={'schema_version':1,'mode':'green','status':'passed' if primary is None else 'failed','passed_checks':['production_adapter_four_tests'] if primary is None else [],'error':None if primary is None else {'type':type(primary).__name__,'message':str(primary)},'native':native,'pytest_exit_code':code,'collected':observer.collected,'outcomes':observer.outcomes,'qualification':'Four new finite production-adapter tests, real selected constructors and actual tiny checkpoint; synthetic admission mocks source/guard and does not prove real full-size admission/capacity. Closed numerical oracle not rerun; no empirical inputs.'}
    raw=(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+'
').encode();assert len(raw)<65536
    with args.report.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    if primary is not None:raise primary
    return 0
if __name__=='__main__':raise SystemExit(main())
