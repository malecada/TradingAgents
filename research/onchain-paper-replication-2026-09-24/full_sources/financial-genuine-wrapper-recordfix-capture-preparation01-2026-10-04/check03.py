import ast,copy,json,os,sys
from pathlib import Path
import capture01 as C
R=C.R;H=Path(__file__).resolve().parent;checks=[]
def ok(n,v):assert v,n;checks.append(n)
def refuse(n,fn):
 try:fn()
 except (ValueError,TypeError,KeyError,FileExistsError):ok(n,True)
 else:raise AssertionError(n)
q=json.loads((H/'REQUEST_TEMPLATE01.json').read_text())
refuse('null draft refused',lambda:C.validate_request(q))
for key,value in [('source','0'*40),('capsule_root','/'),('schema_version',True),('manifest_sha256','0'*64)]:
 t=copy.deepcopy(q);t[key]=value;refuse('request refusal '+key,lambda:C.validate_request(t))
m=q['manifest'];R.validate(m);ok('actual complete denominator',len(m['members'])==986 and sum(r['kind']=='file' for r in m['members'])==713)
for name in ['recovery04.py','owned_io.py','bounded_git01.py']:
 old=H.parent/'financial-genuine-wrapper-parent-preparation03-2026-10-04'/name;ok('unchanged helper '+name,(H/name).read_bytes()==old.read_bytes())
for path in ['../escape','/absolute','a/../b','a/.env','a//b','a\\b']:
 refuse('path '+path,lambda:R.path_name(path))
for kind in ['duplicate','badmode','bigfile','unordered','absentparent']:
 t=copy.deepcopy(m)
 if kind=='duplicate':t['members'].append(t['members'][0])
 if kind=='badmode':t['members'][0]['mode']=-1
 if kind=='bigfile':next(r for r in t['members'] if r['kind']=='file')['bytes']=R.FILE+1
 if kind=='unordered':t['members'].reverse()
 if kind=='absentparent':t['members']=[r for r in t['members'] if r['path']!='.git']
 refuse('manifest '+kind,lambda:R.validate(t))
owned=H/'owned03';owned.mkdir();src=owned/'source';src.mkdir();(src/'dir').mkdir();(src/'dir/a').write_bytes(b'opaque\0bytes');(src/'z').write_bytes(b'last')
tiny=R.scan(src);archive=owned/'tiny.tar.gz';info=R.pack(src,tiny,archive);ok('bounded canonical tiny archive',info['bytes']<=R.FILE)
(owned/'flat').mkdir(mode=0o700);restore=R.restore(archive,info,tiny,owned/'flat');ok('actual opaque flat restore',restore['regular_bodies']==2 and not restore['instantiated_posix_tree'])
refuse('archive identity once',lambda:R.pack(src,tiny,archive));refuse('flat identity once',lambda:R.restore(archive,info,tiny,owned/'flat'))
bad=dict(info);bad['sha256']='0'*64;refuse('archive corruption pin',lambda:R.restore(archive,bad,tiny,owned/'wrong'))
(src/'z').write_bytes(b'changed');refuse('source change',lambda:R.same(src,tiny))
link=owned/'redirect';link.symlink_to(src,target_is_directory=True);refuse('redirected source',lambda:R.scan(link))
parent=owned/'exclusive';parent.mkdir();C.reserve(parent/'new');refuse('exclusive one use reserve',lambda:C.reserve(parent/'new'))
primary=KeyboardInterrupt('primary');events=[]
def close():events.append('close');raise OSError('secondary')
def later():events.append('later')
try:R._cleanup((close,later),primary=primary)
except BaseException as e:ok('first fatal identity',e is primary)
ok('all cleanup attempted',events==['close','later'])
ok('no numerical imports',all(n not in sys.modules for n in ['numpy','torch','pandas','scipy']))
(H/'CHECKS01.json').write_bytes(R.encode({'count':len(checks),'checks':checks,'actual_CAP_captures':0,'native_jobs':0,'fake_claims':0}))
print('PASS',len(checks))
