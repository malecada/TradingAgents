import ast, hashlib, importlib.util, itertools, json, os, stat, struct, sys, traceback
from pathlib import Path
import npy_bytes01 as N
ROOT = Path(__file__).resolve().parent
R = ROOT.parents[3]
S = Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
checks = []; cases = ROOT/'cases01'; cases.mkdir()
def ok(value, name):
    assert value, name
    checks.append(name)
def refuses(call, name, typ=ValueError):
    try: call()
    except typ as e: checks.append(name + ': ' + type(e).__name__ + ': ' + str(e)); return e
    raise AssertionError('accepted ' + name)
def header(n=4, version=(1,0), body=None):
    body = body or "{'descr': '<f4', 'fortran_order': False, 'shape': (%d, 32), }" % n
    code = '<H' if version==(1,0) else '<I'
    length=len(body)+1; padding=64-((8+struct.calcsize(code)+length)%64)
    return b'\x93NUMPY'+bytes(version)+struct.pack(code,length+padding)+body.encode()+b' '*padding+b'\n'
def meta(h, raw):
    v = {key:N.sha(('opaque-role:'+key).encode()) for key in N.ROLES}
    v.update(member='array-000000.npy', rows=4, columns=32, dtype='<f4', order='C', file_bytes=len(h+raw), file_sha256=N.sha(h+raw), header_sha256=N.sha(h), payload_sha256=N.sha(raw))
    return N.canonical(v)
def fixture(name, data=None, m=None):
    d=cases/name; d.mkdir(); p=d/'array-000000.npy'
    h=header(); raw=b'opaque-0123456789'*32
    p.write_bytes(h+raw if data is None else data); p.chmod(0o600)
    return p, meta(h,raw) if m is None else m
h=header(); raw=b'opaque-0123456789'*32
ok(len(raw)==512,'opaque extent')
# Pin source text; never import NumPy or scientific modules.
pins=[]
for p in [R/'.venv/lib/python3.13/site-packages/numpy/lib/_format_impl.py', R/'.venv/lib/python3.13/site-packages/numpy/lib/format.py', S/'tradingagents/research/onchain_replication/component_store.py', S/'tradingagents/research/onchain_replication/compact_graph_artifacts.py', S/'tradingagents/research/onchain_replication/compact_features.py', S/'tradingagents/research/onchain_replication/compact_owner.py']:
    b=p.read_bytes(); pins.append({'path':str(p),'sha256':N.sha(b),'bytes':len(b),'mode':stat.S_IMODE(p.stat().st_mode)})
(ROOT/'SOURCE_PINS01.json').write_bytes(N.canonical({'sources':pins,'python':sys.version,'executable':str(Path(sys.executable).resolve()),'executable_sha256':N.sha(Path(sys.executable).resolve().read_bytes())}))
# Exact isolated pinned writer AST: no NumPy import, no array creation.
tree=ast.parse(Path(pins[0]['path']).read_text()); wrap=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='_wrap_header')
ns={'_header_size_info':{(1,0):('<H','latin1'),(2,0):('<I','latin1'),(3,0):('<I','utf8')},'ARRAY_ALIGN':64,'MAGIC_LEN':8,'magic':lambda a,b:b'\x93NUMPY'+bytes((a,b))}
exec(compile(ast.Module(body=[wrap],type_ignores=[]),'pinned_numpy_wrap_header','exec'),ns)
(ROOT/'PINNED_WRAP_HEADER01.py').write_text(ast.get_source_segment(Path(pins[0]['path']).read_text(),wrap)+'\n')
for version in ((1,0),(2,0),(3,0)):
    body="{'descr': '<f4', 'fortran_order': False, 'shape': (4, 32), }"
    hv=header(version=version)
    ok(hv==ns['_wrap_header'](body,version),'literal pinned header writer '+str(version))
    e=N.parse_header(hv); ok(e.rows==4 and e.payload_bytes==512 and e.literal_header==hv,'envelope '+str(version))
    p,m=fixture('v'+str(version[0]),hv+raw,meta(hv,raw)); c=N.Cursor(p,m)
    out=b''.join(c.read(i,4) for i in range(0,512,4)); proof=json.loads(c.finish())
    ok(out==raw and proof['header_hex']==hv.hex() and proof['file_sha256']==N.sha(hv+raw),'actual aligned cursor '+str(version))
    refuses(c.finish,'finish replay '+str(version)); ok(c.state=='FAILED' and c.fd is None,'terminal replay failed')
for perm in itertools.permutations(["'descr': '<f4'","'shape': (4, 32)","'fortran_order': False"]):
    ok(N.parse_header(header(body='{'+', '.join(perm)+', }')).rows==4,'unordered keys '+str(perm))
bad_bodies=["{'descr': '>f4', 'fortran_order': False, 'shape': (4, 32), }", "{'descr': '=f4', 'fortran_order': False, 'shape': (4, 32), }", "{'descr': '|f4', 'fortran_order': False, 'shape': (4, 32), }", "{'descr': '<f8', 'fortran_order': False, 'shape': (4, 32), }", "{'descr': '|O', 'fortran_order': False, 'shape': (4, 32), }", "{'descr': '<f4', 'fortran_order': True, 'shape': (4, 32), }", "{'descr': '<f4', 'fortran_order': 0, 'shape': (4, 32), }", "{'descr': '<f4', 'fortran_order': False, 'shape': (0, 32), }", "{'descr': '<f4', 'fortran_order': False, 'shape': (4, 31), }", "{'descr': '<f4', 'fortran_order': False, 'shape': (True, 32), }", "{'descr': '<f4', 'fortran_order': False, 'shape': (04, 32), }", "{'descr': '<f4', 'fortran_order': False, 'shape': (4, 32, 1), }", "{'descr': '<f4', 'fortran_order': False, 'shape': (__import__('os'), 32), }", "{'descr': '<f4', 'descr': '<f4', 'fortran_order': False, 'shape': (4, 32), }", "{'descr': '<f4', 'fortran_order': False, 'shape': (4, 32), 'extra': False}"]
for i,b in enumerate(bad_bodies): refuses(lambda b=b:N.parse_header(header(body=b)),'bad header grammar '+str(i))
for i,b in enumerate([b'BADNPY'+h[6:],h[:6]+b'\x04\x00'+h[8:],h[:-1],h[:-1]+b'X',h[:-2]+b'\t\n',h[:8]+b'\xff\xff'+h[10:],h+b' '*64]):
    refuses(lambda b=b:N.parse_header(b),'bad framing '+str(i))
for key in ('rows','columns','file_bytes'):
    for v in (True,4.0,'4'):
        m=json.loads(meta(h,raw));m[key]=v
        refuses(lambda m=m:N.expected(N.canonical(m)),'strict expected '+key+str(v))
refuses(lambda:N.expected(json.loads(meta(h,raw))),'mutable expected dict')
for key in N.ROLES:
    m=json.loads(meta(h,raw));m.pop(key)
    refuses(lambda m=m:N.expected(N.canonical(m)),'missing role '+key)
for name,data in [('truncated',h+raw[:-1]),('extra',h+raw+b'x'),('corrupt',h+raw[:-1]+b'X')]:
    p,m=fixture(name,data)
    if name!='corrupt': refuses(lambda:N.Cursor(p,m),name)
    else:
        c=N.Cursor(p,m);c.read(0,512);refuses(c.finish,name);ok(c.state=='FAILED','hash failure terminal')
for name,offset,size in [('misaligned',0,3),('skip',4,4),('bool',False,4),('float',0,4.0),('oversize',0,N.READ_LIMIT+4),('extent',0,516)]:
    p,m=fixture(name);c=N.Cursor(p,m);refuses(lambda:c.read(offset,size),name);ok(c.state=='FAILED' and c.fd is None,'failed closed '+name)
p,m=fixture('replay');c=N.Cursor(p,m);c.read(0,4);refuses(lambda:c.read(0,4),'offset replay')
p,m=fixture('incomplete');c=N.Cursor(p,m);refuses(c.finish,'incomplete finish')
p,m=fixture('mutated-metadata');c=N.Cursor(p,m);c.spec['rows']=5;refuses(lambda:c.read(0,4),'changed expected dictionary')
p,m=fixture('short');c=N.Cursor(p,m); realread=os.read
try:
    os.read=lambda fd,n:realread(fd,max(0,n-1))
    refuses(lambda:c.read(0,128),'actual short read')
finally:os.read=realread
# Same extent final-close corruption must refuse through current file signatures.
p,m=fixture('close-corruption');c=N.Cursor(p,m);c.read(0,512);realclose=os.close; target=c.fd
try:
    def close_corrupt(fd):
        realclose(fd)
        if fd==target:
            with p.open('r+b') as f:f.seek(len(h));f.write(b'X');f.flush();os.fsync(f.fileno())
    os.close=close_corrupt
    refuses(c.finish,'actual post-close same-extent corruption')
finally:os.close=realclose
ok(c.state=='FAILED' and c.fd is None,'post-close retained failed')
# Real descriptor closes then injected failures; all nine ordered primary pairs.
for i,A in enumerate((ValueError,MemoryError,SystemExit)):
 for j,B in enumerate((ValueError,MemoryError,SystemExit)):
    p,m=fixture('fatal-%d-%d'%(i,j));c=N.Cursor(p,m);target=c.fd;a=A('read-primary');b=B('close-secondary');closed=[]
    def read_bad(fd,n):raise a
    def close_bad(fd):realclose(fd);closed.append(fd);raise b
    os.read=read_bad;os.close=close_bad
    try:
        try:c.read(0,4)
        except BaseException as error:
            selected=a if A in (MemoryError,SystemExit) else b if B in (MemoryError,SystemExit) else None
            ok(error is selected if selected is not None else isinstance(error,N.IO.CleanupFailure),'first fatal identity %d %d'%(i,j))
            ok(c.fd is None and c.state=='FAILED' and closed==[target],'one actual close %d %d'%(i,j))
        else:raise AssertionError('fatal accepted')
    finally:os.read=realread;os.close=realclose
# Metadata-only projected extent is permitted to describe; local file cap unchanged.
n=N.RAW_LIMIT//128; big=N.parse_header(header(n=n));ok(big.payload_bytes==N.RAW_LIMIT,'projected envelope only no allocation')
refuses(lambda:N.production(None),'production no authority',PermissionError)
ok(not any(x in sys.modules for x in ('numpy','torch','scipy')),'no numerical imports')
(ROOT/'CHECKS01.json').write_bytes(N.canonical({'count':len(checks),'checks':checks,'numerical_imports':False,'actual_genuine_handles':False,'fixtures':'opaque byte strings only'}))
print(json.dumps({'checks':len(checks),'status':'PASS'}))
