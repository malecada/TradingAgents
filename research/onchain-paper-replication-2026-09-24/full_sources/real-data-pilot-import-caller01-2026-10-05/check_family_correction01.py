"""One changed metadata predicate; no admission, arrays or numerical imports."""
import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

D=Path(__file__).resolve().parent
old=(D/'before-family-correction01/real_pilot_import_caller.py').read_text()
new=(D/'real_pilot_import_caller.py').read_text()
needle="ad.family['mechanism_id'] == KIND"
replacement="ad.family['mechanism_id'] == 'celik-sefer-transaction-graph-full-neural-replication'"
assert old.count(needle)==new.count(replacement)==1
assert new.replace(replacement,needle)==old
assert hashlib.sha256(old.encode()).hexdigest()=='26811202626f81431371fbc289d93699a33f4cbfe38005a515d0553bca677095'
fn=next(n for n in ast.parse(new).body if isinstance(n,ast.FunctionDef) and n.name=='admitted')
call=next(n.value for n in fn.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)
          and any(isinstance(a,ast.Constant) and a.value=='separate one-cell resource pilot admission required' for a in n.value.args))
expr=compile(ast.Expression(call.args[0]),'<actual family/cell predicate>','eval')
for family,cells,expected in [
 ('celik-sefer-transaction-graph-full-neural-replication',['one'],True),
 ('real-data-import-training-pilot-v1',['one'],False),
 ('celik-sefer-transaction-graph-full-neural-replication',['one','two'],False),
 ('celik-sefer-transaction-graph-full-neural-replication',['other'],False)]:
 result=eval(expr,{'__builtins__':{}},{'ad':SimpleNamespace(family={'mechanism_id':family},experiment={'cells':cells}),'p':{'cell_id':'one'}})
 assert result is expected
print(json.dumps({'status':'passed','source_sha256':hashlib.sha256(new.encode()).hexdigest(),
 'exact_inverse':True,'predicate_cases':4,'admission_executed':False,'numerical_imports':False}))
