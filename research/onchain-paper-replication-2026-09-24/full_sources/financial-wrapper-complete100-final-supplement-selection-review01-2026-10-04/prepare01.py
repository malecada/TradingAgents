import ast,hashlib,json,os,stat
from pathlib import Path
D=Path(__file__).resolve().parent;F=D.parent;B=F/'financial-wrapper-complete100-final-supplement-capture01-2026-10-04';T=F/'financial-wrapper-complete100-final-supplement-tooling01-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest()
r=json.loads((B/'REQUIRED_BODIES01.json').read_bytes());source=(T/'recover01.py').read_bytes();assert sha(source)=='25080e2eeceb234fe63e69ab093c3d1c6af84d6584f476cc872ed43666056c1b'
a=ast.parse(source);required=ast.literal_eval(next(x.value for x in a.body if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id=='REQUIRED' for y in x.targets)));assert required==r
assert len(r)==7 and sum(x['bytes'] for x in r.values())==1063336 and 11+2*len(r)==25
for name,row in r.items():
 p=F.parents[2]/name;b=p.read_bytes();assert stat.S_ISREG(p.lstat().st_mode) and len(b)==row['bytes'] and sha(b)==row['sha256']
assert sha((T/'restore02.py').read_bytes())=='dcbf5ec290b1f34cb3a238be76976a0ad8ebf07003e8d5f43cfcbaacc1d8d5a0'
out={'schema_version':1,'status':'DRAFT_NOT_RELEASED','required_rows':[dict(path=k,**v) for k,v in sorted(r.items())],'remote_source_sha256':sha(source),'flat_source_sha256':sha((T/'restore02.py').read_bytes()),'actual_committed_selection_sha256':None,'actual_Main_and_remote_commit':None,'independent_tooling_review_manifest':None,'remote_namespace':None,'actual_remote_release':None,'numerical_release':None}
(D/'PREPARED01.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print('Seven current bodies/source predicates authenticated; no actual selection release.')
