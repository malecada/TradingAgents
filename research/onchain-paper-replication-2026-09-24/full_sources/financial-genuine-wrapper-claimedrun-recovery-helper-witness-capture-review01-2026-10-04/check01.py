import ast,gzip,hashlib,io,json,os,stat,sys,tarfile,time,types
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;A=B/'financial-genuine-wrapper-claimedrun-recovery-helper-witness-capture-preparation01-2026-10-04';sys.path.insert(0,str(B/'held-consumer-final-recovery-preparation04-2026-10-03'));import recovery04 as R
count=0;events=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def ck(v,n):
 global count
 assert v,n;count+=1
def refuse(fn,n):
 try:fn()
 except (ValueError,TypeError,KeyError,OSError) as e:events.append({'control':n,'exception':type(e).__name__,'message':str(e)});ck(True,n)
 else:raise AssertionError('not refused '+n)
def scan(root):
 out=[]
 def visit(p,n):
  s=p.lstat();r={'path':n,'mode':stat.S_IMODE(s.st_mode)}
  if stat.S_ISLNK(s.st_mode):r.update(kind='lexical-symlink',target=os.readlink(p))
  elif stat.S_ISDIR(s.st_mode):
   r['kind']='directory';out.append(r)
   for c in sorted(p.iterdir()):visit(c,c.name if n=='.' else n+'/'+c.name)
   return
  else:ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1,'singlelink ordinary');b=R.read(root,n);r.update(kind='file',bytes=len(b),sha256=sha(b))
  out.append(r)
 visit(root,'.');return sorted(out,key=lambda r:r['path'])
def seal(root,pin):
 b=R.read(root,'MANIFEST01.json');ck(sha(b)==pin,'genuine seal');rr=scan(root);by={r['path']:r for r in rr};decl=json.loads(b)['members']
 for r in decl:
  d=dict(r);d['kind']='lexical-symlink' if d['kind']=='symlink' else d['kind'];ck(by[d['path']]==d,'complete sealed type/mode/body')
 ck(set(by)=={r['path'] for r in decl}|{'.','MANIFEST01.json'},'complete current seal scope');return rr
seal(A,'73cea960c32019158961df0dcfa6f42032697d6da682a7a199b3c592dfc84d51');s=R.read(A,'capture_helpers01.py');ck(sha(s)=='06f1a923e4b1d77d019276117a55d34f5942990c7e19f631783a62116224d4da','candidate');x=s.decode()
for e in reversed(json.loads(R.read(A,'INVERSE01.json'))['edits']):ck(x.count(e['new'])==e.get('count',1),'exact inverse occurrence');x=x.replace(e['new'],e['old'])
o=R.read(A,'original-capture_tooling01.py');ck(x.encode()==o and ast.dump(ast.parse(x))==ast.dump(ast.parse(o)),'full byte AST inverse');ck(sha(o)=='853684447129233759f1e21de2aaef686eff07a88f047c47356663d318904e43' if False else o==R.read(B/'financial-genuine-wrapper-claimedrun-witness-tooling-capture-preparation01-2026-10-04','capture_tooling01.py'),'exact actual original tooling source')
ns={'__name__':'review_only','__file__':str(A/'capture_helpers01.py')};exec(compile(s,'candidate','exec'),ns)
for n,pin in ns['PINS'].items():ck(sha(R.read(ns['PRIMITIVES'],n))==pin,'unchanged primitive')
refuse(ns['main'],'uninstalled actual Root refuses');ck(not os.path.lexists(ns['HERE']),'actual Root namespace absent');inventory=[];bodycount=total=links=0;feasibility=[];authormeasure={r['scope']:r for r in json.loads(R.read(A,'FEASIBILITY01.json'))}
for scope,root in sorted(ns['SCOPES'].items()):
 rows=seal(root,ns['SEALS'][scope]);members=[];bodies={};ordinary=[]
 for r in rows:
  rr=dict(r)
  if r['kind']=='file':
   rr['union_path']=scope+'/'+r['path'];bodycount+=1;total+=r['bytes'];bodies[r['path']]=R.read(root,r['path']);ordinary.append(dict(r,mode=384))
  elif r['kind']=='directory' and r['path']!='.':ordinary.append(dict(r,mode=448))
  elif r['kind']=='lexical-symlink':links+=1
  members.append(rr)
 item={'scope':scope,'original_root':str(root),'members':members};inventory.append(item);metadata={'schema_version':1,'original_tree':item,'source_commit':'0a2e7639b42b9423b90743feadcda4078aa21816','links_followed_or_extracted':False,'research_authority':False};mb=ns['encoded'](metadata);bodies['CAPTURE_ORIGINAL_TREE01.json']=mb;ordinary.append({'path':'CAPTURE_ORIGINAL_TREE01.json','kind':'file','mode':384,'bytes':len(mb),'sha256':sha(mb)});manifest={'schema_version':1,'root_mode':448,'members':sorted(ordinary,key=lambda r:r['path'])};R.validate(manifest)
 out=io.BytesIO()
 with gzip.GzipFile(fileobj=out,mode='wb',filename='',mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tf:
   for r in manifest['members']:
    t=tarfile.TarInfo(r['path']);t.mode=r['mode'];t.uid=t.gid=t.mtime=0;t.uname=t.gname=''
    if r['kind']=='directory':t.type=tarfile.DIRTYPE;tf.addfile(t)
    else:t.size=len(bodies[r['path']]);tf.addfile(t,io.BytesIO(bodies[r['path']]))
 raw=out.getvalue();ck(len(raw)<=4194304,'actual independent canonical archive feasibility');expected=authormeasure[scope];ck(len(raw)==expected['exact_canonical_simulated_archive_bytes'] and sha(raw)==expected['exact_canonical_simulated_archive_sha256'],'independent entire canonical byte projection')
 frames=list(R.framed_members(raw));ck(len(frames)==len(manifest['members']),'unchanged R4 no cutoff slash refusal')
 for (n,t,b),r in zip(frames,manifest['members']):ck(n==r['path'] and t.mode==r['mode'] and ((t.isdir() and not b) if r['kind']=='directory' else b==bodies[n]),'all virtual regular/directory bytes framed')
 feasibility.append({'scope':scope,'archive_bytes':len(raw),'archive_sha256':sha(raw),'original_typed':len(rows),'ordinary_typed':len(ordinary),'metadata_bytes':len(mb),'R4_framing_passes':True,'read_only_not_capture':True})
ck(bodycount==4220 and total==9187425,'complete six original file census')
node=next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='main');ma=next(n for n in node.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='mapping' for t in n.targets));local=dict(ns,inventory=inventory,total=total);exec(compile(ast.Module(body=[ma],type_ignores=[]),'literal mapping','exec'),local);logical=total+len(ns['encoded'](local['mapping']))+sum(r['metadata_bytes'] for r in feasibility);ck(logical<=67108864,'whole originals plus six metadata plus mapping under64MiB')
sm=json.loads(R.read(ns['SOURCE_CAPTURE'],'source-manifest.json'));ck(sha(R.encode(sm))=='fdf77348b81a4d6df8b420b98530f5485900a0461636e1c201506106b036dfd8','actual Source manifest');R.same(ns['SOURCE'],sm);ck(sha(R.read(ns['SOURCE_CAPTURE'],'source.tar.gz'))=='b5b6aad2f515447dc6566cfb716a20ef90031313d48f1ac903ab756735431e24','Source archive');ck(sha(R.read(ns['PARENT'],'REQUEST_FINAL03.json'))=='529c9bf3c587e6160a217e8eb339882e59433b6fc0f759d0009d261f872b2bd8','actual Parent request');ck(not (ns['PARENT']/'attempt').exists(),'no Parent attempt');ck(sha(R.read(ns['PARENT'],'proofs/FULL_SOURCE_RECOVERY01.json'))=='468dac2c06e570a89a30771c3f7e1b8e064e6f27e610acf01edcccf91c9a2825','genuine separate Source proof')
# Extract the exact source suffix, execute only owned six-tree utility projections.
pos=next(i for i,n in enumerate(node.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='union' for t in n.targets));fn=ast.FunctionDef(name='projection',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='r4')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=node.body[pos:],decorator_list=[]);ast.fix_missing_locations(fn)
for case in ('valid','late-extra','body-change','mode-change','link-change'):
 h=H/case;h.mkdir(mode=0o700);scopes={}
 for i in range(6):
  p=h/('original'+str(i));p.mkdir(mode=0o700);(p/'empty').mkdir(mode=0o700);(p/'file').write_bytes(bytes([i])*17);(p/'file').chmod(0o600);(p/'link').symlink_to('../never-followed');scopes[str(i)]=p
 src=h/'source';src.mkdir(mode=0o700);(src/'opaque').write_bytes(b's');local=dict(ns,HERE=h,SCOPES=scopes,SOURCE=src,source_manifest=R.scan(src),start=time.monotonic());proxy=types.SimpleNamespace(**{n:getattr(R,n) for n in dir(R)});fired=[]
 def pack(root,m,dest):
  info=R.pack(root,m,dest)
  if not fired:
   fired.append(True)
   if case=='late-extra':(scopes['0']/'extra').write_bytes(b'x')
   elif case=='body-change':(scopes['0']/'file').write_bytes(b'x')
   elif case=='mode-change':(scopes['0']/'file').chmod(0o644)
   elif case=='link-change':(scopes['0']/'link').unlink();(scopes['0']/'link').symlink_to('changed')
  return info
 proxy.pack=pack;exec(compile(ast.Module(body=[fn],type_ignores=[]),'owned suffix','exec'),local)
 if case!='valid':refuse(lambda:local['projection'](proxy),'complete final census '+case);ck(not (h/'UNION_AUTHENTICATION01.json').exists(),'no false complete auth');continue
 local['projection'](proxy);auth=json.loads(R.read(h,'UNION_AUTHENTICATION01.json'));ck(len(auth['archives'])==6 and auth['original_regular_members']==6 and auth['original_lexical_links']==6,'actual six projection counts')
 for scope,row in auth['archives'].items():
  flat=h/('flat-'+scope);flat.mkdir(mode=0o700);m=json.loads(R.read(h,row['manifest']['path']));result=R.restore(h/row['archive']['path'],{k:v for k,v in row['archive'].items() if k!='path'},m,flat);meta=json.loads(R.read(flat,result['metadata_file']));ck(R.read(flat,meta['flat_members']['file'])==R.read(scopes[scope],'file'),'tiny actual original recovered');md=json.loads(R.read(flat,meta['flat_members']['CAPTURE_ORIGINAL_TREE01.json']));ck(any(r['kind']=='lexical-symlink' and r['target']=='../never-followed' for r in md['original_tree']['members']),'tiny literal link metadata');ck(any(r['kind']=='directory' and r['path']=='empty' for r in md['original_tree']['members']),'empty directory preserved')
 refuse(lambda:local['projection'](R),'fresh namespace one-use')
for i,typ in enumerate((MemoryError,KeyboardInterrupt,SystemExit)):
 first=typ('first body fatal');oldwrite=os.write;oldclose=os.close;closed=[]
 def write(fd,b):raise first
 def close(fd):oldclose(fd);closed.append(fd);raise OSError('close diagnostic')
 os.write=write;os.close=close
 try:
  try:ns['put'](R,H/('fd-fatal'+str(i)),b'opaque')
  except BaseException as e:ck(e is first,'actual put first fatal identity')
  else:raise AssertionError('missing fatal')
 finally:os.write=oldwrite;os.close=oldclose
 ck(len(closed)==2 and len(set(closed))==2 and all(not Path('/proc/self/fd/'+str(fd)).exists() for fd in closed),'both original IO descriptors closed')
for item in inventory:
 rr=scan(Path(item['original_root']));decl=[{k:v for k,v in r.items() if k!='union_path'} for r in item['members']];ck(rr==decl,'final original scope unchanged')
ck(not any(k in sys.modules for k in ('numpy','torch','scipy','pandas')),'no numerical imports')
q={'schema_version':1,'decision':'accepted-source-only-six-recovery-helper-witness-capture','source_sha256':sha(s),'author_manifest_sha256':'73cea960c32019158961df0dcfa6f42032697d6da682a7a199b3c592dfc84d51','checks':count,'original_regular_bodies':bodycount,'original_regular_bytes':total,'literal_links':links,'whole_logical_with_metadata':logical,'feasibility':feasibility,'refusals':events,'actual_Root_capture':False,'actual_external_recovery':False,'native_or_numerical_authority':False};(H/'READBACK01.json').write_text(json.dumps(q,sort_keys=True,indent=2)+'\n');print('PASS',count,'logical',logical)
