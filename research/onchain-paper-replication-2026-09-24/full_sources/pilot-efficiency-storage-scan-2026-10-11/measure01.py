"""Finite synthetic component observation, not a native monitor benchmark."""
from pathlib import Path
import tempfile,time,json,os
from tradingagents.research.onchain_replication import real_pilot_storage as m

def timed(fn):
    wall=time.perf_counter();cpu=time.process_time();value=fn()
    return {'wall_seconds':time.perf_counter()-wall,'process_cpu_seconds':time.process_time()-cpu},value
with tempfile.TemporaryDirectory(prefix='pilot-storage-synthetic-') as temp:
    root=Path(temp);(root/'research_artifacts').mkdir();(root/'research_runs').mkdir();(root/'research_runs/.lock').touch()
    for paths in m.residual_paths(root).values():
        for path in paths:path.mkdir(parents=True,exist_ok=True)
    runtime=m.residual_paths(root)['runtime_temp_cache'][0]
    for i in range(256):(runtime/str(i)).write_bytes(b'x'*32)
    limits=dict(max_allocated_bytes=10**8,max_logical_bytes=10**7,max_entries=10000,max_depth=64,max_scan_seconds=5)
    budget=dict(schema_version=2,kind=m.KIND,authority_root=str(root),experiment=m.EXPERIMENT,
        roots=[str(root/'research_artifacts'),str(root/'research_runs'/m.EXPERIMENT)],shared_files=[str(root/'research_runs/.lock')],limits=limits)
    union=m.WritableUnion(budget,root);samples=[]
    for i in range(3):
        shared,result=timed(union.check)
        extra,_=timed(lambda:m.residual_check(root))
        def publish():
            body=json.dumps(result,sort_keys=True).encode();path=root/'observation.tmp'
            with path.open('wb') as f:f.write(body);f.flush();os.fsync(f.fileno())
            path.replace(root/'observation.json');fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY)
            try:os.fsync(fd)
            finally:os.close(fd)
        publication,_=timed(publish)
        samples.append({'shared_walk':shared,'separate_residual_walk_only':extra,'json_write_file_and_directory_fsync':publication,'union_entries':result['entries']})
    print(json.dumps({'classification':'SYNTHETIC_COMPONENT_ONLY','files':256,'samples':samples,'qualification':'Same tiny synthetic tree, sequential warm-cache samples. Extra standalone walk is separately measured removed work, not an exact old-algorithm timing or monitor-process profile. No real-data saving, contention or capacity claim.'},indent=2))
