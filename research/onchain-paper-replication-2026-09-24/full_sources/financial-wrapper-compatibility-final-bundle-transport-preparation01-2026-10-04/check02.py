from pathlib import Path
import sys,json,ast,hashlib,copy
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));import binding01 as B
import restore_bundle01 as S
R=B.R;n=0
def ok(v):
 global n
 assert v;n+=1
def refuse(fn):
 try:fn()
 except (ValueError,TypeError,KeyError):ok(True)
 else:raise AssertionError('unreleased accepted')
q=json.loads((D/'REQUEST_DRAFT01.json').read_bytes());refuse(lambda:B.validate(q));refuse(lambda:B.remote_source(q))
for field in B.FIELDS:
 x=copy.deepcopy(q);x['status']='ROOT_FROZEN_FINAL_POPULATION_REQUIRES_CALLER_REVIEW';x[field]=None;refuse(lambda:B.validate(x))
for value in [None,True,{},'x'*64,'0'*63]:refuse(lambda:B.hexpin(value))
for value in [{'path':'/etc/passwd','bytes':3,'sha256':'0'*64},{'path':'research/../keys/x','bytes':0,'sha256':'0'*64},{'path':B.PREFIX+'x','bytes':True,'sha256':'0'*64}]:refuse(lambda:B.ref(value))
# Exact source population inverse; no authority or future receipt fabricated.
inv=json.loads((D/'SOURCE_INVERSE01.json').read_bytes());s=(D/'recover.template01.py').read_text()
for e in reversed(inv['literal_edits']):ok(s.count(e['new'])==1);s=s.replace(e['new'],e['old'])
ok(s==(D/'ORIGINAL_REMOTE01.py').read_text());ok(ast.dump(ast.parse(s))==ast.dump(ast.parse((D/'ORIGINAL_REMOTE01.py').read_bytes())))
a=ast.parse((D/'ORIGINAL_FLAT01.py').read_bytes());b=ast.parse((D/'cohort01.py').read_bytes());ok(ast.dump(next(x for x in a.body if isinstance(x,ast.ClassDef) and x.name=='VerifiedCohort'))==ast.dump(next(x for x in b.body if isinstance(x,ast.ClassDef) and x.name=='VerifiedCohort')))
# Genuine owned opaque archive utility; no mocked remote or research handles.
t=D/'tiny02';t.mkdir();selected=t/'selected';selected.mkdir();output=t/'output';output.mkdir();bundles=[]
for name in ('first','second'):
 src=t/name;src.mkdir();(src/'opaque').write_bytes(name.encode());(src/'empty').mkdir();m=R.scan(src);R.put(selected/(name+'.json'),m);arc=R.pack(src,m,selected/(name+'.tgz'));bundles.append({'name':name,'manifest':{'path':name+'.json','bytes':len(R.encode(m)),'sha256':R.digest(R.encode(m))},'archive':{'path':name+'.tgz','bytes':arc['bytes'],'sha256':arc['sha256']}})
results=S.restore_archives({'bundles':bundles},selected,output,lambda:None);ok(set(results)=={'first','second'});refuse(lambda:S.restore_archives({'bundles':bundles},selected,output,lambda:None))
for name,result in results.items():
 md=json.loads((output/('flat-'+name)/result['metadata_file']).read_bytes());ok((output/('flat-'+name)/md['flat_members']['opaque']).read_bytes()==name.encode())
for primary in (KeyboardInterrupt('p'),MemoryError('p')):
 try:
  try:raise primary
  except BaseException:
   R._cleanup((lambda:(_ for _ in ()).throw(OSError('close')),),primary=primary);raise
 except BaseException as e:ok(e is primary)
(D/'CHECKS01.json').write_text(json.dumps({'checks':n,'actual_network':False,'actual_Root_restore':False,'fake_research_objects':False,'owned_tiny_scopes':2},indent=2)+'\n');print(n)
