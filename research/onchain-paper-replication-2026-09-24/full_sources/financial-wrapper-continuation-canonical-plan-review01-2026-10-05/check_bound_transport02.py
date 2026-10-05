"""Changed-context-only source review and literal actual bound-source readback."""
from pathlib import Path
import ast,json,sys
H=Path(__file__).resolve().parent;F=H.parent;T=F/'financial-wrapper-continuation-canonical-transport-preparation01-2026-10-05';OLD=F/'financial-wrapper-continuation-current-transport-preparation01-2026-10-05';B=F/'financial-wrapper-continuation-canonical-transport-bound01-2026-10-05';D=F/'financial-wrapper-continuation-canonical-delta-root01-2026-10-05'
sys.path.insert(0,str(F/'financial-wrapper-compatibility-complete100-recovery-review01-2026-10-05'))
from verify_capture01 import Reader,R
rd=Reader();mr=rd.read(T/'MANIFEST01.json','f1411431ff20a81403e5e31b7f48ae14e466347beeacb3eec9366fe5d002ae87');m=json.loads(mr)
for row in m['members']:
 if row['kind']=='file':rd.need(len(rd.read(T/row['path'],row['sha256']))==row['bytes'],'all exact frozen source/evidence bodies')
inverse=json.loads(rd.read(T/'SOURCE_INVERSE01.json'));unchanged=[]
for name,pins in inverse['unchanged'].items():
 rd.need(rd.read(T/name,pins['candidate']['sha256'])==rd.read(OLD/name,pins['original']['sha256']),'entire previously accepted immutable primitive/template equality');unchanged.append(name)
rd.need(len(unchanged)==12,'exact unchanged dependency denominator')
old=rd.read(OLD/'outcome01.py').decode();new=rd.read(T/'outcome01.py').decode()
a='Exact current continuation incremental capture and all declared closed source/review dependencies. Accepted old818 capsule bodies and407 Git basis are reused; five current inputs, eleven Parent bodies, two proof bodies and nine Git payloads are retained. No claim is started; full current recovery still requires independent actual composition.'
b='Exact current continuation incremental capture and all declared closed source/review dependencies. Accepted complete capsule and416 Git basis are reused; two corrected metadata bodies, six new Git objects and the complete actual canonical Parent/proof population are retained. No claim is started; full current recovery still requires independent actual composition.'
changes=[("CAPTURE='8f9ef845c73b33076b4a81c4816e2d38528570a497706732f6a7c6ce0eb9d146'",'CAPTURE=None'),('financial-wrapper-continuation-current-transport-preparation01-2026-10-05','financial-wrapper-continuation-canonical-delta-root01-2026-10-05'),('664e2ca5fa11d6640ab79f64c5aa222aeb3a9128','d4c81c0961342bfe4c5771aabbef1d46a14cffb8'),('continuation-current','continuation-canonical'),('CONTINUATION_CURRENT','CONTINUATION_CANONICAL'),('capture_increment01.py','bind_capture01.py'),(a,b)]
expected=old
for x,y in changes:rd.need(x in expected,'declared changed-context seam present');expected=expected.replace(x,y)
# Original review01's blanket context-name substitution also changed the
# deliberately unchanged capture kind. Retain that failed harness/output;
# the actual context AST below must remain identical to the accepted source.
expected=expected.replace('continuation-canonical-incremental-byte-capture','continuation-current-incremental-byte-capture')
rd.need(expected==new,'complete outcome source contains only independently enumerated context changes')
for name in ('bind_entry01.py','space01.py'):
 original=rd.read(OLD/name).decode();candidate=rd.read(T/name).decode();rd.need(original.replace('continuation-current','continuation-canonical').replace('CONTINUATION_CURRENT','CONTINUATION_CANONICAL')==candidate,'complete exact root/status substitution only')
nf={n.name:n for n in ast.parse(new).body if isinstance(n,ast.FunctionDef)};of={n.name:n for n in ast.parse(old).body if isinstance(n,ast.FunctionDef)}
for name in ('context','expected_required','request_core_sha256'):rd.need(ast.dump(nf[name])==ast.dump(of[name]),'unchanged exact core/capture predicates')
helpers=ast.literal_eval(next(n.value for n in ast.parse(new).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='HELPERS' for t in n.targets)))
bound={}
for name in helpers:
 raw=rd.read(T/name);expected=raw.replace(b'CAPTURE=None',b"CAPTURE='2716035164b63c4149b7bb74d5e098ca08a40896bc1b4970dbe3a3246c3fe39f'") if name=='outcome01.py' else raw
 actual=rd.read(B/name);rd.need(actual==expected,'actual bound helper exact equality or single genuine capture literal');bound[name]={'sha256':R.digest(actual),'bytes':len(actual)}
for name in ('CAPTURE01.json','archive-manifest.json','increment.tar.gz'):
 actual=rd.read(B/name);rd.need(actual==rd.read(D/name),'three actual bound capture bytes unchanged');bound[name]={'sha256':R.digest(actual),'bytes':len(actual)}
rd.need({r['path'] for r in R.scan(B)['members'] if r['kind']=='file'}==set(bound),'complete actual bound source/body namespace')
rd.finish();value={'schema_version':1,'decision':'ACCEPTED_ACTUAL_CAPTURE_BOUND_CANONICAL_TRANSPORT_SOURCE_ONLY','source':'d4c81c0961342bfe4c5771aabbef1d46a14cffb8','author_manifest_sha256':R.digest(mr),'bound_root':str(B),'actual_bound_files':bound,'unchanged_accepted_dependencies':unchanged,'changed_source_scope':'fixed source/roots/status/capture/helper-name and truthful basis prose only; exact signing/currentness/limits/cleanup bodies preserved','watch_is_dependency_only_not_self_review':True,'capture_readback':{'path':str(H/'DELTA_CAPTURE_READBACK01.json'),'sha256':R.digest(rd.read(H/'DELTA_CAPTURE_READBACK01.json'))},'actual_remote_commit':None,'entry_release':None,'external_recovery':False,'numerical_authority':False,'checks':rd.checks,'read_bytes':rd.total};rd.finish();R.put(H/'BOUND_TRANSPORT_READBACK01.json',value);print(json.dumps({'readback_sha256':R.digest(R.encode(value)),'bound_outcome_sha256':bound['outcome01.py']['sha256'],'checks':rd.checks}))
