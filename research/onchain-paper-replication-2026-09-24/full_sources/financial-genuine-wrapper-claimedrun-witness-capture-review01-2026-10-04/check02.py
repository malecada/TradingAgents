import ast,gzip,hashlib,io,json,os,shutil,stat,sys,tarfile,time,types
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;A=F/'financial-genuine-wrapper-claimedrun-witness-capture-preparation01-2026-10-04';sys.path.insert(0,str(F/'held-consumer-final-recovery-preparation04-2026-10-03'));import recovery04 as R
sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ck(v,m):assert v,m;checks.append(m)
def read(p):return R.read(p.parent,p.name)
ck(sha(read(A/'capture01.py'))=='e4ee138df24ab2ce90c105fceb294ceb0749b2a541f7541b73afea723032d7cb','actual candidate filename capture01 not message alias helpercapture01');ck(sha(read(A/'MANIFEST01.json'))=='13273cfa4436f9a687e18a9bb48a58eb3a4cfbfeed14ed37d45a11e919b88b2b','author manifest hash')
m=json.loads(read(A/'MANIFEST01.json'));actual={p.relative_to(A).as_posix() for p in A.rglob('*')};ck(actual=={r['path'] for r in m['members']}|{'MANIFEST01.json'},'whole candidate membership')
for r in m['members']:
 p=A/r['path'];s=p.lstat();ck(stat.S_IMODE(s.st_mode)==int(r['mode'],8),'member literal mode')
 if r['kind']=='file':b=read(p);ck(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and len(b)==r['bytes'] and sha(b)==r['sha256'],'member exact regular')
 elif r['kind']=='directory':ck(stat.S_ISDIR(s.st_mode),'member directory')
 else:ck(stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['target'],'literal link never followed')
s=read(A/'capture01.py').decode();old=read(A/'original-capture03.py').decode();inv=s
for e in reversed(json.loads(read(A/'INVERSE01.json'))['edits']):ck(inv.count(e['new'])==e.get('count',1),'inverse exact multiplicity');inv=inv.replace(e['new'],e['old'])
ck(inv==old and ast.dump(ast.parse(inv))==ast.dump(ast.parse(old)),'full byte AST inverse');ns={'__name__':'independent_source_only','__file__':str(A/'capture01.py')};exec(compile(s,'<candidate definitions>','exec'),ns)
try:ns['main']()
except ValueError as e:ck(str(e)=='fixed Root-installed capture scope','uninstalled real main refuses before capture')
else:raise AssertionError('uninstalled capture accepted')
ck(not os.path.lexists(ns['HERE']),'actual Root future output absent')
for n,pin in ns['PINS'].items():ck(sha(read(ns['PRIMITIVES']/n))==pin,'unchanged R4 primitive')
census=F/'financial-genuine-wrapper-claimedrun-preservation-census01-2026-10-04';total=0;links=[];counts=[]
for scope,root in ns['SCOPES'].items():
 original=json.loads(read(census/(root.name+'.manifest.json')));seen=[]
 for p in sorted(root.rglob('*')):
  st=p.lstat();r={'path':p.relative_to(root).as_posix(),'mode':stat.S_IMODE(st.st_mode)}
  if stat.S_ISDIR(st.st_mode):r['kind']='directory'
  elif stat.S_ISLNK(st.st_mode):r.update(kind='lexical-symlink',target=os.readlink(p));links.append({'scope':scope,**r})
  else:b=read(p);r.update(kind='file',bytes=len(b),sha256=sha(b));total+=len(b)
  seen.append(r)
 ck(seen==original['members'] and stat.S_IMODE(root.stat().st_mode)==original['root_mode'],'entire actual original scope identical to independently frozen census');counts.append({'scope':scope,'root':str(root),'members_including_root':len(seen)+1,'regular':sum(r['kind']=='file' for r in seen)})
ck(len(links)==13 and total<=ns['LIMIT'],'actual13 metadata links and64MiB bound');capture=ns['SOURCE_CAPTURE'];ck(sha(read(capture/'source.tar.gz'))=='b5b6aad2f515447dc6566cfb716a20ef90031313d48f1ac903ab756735431e24','actual source archive');ck(sha(read(capture/'source-manifest.json'))=='fdf77348b81a4d6df8b420b98530f5485900a0461636e1c201506106b036dfd8','actual source manifest');R.same(ns['SOURCE'],json.loads(read(capture/'source-manifest.json')))
for name,pin in [('MANIFEST01.json','24e6451d2a9c5ec516b99ca95bb477567e5f9ef5d13adef3bb41c0633b93e5c7'),('INDEPENDENT_SOURCE_INPUT_RUNTIME01.json','059232d0f7fc8922cee526a1bd30fef2ecb51ee17103284bcaac18c77e77641c')]:ck(sha(read(ns['SOURCE_REVIEW']/name))==pin,'actual metadata admission proof body')
# Exact source suffix, only owned tiny trees; emitted fixed source annotations are projections, not actual receipts.
node=next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='main');start=next(i for i,n in enumerate(node.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='union' for t in n.targets));fn=ast.FunctionDef(name='tiny_pipeline',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='r4')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=node.body[start:],decorator_list=[]);ast.fix_missing_locations(fn)
results=[]
for label in ['valid','late-extra','late-mode','late-link','late-body']:
 here=O/(label+'02');here.mkdir(mode=0o700);scopes={}
 for i in range(4):
  root=here/('original'+str(i));root.mkdir(mode=0o700);(root/'body').write_bytes(b'opaque\x00'+bytes([i]));(root/'literal').symlink_to('unavailable-target');scopes[str(i)]=root
 src=here/'tiny-source';src.mkdir(mode=0o700);(src/'opaque').write_bytes(b'x');local=dict(ns,HERE=here,SCOPES=scopes,SOURCE=src,source_manifest=R.scan(src),start=time.monotonic());proxy=types.SimpleNamespace(**{n:getattr(R,n) for n in dir(R)})
 def pack(root,m,path):
  result=R.pack(root,m,path);r=scopes['0']
  if label=='late-extra':(r/'added').write_bytes(b'late')
  if label=='late-mode':os.chmod(r/'body',0o600)
  if label=='late-link':(r/'literal').unlink();(r/'literal').symlink_to('changed-target')
  if label=='late-body':(r/'body').write_bytes(b'changed')
  return result
 proxy.pack=pack;exec(compile(ast.Module(body=[fn],type_ignores=[]),'<exact owned tiny capture suffix>','exec'),local)
 try:local['tiny_pipeline'](proxy)
 except ValueError as e:ck(label!='valid' and str(e)=='complete original membership/body/mode/literal-link differs','final complete reenumeration refuses '+label);ck(not (here/'UNION_AUTHENTICATION01.json').exists(),'no success receipt on changed original');results.append({'control':label,'refusal':str(e)})
 else:
  ck(label=='valid','only unchanged tiny tree accepted');mapping=json.loads(read(here/'union-bytes01/ORIGINAL_TREES01.json'));ck(mapping['source_full_recovery_readback_sha256'] is None and len(mapping['scope_trees'])==4,'no inherited recovery authority');ck(not any(p.is_symlink() for p in (here/'union-bytes01').rglob('*')),'only metadata stored for literal links');results.append({'control':label,'tiny_only':True})
  # Independent canonical archive recompression over every tiny copied regular body.
  manifest=json.loads(read(here/'union-manifest.json'));sink=io.BytesIO()
  with gzip.GzipFile(fileobj=sink,mode='wb',filename='',mtime=0) as gz:
   with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as t:
    for row in manifest['members']:
     info=tarfile.TarInfo(row['path']);info.mode=row['mode'];info.mtime=0
     if row['kind']=='directory':info.type=tarfile.DIRTYPE;t.addfile(info)
     else:b=read(here/'union-bytes01'/row['path']);ck(sha(b)==row['sha256'],'tiny complete archive body');info.size=len(b);t.addfile(info,io.BytesIO(b))
  ck(sink.getvalue()==read(here/'union.tar.gz'),'independent whole tiny compressed inverse')
  try:local['tiny_pipeline'](proxy)
  except FileExistsError:checks.append('actual same namespace refuses reuse')
  else:raise AssertionError('reuse accepted')
# Inject actual put write/close pairs; use unchanged R.new_file and original actual descriptors.
realwrite=os.write;realclose=os.close
for i,first in enumerate([MemoryError('original-fatal'),SystemExit(17),KeyboardInterrupt('original-interrupt')]):
 closed=[]
 def badwrite(fd,b):raise first
 def badclose(fd):realclose(fd);closed.append(fd);raise OSError('after real close')
 os.write=badwrite;os.close=badclose
 try:
  try:ns['put'](R,O/('fatal-partial02-'+str(i)),b'opaque')
  except BaseException as got:ck(got is first,'actual put firstfatal unchanged through closefailure')
  else:raise AssertionError('fatal accepted')
 finally:os.write=realwrite;os.close=realclose
 ck(len(closed)==len(set(closed))==2,'actual body and parent FDs each closed once')
 for descriptor in closed:
  try:os.fstat(descriptor)
  except OSError:checks.append('actual put FD absent')
  else:raise AssertionError('FD leaked')
ck(not os.path.lexists(ns['HERE']),'Root capture never executed');ck(not any(n.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for n in sys.modules),'no research/numerical import');x={'schema_version':1,'decision':'ACCEPTED_FOUR_HANDOFF_WITNESS_CAPTURE_SOURCE_ONLY','source_sha256':sha(read(A/'capture01.py')),'author_manifest_sha256':sha(read(A/'MANIFEST01.json')),'checks':len(checks),'actual_scopes':counts,'actual_original_regular_bytes':total,'actual_literal_links':links,'source_commit':'0a2e7639b42b9423b90743feadcda4078aa21816','source_full_recovery':None,'actual_Root_capture':False,'tiny_controls':results,'qualification':'Fixed local source-only helper; actual complete capture, selected committed scope, external recovery and final caller/review union require separate exact outcome review. Tiny projected annotations are not genuine Root receipts.'};(O/'READBACK01.json').write_text(json.dumps(x,sort_keys=True,indent=2)+'\n');print(json.dumps({'checks':len(checks),'regular_bytes':total,'links':len(links)}))
