from pathlib import Path
import ast,json,hashlib,types,difflib
R=Path(__file__).resolve().parents[4];F=R/'research/onchain-paper-replication-2026-09-24/full_sources';C=F/'pilot-matching-weight-cache-candidate-2026-10-12'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((C/'SOURCE_MANIFEST03.json').read_bytes())
assert h(C/'SOURCE_MANIFEST03.json')=='706416be05370f50bd6eb193c0210419f11d2a06e97b99ceacf5e5874358e759'
for row in m['files']:
 p=R/row['path'];assert h(p)==row['sha256'] and p.stat().st_size==row['bytes'],str(p)
for name in ('matching_numeric_policy.py','matching_immutable_session.py','numeric_harness.py','numeric_checks01.py','benchmark01.py','static_check01.py'):
 a=(C/'iteration01'/name).read_text();b=((C/'iteration02'/name) if name in ('matching_numeric_policy.py','static_check01.py') else C/name).read_text()
 for x,y,suffix in ((a,b,'.diff'),(b,a,'.inverse.diff')):
  expected=''.join(difflib.unified_diff(x.splitlines(True),y.splitlines(True))).splitlines(True)[2:]
  assert (C/('AMENDMENT02_'+name+suffix)).read_text().splitlines(True)[2:]==expected,name+suffix
s=ast.parse((C/'matching_immutable_session.py').read_text());cls=next(n for n in s.body if isinstance(n,ast.ClassDef));ctor=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
tail=ast.Module(body=ctor.body[-2:],type_ignores=[]);code=compile(tail,'actual-amended-constructor-tail','exec')
for mode in ('mutating_selector_fatal','install_fatal','captured_release','default'):
 calls=[];primary=KeyboardInterrupt('original')
 def prior():calls.append('backend')
 class Session(types.SimpleNamespace):
  def __setattr__(self,k,v):
   if mode=='install_fatal' and k=='_normalizer_cleanup' and hasattr(self,k):raise primary
   super().__setattr__(k,v)
 obj=Session(_normalizer_cleanup=prior,_numeric_adapter=object())
 def selected(a):
  if mode=='mutating_selector_fatal':
   obj._normalizer_cleanup=lambda:calls.append('wrong replacement')
   raise primary
  return mode!='default'
 policy=types.SimpleNamespace(cache_selected=selected,_cache_release=lambda a:calls.append('cache'))
 try:exec(code,{'self':obj,'matching_numeric_policy':policy})
 except BaseException as caught:
  assert mode in ('mutating_selector_fatal','install_fatal') and caught is primary and calls==['backend'],mode
 else:
  assert mode in ('captured_release','default')
  policy._cache_release=lambda a:calls.append('wrong replacement')
  obj._normalizer_cleanup()
  assert calls==(['cache','backend'] if mode=='captured_release' else ['backend']),mode
# Original session AST exactly after removing only the new guarded two-statement tail.
ctor.body=ctor.body[:-2]
assert ast.dump(s)==ast.dump(ast.parse((C/'BASELINE_matching_immutable_session.py').read_text()))
p=ast.parse((C/'matching_numeric_policy.py').read_text());fs={n.name:n for n in p.body if isinstance(n,ast.FunctionDef)}
domain=ast.unparse(fs['_cache_domain']);fill=ast.unparse(fs['_cache_fill'])
assert all(x in domain for x in ('kernel._immutable','np.geterr','np.shares_memory','np.any'))
assert all(x not in domain for x in ('np.isfinite','np.abs','left[il]','right[ir]'))
assert fill.index('_feature_current(left')<fill.index('missing =')
assert fill.index('kernel.fill_agreement')<fill.index('weights = np.empty(total')<fill.index('adapter._cache_valid[locations] = True')<fill.index('out[:count]')<fill.index('progress[0]')
text=(C/'numeric_harness.py').read_text();assert 'engine.result(' not in text and 'engine.score_only(' in text
assert text.index('start=time.perf_counter()')<text.index('state=engine.create(')
assert text.index('engine.close(state);state=None')<text.index('elapsed=time.perf_counter()-start')
assert text.count('edge_cache_policy=dict(ann.ADAPTIVE_EDGE_POLICY)')==2
assert 'default=1000000' in (C/'benchmark01.py').read_text()
# The only policy03 source delta moves existing refusal ahead of cache parse.
a=(C/'iteration02/matching_numeric_policy.py').read_text();b=(C/'matching_numeric_policy.py').read_text()
for x,y,suffix in ((a,b,'.diff'),(b,a,'.inverse.diff')):
 expected=''.join(difflib.unified_diff(x.splitlines(True),y.splitlines(True))).splitlines(True)[2:]
 assert (C/('AMENDMENT03_matching_numeric_policy.py'+suffix)).read_text().splitlines(True)[2:]==expected
cl=next(n for n in p.body if isinstance(n,ast.ClassDef));current=next(n for n in cl.body if isinstance(n,ast.FunctionDef) and n.name=='current')
ns={'kernel':types.SimpleNamespace(np=object()),'CACHE_POLICY':{'format':'bounded-numpy-agreement-c05-v2'},'_cache_current':lambda a:(_ for _ in ()).throw(AssertionError('cache parsed before identity refusal'))}
exec(compile(ast.Module(body=[current],type_ignores=[]),'actual-current','exec'),ns)
for bad in (None,42,(('format','bounded-numpy-agreement-c05-v2'),)):
 obj=types.SimpleNamespace(policy=bad,_pin=object(),_numpy=ns['kernel'].np)
 try:ns['current'](obj)
 except ValueError as e:assert str(e)=='numeric adapter changed'
 else:raise AssertionError('changed policy accepted')
print(json.dumps({'result':'PASS','amendment_hashes_and_inverses':True,'constructor_controls':['mutating selector preserves captured backend cleanup and fatal','closure installation fatal releases backend','successful closure retains captured original release','default retains backend cleanup'],'session_default_ast':True,'immutable_hit_miss_order':True,'hook_timing_sparse_scoring_budget':True,'numerical_imports':False},indent=2))
