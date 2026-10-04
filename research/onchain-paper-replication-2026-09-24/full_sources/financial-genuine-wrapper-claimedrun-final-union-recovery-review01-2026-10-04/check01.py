import ast,copy,hashlib,importlib.util,json,os,stat,sys
from pathlib import Path
H=Path(__file__).resolve().parent;P=H.parent/'financial-genuine-wrapper-claimedrun-final-union-recovery-preparation01-2026-10-04';checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ok(v,n):assert v,n;checks.append(n)
def refuse(f,n):
 try:f()
 except (ValueError,KeyError,TypeError,FileExistsError):checks.append(n)
 else:raise AssertionError(n)
ok(sha(P/'MANIFEST01.json')=='5e6eca11c607f2731179e491dc379773983f899e71fc7a09156ec9c6e6c0b578','exact frozen candidate manifest');m=json.loads((P/'MANIFEST01.json').read_bytes());actual=[]
for root,ds,fs in os.walk(P,followlinks=False):
 for n in ds+fs:actual.append((Path(root)/n).relative_to(P).as_posix())
ok(set(actual)=={r['path'] for r in m['members']}|{'MANIFEST01.json'},'complete candidate membership')
for row in m['members']:
 f=P/row['path'];s=f.lstat();ok(oct(stat.S_IMODE(s.st_mode))==row['mode'],'candidate mode '+row['path'])
 if row['kind']=='file':ok(stat.S_ISREG(s.st_mode) and s.st_size==row['bytes'] and sha(f)==row['sha256'],'candidate body '+row['path'])
 elif row['kind']=='symlink':ok(stat.S_ISLNK(s.st_mode) and os.readlink(f)==row['target'],'literal evidence link')
 else:ok(stat.S_ISDIR(s.st_mode),'candidate directory')
sys.path.insert(0,str(P));import restore_union01 as S
ok(sha(P/'restore_union01.py')=='4992e3685e0ffd977c305e3a943197a1f57a2f38dc19ec7447b4f2ef08a9eb60','exact helper')
source=(P/'restore_union01.py').read_text();old=(P/'original-restore_union01.py').read_text();back=source
for e in reversed(json.loads((P/'INVERSE01.json').read_bytes())['edits']):ok(back.count(e['new'])==1,'unique inverse');back=back.replace(e['new'],e['old'])
ok(back==old,'full byte inverse');ok(ast.dump(ast.parse(back))==ast.dump(ast.parse(old)),'full AST inverse')
for name in ('selected','reference','reserve','restore_ordinary','manifest_join'):
 get=lambda s:ast.get_source_segment(s,next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name==name));ok(get(source)==get(old),'unchanged exact IO '+name)
for n,pin in S.PINS.items():ok(sha(P/n)==pin,'accepted primitive '+n)
expected=json.loads((P/'EXPECTED_ORIGINALS01.json').read_bytes());ok(sha(P/'EXPECTED_ORIGINALS01.json')=='40b4002ee1b0edf1d2d4e4202cf3d5c98834eb9656b02558caedf40d7261dc30','exact census pin');trees=expected['scope_trees'];S.validate_expected_trees(trees)
# Independently re-enumerate closed actual roots without following literal links.
for tree in trees:
 root=Path(tree['original_root']);observed=[]
 def visit(f,rel):
  z=f.lstat();r={'path':rel,'mode':stat.S_IMODE(z.st_mode)}
  if stat.S_ISLNK(z.st_mode):r.update(kind='lexical-symlink',target=os.readlink(f))
  elif stat.S_ISDIR(z.st_mode):
   r['kind']='directory';observed.append(r)
   for child in sorted(f.iterdir(),key=lambda x:x.name):visit(child,child.name if rel=='.' else rel+'/'+child.name)
   return
  else:
   ok(stat.S_ISREG(z.st_mode) and z.st_size<=S.R.FILE,'actual original bounded regular');r.update(kind='file',bytes=z.st_size,sha256=sha(f),union_path=tree['scope']+'/'+rel)
  observed.append(r)
 visit(root,'.');ok(sorted(observed,key=lambda r:r['path'])==tree['members'],'actual complete closed tree '+tree['scope'])
for i in range(20):
 for kind in ('omit','root','mode','late'):
  v=copy.deepcopy(trees)
  if kind=='omit':v.pop(i)
  elif kind=='root':v[i]['original_root']='/wrong'
  elif kind=='mode':v[i]['members'][0]['mode']^=1
  else:v[i]['members'].append({'path':'late','mode':384,'kind':'file','bytes':0,'sha256':'0'*64,'union_path':v[i]['scope']+'/late'})
  refuse(lambda:S.validate_expected_trees(v),'fixed scope refuses '+kind+str(i))
for kind in ('hash','link','order','missingrow'):
 v=copy.deepcopy(trees)
 if kind=='hash':next(r for t in v for r in t['members'] if r['kind']=='file')['sha256']='0'*64
 elif kind=='link':next(r for t in v for r in t['members'] if r['kind']=='lexical-symlink')['target']='/redirect'
 elif kind=='order':v.reverse()
 else:v[0]['members'].pop()
 refuse(lambda:S.validate_expected_trees(v),'mapping mutation '+kind)
q=json.loads((P/'REQUEST_TEMPLATE01.json').read_bytes());refuse(lambda:S.request(q),'unreleased actual template')
for k in q:
 v=dict(q);v.pop(k);refuse(lambda:S.request(v),'missing request '+k)
root=H/'owned';root.mkdir();src=root/'src';src.mkdir();(src/'regular').write_bytes(b'opaque independent bytes');(src/'literal-link-metadata').write_bytes(b'{"literal":"/never-follow"}');manifest=S.R.scan(src);archive=root/'bytes.tar.gz';info=S.R.pack(src,manifest,archive);dest=root/'flat';S.reserve(dest);result=S.restore_ordinary(archive,info,manifest,dest);metadata=json.loads(S.R.read(dest,result['metadata_file']))
ok(result['regular_bodies']==2 and len(list(dest.iterdir()))==3,'independent real tiny full flat');ok(S.R.read(dest,metadata['flat_members']['regular'])==b'opaque independent bytes','actual bytes equal');refuse(lambda:S.reserve(dest),'one-use reserve')
redirect=root/'link';redirect.symlink_to(src,target_is_directory=True);refuse(lambda:S.reserve(redirect/'bad'),'anchored redirected parent refusal');ok(not (src/'bad').exists(),'no redirected side effect')
for firsttype in (MemoryError,KeyboardInterrupt):
 for secondtype in (OSError,MemoryError,KeyboardInterrupt):
  first=firsttype('primary');second=secondtype('close');fd=os.open(root/'fd',os.O_WRONLY|os.O_CREAT,0o600)
  def close():os.close(fd);raise second
  try:
   try:raise first
   finally:S.R._cleanup((close,))
  except BaseException as e:ok(e is first,'actual fd first fatal')
  ok(not Path('/proc/self/fd/'+str(fd)).exists(),'actual fd reaped')
ok(not any(n in sys.modules for n in ('numpy','torch','pandas')),'no numerical imports')
(H/'CHECKS01.json').write_bytes(S.R.encode({'count':len(checks),'checks':checks,'actual_final_recovery':False,'actual_network':False,'new_claims':0}));print(len(checks))
