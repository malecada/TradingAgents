"""One COPY native job, then one separately released RETIRE; no automatic chaining."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,os,shutil,subprocess,sys
from tradingagents.research.onchain_replication.environment import inventory
from tradingagents.research.onchain_replication.resources import guarded_run,assert_guarded_worker,mem_available
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
ID='real-pilot-may30-ledger-relocation-20261006-01';DATA=Path('/home/malecada/Data');GIB=1024**3

def need(ok,message):
    if not ok:raise ValueError(message)
def body(ref):
    q=Path(ref['path']);p=ROOT/q
    need(not q.is_absolute() and '..' not in q.parts and p.resolve(strict=True)==p and p.is_file() and p.stat().st_nlink==1 and p.stat().st_size<=4*1024**2,'canonical bounded evidence required')
    raw=p.read_bytes();need(hashlib.sha256(raw).hexdigest()==ref['sha256'],'exact evidence changed');return raw
def publish(name,value):
    with (HERE/name).open('x') as f:json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
def frozen(phase):
    need(phase in ('copy','retire'),'exact separate phase required')
    p=HERE/(phase+'-envelope01.json');raw=p.read_bytes();e=json.loads(raw)
    need(e['identity']==ID and e['phase']==phase,'fixed phase identity required')
    for path,pin in e['source_files'].items():body({'path':path,'sha256':pin})
    for ref in e['evidence']:body(ref)
    need(inventory(ROOT)==json.loads(body(e['environment'])),'runtime inventory differs')
    c=json.loads(body(e['selection']));need(c['status']=='FROZEN_FOR_REVIEW','draft cannot execute')
    source=body(e['helper']);spec=importlib.util.spec_from_file_location('exact_relocation',ROOT/e['helper']['path']);m=importlib.util.module_from_spec(spec);exec(compile(source,e['helper']['path'],'exec'),vars(m))
    need(e['source_files'].get(e['helper']['path'])==e['helper']['sha256'] and e['source_files'].get(str(Path(__file__).relative_to(ROOT)))==hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'exact entry/helper closure required')
    m.validate(c)
    return e,c,m,hashlib.sha256(raw).hexdigest()

def worker():
    e,c,m,digest=frozen('copy');o=json.loads((HERE/'copy-preflight01.json').read_bytes())
    need(o['head']==subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() and o['envelope_sha256']==digest,'source/preflight changed')
    def guard():
        v=assert_guarded_worker(HERE/'copy-guard01',sys.orig_argv,required_paths=[ROOT,DATA],wall_seconds=14400,memory_max_bytes=256*1024**2,memory_high_bytes=192*1024**2,disk_floor_bytes=10*GIB)
        need(v['memory_swap_max_bytes']==0 and v['reserve_bytes']==3*GIB and v['start_reserve_bytes']==int(3.5*GIB)
            and v['storage_budget']=={'root':str(HERE),'limits':{'max_allocated_bytes':5*GIB,'max_logical_bytes':5*GIB,'max_entries':4096,'max_depth':16,'max_scan_seconds':5}},'selected native controls differ')
        return v
    guard();m.copy(ROOT,HERE,c,guard)

def launch(phase):
    e,c,m,digest=frozen(phase);rp=HERE/(phase+'-RELEASE_REVIEW01.json');release=json.loads(rp.read_bytes())
    need(release.get('decision')=='accepted' and release['identity']==ID and release['phase']==phase and release['envelope_sha256']==digest,'exact independent phase release required')
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    refs=[e['selection'],e['helper'],e['environment']]+e['evidence']
    pins={**e['source_files'],**release['evidence'],**{r['path']:r['sha256'] for r in refs}}
    for p in (HERE/(phase+'-envelope01.json'),rp):pins[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
    for path,pin in pins.items():
        body({'path':path,'sha256':pin})
        need(hashlib.sha256(subprocess.check_output(['git','show',head+':'+path],cwd=ROOT)).hexdigest()==pin,'phase evidence/source not committed')
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip();need(branch=='research/onchain-paper-replication-2026-09-24','fixed branch required')
    need(subprocess.check_output(['git','ls-remote','--exit-code','origin','refs/heads/'+branch],cwd=ROOT,text=True).split()[0]==head,'actual external source readback differs')
    for name in (phase+'-preflight01.json',phase+'-launch-attempt01.json',phase+'-attempt01.json',phase+'-complete01.json',phase+'-failed01.json',phase+'-outer-exit01.json'):
        need(not os.path.lexists(HERE/name),'phase identity already spent')
    m.base().inactive();m.room(c,m.BYTES if phase=='copy' else 0)
    if phase=='copy':need(not os.path.lexists(HERE/'copy-guard01') and not os.path.lexists(m.TARGET.parent) and mem_available()>=int(3.5*GIB),'copy namespace or startup unavailable')
    observation={'identity':ID,'phase':phase,'head':head,'envelope_sha256':digest,'root_free_bytes':shutil.disk_usage(ROOT).free,'data_free_bytes':shutil.disk_usage(DATA).free,'at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    publish(phase+'-preflight01.json',observation);publish(phase+'-launch-attempt01.json',observation)
    result=None;selected=1;fatal=None
    try:
        if phase=='copy':
            result=guarded_run([str(ROOT/'.venv/bin/python'),'-B',str(HERE/'entry01.py'),'--copy-worker'],cwd=ROOT,receipt_dir=HERE/'copy-guard01',memory_max_bytes=256*1024**2,memory_high_bytes=192*1024**2,memory_swap_max_bytes=0,reserve_bytes=3*GIB,start_reserve_bytes=int(3.5*GIB),disk_paths=[ROOT,DATA],disk_floor_bytes=10*GIB,wall_seconds=14400,storage_budget={'root':str(HERE),'limits':{'max_allocated_bytes':5*GIB,'max_logical_bytes':5*GIB,'max_entries':4096,'max_depth':16,'max_scan_seconds':5}})
            selected=0 if result['phase']=='complete' and result['child_exit_code']==0 and result['cleanup_verified'] is True else 1
        else:
            for ref in (release['copy_receipt'],release['copy_review']):need(pins.get(ref['path'])==ref['sha256'],'copy proof must be committed release evidence')
            native=json.loads(body(release['copy_native']));outer=json.loads(body(release['copy_outer']));root=json.loads(body(release['copy_root']))
            for ref in (release['copy_native'],release['copy_outer'],release['copy_root']):need(pins.get(ref['path'])==ref['sha256'],'copy native/Root proof must be committed')
            need(native['phase']=='complete' and native['child_exit_code']==0 and native['cleanup_verified'] is True and not Path(native['cgroup']).exists() and outer['entry_selected_exit_code']==0 and root['actual_root_tool_exit_code']==0,'actual copy/native/Root completion required')
            m.retire(ROOT,HERE,c,release);selected=0
    except BaseException as error:fatal=error
    try:publish(phase+'-outer-exit01.json',{'identity':ID,'phase':phase,'entry_selected_exit_code':selected,'guard_phase':None if result is None else result['phase'],'guard_child_exit_code':None if result is None else result['child_exit_code'],'cleanup_verified':None if result is None else result['cleanup_verified'],'fatal_type':None if fatal is None else type(fatal).__name__,'qualification':'Actual return fields; retire has no native child. No retry.'})
    except BaseException as secondary:
        if fatal is None:raise
        fatal.add_note('Outer receipt failed: '+repr(secondary))
    if fatal is not None:raise fatal
    raise SystemExit(selected)

if __name__=='__main__':
    if sys.argv[1:]==['--copy-worker']:worker()
    elif sys.argv[1:] in (['copy'],['retire']):launch(sys.argv[1])
    else:raise ValueError('use exactly copy or retire; no automatic chaining')
