from pathlib import Path
import json,hashlib,difflib
P=Path(__file__).resolve().parent;R=P.parents[3]
(P/'AMENDMENT02.md').write_text('''# FIFO refusal amendment02

Candidate01 and manifest669bb0d07ca9c9f2e15d8327a534c1a60896e51fc36a5e910a4b3c0e331cc85d are preserved verbatim in iteration01; original SOURCE_MANIFEST01 remains unchanged. Independent reviewer retained actual FIFO-hang RED in its FRONTIER_CHECK01 evidence. O_RDONLY can block while opening a FIFO before the regular-file fstat. The only admission semantic delta adds O_NONBLOCK and O_CLOEXEC to this same bounded open; fstat and all body/hash checks remain.

FIFO_CHECK02 passes the single actual temporary FIFO control through the exact extracted _history_frontier under a250ms alarm in0.020s. No unchanged matrix was repeated. Benchmark output now explicitly labels the measured history-frontier/audit component and excludes current admission checks, warm own-claim verification and production warm latency. Benchmark algorithm and scope are unchanged and were not executed. No live source, registration, claims, Git or state mutation.
''')
for name in ('admission.py','benchmark01.py'):
 a=(P/'iteration01'/name).read_text();b=(P/name).read_text();compile(b,str(P/name),'exec')
 for suffix,x,y,xf,yf in [('diff',a,b,'iteration01/'+name,'iteration02/'+name),('inverse.diff',b,a,'iteration02/'+name,'iteration01/'+name)]:
  (P/('AMENDMENT02_'+name+'.'+suffix)).write_text(''.join(difflib.unified_diff(x.splitlines(True),y.splitlines(True),fromfile=xf,tofile=yf)))
def pin(p):return {'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
old=json.loads((P/'SOURCE_MANIFEST01.json').read_text())
for t in old['targets']:t['candidate_sha256']=hashlib.sha256((P/Path(t['target']).name).read_bytes()).hexdigest()
m={'status':'UNINSTALLED_FIFO_REFUSAL_AMENDMENT02','prior_manifest':pin(P/'iteration01/SOURCE_MANIFEST01.json'),'targets':old['targets'],'files':[pin(p) for p in sorted(P.iterdir()) if p.is_file() and p.name!='SOURCE_MANIFEST02.json']}
(P/'SOURCE_MANIFEST02.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps({n:pin(P/n) for n in ('SOURCE_MANIFEST02.json','admission.py','benchmark01.py')},indent=2))
