import ast,hashlib,json,os,stat,sys,pathlib
D=pathlib.Path(__file__).resolve().parent
P=D.parent/'financial-batch-output-genuine-byte-bridge-preparation02-2026-10-04'
R=D.parents[3]
sys.path.insert(0,str(P))
import byte_bridge01 as B,codec01 as C,local_store01 as L,recovery04 as RR,owned_io as IO
checks=[]
def ck(x,n):
 if not x:raise AssertionError(n)
 checks.append(n)
def refuse(fn,n,identity=None):
 try:fn()
 except BaseException as e:
  if identity is not None:ck(e is identity,n+' primary identity')
  ck(True,n);return type(e).__name__+': '+str(e)
 raise AssertionError('unexpected acceptance '+n)
def save(n,x):
 with (D/n).open('x')as f:json.dump(x,f,indent=2,sort_keys=True);f.write('\n')
def sha(b):return hashlib.sha256(b).hexdigest()
mraw=(P/'MANIFEST02.json').read_bytes();ck(sha(mraw)=='d0a5d0600cf0e169269b7fb0f0946c35355251e04286d2f7c0179420cf389a73','exact author seal')
m=json.loads(mraw);expected=set()
for row in m['members']:
 p=P/row['path'];s=p.lstat();expected.add(row['path']);ck(stat.S_IMODE(s.st_mode)==int(row['mode'],8),'mode '+row['path'])
 if row['kind']=='file':ck(stat.S_ISREG(s.st_mode) and s.st_size==row['bytes'] and sha(p.read_bytes())==row['sha256'],'body '+row['path'])
 elif row['kind']=='directory':ck(stat.S_ISDIR(s.st_mode),'directory '+row['path'])
 elif row['kind']=='symlink':ck(stat.S_ISLNK(s.st_mode) and os.readlink(p)==row.get('target',row.get('link_target')),'literal link '+row['path'])
 else:raise AssertionError(row)
actual={str(p.relative_to(P))for p in P.rglob('*') if p.name!='MANIFEST02.json'}
ck(actual==expected,'complete author membership')
for n,row in json.loads((P/'DEPENDENCIES01.json').read_text()).items():ck((P/n).read_bytes()==(R/row['origin']).read_bytes() and sha((P/n).read_bytes())==row['sha256'],'literal original dependency '+n)
for n in ['held_score_consumer','completed_f32']:
 a=(P/(n+'.original.py')).read_bytes();b=(P/(n+'.py')).read_bytes();ck(b.startswith(a),'whole byte prefix '+n)
 old=ast.parse(a);new=ast.parse(b);ck(len(new.body)==len(old.body)+1 and ast.dump(old,include_attributes=False)==ast.dump(ast.Module(body=new.body[:-1],type_ignores=[]),include_attributes=False),'whole AST inverse '+n)
ck(not any(n in sys.modules for n in ['numpy','torch','scipy','pandas','tradingagents']),'stdlib engineering modules only')
def desc(role,n):return {'schema_version':1,'kind':'mcm-batch-output-bytes','role':role,'dtype':'<f8' if role=='score-batches' else '<f4','shape':[n,32],'order':'C','scope':{s:sha(s.encode())for s in C.SCOPE},'motifs':32,'spent_samples':512}
outputs=[]
def pipeline(name,role,n,split,chunk):
 width=8 if role=='score-batches' else 4
 raw=(bytes(range(253))*((n*32*width+252)//253))[:n*32*width]
 root=D/name;root.mkdir(mode=0o700);storepath=root/'codec';storepath.mkdir(mode=0o700)
 pieces={};rows=[];at=0
 for i,size in enumerate(split):
  member='piece-'+str(i);pieces[member]=raw[at:at+size];at+=size;rows.append((member,size,sha(pieces[member])))
 ck(at==len(raw),'exact fixture split '+name)
 def read(member,off,count):ck(type(off)is int and off%width==count%width==0,'aligned actual range');return pieces[member][off:off+count]
 cursor=B.Cursor(rows,width,read,lambda:None)
 with L.LocalStore(storepath) as store:
  pin=C.encode_stream(cursor,desc(role,n),store.put,chunk_bytes=chunk);recovered=[];proof=store.verify(pin,desc(role,n),recovered.append)
  ck(b''.join(recovered)==raw and cursor.completion()['sha256']==sha(raw)==proof['raw_sha256'],'complete original byte reassembly '+name)
  ck({p.name for p in storepath.iterdir()}==set(proof['members']),'all codec members '+name)
  fixture={p.name:p.read_bytes()for p in storepath.iterdir()}
  for member in sorted(fixture):
   changed=dict(fixture);changed[member]=changed[member][:-1]
   refuse(lambda:C.verify_stream(changed.__getitem__,pin,desc(role,n)),'truncate '+name+'/'+member)
  for key,value in [('dtype','<f4' if role=='score-batches' else '<f8'),('motifs',31),('spent_samples',511)]:
   changed=desc(role,n);changed[key]=value;refuse(lambda:C.verify_stream(fixture.__getitem__,pin,changed),'descriptor '+key)
  refuse(lambda:C.verify_stream(fixture.__getitem__,'0'*64,desc(role,n)),'wrong whole terminal')
  refuse(lambda:C.encode_stream(cursor,desc(role,n),store.put,chunk_bytes=chunk),'replay source/store')
 outputs.append({'name':name,'bytes':len(raw),'members':len(fixture),'sha256':sha(raw),'terminal':pin})
pipeline('fresh-f64','score-batches',5,[128,256,896],16)
pipeline('fresh-f32','mcm-output',3,[128,128,128],64)
for typ in [ValueError,RuntimeError,MemoryError,KeyboardInterrupt,SystemExit,GeneratorExit,BaseException]:
 for site in ['read','check']:
  e=typ('independent genuine exception')
  def fail(*a):raise e
  cur=B.Cursor([('raw',16,sha(b'x'*16))],8,fail if site=='read' else lambda n,o,c:b'x'*c,fail if site=='check' else lambda:None)
  refuse(lambda:cur.read(8),typ.__name__+site,e);ck(cur.failed,'failed cursor permanent');refuse(lambda:cur.read(8),'retry refused');refuse(cur.completion,'completion refused')
for count in [True,False,0,-1,1.0,3,B.PART+8]:
 cur=B.Cursor([('raw',16,sha(b'x'*16))],8,lambda n,o,c:b'x'*c,lambda:None);refuse(lambda:cur.read(count),'invalid count '+repr(count))
for raw in [b'',b'x'*7,b'x'*9,bytearray(b'x'*8),None]:
 cur=B.Cursor([('raw',8,sha(b'x'*8))],8,lambda *a:raw,lambda:None);refuse(lambda:cur.read(8),'invalid returned range')
for rows,width in [([('x',8,'0'*64)],8),([('x',8,sha(b'x'*8)),('x',8,sha(b'x'*8))],8),([('../x',8,sha(b'x'*8))],8),([('x',8.0,sha(b'x'*8))],8),([('x',8,sha(b'x'*8))],True)]:
 def run():return B.Cursor(rows,width,lambda n,o,c:b'x'*c,lambda:None).read(8)
 refuse(run,'invalid rows/hash')
# Strict original policy and real absent modules refuse without fake handles.
for sample,motif in [(511,32),(512,31),(True,32),(512,32.0)]:refuse(lambda:B.original_cardinality({'sample_count':sample,'motif_count':motif}),'original policy strict')
refuse(lambda:B.encode_held(None,None),'no genuine loaded source');refuse(lambda:B.encode_completed(None,None),'no fabricated producer');refuse(B.release,'production unavailable')
save('CHECKS01.json',{'checks':len(checks),'names':checks,'pipelines':outputs,'no_genuine_handles':True})
print(json.dumps({'checks':len(checks),'pipelines':outputs}))
