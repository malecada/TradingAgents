"""Install a reviewed flat-only helper in an already completed receiver."""
from pathlib import Path
import hashlib, json, os, stat, time, datetime, sys

ROOT = Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
FS = ROOT/'research/onchain-paper-replication-2026-09-24/full_sources'
D = FS/'financial-wrapper-compatibility-operational-delta-root-remote03-2026-10-04'
A = FS/'financial-wrapper-compatibility-operational-delta-flat-source-mode-successor04-2026-10-04'
V = FS/'financial-wrapper-compatibility-operational-delta-flat-source-mode-review04-2026-10-04'

def digest(b): return hashlib.sha256(b).hexdigest()
def signature(s): return tuple(getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns','st_blocks'))
def read(p, pin):
    s=p.lstat()
    assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304
    b=p.read_bytes()
    assert digest(b)==pin and signature(p.lstat())==signature(s)
    return b
def write(p,b):
    assert not os.path.lexists(p)
    fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as f: f.write(b); f.flush(); os.fsync(f.fileno())
    assert p.read_bytes()==b and stat.S_IMODE(p.lstat().st_mode)==0o600

requirements_raw=read(A/'INSTALLATION_REQUIREMENTS01.json','0a14ec3786d6d47c9cb59ee5e51b04492c5d0671036f9e50183122d4e81be7a4')
req=json.loads(requirements_raw)
am=read(A/'MANIFEST01.json','29db85f0e660532afd721f6889c3b34322737ab3c4a9739a37bf2bf6e292225a')
vm=read(V/'MANIFEST01.json','c1ed84e2e6ca5b46b10b6be03f5e80d41dada73611643997661d9e5d4f783aa8')
machine_raw=read(V/'MACHINE01.json','c1f124a6952a3006d8b4f6f4669cf0d5a2768343cfbd94f7004d586505f76f98')
machine=json.loads(machine_raw)
assert machine['decision']=='ACCEPTED_SOURCE_ONLY_EXACT_COMPLETED_INPUT_MODE_PROFILE'
assert machine['source_sha256']==req['restore_helper']['sha256'] and machine['author_manifest_sha256']==digest(am)
assert req['receiver_root']==str(D) and req['actual_entry_release'] is None and req['actual_root_installation'] is None
assert any(x.get('path')=='MACHINE01.json' and x.get('sha256')==digest(machine_raw) for x in json.loads(vm)['members'])
assert any(x.get('path')=='restore01.py' and x.get('sha256')==req['restore_helper']['sha256'] for x in json.loads(am)['members'])
assert D.resolve()==D and stat.S_IMODE(D.lstat().st_mode)==0o700
for name in ('flat-operational-delta01','flat-failed-remote02-01','FLAT_INTENT01.json','FLAT_RECOVERY01.json','FLAT_FAILED01.json','FLAT_POSTWRITE_OBSERVATION01.json','ROOT_FLAT04_INTENT01.json','ROOT_FLAT04.stdout','ROOT_FLAT04.stderr','ROOT_FLAT04_EXIT01.json'):
    assert not os.path.lexists(D/name)
bindings={}
for name,pin in req['unchanged_dependencies'].items():
    b=read(D/name,pin); bindings[name]={'sha256':pin,'bytes':len(b),'mode':stat.S_IMODE((D/name).lstat().st_mode)}
sys.path.insert(0,str(D)); sys.path.insert(0,str(D/'utilities'))
import watch01 as W
before=W.census(D)
for name,pin in {'REMOTE_RECOVERY01.json':req['actual_remote_receipt_sha256'],'ROOT_REMOTE03_EXIT01.json':req['actual_root_exit_sha256'],'SELECTED_BODIES01.json':req['actual_selection_sha256']}.items():
    read(D/name,pin)
new={req['restore_helper']['file']:read(A/req['restore_helper']['file'],req['restore_helper']['sha256'])}
for name,row in req['new_exact_metadata_dependencies'].items():
    b=read(A/name,row['sha256']); assert len(b)==row['bytes']; new[name]=b
assert len(new)==4 and all(not os.path.lexists(D/n) for n in new)
for name,b in new.items():
    write(D/name,b); bindings[name]={'sha256':digest(b),'bytes':len(b),'mode':0o600}
after=W.census(D)
draft={'schema_version':1,'status':'INSTALLED_FLAT04_DRAFT_NOT_RELEASED','owned_root':str(D),'source_only':True,'requirements_sha256':digest(requirements_raw),'author_manifest_sha256':digest(am),'source_review_machine_sha256':digest(machine_raw),'source_review_manifest_sha256':digest(vm),'source_sha256':req['restore_helper']['sha256'],'remote_receipt_sha256':req['actual_remote_receipt_sha256'],'original_Root_exit_sha256':req['actual_root_exit_sha256'],'selection_sha256':req['actual_selection_sha256'],'helpers_and_metadata':bindings,'new_files':sorted(new),'new_output_names':['flat-operational-delta01','flat-failed-remote02-01'],'initial_owned_observation':before,'installed_owned_observation':after,'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'original_receiver_modes_mutated':False,'numerical_authority':False,'actual_flat_release':None,'actual_flat_result':None}
write(D/'ROOT_FLAT04_INSTALLATION_DRAFT01.json',(json.dumps(draft,sort_keys=True,indent=2)+'\n').encode())
print(json.dumps({'installed':len(new),'draft_sha256':digest((D/'ROOT_FLAT04_INSTALLATION_DRAFT01.json').read_bytes()),'after':after}))
