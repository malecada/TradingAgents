"""One-use stdlib native cleanup smoke; no numerical imports or model execution."""
import argparse,json,os,shutil
from pathlib import Path
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
    raw=b'x'*37
    with (args.report.parent/'scratch.bin').open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    assert (args.report.parent/'scratch.bin').read_bytes()==raw
    report={'schema_version':1,'mode':'green','status':'passed','passed_checks':['native_child_readback'],'error':None,'native':native,'scope':'stdlib OS cleanup ownership proof only; no numerical model or empirical data','scratch_bytes':37}
    raw=(json.dumps(report,sort_keys=True,indent=2)+'\n').encode();assert len(raw)<65536
    with args.report.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    return 0
if __name__=='__main__':raise SystemExit(main())
