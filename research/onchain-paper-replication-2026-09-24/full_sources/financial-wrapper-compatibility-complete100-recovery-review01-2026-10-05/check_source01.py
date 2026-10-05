"""Focused new-source/inverse checks; no receiver, restoration entry or genuine releases."""
from verify_capture01 import *
import ast,copy,importlib.util
P=F/'financial-wrapper-compatibility-complete100-outcome-recovery-preparation01-2026-10-05'
S=F/'financial-wrapper-compatibility-final-supplement-transport-preparation02-2026-10-05'
rd=Reader();manifest=json.loads(rd.read(P/'MANIFEST01.json','eee2281d5b23a4560dfd64ac7ec36ef05b76536908f867f6fca0eec37c3459fc'))
for r in manifest['members']:
 p=P/r['path'];rd.pin(p);rd.need(stat.S_IMODE(p.lstat().st_mode)==r['mode'],'author typed mode')
 if r['kind']=='file':rd.need(len(rd.read(p,r['sha256']))==r['bytes'],'author full declared body')
actual=[]
for root,dirs,files in os.walk(P,followlinks=False):
 for n in dirs+files:
  p=Path(root)/n;rd.need(not p.is_symlink(),'no author links');name=p.relative_to(P).as_posix()
  if name!='MANIFEST01.json':actual.append(name)
rd.need(sorted(actual)==sorted(r['path'] for r in manifest['members']),'entire sealed author population')
unchanged=[]
for n in ('caller_remote01.py','caller_flat01.py','cohort01.py','receipt01.py','watch01.py','utilities/recovery_pax01.py','utilities/owned_io.py','utilities/bounded_git01.py'):
 rd.need(rd.read(P/n)==rd.read(S/n),'accepted immutable dependency '+n);unchanged.append(n)
# Receiver template and exact extracted two flat functions retain their earlier bodies.
rd.need(rd.read(P/'recover.template01.py')==rd.read(S/'recover.template01.py'),'unchanged receiver template')
def funcs(b):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(b).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
a=funcs(rd.read(P/'flat_primitives01.py'));b=funcs(rd.read(S/'restore_bundle01.py'))
for n in a:rd.need(n in b and a[n]==b[n],'exact original primitive AST '+n)
# Import only stdlib metadata source, whose guarded entry is never called.
sys.path[:0]=[str(P),str(P/'utilities')]
spec=importlib.util.spec_from_file_location('reviewed_outcome01',P/'outcome01.py');O=importlib.util.module_from_spec(spec);spec.loader.exec_module(O)
c=O.context(rd.read(D/'CAPTURE01.json'))
rd.need([len(x) for x in O.LANES]==[7,7,6,6] and sorted(j for lane in O.LANES for j in lane)==list(range(26)),'disjoint exact four lanes')
refusals=[]
for i in range(4):
 q=json.loads(rd.read(P/('LANE%02d_DRAFT01.json'%(i+1))))
 try:O.selected_required(q,i,c)
 except ValueError as e:refusals.append({'lane':i,'result':type(e).__name__,'message':str(e)})
 else:raise AssertionError('null draft accepted')
# Exact extracted public loader and run predicates expose the ordinary freeze cycle.
source=rd.read(P/'outcome01.py').decode();loader=rd.read(P/'restore_bundle01.py').decode()
rd.need("ref=q['release']" in loader and "ref['sha256']" in loader and "'request_sha256':request_sha" in source,'actual request/release cyclic dependency')
q={'ordinary_opaque_payload':'no authority','release':None};initial=R.digest(R.encode(q));rel={'request_sha256':initial};q['release']={'name':'ordinary-release.json','sha256':R.digest(R.encode(rel))};actual=R.digest(R.encode(q))
rd.need(actual!=rel['request_sha256'],'adding release hash changes the formerly signed request')
rel['request_sha256']=actual;rd.need(R.digest(R.encode(rel))!=q['release']['sha256'],'updating request pin invalidates release reference')
rd.finish();result={'schema_version':1,'author_manifest_sha256':R.digest((P/'MANIFEST01.json').read_bytes()),'actual_source_sha256':R.digest(source.encode()),'declared_members':len(manifest['members']),'unchanged_dependencies':unchanged+['recover.template01.py'],'exact_extracted_AST':sorted(a),'lanes':[7,7,6,6],'draft_refusals':refusals,'source_disposition':'WITHHELD_FLAT_REQUEST_RELEASE_SELF_REFERENCE','witness':'ordinary request with release null signed; installing release reference changes request SHA; repairing release request SHA changes release SHA','author_conclusion_not_reused':True,'public_entries_executed':False,'checks':rd.checks}
(HERE/'SOURCE01_CHECKS.json').write_bytes(R.encode(result));print(json.dumps({'checks':rd.checks,'disposition':result['source_disposition']}))
