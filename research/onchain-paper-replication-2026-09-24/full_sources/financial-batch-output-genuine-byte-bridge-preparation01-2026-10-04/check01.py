"""Opaque utility controls only; genuine source classes are AST inspected only."""
import ast,difflib,hashlib,json,os,sys
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import byte_bridge01 as B
import codec01 as C
import local_store01 as L
checks=[];witnesses=[]
def check(ok,name):
    if not ok:raise AssertionError(name)
    checks.append(name)
def refuse(fn,name,identity=None):
    try:fn()
    except BaseException as e:
        if identity is not None:check(e is identity,name+' exact primary')
        check(True,name);return e
    raise AssertionError('accepted '+name)
def descriptor(role,rows):return {'schema_version':1,'kind':'mcm-batch-output-bytes','role':role,'dtype':'<f8' if role=='score-batches' else '<f4','shape':[rows,32],'order':'C','scope':{n:hashlib.sha256(n.encode()).hexdigest() for n in C.SCOPE},'motifs':32,'spent_samples':512}
def save(name,obj):
    with (P/name).open('x') as f:json.dump(obj,f,sort_keys=True,indent=2);f.write('\n')

# Exact predecessor bodies and every pre-existing AST node remain unchanged.
for n,added in [('held_score_consumer','encode_codec_held'),('completed_f32','encode_codec_completed')]:
    old=(P/(n+'.original.py')).read_bytes();new=(P/(n+'.py')).read_bytes()
    check(new.startswith(old),'full literal predecessor '+n)
    a=ast.parse(old);b=ast.parse(new);check(len(b.body)==len(a.body)+1 and isinstance(b.body[-1],ast.FunctionDef) and b.body[-1].name==added,'single appended entrypoint '+n)
    inverse=ast.Module(body=b.body[:-1],type_ignores=[])
    check(ast.dump(a,include_attributes=False)==ast.dump(inverse,include_attributes=False),'full AST inverse '+n)
    (P/(n+'.patch')).write_text(''.join(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),fromfile=n+'.original.py',tofile=n+'.py')))
    check(new[:len(old)]==old,'inverse bytes '+n)
deps=json.loads((P/'DEPENDENCIES01.json').read_bytes())
for n,row in deps.items():
    check(hashlib.sha256((P/n).read_bytes()).hexdigest()==row['sha256']==B.PINS[n[:-3]],'unchanged dependency '+n)
for n in ['byte_bridge01.py','held_score_consumer.py','completed_f32.py']:ast.parse((P/n).read_bytes());check(True,'source parses '+n)
tree=ast.parse((P/'byte_bridge01.py').read_bytes())
imports=[node for node in tree.body if isinstance(node,(ast.Import,ast.ImportFrom))]
check(all(not isinstance(n,ast.ImportFrom) or n.module=='pathlib' for n in imports),'no eager project imports')
check(not any(n in sys.modules for n in ('numpy','torch','scipy','pandas','tradingagents')),'no numerical or genuine authority imports')

def pipeline(name,role,rows,chunks,codec_chunk):
    width=8 if role=='score-batches' else 4
    raw=(bytes(range(251))*((rows*32*width+250)//251))[:rows*32*width]
    root=P/name;root.mkdir(mode=0o700);src=root/'original';src.mkdir(mode=0o700);dest=root/'codec';dest.mkdir(mode=0o700)
    pieces={};at=0;spec=[]
    for i,n in enumerate(chunks):
        q=raw[at:at+n];at+=n;member=('chunk-%012d.bin'%i) if role=='score-batches' else 'matrix.f32'
        check(member not in pieces and len(q)==n and n%width==0,name+' original aligned piece '+str(i))
        pieces[member]=q;(src/member).write_bytes(q);spec.append((member,n,B.digest(q)))
    check(at==len(raw),name+' complete original denominator')
    calls=[];boundaries=[]
    def boundary():boundaries.append(len(calls))
    def read(member,offset,count):
        check(0<count<=B.PART and offset%width==0 and count%width==0,name+' aligned range '+str(len(calls)))
        calls.append((member,offset,count));return pieces[member][offset:offset+count]
    cursor=B.Cursor(spec,width,read,boundary)
    with L.LocalStore(dest) as store:
        terminal=C.encode_stream(cursor,descriptor(role,rows),store.put,chunk_bytes=codec_chunk)
        output=[];proof=store.verify(terminal,descriptor(role,rows),output.append)
        check(b''.join(output)==raw,name+' exact opaque reconstruction')
        done=cursor.completion();check(done['bytes']==len(raw) and done['sha256']==B.digest(raw)==proof['raw_sha256'],name+' whole raw hash')
        check(store.total==sum((dest/n).stat().st_size for n in store.names),name+' actual retained logical bytes')
    check(len(boundaries)>=2*len(calls),name+' boundary calls around every original range')
    witnesses.append({'name':name,'role':role,'original_members':len(spec),'bytes':len(raw),'codec_members':len(proof['members']),'ranges':calls,'raw_sha256':B.digest(raw),'terminal_sha256':terminal,'engineering_only':True})
    refuse(lambda:C.encode_stream(cursor,descriptor(role,rows),lambda n,b:None,chunk_bytes=codec_chunk),name+' no source replay')
    return raw,spec

raw,spec=pipeline('f64-cross-member','score-batches',3,[128,256,384],512)
pipeline('f32-raw','mcm-output',3,[384],128)
pipeline('f64-multipage','score-batches',5,[256,256,256,256,256],8)
pipeline('f64-one-mib-bound','score-batches',4097,[1048576,256],1048576)

# Generic byte cursors do not impersonate a Target/Owner/Run. Callback errors
# are real exception objects and no source exception is converted to success.
fault_types=[ValueError,RuntimeError,MemoryError,KeyboardInterrupt,SystemExit,GeneratorExit,BaseException]
for typ in fault_types:
    for site in ('reader','boundary'):
        error=typ('opaque-fault');state={'count':0}
        def fail(*args):raise error
        cur=B.Cursor([('raw',32,B.digest(b'x'*32))],8,fail if site=='reader' else lambda n,o,c:b'x'*c,fail if site=='boundary' else lambda:None)
        refuse(lambda:cur.read(8),typ.__name__+' '+site,error)
        check(cur.failed,typ.__name__+' '+site+' poisoned')
        refuse(lambda:cur.read(8),typ.__name__+' '+site+' no retry')
        refuse(cur.completion,typ.__name__+' '+site+' no completion')
for bad in (b'',b'x'*7,b'x'*9,bytearray(b'x'*8),None):
    cur=B.Cursor([('raw',8,B.digest(b'x'*8))],8,lambda *a:bad,lambda:None)
    refuse(lambda:cur.read(8),'short/long/nonbytes '+type(bad).__name__+str(len(bad) if bad is not None else 0));check(cur.failed,'range failure poisoned')
for rows,width in [([],8),([('a',8,'x'*64)],8),([('a',8,B.digest(b'x'*8)),('a',8,B.digest(b'x'*8))],8),([('../a',8,B.digest(b'x'*8))],8),([('a',7,B.digest(b'x'*7))],8),([('a',8,B.digest(b'x'*8))],True)]:
    refuse(lambda:B.Cursor(rows,width,lambda *a:b'',lambda:None),'invalid original cursor descriptor '+str(len(checks)))
for count in (0,-1,True,3,B.PART+8):
    cur=B.Cursor([('raw',8,B.digest(b'x'*8))],8,lambda n,o,c:b'x'*c,lambda:None)
    refuse(lambda:cur.read(count),'invalid read count '+str(count));check(cur.failed,'invalid count poison')
cur=B.Cursor([('raw',8,B.digest(b'y'*8))],8,lambda n,o,c:b'x'*c,lambda:None)
refuse(lambda:cur.read(8),'original whole member mismatch');check(cur.failed,'hash mismatch poison')
mutable=[['a',8,B.digest(b'x'*8)]];cur=B.Cursor(mutable,8,lambda n,o,c:b'x'*c,lambda:None);mutable[0][0]='evil'
check(cur.read(8)==b'x'*8 and cur.rows[0][0]=='a','caller descriptor mutation cannot change frozen cursor')
cur=B.Cursor([('a',8,B.digest(b'x'*8))],8,lambda n,o,c:b'x'*c,lambda:None);cur.rows=(('evil',8,B.digest(b'x'*8)),)
refuse(lambda:cur.read(8),'cursor descriptor rebound refused')

# Actual retained partial codec on a later source failure; no footer/proof.
root=P/'partial-source';root.mkdir(mode=0o700);error=KeyboardInterrupt('partial');calls=[]
def partial(n,o,c):
    if o>=8:raise error
    calls.append((n,o,c));return b'x'*c
cur=B.Cursor([('raw',256,B.digest(b'x'*256))],8,partial,lambda:None)
with L.LocalStore(root) as store:
    refuse(lambda:C.encode_stream(cur,descriptor('score-batches',1),store.put,chunk_bytes=8),'actual retained source partial',error)
    check((root/'start.json').is_file() and (root/'chunk-00000.bin').is_file() and not (root/'terminal.json').exists(),'partial files retained no terminal')
    refuse(cur.completion,'partial no complete proof')

# Metadata-only grant matrix: no admitted input or authority is synthesized.
graphs={B.digest(b'graph-a'):2,B.digest(b'graph-b'):3};job=B.digest(b'job')
grant={'schema_version':1,'kind':'two-imported-target-local-codec-v1','job_input':'execution_job','job_sha256':job,'role':'score-batches','targets':graphs,'max_logical_bytes':B.LIMIT,'max_allocated_bytes':B.LIMIT,'scientific_publication':False,'transport':False,'retirement':False}
reserve=B.validate_grant(grant,'score-batches',graphs,job);check(0<reserve<B.LIMIT,'full finite two-target metadata reservation')
for key in grant:
    v=dict(grant);del v[key];refuse(lambda:B.validate_grant(v,'score-batches',graphs,job),'missing grant field '+key)
for key,value in [('schema_version',True),('kind','financial'),('job_sha256','0'*64),('role','mcm-output'),('targets',{next(iter(graphs)):2}),('max_logical_bytes',1),('max_allocated_bytes',B.LIMIT+1),('transport',True),('retirement',True),('scientific_publication',True)]:
    v=dict(grant);v[key]=value;refuse(lambda:B.validate_grant(v,'score-batches',graphs,job),'mutated grant '+key)
for n in (0,1,4,1000000,True):
    g=dict(graphs);g[next(iter(g))]=n;v=dict(grant,targets=g);refuse(lambda:B.validate_grant(v,'score-batches',g,job),'unsupported target nodes '+str(n))
refuse(lambda:B.release(),'release unconditionally unavailable')
refuse(lambda:B._module('tradingagents.research.onchain_replication.held_score_consumer'),'no imports or fallback when genuine module absent')
check(not any(n in sys.modules for n in ('numpy','torch','scipy','pandas','tradingagents')),'no numerical/project imports at completion')
save('CHECKS01.json',{'status':'ENGINEERING_BYTE_SOURCE_CHECKS_ONLY','count':len(checks),'checks':checks,'witnesses':witnesses,'grant_reservation':reserve,'genuine_execution':None,'native_capacity':None})
print(json.dumps({'checks':len(checks),'pipelines':len(witnesses),'numerical_imports':False,'genuine_handle_construction':False}))
