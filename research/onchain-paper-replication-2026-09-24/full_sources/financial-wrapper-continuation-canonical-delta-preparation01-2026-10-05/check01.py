from pathlib import Path
import ast,copy,hashlib,json,sys
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import delta01 as D
checks=[]
def ck(n,v):assert v,n;checks.append(n)
def refusal(n,fn):
 try:fn()
 except ValueError:checks.append(n);return
 raise AssertionError(n)
q=json.loads((H/'REQUEST_DRAFT01.json').read_bytes());refusal('missing actual dependencies',lambda:D.schema(q))
prior=json.loads(D.COMPOSITION.read_bytes());ck('actual accepted composition pin',hashlib.sha256(D.COMPOSITION.read_bytes()).hexdigest()==D.COMPOSITION_PIN)
by={r['path']:r for r in prior['capsule']['members']};changed={n:dict(by[n],sha256='0'*64) for n in D.CHANGED};out=D.merge(prior['capsule'],changed);now={r['path']:r for r in out['members']};ck('unchanged inherited rows',all(now[n]==r for n,r in by.items() if n not in D.CHANGED));ck('original unchanged',all(by[n]['sha256']!='0'*64 for n in D.CHANGED));ck('exact changed membership',set(n for n in by if by[n]!=now[n])==D.CHANGED)
for n in D.CHANGED:
 bad=copy.deepcopy(changed);del bad[n];refusal('missing delta '+n,lambda:D.merge(prior['capsule'],bad))
bad=copy.deepcopy(changed);bad['extra']={};refusal('extra delta',lambda:D.merge(prior['capsule'],bad))
for n,pin in json.loads((H/'REUSED01.json').read_bytes()).items():ck('unchanged primitive '+n,hashlib.sha256((H/n).read_bytes()).hexdigest()==pin)
# Real small owned descriptor census via unchanged accepted primitive; no original scope capture.
r=H/'tiny-owned';r.mkdir(mode=0o700);(r/'opaque').write_bytes(b'opaque\x00metadata');c=D.B.Census();m=c.tree(r,{'opaque':'file'},{'opaque'});ck('actual tiny bytes',c.saved[(str(r),'opaque')]==b'opaque\x00metadata');c.finish();(r/'late').write_bytes(b'late');refusal('actual extra namespace',lambda:D.B.Census().tree(r,{'opaque':'file'},{'opaque'}));refusal('late signature',c.finish)
for p in H.glob('*.py'):ast.parse(p.read_bytes())
ck('no numerical imports',not set(('numpy','torch','pandas')).intersection(sys.modules));(H/'CHECKS01.json').write_text(json.dumps({'count':len(checks),'checks':checks,'actual_materialization':False,'actual_dependencies_unavailable':True},indent=2)+'\n');print(len(checks))
