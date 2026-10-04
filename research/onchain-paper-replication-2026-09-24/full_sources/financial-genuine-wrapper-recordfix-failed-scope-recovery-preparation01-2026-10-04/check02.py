"""Additive corrected literal and exact-request refusal checks; no actual restore."""
import ast,hashlib,json,sys
from pathlib import Path
import restore01 as S
H=Path(__file__).resolve().parent
checks=[]
def ok(v,n):
 assert v,n
 checks.append(n)
def refuses(f,n):
 try:f()
 except (ValueError,TypeError,KeyError,AssertionError):checks.append(n)
 else:raise AssertionError(n)
old=(H/'original-review-pin-draft01.py').read_bytes();new=(H/'restore01.py').read_bytes()
wrong=(S.CAPTURE_REVIEW+'19').encode()
ok(old.replace(wrong,S.CAPTURE_REVIEW.encode())==new,'exact single literal byte inverse')
ok(ast.dump(ast.parse(old.decode().replace(wrong.decode(),S.CAPTURE_REVIEW)))==ast.dump(ast.parse(new)),'exact AST inverse')
ok(len(S.CAPTURE_REVIEW)==64,'actual review SHA length')
q=json.loads((H/'REQUEST_TEMPLATE01.json').read_bytes())
ok(hashlib.sha256(S.ref(q['capture_review_manifest'])).hexdigest()==S.CAPTURE_REVIEW,'actual independent capture review body')
refuses(lambda:S.request(q),'unreleased corrected draft')
for key in ('schema_version','remote_root','release','review','output_root'):
 bad=dict(q);bad.pop(key)
 refuses(lambda:S.request(bad),'missing '+key)
for name in S.PINS:ok(hashlib.sha256((H/name).read_bytes()).hexdigest()==S.PINS[name],'unchanged '+name)
ok(not any(n.split('.')[0] in ('torch','numpy','pandas') for n in sys.modules),'no numerical imports')
(H/'CHECKS02.json').write_text(json.dumps({'count':len(checks),'checks':checks,'actual_restore':False,'network':False,'claims':0},indent=2,sort_keys=True)+'\n')
print(json.dumps({'checks':len(checks),'status':'passed'}))
