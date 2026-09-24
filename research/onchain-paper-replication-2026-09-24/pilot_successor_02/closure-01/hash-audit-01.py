"""One-shot guarded byte hashing of closed pilot artifacts; no data decoding."""
from pathlib import Path
import hashlib,json,os,sys,time
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
HERE=Path(__file__).resolve().parent
from tradingagents.research.onchain_replication.resources import guarded_run,assert_guarded_worker
from tradingagents.research.lifecycle import _immutable

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def worker():
    contract=json.loads((HERE/'hash-audit-01-contract.json').read_bytes())
    assert_guarded_worker(HERE/'hash-audit-01-guard',sys.orig_argv,required_paths=[ROOT],wall_seconds=900,memory_max_bytes=512*1024**2,memory_high_bytes=384*1024**2)
    assert sha(__file__)==contract['script_sha256']
    assert sha(ROOT/'tradingagents/research/onchain_replication/resources.py')==contract['resource_guard_sha256']
    assert sha(contract['artifact_index'])==contract['artifact_index_sha256']
    records=[];started=time.monotonic()
    try:
        for number,(name,meta) in enumerate(contract['members'].items()):
            fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW)
            try:
                before=os.fstat(fd);assert before.st_size==meta['bytes']
                h=hashlib.sha256();count=0;discarded=0
                while block:=os.read(fd,1024**2):
                    count+=len(block)
                    if count>meta['bytes']:raise ValueError('file exceeded registered byte size')
                    h.update(block)
                    if count-discarded>=64*1024**2:
                        os.posix_fadvise(fd,discarded,count-discarded,os.POSIX_FADV_DONTNEED);discarded=count
                os.posix_fadvise(fd,discarded,count-discarded,os.POSIX_FADV_DONTNEED)
                after=os.fstat(fd)
                assert (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)
                if count!=meta['bytes'] or h.hexdigest()!=meta['sha256']:raise ValueError('closed artifact bytes differ')
                record={'path':name,'bytes':count,'sha256':h.hexdigest(),'status':'verified'}
            finally:os.close(fd)
            _immutable(HERE/f'hash-audit-01-member-{number:02d}.json',record);records.append(record)
        assert sha(contract['artifact_index'])==contract['artifact_index_sha256']
        result={'status':'complete','members':len(records),'bytes':sum(x['bytes'] for x in records),'elapsed_seconds':time.monotonic()-started,'contract_sha256':sha(HERE/'hash-audit-01-contract.json'),'scope':'read-only byte hash verification, no decode or computation of financial outcomes'}
        _immutable(HERE/'hash-audit-01-complete.json',result);print(json.dumps(result),flush=True);return 0
    except BaseException as error:
        _immutable(HERE/'hash-audit-01-failed.json',{'status':'failed','verified_members':len(records),'reason':type(error).__name__+': '+str(error),'contract_sha256':sha(HERE/'hash-audit-01-contract.json')});raise

def main():
    if sys.argv[1:]==['--worker']:return worker()
    if sys.argv[1:]:raise ValueError('unexpected argument')
    command=[str(ROOT/'.venv/bin/python'),'-B',str(Path(__file__).resolve()),'--worker']
    final=guarded_run(command,cwd=ROOT,receipt_dir=HERE/'hash-audit-01-guard',memory_max_bytes=512*1024**2,memory_high_bytes=384*1024**2,memory_swap_max_bytes=0,reserve_bytes=3*1024**3,start_reserve_bytes=3584*1024**2,disk_paths=[ROOT],disk_floor_bytes=20*1024**3,wall_seconds=900)
    print(json.dumps({k:final.get(k) for k in ['phase','child_exit_code','cleanup_verified','limit_reason','elapsed_seconds','peak_sampled_memory_current_bytes']}),flush=True)
    return 0 if final.get('phase')=='complete' and final.get('child_exit_code')==0 and final.get('cleanup_verified') else 1
if __name__=='__main__':raise SystemExit(main())
