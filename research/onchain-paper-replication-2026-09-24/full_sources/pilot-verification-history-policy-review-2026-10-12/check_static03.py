from pathlib import Path
import ast,json,hashlib,difflib
C=Path('research/onchain-paper-replication-2026-09-24/full_sources/pilot-verification-history-policy-candidate-2026-10-12')
# Final manifest check is supplied separately after amendment freeze.
results=[]
for name in ('admission.py','lifecycle.py','compact_mcm_batched.py'):
 a=(C/('BASELINE_'+name)).read_text();b=(C/name).read_text();path='tradingagents/research/'+('onchain_replication/' if name=='compact_mcm_batched.py' else '')+name
 initial=(C/'iteration01/admission.py').read_text() if name=='admission.py' else b
 assert ''.join(difflib.unified_diff(a.splitlines(True),initial.splitlines(True),fromfile='a/'+path,tofile='b/'+path))==(C/(name+'.diff')).read_text()
 assert ''.join(difflib.unified_diff(initial.splitlines(True),a.splitlines(True),fromfile='b/'+path,tofile='a/'+path))==(C/(name+'.inverse.diff')).read_text()
 if name=='admission.py':
  for index in (2,3,4):
   left=(C/f'iteration{index-1:02d}/admission.py').read_text();right=(C/f'iteration{index:02d}/admission.py').read_text() if index<4 else b
   for reverse in (False,True):
    label=f'AMENDMENT{index:02d}_admission.py'+('.inverse.diff' if reverse else '.diff');patch=(C/label).read_text();headers=patch.splitlines();x,y=(right,left) if reverse else (left,right)
    assert ''.join(difflib.unified_diff(x.splitlines(True),y.splitlines(True),fromfile=headers[0][4:],tofile=headers[1][4:]))==patch
 old=ast.parse(a);new=ast.parse(b)
 class Original(ast.NodeTransformer):
  def visit_FunctionDef(self,n):
   if n.name=='admit':
    n.args.kwonlyargs=n.args.kwonlyargs[:-2];n.args.kw_defaults=n.args.kw_defaults[:-2]
   if n.name=='_check_source':n.args.kwonlyargs=[];n.args.kw_defaults=[]
   return self.generic_visit(n)
  def visit_If(self,n):
   text=ast.unparse(n.test)
   if text.startswith('type(_force_history)') or text.startswith('type(force_history)'):return None
   if text=='history_seconds is None':return n.body
   if "'bounded-claims-v2'" in text and ('self.admission.spec' in text):return n.orelse
   if 'history_run.admission.spec' in text:return None
   return self.generic_visit(n)
  def visit_Assign(self,n):
   names=[x.id for x in n.targets if isinstance(x,ast.Name)]
   if names and (names[0] in ('history_policy','history_args','history_run') or (names[0]=='selected' and 'history_policy' in ast.unparse(n.value))):return None
   if any(isinstance(x,ast.Tuple) and any(isinstance(y,ast.Name) and y.id=='history_seconds' for y in x.elts) for x in n.targets):
    return next(x for x in ast.walk(old) if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id=='claim_workers' for y in x.targets))
   return self.generic_visit(n)
  def visit_Call(self,n):
   n=self.generic_visit(n);n.keywords=[k for k in n.keywords if not(k.arg is None and isinstance(k.value,ast.Name) and k.value.id=='history_args')];return n
 if name=='admission.py':
  # Remove only newly introduced module items; existing function names are exact.
  old_funcs={n.name for n in old.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
  new.body=[n for n in new.body if not(isinstance(n,ast.FunctionDef) and n.name.startswith('_history')) and not(isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id.startswith('_HISTORY') for t in n.targets)) and not(isinstance(n,(ast.Import,ast.ImportFrom)) and ast.dump(n) not in {ast.dump(x) for x in old.body if isinstance(x,(ast.Import,ast.ImportFrom))})]
 assert ast.dump(Original().visit(new))==ast.dump(old),name
 results.append({'source':name,'literal_inverse':True,'default_module_ast_restored':True})
benchmark=ast.parse((C/'benchmark01.py').read_text());calls=[ast.unparse(n.func) for n in ast.walk(benchmark) if isinstance(n,ast.Call)];assert not any(x.endswith('.admit') or x.endswith('.start') or x.endswith('._history_prior') for x in calls);assert 'module._history_scan' in calls
print(json.dumps({'status':'PASS','sources':results,'benchmark_calls_only_capability_free_history_scan':True,'benchmark_not_executed':True},indent=2))
