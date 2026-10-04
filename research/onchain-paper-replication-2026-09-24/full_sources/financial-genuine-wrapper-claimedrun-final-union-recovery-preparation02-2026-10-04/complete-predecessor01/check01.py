import ast,copy,json,os,sys
from pathlib import Path
import restore_union01 as M
R=M.R;H=Path(__file__).resolve().parent;checks=[]
def ok(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def refuse(n,f):
 try:f()
 except (ValueError,KeyError,TypeError,FileExistsError):ok(n,True)
 else:raise AssertionError(n)
q=json.loads(R.read(H,'REQUEST_TEMPLATE01.json'));refuse('NULL future actual request refuses',lambda:M.request(q));ok('exact fresh output namespace',q['output_root']==str(M.BASE/'financial-genuine-wrapper-claimedrun-final-union-flat-20261004-01'))
expected=json.loads(R.read(H,'EXPECTED_ORIGINALS01.json'));trees=expected['scope_trees'];ok('complete actual frozen20 original census',M.validate_expected_trees(trees)==expected)
ok('1185regular50literal links',sum(r['kind']=='file' for t in trees for r in t['members'])==1185 and sum(r['kind']=='lexical-symlink' for t in trees for r in t['members'])==50)
for idx,t in enumerate(trees):
 for kind in ('missing-scope','missing-row','extra-row','changed-root','changed-mode'):
  x=copy.deepcopy(trees)
  if kind=='missing-scope':del x[idx]
  elif kind=='missing-row':x[idx]['members'].pop()
  elif kind=='extra-row':x[idx]['members'].append({'path':'opaque-late-extra','mode':384,'kind':'file','bytes':1,'sha256':R.digest(b'x'),'union_path':t['scope']+'/opaque-late-extra'})
  elif kind=='changed-root':x[idx]['original_root']='/opaque/other'
  else:x[idx]['members'][0]['mode']^=1
  refuse('exact census '+t['scope']+' '+kind,lambda x=x:M.validate_expected_trees(x))
for kind in ('body-hash','link-target','row-order','tree-order'):
 x=copy.deepcopy(trees)
 if kind=='body-hash':next(r for t in x for r in t['members'] if r['kind']=='file')['sha256']='0'*64
 elif kind=='link-target':next(r for t in x for r in t['members'] if r['kind']=='lexical-symlink')['target']='/wrong/literal'
 elif kind=='row-order':x[0]['members'].reverse()
 else:x.reverse()
 refuse('whole mapping '+kind,lambda x=x:M.validate_expected_trees(x))
# Complete declared byte and AST inverse; primitive and reservation functions identical.
new=R.read(H,'restore_union01.py');old=R.read(H,'original-restore_union01.py');inverse=json.loads(R.read(H,'INVERSE01.json'));back=new.decode();ok('original helper2bda',R.digest(old).startswith('2bda6b41'))
for edit in reversed(inverse['edits']):ok('unique exact inverse seam',back.count(edit['new'])==1);back=back.replace(edit['new'],edit['old'])
ok('full inverse bytes and AST',back.encode()==old and ast.dump(ast.parse(back))==ast.dump(ast.parse(old)))
olddefs={n.name:ast.get_source_segment(old.decode(),n) for n in ast.parse(old).body if isinstance(n,ast.FunctionDef)};newdefs={n.name:ast.get_source_segment(new.decode(),n) for n in ast.parse(new).body if isinstance(n,ast.FunctionDef)}
for name in ('hashed','reference','contract','selected','manifest_join','reserve','restore_ordinary'):ok('unchanged function bytes '+name,newdefs[name]==olddefs[name])
for name,pin in M.PINS.items():ok('unchanged helper '+name,R.digest(R.read(H,name))==pin)
# Owned tiny ordinary archive only; no actual Source or final union restoration.
root=H/'owned01';root.mkdir();src=root/'ordinary';src.mkdir();(src/'bodies').mkdir();(src/'bodies/a').write_bytes(b'opaque utility body');(src/'literal.json').write_bytes(R.encode({'literal-link':'/never-follow-owned-negative','not_actual_capture':True}));m=R.scan(src);small={'expected_members':3,'expected_files':2,'expected_logical_bytes':sum(r.get('bytes',0) for r in m['members'])};ok('tiny manifest denominator',M.manifest_join(small,R.encode(m))==m)
for key,value in [('expected_members',2),('expected_files',3),('expected_logical_bytes',0)]:
 z=dict(small);z[key]=value;refuse('wrong complete denominator '+key,lambda z=z:M.manifest_join(z,R.encode(m)))
for kind in ('duplicate','link','oversized','traversal','missingparent','unsorted','mode'):
 z=copy.deepcopy(m)
 if kind=='duplicate':z['members'].append(z['members'][-1])
 elif kind=='link':z['members'][-1]={'path':'literal.json','mode':511,'kind':'symlink','target':'/never-follow'}
 elif kind=='oversized':z['members'][-1]['bytes']=R.FILE+1
 elif kind=='traversal':z['members'][-1]['path']='../escape'
 elif kind=='missingparent':z['members'].pop(0)
 elif kind=='unsorted':z['members'].reverse()
 else:z['members'][-1]['mode']=-1
 refuse('tiny manifest '+kind,lambda z=z:M.manifest_join(small,R.encode(z)))
archive=root/'tiny.tar.gz';info=R.pack(src,m,archive);dest=root/'flat';M.reserve(dest);result=M.restore_ordinary(archive,info,m,dest);md=json.loads(R.read(dest,result['metadata_file']));ok('tiny complete flat two bodies plus metadata',result['regular_bodies']==2 and set(p.name for p in dest.iterdir())==set(md['flat_members'].values())|{result['metadata_file']});ok('opaque literal retained bytes',R.read(dest,md['flat_members']['literal.json'])==R.read(src,'literal.json'));ok('noPOSIX/runtime/science authority',result['instantiated_posix_tree'] is False and result['research_authority'] is False)
refuse('repeat reserve refuses',lambda:M.reserve(dest));refuse('repeat flat refuses',lambda:M.restore_ordinary(archive,info,m,dest))
wrong=root/'wrong';M.reserve(wrong);refuse('wrong archive refuses',lambda:M.restore_ordinary(archive,dict(info,sha256='0'*64),m,wrong))
(src/'late-extra').write_bytes(b'opaque retained late extra');refuse('real owned late-extra refuses original same',lambda:R.same(src,m))
redirect=root/'redirect';redirect.symlink_to(src,target_is_directory=True);refuse('real owned redirected parent reservation refuses',lambda:M.reserve(redirect/'new'))
for first in (ValueError('ordinary'),MemoryError('primary-memory'),KeyboardInterrupt('primary-interrupt')):
 for second in (OSError('secondary-ordinary'),MemoryError('secondary-memory'),KeyboardInterrupt('secondary-interrupt')):
  events=[]
  def failing():events.append('first');raise second
  def final():events.append('last')
  actual=None
  try:R._cleanup((failing,final),primary=first)
  except BaseException as e:actual=e
  fatal=lambda e:not isinstance(e,Exception) or isinstance(e,MemoryError)
  valid=actual is None if fatal(first) else actual is second if fatal(second) else type(actual).__name__=='CleanupFailure' and actual.failures==(first,second)
  ok('first fatal identity '+type(first).__name__+'/'+type(second).__name__,valid);ok('all cleanup callbacks '+type(first).__name__+'/'+type(second).__name__,events==['first','last'])
ok('no numerical imports',all(n not in sys.modules for n in ('numpy','torch','scipy','pandas')))
out={'checks':len(checks),'check_names':checks,'actual_capture':None,'actual_final_union_restored':False,'fake_authority_or_release_created':False,'network':False,'numerical_execution':False,'only_opaque_tiny_flat':True};(H/'CHECKS01.json').write_bytes(R.encode(out));print(json.dumps({k:v for k,v in out.items() if k!='check_names'}))
