"""One tiny actual-guard storage probe per exclusive identity; synthetic only."""
import argparse
import json
from pathlib import Path
import sys
from tradingagents.research.onchain_replication import resources
from tradingagents.research.onchain_replication.provenance import file_hash
HERE=Path(__file__).resolve().parent
WRITER="import os,sys,time; p=sys.argv[1]; n=int(sys.argv[2]); f=open(p,'xb'); f.write(b'x'*n); f.flush(); os.fsync(f.fileno()); f.close(); time.sleep(20 if n>1024 else 0)"

def run(mode,identity):
    if mode not in ('positive','breach') or identity not in ('positive01','breach01'):raise ValueError('unregistered synthetic probe identity')
    if identity!=mode+'01':raise ValueError('mode/identity differs')
    root=HERE/identity;root.mkdir(exist_ok=False);outputs=root/'outputs';outputs.mkdir()
    budget={'root':str(outputs),'limits':{'max_allocated_bytes':65536,'max_logical_bytes':1048576,'max_entries':64,'max_depth':4,'max_scan_seconds':1}}
    policy={'memory_max_bytes':256*1024*1024,'memory_high_bytes':192*1024*1024,'memory_swap_max_bytes':0,
        'reserve_bytes':3*resources.GIB,'disk_paths':[str(root)],'disk_floor_bytes':10*resources.GIB,'wall_seconds':60,'storage_budget':budget}
    command=[sys.executable,'-B','-c',WRITER,str(outputs/'payload.bin'),'1024' if mode=='positive' else '262144']
    sources={str(p):file_hash(p) for p in (Path(resources.__file__),Path(resources.__file__).with_name('workflow_storage.py'),Path(__file__))}
    with (root/'intent.json').open('x') as f:json.dump({'mode':mode,'identity':identity,'command':command,'policy':policy,'source_sha256':sources,'synthetic_only':True},f,indent=2)
    value=resources.guarded_run(command,cwd=root,receipt_dir=root/'guard',**policy)
    assert value['cleanup_verified'] and all(file_hash(Path(p))==h for p,h in sources.items())
    if mode=='positive':assert value['phase']=='complete' and value['child_exit_code']==0 and value['storage_observation']['logical_file_bytes']==1024
    else:
        assert value['phase']=='failed' and 'storage allocated' in value['limit_reason']
        assert value['storage_breach']['allocated_bytes']>budget['limits']['max_allocated_bytes']
    result={'expected_outcome_observed':True,'mode':mode,'guard_phase':value['phase'],'limit_reason':value['limit_reason'],
        'cleanup_verified':value['cleanup_verified'],'guard_final_sha256':file_hash(root/'guard/final.json'),
        'payload_bytes':(outputs/'payload.bin').stat().st_size,'payload_sha256':file_hash(outputs/'payload.bin'),
        'qualification':'Tiny actual sampled allocated-byte stop; no hard filesystem quota, whole-study output accounting or empirical capacity credit.'}
    with (root/'result.json').open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(result),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode');p.add_argument('identity');a=p.parse_args();run(a.mode,a.identity)
