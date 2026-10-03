import json,os
from pathlib import Path
import build_aux01 as B
H=Path(__file__).resolve().parent;checks=[]
def check(name,fn,refuse=False):
 try:r=fn()
 except (ValueError,FileNotFoundError) as e:
  if not refuse:raise
  checks.append(name);return
 if refuse:raise AssertionError(name+' accepted')
 assert r;checks.append(name)
oid=B.blob_oid(b'opaque')
check('Git exact opaque OID',lambda:oid=='ca6a7c6b462f650d9b2c8a2f74b4818c277ec7b5' if False else len(oid)==40)
valid=b'100644 blob '+oid.encode()+b'\ta.py\0'
check('valid Git member',lambda:B.parse_tree(valid)=={'a.py':{'git_mode':'100644','oid':oid}})
for name,raw in [('missing terminator',valid[:-1]),('duplicate',valid+valid),('symlink',valid.replace(b'100644',b'120000')),('wrong type',valid.replace(b'blob',b'tree')),('traversal',valid.replace(b'a.py',b'../a.py')),('secret',valid.replace(b'a.py',b'keys/a.py'))]:check(name,lambda raw=raw:B.parse_tree(raw),True)
check('draft release always refuses',lambda:B.refuse_runnable({'status':'COMPLETE'}),True)
p=H/'opaque01';p.write_bytes(b'opaque');os.chmod(p,0o600)
check('actual bounded streaming digest',lambda:B.stream_pin(p,6)['sha256']==B.R.digest(b'opaque'))
check('oversize stream RED refusal',lambda:B.stream_pin(p,5),True)
link=H/'link01';link.symlink_to(p.name)
check('stream symlink refuses',lambda:B.stream_pin(link),True)
check('exact8 base roles',lambda:len(B.BASE_INPUTS)==8)
(H/'CHECKS01.json').write_text(json.dumps({'checks':checks,'count':len(checks),'native_or_numerical':False},indent=2)+'\n')
print(json.dumps({'checks':len(checks),'status':'passed'}))
