import ast,copy,hashlib,importlib.util,json,os,stat,sys,time,types
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent
sys.path.insert(0,str(B/'held-consumer-final-recovery-preparation04-2026-10-03'));import recovery04 as R
s=(H/'capture_witness02.py').read_text();old=(H/'original-capture_witness01.py').read_text();ns={'__name__':'offline','__file__':str(H/'capture_witness02.py')};exec(compile(s,'candidate','exec'),ns)
sp=importlib.util.spec_from_file_location('planner',H/'shards01.py');P=importlib.util.module_from_spec(sp);sp.loader.exec_module(P)
checks=[]
def ok(v,n):assert v,n;checks.append(n)
def refuse(fn,n):
 try:fn()
 except (ValueError,TypeError,KeyError,OSError):ok(True,n)
 else:raise AssertionError(n)
x=s
for e in reversed(json.loads((H/'INVERSE01.json').read_bytes())['edits']):ok(x.count(e['new'])==1,'exact inverse segment');x=x.replace(e['new'],e['old'])
ok(x==old and ast.dump(ast.parse(x))==ast.dump(ast.parse(old)),'whole byte and AST inverse')
ok(hashlib.sha256((H/'shards01.py').read_bytes()).hexdigest()=='9c38c0893790c22e3b0142a8ab175dceb9b14dd0aeeb80edc206e5329ffcbbba','unchanged planner')
for label,root in ns['SCOPES'].items():ok(hashlib.sha256(R.read(root,'MANIFEST02.json' if label=='actual-capture-review' else 'MANIFEST01.json')).hexdigest()==ns['SEALS'][label],'actual frozen seal '+label)
direct=ns['DIRECT'];body=R.read(ns['MAIN'],direct['source_path']);ok(len(body)==direct['bytes'] and hashlib.sha256(body).hexdigest()==direct['sha256'] and stat.S_IMODE((ns['MAIN']/direct['source_path']).lstat().st_mode)==direct['mode'],'actual unchanged2.53MiB original direct body')
node=next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='main');start=next(i for i,n in enumerate(node.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='union' for t in n.targets));fn=ast.FunctionDef(name='fixture',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='r4')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=node.body[start:],decorator_list=[]);ast.fix_missing_locations(fn)
for case in ('valid','late-extra','direct-changed','direct-mode'):
 here=H/case;here.mkdir(mode=0o700);scopes={}
 for i in range(5):
  root=here/('original'+str(i));root.mkdir(mode=0o700);(root/'empty').mkdir(mode=0o700);(root/'literal').symlink_to('not-followed');scopes[str(i)]=root
  p=root/'opaque';p.write_bytes((b'opaque-byte-'+bytes([i]))*(200000 if i==0 else 1));p.chmod(0o600)
 if case=='valid':
  for i in range(3):(scopes['1']/('chunk'+str(i))).write_bytes(bytes([i])*1100000)
 p=scopes['0']/'opaque';bb=p.read_bytes();d={'scope':'0','path':'opaque','source_path':p.relative_to(H).as_posix(),'bytes':len(bb),'sha256':R.digest(bb),'mode':384};ok(2097152<len(bb)<=4194304,'real opaque oversized direct body')
 source=here/'source';source.mkdir();(source/'body').write_bytes(b'source');sm=R.scan(source)
 local=dict(ns,HERE=here,MAIN=H,SCOPES=scopes,DIRECT=d,SOURCE=source,source_manifest=sm,start=time.monotonic(),planner=P)
 # Exact functions resolve their metadata globals in this isolated tiny namespace.
 exec(compile(s,'owned candidate definitions','exec'),local);local.update(HERE=here,MAIN=H,SCOPES=scopes,DIRECT=d,SOURCE=source,source_manifest=sm,start=time.monotonic(),planner=P)
 proxy=types.SimpleNamespace(**{n:getattr(R,n) for n in dir(R)})
 def pack(a,b,c):
  result=R.pack(a,b,c)
  if case=='late-extra':(scopes['2']/'late').write_bytes(b'late')
  elif case=='direct-changed':p.write_bytes(b'wrong direct')
  elif case=='direct-mode':p.chmod(0o644)
  return result
 proxy.pack=pack;exec(compile(ast.Module(body=[fn],type_ignores=[]),'owned main suffix','exec'),local)
 if case!='valid':refuse(lambda:local['fixture'](proxy),case+' refuses');ok(not (here/'UNION_AUTHENTICATION01.json').exists(),'no false success '+case);continue
 local['fixture'](proxy);mapping=json.loads((here/'union-bytes01/ORIGINAL_TREES01.json').read_bytes());idx=json.loads((here/'SHARD_INDEX01.json').read_bytes());m=json.loads((here/'union-manifest.json').read_bytes());auth=json.loads((here/'UNION_AUTHENTICATION01.json').read_bytes())
 ok(len(idx['shards'])>=3 and idx['direct_bodies']==[d] and auth['direct_regular_members']==1,'real multiple shards plus exactly1 direct')
 recovered={}
 for i,row in enumerate(idx['shards']):
  out=here/('flat'+str(i));out.mkdir(mode=0o700);mm=json.loads((here/row['manifest']['path']).read_bytes());r=R.restore(here/row['archive']['path'],{k:v for k,v in row['archive'].items() if k!='path'},mm,out);meta=json.loads(R.read(out,r['metadata_file']))
  for name,leaf in meta['flat_members'].items():ok(name not in recovered,'disjoint restored path');recovered[name]=R.read(out,leaf)
 # Explicit synthetic direct-selection copy; no claim of real transport or authority.
 direct_dest=here/'direct-selected';direct_dest.mkdir(mode=0o700);local['put'](R,direct_dest/'opaque',R.read(H,d['source_path']));direct_body=R.read(direct_dest,'opaque')
 for tree in mapping['scope_trees']:
  for row in tree['members']:
   if row['kind']!='file':continue
   rb=direct_body if 'direct_source_path' in row else recovered[row['union_path']]
   ok(len(rb)==row['bytes'] and R.digest(rb)==row['sha256'],'full original byte reconstruction')
 local['partition_join'](mapping['scope_trees'],m,d)
 for mutation in ('missing','duplicate','hash','path','mode'):
  bad=copy.deepcopy(mapping['scope_trees']);r=next(r for r in bad[0]['members'] if r['kind']=='file')
  if mutation=='missing':bad[0]['members'].remove(r)
  elif mutation=='duplicate':bad[0]['members'].append(copy.deepcopy(r))
  elif mutation=='hash':r['sha256']='0'*64
  elif mutation=='path':r['direct_source_path']+='wrong'
  else:r['mode']^=1
  refuse(lambda:local['partition_join'](bad,m,d),'direct '+mutation+' refuses')
for firstcls in (MemoryError,KeyboardInterrupt):
 for secondcls in (OSError,MemoryError,KeyboardInterrupt):
  fd=os.open(H/'owned-fd',os.O_CREAT|os.O_WRONLY,0o600);first=firstcls('first');second=secondcls('close');events=[]
  def close():os.close(fd);events.append(1);raise second
  def final():events.append(2)
  try:
   try:raise first
   finally:R._cleanup((close,final))
  except BaseException as e:ok(e is first,'first fatal retained')
  ok(events==[1,2] and not Path('/proc/self/fd/'+str(fd)).exists(),'all cleanup and genuine closed fd')
ok(not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')),'no scientific imports')
(H/'CHECKS01.json').write_text(json.dumps({'count':len(checks),'checks':checks,'actual_Root_capture':False,'actual_transport':False},indent=2)+'\n');print('PASS',len(checks))
