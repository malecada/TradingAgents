from pathlib import Path
import json,hashlib,difflib
P=Path(__file__).resolve().parent;R=P.parents[3]
(P/'AMENDMENT03.md').write_text('''# Actual Run identity seal amendment03

All frozen02 files/manifest2527272ba02fbb1f4023ea1eb1f337223a06982bb9e0b99d3f03919f9edbf919 remain unchanged under iteration02; original top-level manifest02 is unchanged. Independent reviewer BINDING_CHECK01 retained the original same-fields distinct-Run private-table transplant RED. The only source change adds id(run) to _history_anchor canonical bytes, hence its existing HMAC seal. A different live object with identical fields cannot reuse a copied sealed snapshot. Original run is weakly keyed; strong references during verification prevent identity reuse in an active comparison.

IDENTITY_CHECK03 passes one focused synthetic control in0.024s: copy an intact seal into a distinct fixture Run with identical __dict__, require refusal before any own/history verifier call, invalidate clone state while leaving original state intact. This is private-table mutation engineering evidence, not a genuine Run or release. No unchanged matrices or actual115 scan were executed. Benchmark/lifecycle/compact sources unchanged from02.
''')
a=(P/'iteration02/admission.py').read_text();b=(P/'admission.py').read_text();compile(b,str(P/'admission.py'),'exec')
for suffix,x,y,xf,yf in [('diff',a,b,'iteration02/admission.py','iteration03/admission.py'),('inverse.diff',b,a,'iteration03/admission.py','iteration02/admission.py')]:
 (P/('AMENDMENT03_admission.py.'+suffix)).write_text(''.join(difflib.unified_diff(x.splitlines(True),y.splitlines(True),fromfile=xf,tofile=yf)))
def pin(p):return {'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
old=json.loads((P/'SOURCE_MANIFEST02.json').read_text())
for t in old['targets']:t['candidate_sha256']=hashlib.sha256((P/Path(t['target']).name).read_bytes()).hexdigest()
m={'status':'UNINSTALLED_RUN_IDENTITY_SEAL_AMENDMENT03','prior_manifest':pin(P/'iteration02/SOURCE_MANIFEST02.json'),'targets':old['targets'],'files':[pin(p) for p in sorted(P.iterdir()) if p.is_file() and p.name!='SOURCE_MANIFEST03.json']}
(P/'SOURCE_MANIFEST03.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps({n:pin(P/n) for n in ('SOURCE_MANIFEST03.json','admission.py')},indent=2))
