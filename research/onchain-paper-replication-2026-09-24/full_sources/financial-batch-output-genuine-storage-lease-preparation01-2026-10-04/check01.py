import ast,hashlib,importlib.util,json,os,stat,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import storage_lease01 as L
CHECKS=[]
def ok(value,name):
    if not value:raise AssertionError(name)
    CHECKS.append(name)
def reject(fn,name,types=(BaseException,)):
    try:fn()
    except types as e:CHECKS.append(name+':'+type(e).__name__);return e
    raise AssertionError('accepted '+name)
ROOT=HERE/'opaque01';ROOT.mkdir(mode=0o700)
def fresh(name):
    root=ROOT/name;root.mkdir(mode=0o700)
    roles={r:r for r in L.ROLES}
    for p in roles.values():(root/p).mkdir(mode=0o700)
    return root,roles

def lease(name,callback=lambda:None):
    root,roles=fresh(name)
    return root,L.OwnedLease(root,'lease',roles,64*L.MIB,64*L.MIB,callback)

def all_closed(fds):
    for fd in fds:
        try:os.fstat(fd)
        except OSError:continue
        return False
    return True

root,le=lease('retained')
first=le.check();prior=(le.logical_reserved,le.allocated_reserved)
for role in L.ROLES:
    name=role+'/body';raw=(role+' opaque').encode()
    ticket=[(name,'file',len(raw))]
    le.perform(role,ticket,lambda check,name=name,raw=raw: ((root/name).write_bytes(raw),check()))
    sample=le.check()
    ok(sample['logical_reserved']>prior[0] and sample['allocated_reserved']>prior[1],'monotone reservation '+role)
    prior=(le.logical_reserved,le.allocated_reserved)
    ok((root/name).read_bytes()==raw,'retained body '+role)
le.reserve('codec',[('codec/nested','directory',L.DIRECTORY),('codec/nested/second','file',7)],scratch_bytes=8192)
(root/'codec/nested').mkdir(mode=0o700);(root/'codec/nested/second').write_bytes(b'opaque!');le.check()
ok(len([p for p in root.rglob('*') if p.is_file()])>=10,'all simultaneous retained roles')
fdset=(le.fd,le.ledger_fd);le.close();ok(all_closed(fdset),'normal owned descriptors closed')
reject(le.check,'closed never reusable')
reject(lambda:L.OwnedLease(root,'lease',{r:r for r in L.ROLES},64*L.MIB,64*L.MIB,lambda:None),'same namespace never reopened')

# Mutation and failed checks are all retained in independent real tiny trees.
for kind in ('unreserved','oversize','hardlink','symlink','redirect','missing','replace','mode','partial','reuse','state','callbackstate'):
    rt,x=lease(kind);fds=(x.fd,x.ledger_fd)
    if kind=='unreserved':(rt/'codec/unreserved').write_bytes(b'x');fn=x.check
    elif kind=='oversize':
        x.reserve('codec',[('codec/x','file',1)]);(rt/'codec/x').write_bytes(b'xx');fn=x.check
    elif kind=='hardlink':
        x.reserve('codec',[('codec/x','file',1)]);(rt/'codec/x').write_bytes(b'x');os.link(rt/'codec/x',rt/'codec/y');fn=x.check
    elif kind=='symlink':os.symlink('codec',rt/'link');fn=x.check
    elif kind=='redirect':
        moved=rt.parent/(rt.name+'-retained');rt.rename(moved);os.symlink(moved,rt);fn=x.check
    elif kind=='missing':(rt/'spool').rmdir();fn=x.check
    elif kind=='replace':
        (rt/'spool').rename(rt/'old-spool');(rt/'spool').mkdir();fn=x.check
    elif kind=='mode':(rt/'spool').chmod(0o755);fn=x.check
    elif kind=='partial':
        x.reserve('codec',[('codec/x','file',3)]);(rt/'codec/x').write_bytes(b'x');x.check();(rt/'codec/x').write_bytes(b'xyz');x.check();(rt/'codec/x').write_bytes(b'abc');fn=x.check
    elif kind=='reuse':
        x.reserve('codec',[('codec/x','file',3)]);fn=lambda:x.reserve('codec',[('codec/x','file',3)])
    elif kind=='state':x.logical_reserved-=1;fn=x.check
    else:
        class Mutator:
            def __call__(self):x.logical_reserved-=1
        # Actual callback identity intentionally cannot be replaced either.
        x._callback=Mutator();fn=x.check
    e=reject(fn,kind);ok(x.failed,kind+' poisoned');ok(all_closed(fds),kind+' actual descriptors closed')
    reject(x.check,kind+' cannot retry');x.close()

# File cap: sparse opaque file is a negative utility fixture, not scientific data.
rt,roles=fresh('file-cap');f=rt/'producer/large'
with f.open('xb') as stream:stream.truncate(L.FILE+1)
reject(lambda:L.OwnedLease(rt,'lease',roles,64*L.MIB,64*L.MIB,lambda:None),'actual 4MiB+1 per-file refusal')

for bad in ('/absolute','../escape','a//b','a/../b','keys/x','x/.env',''):
    reject(lambda bad=bad:L.relative(bad),'path '+repr(bad))
for role in L.ROLES:
    rt,x=lease('badrole-'+role);fds=(x.fd,x.ledger_fd)
    reject(lambda:x.reserve(role,[('outside','file',1)]),'role containment '+role);ok(all_closed(fds),'role failure cleanup '+role)
rt,x=lease('parent');reject(lambda:x.reserve('codec',[('codec/missing/x','file',1)]),'missing parent projected first')
rt,x=lease('cap');before=(x.logical_reserved,x.allocated_reserved)
# Exact prospective full-cap refusal with only tiny actual bytes; no 64MiB outcome.
reject(lambda:x.reserve('codec',[('codec/a'+str(i),'file',L.FILE) for i in range(16)]),'prospective 64MiB plan exceeds cumulative cap')
ok((x.logical_reserved,x.allocated_reserved)==before,'pre-refusal not spent but poisoned')

# Floor gate is deterministic syscall-control only; actual initial floor checked above.
rt,x=lease('floor');original=L.os.fstatvfs
class V: f_bavail=L.FLOOR;f_frsize=1
try:
    L.os.fstatvfs=lambda fd:V()
    reject(x.check,'floor requires outstanding committed headroom')
finally:L.os.fstatvfs=original

# Every BaseException category permanently poisons after a spent reservation.
class Fatal(BaseException):pass
for i,primary in enumerate((ValueError('ordinary'),KeyboardInterrupt(),SystemExit(17),MemoryError(),Fatal())):
    rt,x=lease('fatal-'+str(i));fds=(x.fd,x.ledger_fd);before=x.logical_reserved
    def write(check):
        (rt/'codec/x').write_bytes(b'x')
        raise primary
    got=reject(lambda:x.perform('codec',[('codec/x','file',3)],write),'writer primary '+str(i))
    ok(got is primary,'original primary identity '+str(i));ok(x.failed and x.logical_reserved>before,'spent reservation retained '+str(i));ok(all_closed(fds),'fatal descriptors absent '+str(i));ok((rt/'codec/x').read_bytes()==b'x','partial retained '+str(i));x.close()

# Real two-FD close, injected close exceptions AFTER the genuine close. Preserve
# primary fatal while attempting both actual descriptors; no numerical handles.
for i,(primary,secondary) in enumerate(((KeyboardInterrupt(),SystemExit(7)),(MemoryError(),ValueError('close')),(SystemExit(9),MemoryError()))):
    rt,x=lease('close-'+str(i));fds=(x.fd,x.ledger_fd);seen=[];close=L.os.close
    def closing(fd):
        close(fd)
        if fd in fds:seen.append(fd);raise secondary
    try:
        L.os.close=closing
        def write(check):raise primary
        got=reject(lambda:x.perform('codec',[('codec/x','file',1)],write),'real close fatal '+str(i))
    finally:L.os.close=close
    ok(got is primary,'first fatal preserved '+str(i));ok(set(seen)==set(fds) and all_closed(fds),'all real close attempts '+str(i));x.close()

# Nonrecursive callback guard, no held-lock construction.
rt,roles=fresh('recursive');slot={};count=[0]
def cb():
    count[0]+=1
    if 'x' in slot:slot['x'].check()
x=L.OwnedLease(rt,'lease',roles,64*L.MIB,64*L.MIB,cb);slot['x']=x
reject(x.check,'recursive callback refused without deadlock');ok(x.failed and x.fd is None,'recursive refusal poisoned closed')

# Strict grant/source mechanics only, no fabricated authority object.
roles={r:r for r in L.ROLES};graphs={'a'*64:2,'b'*64:3}
g={'schema_version':1,'kind':'two-imported-target-retained-lease-v1','execution_job_sha256':'c'*64,'roles':roles,'targets':graphs,'max_logical_bytes':64*L.MIB,'max_allocated_bytes':64*L.MIB,'max_file_bytes':L.FILE,'free_floor_bytes':L.FLOOR,'root_scope':'entire-admission-root','publication':False,'transport':False,'retirement':False}
ok(L.validate_grant(g,'c'*64,roles,graphs)==g,'finite genuine grant shape utility')
for key in g:
    m=json.loads(json.dumps(g));m[key]=None
    reject(lambda m=m:L.validate_grant(m,'c'*64,roles,graphs),'grant field '+key)
source=(HERE/'storage_lease01.py').read_text();tree=ast.parse(source)
imports=[n for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom))]
ok(all(not any(word in ast.unparse(n).lower() for word in ('numpy','torch','scipy','pandas')) for n in imports),'no numerical imports')
ok('run.admission.source!=DENIED_SOURCE' in source,'Source339 explicitly unavailable')
ok("job.get('kind')=='compact_resource'" in source,'financial grant explicitly unavailable')
ok('._held(' not in source and '.start(' not in source and '.admit(' not in source,'no owner recursive acquisition or creation/admission')
ok(hashlib.sha256((HERE/'owned_io.py').read_bytes()).hexdigest()==L.IO_SHA,'unchanged genuine first-fatal IO')
result={'checks':len(CHECKS),'names':CHECKS,'source_sha256':hashlib.sha256((HERE/'storage_lease01.py').read_bytes()).hexdigest(),'actual_scientific_handles_executed':False,'actual_capacity_demonstrated':False,'numeric_imports':False,'scope':'owned opaque retained-tree source engineering only'}
(HERE/'CHECKS01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({'checks':len(CHECKS),'status':'PASS'}))
