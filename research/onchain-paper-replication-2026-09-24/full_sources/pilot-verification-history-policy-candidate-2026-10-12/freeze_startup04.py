from pathlib import Path
import json,hashlib,difflib
P=Path(__file__).resolve().parent;R=P.parents[3]
(P/'AMENDMENT04.md').write_text('''# Selected startup bounds amendment04

All frozen03 files/manifestb5e4278ca4228d5c92159526676728500de32b7e985a7cbd2f8d9131cfe24bb5 remain unchanged under iteration03; top-level original manifest03 remains unchanged. Reviewer REMAINING_CHECK01 retains the selected startup cap-bypass RED. Only _history_prior(run=None) changes: call _history_scan(root,workers,previous=None), discard its metadata tuple, return verified prior. Each startup call still performs an original fresh full claims sweep, now after selected roster/body bounds and with the same before/after frontier rejoin. No run snapshot is issued or transferred. Absent/v1 defaults unchanged.

STARTUP_CHECK04 passes one focused reduced-cap startup refusal and no-seed regression in0.022s. A3-claim synthetic roster refuses maxruns1 before any claim verifier; restored bounds permit two independent full3-claim sweeps with both private registries remaining empty. No unchanged matrices or actual115 scan were run. Benchmark, lifecycle and compact sources unchanged.
''')
a=(P/'iteration03/admission.py').read_text();b=(P/'admission.py').read_text();compile(b,str(P/'admission.py'),'exec')
for suffix,x,y,xf,yf in [('diff',a,b,'iteration03/admission.py','iteration04/admission.py'),('inverse.diff',b,a,'iteration04/admission.py','iteration03/admission.py')]:
 (P/('AMENDMENT04_admission.py.'+suffix)).write_text(''.join(difflib.unified_diff(x.splitlines(True),y.splitlines(True),fromfile=xf,tofile=yf)))
def pin(p):return {'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
old=json.loads((P/'SOURCE_MANIFEST03.json').read_text())
for t in old['targets']:t['candidate_sha256']=hashlib.sha256((P/Path(t['target']).name).read_bytes()).hexdigest()
m={'status':'UNINSTALLED_SELECTED_STARTUP_BOUNDS_AMENDMENT04','prior_manifest':pin(P/'iteration03/SOURCE_MANIFEST03.json'),'targets':old['targets'],'files':[pin(p) for p in sorted(P.iterdir()) if p.is_file() and p.name!='SOURCE_MANIFEST04.json']}
(P/'SOURCE_MANIFEST04.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps({n:pin(P/n) for n in ('SOURCE_MANIFEST04.json','admission.py')},indent=2))
