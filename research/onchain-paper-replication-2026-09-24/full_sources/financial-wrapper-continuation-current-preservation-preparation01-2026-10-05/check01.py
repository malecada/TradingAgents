"""Finite owned opaque metadata/refusal checks; no genuine authority constructed."""
import ast,hashlib,json,os
from pathlib import Path
import bind02 as B
H=Path(__file__).resolve().parent
checks=[]
def ok(label,value):
 assert value,label
 checks.append(label)
def refuses(label,fn):
 try:fn()
 except ValueError:checks.append(label)
 else:raise AssertionError(label)
root=H/'tiny-owned';root.mkdir(mode=0o700);p=root/'opaque';p.write_bytes(b'opaque\x00bytes');p.chmod(0o600)
c=B.Census();m=c.tree(root,{'opaque':'file'},{'opaque'});c.finish();ok('actual owned opaque census',m['members'][0]['sha256']==B.sha(b'opaque\x00bytes'))
refuses('unlisted member refused',lambda:B.Census().tree(root,{},set()))
refuses('wrong member type refused',lambda:B.Census().tree(root,{'opaque':'directory'},set()))
p.chmod(0o640);refuses('late mode mutation refused',c.finish)
d=B.Census();d.tree(root,{'opaque':'file'},set());p.write_bytes(b'changed bytes');refuses('late body signature mutation refused',d.finish)
link=H/'tiny-link';link.symlink_to(root,target_is_directory=True);refuses('redirect root refused',lambda:B.Census().tree(link,{'opaque':'file'},set()))
d=B.Census();d.start-=121;refuses('elapsed deadline refused',d.tick)
primary=KeyboardInterrupt('primary');secondary=OSError('secondary');closed=[]
def close():closed.append(True);raise secondary
try:
 try:raise primary
 finally:B.IO._cleanup((close,))
except BaseException as error:ok('original fatal survives real cleanup callback',error is primary and closed==[True])
s=json.loads((H/'SELECTED_BODIES02.json').read_bytes());ok('27 exact incremental bodies',len(s['bodies'])==s['count']==27 and s['bytes']==842160)
for r in s['bodies']:
 raw=(H/r['path']).read_bytes();ok('selected '+r['path'],len(raw)==r['bytes'] and B.sha(raw)==r['sha256'] and len(raw)<=4*1024**2)
c=json.loads((H/'CURRENT_COMPOSITION02.json').read_bytes())
ok('original 818 retained; exact five added',c['old_capsule_files_reused']==818 and len(c['new_capsule_files'])==5)
ok('original407 retained in416',len(c['git']['old407'])==407 and len(c['git']['current416'])==416 and set(c['git']['old407'])<set(c['git']['current416']))
gitrows={r['original_path']:r for r in s['bodies'] if r['role']=='git'}
for r in c['git']['new_objects']:
 raw=(H/gitrows[r['oid']]['path']).read_bytes();ok('actual object '+r['oid'],hashlib.sha1(r['kind'].encode()+b' '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==r['oid'])
ok('old 355 source entries unchanged',all(c['tracked']['current360'][n]==v for n,v in c['tracked']['old355'].items()))
ok('genuine pending recovery/release retained',c['future']['whole_current_recovery'] is None and c['future']['final_release'] is None)
for n in ['bind01.py','bind02.py','supplement02.py']:ast.parse((H/n).read_text());checks.append('AST '+n)
print(json.dumps({'passed':len(checks),'checks':checks,'scope':'stdlib owned opaque/source metadata only; no full Admission/native/restore'},sort_keys=True))
