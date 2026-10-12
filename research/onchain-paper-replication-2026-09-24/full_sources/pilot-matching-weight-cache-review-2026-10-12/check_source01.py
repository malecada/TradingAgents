from pathlib import Path
import ast,json,hashlib,difflib,types
R=Path(__file__).resolve().parents[4]
F=R/'research/onchain-paper-replication-2026-09-24/full_sources'
C=F/'pilot-matching-weight-cache-candidate-2026-10-12';I=F/'pilot-matching-weight-cache-integration-2026-10-12'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((C/'SOURCE_MANIFEST01.json').read_bytes());results={}
for row in m['files']+m['unchanged_source_pins']:
 p=R/row['path'];assert h(p)==row['sha256'] and p.stat().st_size==row['bytes'],str(p)
for row in m['targets']:
 a=(R/row['baseline']['path']).read_text();b=(R/row['candidate']['path']).read_text();name=Path(row['target']).name
 for x,y,suffix in ((a,b,'.diff'),(b,a,'.inverse.diff')):
  expected=''.join(difflib.unified_diff(x.splitlines(True),y.splitlines(True),fromfile='a/'+row['target'],tofile='b/'+row['target']))
  actual=(C/(name+suffix)).read_text()
  # Direction names may be reversed in published inverse; hunk payload is exact.
  assert actual.splitlines(True)[2:]==expected.splitlines(True)[2:],name+suffix
results['manifest_and_literal_inverse']='PASS'
tree=ast.parse((C/'matching_numeric_policy.py').read_text());nodes=[n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom))]
def fun(*a,**k):return True
np=types.SimpleNamespace()
for name in ('frombuffer','shares_memory','any','isfinite','abs','subtract','square','sum','negative','divide','exp','geterr','ndarray','dtype','float64','int64','bool_','empty','zeros','flatnonzero','multiply','add','repeat','all'):setattr(np,name,fun)
ker=types.SimpleNamespace(fill_agreement=fun,_immutable=fun,np=np);ann=types.SimpleNamespace(_reuse_runtime=fun,_nearest_rounding=fun)
ns={'MappingProxyType':types.MappingProxyType,'np':np,'kernel':ker,'annealing':ann,'phase_timing':types.SimpleNamespace(add_count=fun)}
exec(compile(ast.Module(body=nodes,type_ignores=[]),'candidate-policy','exec'),ns)
for mutation in ('identity','method_shadow','helper_replace','runtime_replace'):
 a=ns['NumericAgreementAdapter'](dict(ns['CACHE_POLICY']));a.current()
 if mutation=='identity':a._cache_owner=-1
 elif mutation=='method_shadow':a.snapshot=fun
 elif mutation=='helper_replace':old=ns['_feature_pin'];ns['_feature_pin']=fun
 else:old=ann._reuse_runtime;ann._reuse_runtime=lambda:True
 try:a.current()
 except ValueError:pass
 else:raise AssertionError(mutation+' accepted')
 if mutation=='helper_replace':ns['_feature_pin']=old
 if mutation=='runtime_replace':ann._reuse_runtime=old
results['actual_current_function_independent_refusals']='PASS (synthetic objects, no numerical imports)'
patch=json.loads((I/'RESERVATION_PATCH01.json').read_bytes())
def require(ok,msg):
 if not ok:raise ValueError(msg)
for row in patch['targets']:
 name=Path(row['target']).name;a=(I/('BASELINE_'+name)).read_text();b=(I/name).read_text()
 assert h(I/name)==row['candidate_sha256'] and h(I/('BASELINE_'+name))==row['baseline_sha256']
 assert a.count(row['literal_before'])==1 and a.replace(row['literal_before'],row['literal_after'])==b
 if name=='compact_mcm_batched.py':
  import textwrap
  code=compile(textwrap.dedent(row['literal_after']),'reservation-fragment','exec')
  for selected in (None,dict(ns['POLICY']),dict(ns['CACHE_POLICY'])):
   for funding in (751331316,784951283,784951284):
    numeric=dict(schema_version=1,max_buffer_bytes=524288000,edge_chunk=1024,max_output_bytes=227043316,max_numeric_bytes=funding)
    scope={'execution':{'numeric_kernel_policy':selected},'policy':{'numeric':numeric},'pairs':56760829,'matching_numeric_policy':types.SimpleNamespace(cache_reservation=ns['cache_reservation']),'require':require,'_numeric_policy':lambda e:None}
    try:exec(code,scope);accepted=True
    except ValueError:accepted=False
    assert accepted==(selected!=dict(ns['CACHE_POLICY']) or funding>=784951284),(selected,funding)
results['reservation_literal_and_funding_boundary']='PASS'
# Execute only the exact appended constructor statement with synthetic already-owned cleanup.
t=ast.parse((C/'matching_immutable_session.py').read_text());cl=next(n for n in t.body if isinstance(n,ast.ClassDef));ctor=next(n for n in cl.body if isinstance(n,ast.FunctionDef) and n.name=='__init__');tail=ctor.body[-1]
calls=[];fatal=KeyboardInterrupt('selected setup fatal')
def fail(a):raise fatal
obj=types.SimpleNamespace(_numeric_adapter=object(),_normalizer_cleanup=lambda:calls.append('cleanup'))
try:exec(compile(ast.Module(body=[tail],type_ignores=[]),'actual-constructor-tail','exec'),{'self':obj,'matching_numeric_policy':types.SimpleNamespace(cache_selected=fail)})
except BaseException as caught:assert caught is fatal
results['constructor_tail_fatal_cleanup']={'expected_cleanup_calls':1,'actual_cleanup_calls':len(calls),'decision':'PASS' if calls==['cleanup'] else 'RED'}
print(json.dumps(results,indent=2))
assert calls==['cleanup'],'new constructor tail skips owned backend cleanup on fatal'
