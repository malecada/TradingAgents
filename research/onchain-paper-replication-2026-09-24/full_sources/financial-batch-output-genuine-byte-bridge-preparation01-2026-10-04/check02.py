"""Actual opaque owned sidecar IO and correction inverse; no authority objects."""
import ast,errno,hashlib,importlib.util,json,os,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import byte_bridge01 as B,recovery04 as R,owned_io as IO
checks=[];cases=[]
def check(v,n):
    if not v:raise AssertionError(n)
    checks.append(n)
def refuse(f,n):
    try:f()
    except BaseException as e:checks.append(n);return e
    raise AssertionError('accepted '+n)
def dump(n,v):
    with (P/n).open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
old=ast.parse((P/'byte_bridge01.draft01.py').read_bytes());new=ast.parse((P/'byte_bridge01.py').read_bytes())
for name in ('Cursor','validate_grant','_authority','_module','encode_held','encode_completed','release'):
    a=next(n for n in old.body if getattr(n,'name',None)==name);b=next(n for n in new.body if getattr(n,'name',None)==name)
    check(ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False),'earlier 356 control mechanics unchanged '+name)
spec=importlib.util.spec_from_file_location('draft_byte_bridge',P/'byte_bridge01.draft01.py');draft=importlib.util.module_from_spec(spec);spec.loader.exec_module(draft)
root=P/'owned-sidecars';root.mkdir(mode=0o700)
e=refuse(lambda:draft._write(R,IO,root/'red.json',b'opaque'),'original writer exact contextmanager RED')
check(type(e) is IO.CleanupFailure and not (root/'red.json').exists(),'draft failed before actual file creation')
B._write(R,IO,root/'green.json',b'opaque')
check((root/'green.json').read_bytes()==b'opaque','corrected actual writer GREEN')
check((root/'green.json').stat().st_mode&0o777==0o600,'actual exclusive sidecar mode')
refuse(lambda:B._write(R,IO,root/'green.json',b'overwrite'),'existing sidecar refused')
check((root/'green.json').read_bytes()==b'opaque','original sidecar retained after refusal')

original_write=os.write;original_close=os.close
for i,(first,later) in enumerate([(MemoryError('body'),KeyboardInterrupt('close')),(KeyboardInterrupt('body'),MemoryError('close')),(SystemExit('body'),GeneratorExit('close')),(ValueError('body'),MemoryError('close')),(ValueError('body'),OSError('close'))]):
    path=root/('fatal-%02d'%i);closed=[];opened=[]
    def write(fd,raw):opened.append(fd);raise first
    def close(fd):
        original_close(fd);closed.append(fd)
        if len(closed)==1:raise later
    os.write=write;os.close=close
    try:e=refuse(lambda:B._write(R,IO,path,b'bytes'),'real write/close failure '+str(i))
    finally:os.write=original_write;os.close=original_close
    expected=first if IO._fatal(first) else later if IO._fatal(later) else None
    check((e is expected) if expected is not None else type(e) is IO.CleanupFailure,'first-fatal/ordinary uncertainty '+str(i))
    check(len(closed)==2 and len(set(closed))==2 and opened[0] in closed,'file and parent closed once '+str(i))
    for fd in closed:
        try:os.fstat(fd)
        except OSError as ex:check(ex.errno==errno.EBADF,'actual fd absent '+str(i)+' '+str(fd))
        else:raise AssertionError('descriptor retained')
    check(path.exists() and path.stat().st_size==0,'actual partial file retained '+str(i))
    cases.append({'body':type(first).__name__,'cleanup':type(later).__name__,'raised':type(e).__name__,'first_fatal_identity_preserved':expected is first,'all_owned_fds_observed_closed':True,'partial_retained':True})

# R4 new_file checks original parent namespace after every successful body.
anchor=root/'anchor';anchor.mkdir(mode=0o700);moved=root/'retained-anchor';other=root/'other';other.mkdir(mode=0o700)
swapped=[]
def redirect(fd,raw):
    n=original_write(fd,raw)
    if not swapped:
        anchor.rename(moved);anchor.symlink_to(other,target_is_directory=True);swapped.append(True)
    return n
os.write=redirect
try:e=refuse(lambda:B._write(R,IO,anchor/'retained.json',b'redirect-control'),'actual late parent redirect refused')
finally:os.write=original_write
check((moved/'retained.json').read_bytes()==b'redirect-control' and not (other/'retained.json').exists(),'owned retained original parent, no redirected write')
check(anchor.is_symlink(),'literal negative link retained')
check(not any(n in sys.modules for n in ('numpy','torch','scipy','pandas','tradingagents')),'no numerical/project imports')
dump('CHECKS02.json',{'status':'CORRECTED_OWNED_IO_SOURCE_ONLY','checks':checks,'count':len(checks),'cases':cases,'draft_sha256':hashlib.sha256((P/'byte_bridge01.draft01.py').read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256((P/'byte_bridge01.py').read_bytes()).hexdigest(),'original_356_controls_remain_byte_mechanics_not_genuine_execution':True})
print(json.dumps({'checks':len(checks),'actual_fault_pairs':len(cases),'candidate_sha256':hashlib.sha256((P/'byte_bridge01.py').read_bytes()).hexdigest()}))
