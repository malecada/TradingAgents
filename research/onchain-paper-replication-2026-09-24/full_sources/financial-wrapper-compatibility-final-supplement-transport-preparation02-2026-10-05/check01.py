from pathlib import Path
import sys,ast,json,hashlib,os
D=Path(__file__).resolve().parent;sys.path[:0]=[str(D),str(D/'utilities')];import binding01 as B;import restore_bundle01 as S
R=S.R;checks=[]
def ok(v,n):assert v,n;checks.append(n)
for row in json.loads((D/'INVERSE01.json').read_text()):
 s=row['original']
 for a,b in row['changes']:s=s.replace(a,b)
 ok(s==(D/row['file']).read_text(),row['file']+' full forward source inverse')
 if row['file'].startswith('caller'):
  old={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(row['original']).body if isinstance(n,ast.FunctionDef)};new={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)}
  for n in old.keys()-{'contract','main'}:ok(old[n]==new[n],row['file']+' unchanged '+n)
for name,row in json.loads((D/'ORIGINS01.json').read_text()).items():
 if name!='restore_bundle01.py':ok(hashlib.sha256((D/name).read_bytes()).hexdigest()==row['sha256'],'unchanged '+name)
q=json.loads((D/'REQUEST_DRAFT01.json').read_text())
try:B.validate(q)
except (ValueError,TypeError,KeyError):checks.append('null final draft refuses')
else:raise AssertionError('draft released')
for field in B.FINAL:
 try:B.evidence({'round':'FINAL_SUPPLEMENT',**{k:None for k in B.COMMON+B.FINAL}})
 except (ValueError,TypeError,KeyError):checks.append('missing final proof refuses '+field)
 else:raise AssertionError('absent final evidence accepted')
# Actual opaque PAX utility round trip, outside any Root namespace.
original=D/'opaque-original';selected=D/'opaque-selected';out=D/'opaque-output'
for p in (original,selected,out):p.mkdir(mode=0o700)
(original/'tiny.body').write_bytes(b'opaque-final-supplement\0');os.chmod(original/'tiny.body',0o600)
m=R.scan(original);raw=R.encode(m);(selected/'manifest.json').write_bytes(raw);os.chmod(selected/'manifest.json',0o600);a=R.pack(original,m,selected/'body.tar.gz')
q={'bundles':[{'name':'opaque','manifest':{'path':'manifest.json','bytes':len(raw),'sha256':R.digest(raw)},'archive':{'path':'body.tar.gz','bytes':a['bytes'],'sha256':a['sha256']}}]}
r=S.restore_archives(q,selected,out,lambda:None);meta=json.loads((out/'flat-opaque'/r['opaque']['metadata_file']).read_bytes());ok((out/'flat-opaque'/meta['flat_members']['tiny.body']).read_bytes()==(original/'tiny.body').read_bytes(),'real opaque PAX complete recovery')
ok(S.RECEIVER.name=='financial-wrapper-compatibility-final-supplement-root02-2026-10-05','fixed read-only final receiver')
(D/'CHECKS01.json').write_text(json.dumps({'checks':checks,'count':len(checks),'Root_entry':False,'network':False},indent=2)+'\n');print(len(checks))
