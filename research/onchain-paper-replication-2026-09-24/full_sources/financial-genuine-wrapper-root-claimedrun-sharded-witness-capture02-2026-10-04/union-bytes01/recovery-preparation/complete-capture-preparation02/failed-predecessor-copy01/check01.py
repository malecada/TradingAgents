import ast,hashlib,importlib.util,json,os,stat,sys,time,shutil,types
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'held-consumer-final-recovery-preparation04-2026-10-03'));import recovery04 as R
s=(H/'capture01.py').read_text();old=(H/'original-capture03.py').read_text();checks=[]
def ok(x,n):assert x,n;checks.append(n)
inv=s
for e in reversed(json.loads((H/'INVERSE01.json').read_text())['edits']):ok(inv.count(e['new'])==e.get('count',1),'unique inverse');inv=inv.replace(e['new'],e['old'])
ok(inv==old,'whole byte inverse');ok(ast.dump(ast.parse(inv))==ast.dump(ast.parse(old)),'whole AST inverse')
ns={'__file__':str(H/'capture01.py'),'__name__':'test_only'};exec(compile(s,'<candidate definitions>','exec'),ns)
ok(not os.path.lexists(ns['HERE']),'Root output absent observation')
links=0;regular=0
for root in ns['SCOPES'].values():
 for parent,dirs,files in os.walk(root,followlinks=False):
  for n in dirs+files:
   p=Path(parent)/n
   if p.is_symlink():links+=1
   elif p.is_file():regular+=1
ok(links==50,'actual20 scopes50literal links')
# Execute unchanged main's capture/archive/rescan suffix on four tiny owned roots.
node=next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='main');start=next(i for i,n in enumerate(node.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='union' for t in n.targets))
fn=ast.FunctionDef(name='fixture',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='r4')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=node.body[start:],decorator_list=[]);ast.fix_missing_locations(fn)
for label,late in [('valid',False),('late-extra',True)]:
 here=H/label;here.mkdir();scopes={}
 for i in range(4):
  root=here/('original'+str(i));root.mkdir();(root/'body').write_bytes(b'opaque'+bytes([i]));(root/'literal').symlink_to('missing');scopes[str(i)]=root
 source=here/'tiny-source';source.mkdir();(source/'byte').write_bytes(b'source');manifest=R.scan(source)
 local=dict(ns,HERE=here,SCOPES=scopes,SOURCE=source,source_manifest=manifest,start=time.monotonic())
 proxy=types.SimpleNamespace(**{n:getattr(R,n) for n in dir(R)})
 def pack(root,m,dest):
  result=R.pack(root,m,dest)
  if late:(scopes['0']/'late').write_bytes(b'retained late member')
  return result
 proxy.pack=pack
 exec(compile(ast.Module(body=[fn],type_ignores=[]),'<exact capture suffix>','exec'),local)
 try:local['fixture'](proxy)
 except ValueError as e:ok(late and 'complete original membership' in str(e),'late extra refuses after archive')
 else:
  ok(not late,'valid complete fixture');a=json.loads((here/'UNION_AUTHENTICATION01.json').read_bytes());ok(a['original_trees']==4 and a['original_lexical_links']==4 and a['original_regular_members']==4,'four-tree complete counts');m=json.loads((here/'union-bytes01/ORIGINAL_TREES01.json').read_bytes());ok(m['source_full_recovery_readback_sha256']=='468dac2c06e570a89a30771c3f7e1b8e064e6f27e610acf01edcccf91c9a2825','actual new Source339 recovery pin');ok(not any(p.is_symlink() for p in (here/'union-bytes01').rglob('*')),'links metadata only')
for firsttype in (MemoryError,KeyboardInterrupt):
 for secondtype in (OSError,MemoryError,KeyboardInterrupt):
  first=firsttype('body');second=secondtype('close');fd=os.open(H/'owned-fd',os.O_WRONLY|os.O_CREAT,0o600)
  def close():os.close(fd);raise second
  try:
   try:raise first
   finally:R._cleanup((close,))
  except BaseException as e:ok(e is first,'real fd firstfatal')
  ok(not Path('/proc/self/fd/'+str(fd)).exists(),'real fd absent')
ok(len(ns['SCOPES'])==20,'exact20 actual scopes')
ok(hashlib.sha256((ns['SCOPES']['actual-verifier-review']/'MANIFEST01.json').read_bytes()).hexdigest()=='0c39988229162fd10b0d0df77f71163a4675a778251a8d75634283e40482bea2','actual generated verifier review pin')
ok(hashlib.sha256((ns['PARENT']/'REQUEST_FINAL03.json').read_bytes()).hexdigest()=='529c9bf3c587e6160a217e8eb339882e59433b6fc0f759d0009d261f872b2bd8','actual final request pin')
(H/'CHECKS01.json').write_text(json.dumps({'count':len(checks),'checks':checks,'actual_four_scope_regular_files':regular,'actual_links':links,'actual_Root_capture':False},indent=2)+'\n');print(len(checks))
