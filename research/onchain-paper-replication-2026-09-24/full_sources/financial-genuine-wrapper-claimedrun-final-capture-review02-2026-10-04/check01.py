import ast,copy,gzip,hashlib,importlib.util,io,json,os,stat,sys,tarfile,time,types
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;A=F/'financial-genuine-wrapper-claimedrun-final-capture-preparation02-2026-10-04';sys.path.insert(0,str(F/'held-consumer-final-recovery-preparation04-2026-10-03'));import recovery04 as R
sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(v,m):assert v,m;checks.append(m)
def read(p):return R.read(p.parent,p.name)
def refusal(fn,label):
 try:fn()
 except (ValueError,FileExistsError) as e:checks.append(label);return str(e)
 raise AssertionError('unexpected '+label)
ck(sha(read(A/'capture02.py'))=='31f8c7dfdc39fdbadd2149cd0c7d9d18e9d6b766841a7171629d6b5b01e47ab0' and sha(read(A/'shards01.py'))=='9c38c0893790c22e3b0142a8ab175dceb9b14dd0aeeb80edc206e5329ffcbbba','exact two source pins');ck(sha(read(A/'MANIFEST01.json'))=='a2b07ace33f3f6a1394e04949c5089a3552567573d858f76f5a5f1462bcb6ea3','author seal');m=json.loads(read(A/'MANIFEST01.json'));ck({p.relative_to(A).as_posix() for p in A.rglob('*')}=={r['path'] for r in m['members']}|{'MANIFEST01.json'},'whole author witness scope')
for r in m['members']:
 p=A/r['path'];s=p.lstat();ck(stat.S_IMODE(s.st_mode)==int(r['mode'],8),'author literal mode')
 if r['kind']=='file':b=read(p);ck(stat.S_ISREG(s.st_mode) and len(b)==r['bytes'] and sha(b)==r['sha256'],'eachauthor body')
 elif r['kind']=='directory':ck(stat.S_ISDIR(s.st_mode),'author dir')
 else:ck(stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['target'],'author lexicaltarget')
s=read(A/'capture02.py').decode();original=read(A/'original-capture01.py').decode();inverse=s
for e in reversed(json.loads(read(A/'INVERSE01.json'))['edits']):ck(inverse.count(e['new'])==1,'exactunique inverse');inverse=inverse.replace(e['new'],e['old'])
ck(inverse==original and ast.dump(ast.parse(inverse))==ast.dump(ast.parse(original)),'complete source byteASTinverse');ck(sha(original.encode())=='1c74338bb78018c8816933c23b850090ef29ebce503ef7420d716e1f2a374749','original failedsource preserved');ns={'__file__':str(A/'capture02.py'),'__name__':'source_only'};exec(compile(s,'<candidate definitions>','exec'),ns);sp=importlib.util.spec_from_file_location('actual_pure_shard_planner',A/'shards01.py');P=importlib.util.module_from_spec(sp);sp.loader.exec_module(P);refusal(ns['main'],'uninstalled main refuses');ck(not os.path.lexists(ns['HERE']),'freshactual successorrootabsent');ck(not os.path.lexists(ns['PARENT']/'attempt'),'Parent noattempt')
for n,pin in ns['PINS'].items():ck(sha(read(ns['PRIMITIVES']/n))==pin,'unchangedR4helpers')
prior=json.loads(read(F/'financial-genuine-wrapper-claimedrun-final-capture-review01-2026-10-04/ACTUAL_ORIGINAL_SCOPES01.json'));ck({r['scope']:Path(r['original_root']) for r in prior}==ns['SCOPES'],'samecomplete20roots');files=links=0
for t in prior:
 root=Path(t['original_root']);ck({'.'}|{p.relative_to(root).as_posix() for p in root.rglob('*')}=={r['path'] for r in t['members']},'entire currentoriginal membership')
 for r in t['members']:
  p=root/r['path'];st=p.lstat();ck(stat.S_IMODE(st.st_mode)==r['mode'],'currentoriginal mode')
  if r['kind']=='file':ck(sha(read(p))==r['sha256'] and st.st_size==r['bytes'],'currenteveryoriginalbody');files+=1
  elif r['kind']=='lexical-symlink':ck(stat.S_ISLNK(st.st_mode) and os.readlink(p)==r['target'],'currentliteral target');links+=1
ck((files,links)==(1185,50),'current1185/50 unchanged');failed=F/'financial-genuine-wrapper-root-claimedrun-final-capture01-2026-10-04';virtual=json.loads(read(failed/'union-manifest.json'));groups=P.partition(virtual);flat=[n for g in groups for n in g['regular_paths']];ck(flat==sorted(r['path'] for r in virtual['members'] if r['kind']=='file') and len(flat)==1186 and len(set(flat))==1186,'actual deterministic1186exactdisjointcover');ck(P.partition(virtual)==groups,'deterministic actual partition');actual_plan=[]
for g in groups:
 ck(g['members']<=256 and g['logical_bytes']<=2*1024**2 and P.gzip_bound(g['tar_bytes_bound'])<=4*1024**2,'actual typed/logical/compressed conservative cap');actual_plan.append({k:v for k,v in g.items() if k!='manifest'})
(O/'ACTUAL_PARTITION_PLAN01.json').write_bytes(R.encode(actual_plan));R.same(ns['SOURCE'],json.loads(read(ns['SOURCE_CAPTURE']/'source-manifest.json')));ck(sha(read(ns['PARENT']/'REQUEST_FINAL03.json'))=='529c9bf3c587e6160a217e8eb339882e59433b6fc0f759d0009d261f872b2bd8','actualfinalParentpin');ck(sha(read(ns['SCOPES']['actual-verifier-review']/'MANIFEST01.json'))=='0c39988229162fd10b0d0df77f71163a4675a778251a8d75634283e40482bea2','actualbindingreviewpin')
# Multi-shard real opaque IO, original R4 pack/restore; owned namespace only.
T=O/'multiple';T.mkdir(mode=0o700);union=T/'union';union.mkdir(mode=0o700)
for i in range(3):p=union/('body'+str(i));p.write_bytes(os.urandom(1100000));p.chmod(0o600)
(union/'empty').mkdir(mode=0o700);vm=R.scan(union);ig,count=ns['pack_shards'](R,P,union,vm,T,time.monotonic());ck(count==3,'real three bounded incompressible shards');index=json.loads(read(T/'SHARD_INDEX01.json'));seen=[]
for i,row in enumerate(index['shards']):
 mm=json.loads(read(T/row['manifest']['path']));archive=T/row['archive']['path'];raw=read(archive);out=T/('flat'+str(i));out.mkdir(mode=0o700);result=R.restore(archive,{k:v for k,v in row['archive'].items() if k!='path'},mm,out);meta=json.loads(read(out/result['metadata_file']));seen.extend(row['regular_paths']);ck(len(raw)<=P.gzip_bound(row['tar_bytes_bound'])<=4*1024**2 and row['logical_bytes']<=2*1024**2 and row['members']<=256,'observedrealshardcaps');sink=io.BytesIO()
 with gzip.GzipFile(filename='',mode='wb',fileobj=sink,mtime=0) as z:
  with tarfile.open(fileobj=z,mode='w|',format=tarfile.PAX_FORMAT) as tar:
   for r in mm['members']:
    ti=tarfile.TarInfo(r['path']);ti.mode=r['mode'];ti.mtime=0
    if r['kind']=='directory':ti.type=tarfile.DIRTYPE;tar.addfile(ti)
    else:b=read(out/meta['flat_members'][r['path']]);ck(b==read(union/r['path']),'everyactual tinyroundtripbody');ti.size=len(b);tar.addfile(ti,io.BytesIO(b))
 ck(sink.getvalue()==raw,'wholecanonical tinyshard reconstructedfromflat')
ck(seen==sorted(r['path'] for r in vm['members'] if r['kind']=='file'),'exact multi-shard bodycover');ck(any(r['path']=='empty' for r in vm['members']) and all('empty' not in g['regular_paths'] for g in P.partition(vm)),'emptydirectory retained in virtualmetadata')
small={'schema_version':1,'root_mode':0o700,'members':[{'path':f'f{i:03d}','kind':'file','mode':0o600,'bytes':0,'sha256':sha(b'')} for i in range(257)]};ck([g['members'] for g in P.partition(small)]==[256,1],'typed boundary257 split')
for label in ['duplicate','missing-parent','oversize','PAX']:
 bad=copy.deepcopy(small)
 if label=='duplicate':bad['members'].append(bad['members'][0])
 elif label=='missing-parent':bad['members'][0]['path']='missing/file'
 elif label=='oversize':bad['members'][0]['bytes']=2*1024**2+1
 else:bad['members'][0]['path']='a'*8200
 refusal(lambda:P.partition(bad),'plannerrefusal '+label)
# Missing virtual body cannot become successful index: unchanged R.same detects omission.
for label in ['omission','mode']:
 d=O/label;d.mkdir(mode=0o700);bad=copy.deepcopy(vm)
 if label=='omission':bad['members']=[r for r in bad['members'] if r['path']!='body2']
 else:next(r for r in bad['members'] if r['kind']=='file')['mode']=0o644
 refusal(lambda:ns['pack_shards'](R,P,union,bad,d,time.monotonic()),'actualpackrefusal '+label);ck(not (d/'SHARD_INDEX01.json').exists(),'noindex for refused '+label)
# Exact final reenumeration suffix still refuses late original extras after sharding.
node=next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='main');offset=next(i for i,n in enumerate(node.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='union' for t in n.targets));fn=ast.FunctionDef(name='tiny_suffix',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='r4')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=node.body[offset:],decorator_list=[]);ast.fix_missing_locations(fn)
d=O/'late-extra';d.mkdir(mode=0o700);root=d/'original';root.mkdir(mode=0o700);(root/'body').write_bytes(b'opaque');(root/'link').symlink_to('absent');source=d/'source';source.mkdir(mode=0o700);(source/'x').write_bytes(b'x');local=dict(ns,HERE=d,SCOPES={'only':root},SOURCE=source,source_manifest=R.scan(source),start=time.monotonic(),planner=P);proxy=types.SimpleNamespace(**{n:getattr(R,n) for n in dir(R)})
def pack(*args):
 result=R.pack(*args);(root/'late').write_bytes(b'late');return result
proxy.pack=pack;exec(compile(ast.Module(body=[fn],type_ignores=[]),'<actual source suffix>','exec'),local);refusal(lambda:local['tiny_suffix'](proxy),'late original addition refuses after shards');ck(not (d/'UNION_AUTHENTICATION01.json').exists(),'lateoriginal noauthentication')
# Real first-fatal descriptor cleanup is retained across shard body writes.
realwrite=os.write;realclose=os.close
for i,first in enumerate([MemoryError('memory'),SystemExit(5),KeyboardInterrupt('interrupt')]):
 closed=[]
 def failwrite(fd,b):raise first
 def failclose(fd):realclose(fd);closed.append(fd);raise OSError('after real close')
 os.write=failwrite;os.close=failclose
 try:
  try:ns['put'](R,O/('fatal'+str(i)),b'opaque')
  except BaseException as e:ck(e is first,'actualput firstfatal identity')
  else:raise AssertionError('fatalaccepted')
 finally:os.write=realwrite;os.close=realclose
 ck(len(closed)==len(set(closed))==2,'bodyparenttwoFDs closedonce')
 for fd in closed:
  try:os.fstat(fd)
  except OSError:checks.append('actualFDabsent')
  else:raise AssertionError('FDleaked')
ck(not os.path.lexists(ns['HERE']) and not os.path.lexists(ns['PARENT']/'attempt'),'noRootcapture orParentattempt');ck(not any(n.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for n in sys.modules),'no research numericalimport');x={'schema_version':1,'decision':'ACCEPTED_SOURCE_ONLY_DETERMINISTIC_BOUNDED_SHARDED_FINAL_CAPTURE02','capture_sha256':sha(read(A/'capture02.py')),'planner_sha256':sha(read(A/'shards01.py')),'author_manifest_sha256':sha(read(A/'MANIFEST01.json')),'checks':len(checks),'actual_virtual_members':1476,'actual_virtual_regular_bodies':1186,'actual_original_trees':20,'actual_original_regular_bodies':1185,'actual_literal_links':50,'prospective_actual_partition_shards':len(groups),'actual_Rootcapture':False,'actual_shard_pins_generated':False,'original_failed01_preserved':True,'numerical_or_finalunion_authority':False};(O/'READBACK01.json').write_bytes(R.encode(x));print(json.dumps(x))
