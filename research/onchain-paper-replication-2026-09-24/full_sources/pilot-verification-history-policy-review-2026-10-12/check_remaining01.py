from pathlib import Path
import ast,runpy,json
C=Path('research/onchain-paper-replication-2026-09-24/full_sources/pilot-verification-history-policy-candidate-2026-10-12');ns=runpy.run_path(str(C/'check01.py'));results=[]
f=ns['Fixture'](2)
try:
 f.admit();f.env['effective_budget']=lambda *a:0
 try:f.admit()
 except ValueError as e:assert 'budget exhausted' in str(e)
 else:raise AssertionError('warm budget bypass')
 results.append({'control':'warm current budget recomputed','pass':True})
finally:f.close()
f=ns['Fixture'](2)
try:
 f.admit();fatal=SystemExit('own proof fatal');f.verify_error=fatal
 try:f.admit()
 except BaseException as e:assert e is fatal and f.run not in f.env['_HISTORY'] and f.run not in f.env['_HISTORY_BUSY']
 else:raise AssertionError('warm own proof fatal bypass')
 results.append({'control':'warm own proof fatal preserved and cache invalidated','pass':True})
finally:f.close()
# Execute only the exact new completed-batch wrapper, no real driver/Run.
t=ast.parse((C/'compact_mcm_batched.py').read_text());compute=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='_compute');branch=next(n for n in ast.walk(compute) if isinstance(n,ast.If) and 'history_run.admission.spec' in ast.unparse(n.test));events=[]
class Run:
 admission=ns['N'](spec={'historical_claim_verification':{'format':'bounded-claims-v2'}})
 def _check_source(self,**kw):assert kw=={'force_history':True};events.append('audit')
env={'history_run':Run(),'post_batch':lambda *a:events.append('prior_post')};exec(compile(ast.Module(body=[branch],type_ignores=[]),'actual-new-post-batch','exec'),env);env['post_batch'](None,0,None,None);assert events==['audit','prior_post'];fatal=KeyboardInterrupt('audit failed');env['history_run']._check_source=lambda **kw:(_ for _ in ()).throw(fatal);events.clear()
try:env['post_batch'](None,0,None,None)
except BaseException as e:assert e is fatal and not events
else:raise AssertionError('forced audit failure did not stop post_batch')
results.append({'control':'completed batch forces before original callback; fatal suppresses callback','pass':True})
# Explicit startup path must satisfy declared frontier bounds as selected path.
f=ns['Fixture'](2)
try:
 f.env['_HISTORY_MAX_RUNS']=1
 try:f.env['_history_prior'](None,f.root,'gate','own','source','source',f.raw,f.policy,False)
 except ValueError:ok=True
 else:ok=False
 results.append({'control':'selected startup enforces finite frontier bound','pass':ok})
finally:f.close()
print(json.dumps(results,indent=2));assert all(x['pass'] for x in results)
