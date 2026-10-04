import copy,json,sys
from pathlib import Path
import restore_union01 as M
R=M.R;H=Path(__file__).resolve().parent;checks=[]
def ok(n,v):assert v,n;checks.append(n)
def refuse(n,fn):
 try:fn()
 except (ValueError,KeyError,TypeError,FileExistsError):ok(n,True)
 else:raise AssertionError(n)
q={'schema_version':1,'remote_root':None,'remote_receipt_sha256':None,'remote_commit':None,'archive':None,'manifest':None,'union_auth':None,'expected_members':None,'expected_files':None,'expected_logical_bytes':None,'output_root':None,'review':None,'release':None}
(H/'REQUEST_TEMPLATE01.json').write_bytes(R.encode(q));refuse('unreleased actual request',lambda:M.request(q))
for n,pin in M.PINS.items():ok('exact unchanged helper '+n,R.digest(R.read(H,n))==pin)
root=H/'owned01';root.mkdir();src=root/'ordinary-union';src.mkdir();(src/'bodies').mkdir();(src/'bodies/a.body').write_bytes(b'opaque full regular body');(src/'tree.json').write_bytes(R.encode({'qualification':'synthetic lexical-link metadata only','links':[{'path':'dangling','literal':'/never/follow/this'}]}));m=R.scan(src);qsmall={'expected_members':3,'expected_files':2,'expected_logical_bytes':sum(x.get('bytes',0) for x in m['members'])};ok('exact ordinary denominator',M.manifest_join(qsmall,R.encode(m))==m)
for key,value in [('expected_members',4),('expected_files',1),('expected_logical_bytes',0)]:
 z=dict(qsmall);z[key]=value;refuse('wrong denominator '+key,lambda:M.manifest_join(z,R.encode(m)))
for mutation in ['duplicate','link','oversize','path','missingparent','unsorted','badmode']:
 z=copy.deepcopy(m)
 if mutation=='duplicate':z['members'].append(z['members'][-1])
 if mutation=='link':z['members'][-1]={'path':'tree.json','kind':'symlink','mode':511,'target':'/forbidden'}
 if mutation=='oversize':z['members'][-1]['bytes']=R.FILE+1
 if mutation=='path':z['members'][-1]['path']='../escape'
 if mutation=='missingparent':z['members']=z['members'][1:]
 if mutation=='unsorted':z['members'].reverse()
 if mutation=='badmode':z['members'][-1]['mode']=-1
 refuse('manifest refusal '+mutation,lambda:M.manifest_join(qsmall,R.encode(z)))
archive=root/'tiny.tar.gz';info=R.pack(src,m,archive);dest=root/'flat';M.reserve(dest);result=M.restore_ordinary(archive,info,m,dest)
ok('complete opaque ordinary restore',result['regular_bodies']==2 and result['members']==3 and not result['instantiated_posix_tree'])
md=json.loads(R.read(dest,result['metadata_file']));ok('lexical-link metadata byte identical',R.read(dest,md['flat_members']['tree.json'])==(src/'tree.json').read_bytes());ok('literal not materialized',not (dest/'dangling').exists())
refuse('present target refused',lambda:M.reserve(dest));refuse('repeated R4 flat target refused',lambda:M.restore_ordinary(archive,info,m,dest))
wrong=dict(info,sha256='0'*64);empty=root/'wrong';M.reserve(empty);refuse('corrupt binding',lambda:M.restore_ordinary(archive,wrong,m,empty))
for first in [ValueError('ordinary'),MemoryError('fatal-memory'),KeyboardInterrupt('fatal-interrupt')]:
 for second in [OSError('ordinary-cleanup'),MemoryError('fatal-cleanup'),KeyboardInterrupt('fatal-cleanup')]:
  events=[]
  def fail():events.append('first');raise second
  def last():events.append('last')
  actual=None
  try:R._cleanup((fail,last),primary=first)
  except BaseException as e:actual=e
  expected=first if not isinstance(first,Exception) or isinstance(first,MemoryError) or (isinstance(second,Exception) and not isinstance(second,MemoryError)) else second
  ok('exact first-fatal pair '+type(first).__name__+'/'+type(second).__name__,actual is expected);ok('all callbacks '+type(first).__name__+'/'+type(second).__name__,events==['first','last'])
ok('no numerical imports',all(n not in sys.modules for n in ['numpy','torch','scipy','pandas']))
(H/'CHECKS01.json').write_bytes(R.encode({'count':len(checks),'checks':checks,'actual_remote_or_union_restore':False,'network':0,'claims':0}));print('PASS',len(checks))
