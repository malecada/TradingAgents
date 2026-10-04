"""One independently released flat-only entry on the completed receiver."""
from pathlib import Path
import argparse, datetime, hashlib, json, os, resource, shutil, signal, stat, subprocess, sys, time

ROOT=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
FS=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources'
D=FS/'financial-wrapper-compatibility-operational-delta-root-remote03-2026-10-04'
V=FS/'financial-wrapper-compatibility-operational-delta-flat-entry-review04-2026-10-04'
DRAFT='770f509c8a65a1a5a6cb33e2efbf8215c9466ba5af235251b883ac1452299e21'
HELPER='17f4ee85d2408cdc1b678e107e82b6e19b674b4b941f1fa51f40f17bbedef282'
REMOTE='64c74556c7060fc7d118b5b07354bb737e5c157446ffef8c27fe77ea6cef4d47'
SELECTION='d2f64f4a7175ab13de9f40bcb7c700dc615197c61e65c39456233a21617bb23b'
FILE=4194304
def digest(b): return hashlib.sha256(b).hexdigest()
def signature(s): return tuple(getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns','st_blocks'))
def read(p,pin=None):
    s=p.lstat()
    assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=FILE
    b=p.read_bytes()
    assert signature(p.lstat())==signature(s)
    assert pin is None or digest(b)==pin
    return b
def put(name,o):
    b=(json.dumps(o,sort_keys=True,indent=2,allow_nan=False)+'\n').encode(); assert len(b)<=FILE
    fd=os.open(D/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as f: f.write(b); f.flush(); os.fsync(f.fileno())

parser=argparse.ArgumentParser(); parser.add_argument('--entry-review-sha256',required=True)
args=parser.parse_args(); raw=read(V/'MACHINE01.json',args.entry_review_sha256); release=json.loads(raw)
assert release['decision']=='ACCEPTED_EXACT_ONE_USE_OPERATIONAL_FLAT_ENTRY_ONLY'
assert release['owned_root']==str(D) and release['root_outer_caller_sha256']==digest(read(Path(__file__).absolute()))
assert release['installation_draft_sha256']==DRAFT and release['flat_helper_sha256']==HELPER
assert release['remote_receipt_sha256']==REMOTE and release['selection_sha256']==SELECTION
assert release['flat_execution_released'] is True and release['remote_execution_released'] is False and release['numerical_authority'] is False
draft=json.loads(read(D/'ROOT_FLAT04_INSTALLATION_DRAFT01.json',DRAFT))
assert draft['status']=='INSTALLED_FLAT04_DRAFT_NOT_RELEASED' and draft['owned_root']==str(D) and draft['actual_flat_release'] is None
assert digest(read(D/'restore01.py'))==HELPER
for name,row in draft['helpers_and_metadata'].items():
    body=read(D/name,row['sha256']); assert len(body)==row['bytes'] and stat.S_IMODE((D/name).lstat().st_mode)==row['mode']
read(D/'REMOTE_RECOVERY01.json',REMOTE); read(D/'SELECTED_BODIES01.json',SELECTION)
read(D/'ROOT_REMOTE03_EXIT01.json',draft['original_Root_exit_sha256'])
for name in ('flat-operational-delta01','flat-failed-remote02-01','FLAT_INTENT01.json','FLAT_RECOVERY01.json','FLAT_FAILED01.json','FLAT_POSTWRITE_OBSERVATION01.json','ROOT_FLAT04_INTENT01.json','ROOT_FLAT04_SPAWN01.json','ROOT_FLAT04.stdout','ROOT_FLAT04.stderr','ROOT_FLAT04_EXIT01.json'):
    assert not os.path.lexists(D/name)
for p in Path('/proc').iterdir():
    if not p.name.isdigit() or int(p.name)==os.getpid(): continue
    try: argv=(p/'cmdline').read_bytes().split(b'\0')
    except (FileNotFoundError,ProcessLookupError,PermissionError): continue
    assert str(D/'restore01.py').encode() not in argv and str(D/'recover01.py').encode() not in argv
sys.path.insert(0,str(D)); sys.path.insert(0,str(D/'utilities'))
import watch01 as W
assert D.resolve()==D and stat.S_IMODE(D.lstat().st_mode)==0o700
assert shutil.disk_usage(D).free>=W.POLICY['floor']
observations=[W.census(D)]
command=[str(ROOT/'.venv/bin/python'),'-B',str(D/'restore01.py'),'--remote-receipt-sha256',REMOTE,'--selection-sha256',SELECTION]
begun=time.monotonic(); child=None; code=None; primary=None; cleanup=[]
resource.setrlimit(resource.RLIMIT_FSIZE,(FILE,FILE))
put('ROOT_FLAT04_INTENT01.json',{'schema_version':1,'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':command,'cwd':str(ROOT),'entry_review_sha256':digest(raw),'installation_draft_sha256':DRAFT,'outer_caller_sha256':digest(read(Path(__file__).absolute())),'parent_pid':os.getpid(),'one_use':True,'remote_relaunched':False,'native_or_claim_started':False})
try:
    outfd=os.open(D/'ROOT_FLAT04.stdout',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    try:
        errfd=os.open(D/'ROOT_FLAT04.stderr',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    except BaseException:
        os.close(outfd); raise
    with os.fdopen(outfd,'wb') as out, os.fdopen(errfd,'wb') as err:
        child=subprocess.Popen(command,cwd=ROOT,stdout=out,stderr=err,start_new_session=True)
        put('ROOT_FLAT04_SPAWN01.json',{'schema_version':1,'pid':child.pid,'parent_pid':os.getpid(),'argv':command,'time':datetime.datetime.now(datetime.timezone.utc).isoformat()})
        while True:
            code=child.poll()
            if code is not None: break
            assert time.monotonic()-begun<210 and len(observations)<128 and shutil.disk_usage(D).free>=W.POLICY['floor']
            observations.append(W.census(D))
            try: code=child.wait(timeout=0.25); break
            except subprocess.TimeoutExpired: pass
except BaseException as error:
    primary=error
finally:
    if child is not None:
        if child.poll() is None:
            try: os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError: pass
            except BaseException as error: cleanup.append(type(error).__name__)
        try: code=child.wait(timeout=10)
        except BaseException as error: cleanup.append(type(error).__name__)
    try: observations.append(W.census(D))
    except BaseException as error:
        cleanup.append(type(error).__name__)
        if primary is None: primary=error
    put('ROOT_FLAT04_EXIT01.json',{'schema_version':1,'actual_outer_exit':code if primary is None and not cleanup else 1,'actual_child_exit':code,'actual_child_pid':None if child is None else child.pid,'elapsed_seconds':time.monotonic()-begun,'parent_failure_type':None if primary is None else type(primary).__name__,'cleanup_failures':cleanup,'stdout_bytes':(D/'ROOT_FLAT04.stdout').stat().st_size if (D/'ROOT_FLAT04.stdout').exists() else None,'stdout_sha256':digest(read(D/'ROOT_FLAT04.stdout')) if (D/'ROOT_FLAT04.stdout').exists() else None,'stderr_bytes':(D/'ROOT_FLAT04.stderr').stat().st_size if (D/'ROOT_FLAT04.stderr').exists() else None,'stderr_sha256':digest(read(D/'ROOT_FLAT04.stderr')) if (D/'ROOT_FLAT04.stderr').exists() else None,'whole_owned_observations':observations,'actual_inherited_child_fsize':[FILE,FILE],'remote_relaunched':False,'native_or_claim_started':False})
if primary is not None: raise primary
assert not cleanup and code is not None
print(json.dumps({'actual_child_exit':code,'elapsed_seconds':time.monotonic()-begun}))
raise SystemExit(code)
