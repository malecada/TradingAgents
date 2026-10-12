from pathlib import Path
import hashlib,json,difflib
P=Path(__file__).resolve().parent;R=P.parents[3]
def pin(p):return {'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
for name in ('matching_numeric_policy.py','matching_immutable_session.py','numeric_harness.py','benchmark01.py','static_check01.py','numeric_checks01.py'):
 a=(P/'iteration01'/name).read_text();b=(P/name).read_text();compile(b,name,'exec')
 for suffix,x,y,xf,yf in [('diff',a,b,'iteration01/'+name,'iteration02/'+name),('inverse.diff',b,a,'iteration02/'+name,'iteration01/'+name)]:
  (P/('AMENDMENT02_'+name+'.'+suffix)).write_text(''.join(difflib.unified_diff(x.splitlines(True),y.splitlines(True),fromfile=xf,tofile=yf)))
old=json.loads((P/'SOURCE_MANIFEST01.json').read_text())
for item in old['targets']:item['candidate']=pin(P/Path(item['target']).name)
m={'status':'UNINSTALLED_COMBINED_AMENDMENT02_NUMERICAL_UNEXECUTED','prior_manifest':pin(P/'iteration01/SOURCE_MANIFEST01.json'),'targets':old['targets'],'caller_reservation_bytes':33619968,'unchanged_source_pins':old['unchanged_source_pins'],'files':[pin(p) for p in sorted(P.iterdir()) if p.is_file() and p.name!='SOURCE_MANIFEST02.json']}
(P/'SOURCE_MANIFEST02.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps({n:pin(P/n) for n in ('SOURCE_MANIFEST02.json','matching_numeric_policy.py','matching_immutable_session.py','numeric_harness.py','benchmark01.py')},indent=2))
