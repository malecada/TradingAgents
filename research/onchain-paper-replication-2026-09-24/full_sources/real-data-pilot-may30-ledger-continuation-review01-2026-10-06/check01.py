from pathlib import Path
import ast,hashlib,importlib.util,json,textwrap,sys
H=Path(__file__).resolve().parent;R=H.parents[3];S=H.parent/'real-data-pilot-may30-ledger-continuation-handoff01-2026-10-06';C=S/'candidate';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(S/'MANIFEST01.json')=='f279b7c11c011e147b4f2f6d068c6baa8046504a72d00097eccd87dfdd0bbf5c'
for p,h in json.loads((S/'MANIFEST01.json').read_text())['files'].items():assert sha(S/p)==h
v=json.loads((S/'SCIENTIFIC_INVERSE01.json').read_text());base=(R/v['baseline']).read_text();assert sha(R/v['baseline'])==v['baseline_sha256'];start=base.index("        observed=db.execute('SELECT DISTINCT asset,week FROM events ORDER BY asset,week').fetchall()")
block=textwrap.dedent(base[start:]).replace(v['literal_edit']['before'],v['literal_edit']['after']);tree=ast.parse((C/'weekly_retained_ledger.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef));assert ast.dump(ast.Module(body=fn.body,type_ignores=[]))==ast.dump(ast.parse(block))
v=json.loads((S/'DISPATCH_INVERSE01.json').read_text());src=(R/v['baseline']).read_text();assert sha(R/v['baseline'])==v['baseline_sha256']
for e in v['edits']:assert src.count(e['before'])==1;src=src.replace(e['before'],e['after'])
assert src==(C/'graph_production.py').read_text()
sp=importlib.util.spec_from_file_location('metadata_only',C/'graph_ledger_continuation.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
p=json.loads((S/'PLAN_DRAFT01.json').read_text())
for change in ({},{'new_experiment_id':m.OLD},{'new_experiment_id':'synthetic-schema-only'},{'new_experiment_id':'synthetic-schema-only','ledger':dict(p['ledger'],sha256='a'*64)}):
 q=dict(p,**change)
 try:m.plan_check(q)
 except ValueError:pass
 else:raise AssertionError('missing mandatory binding accepted')
# Actual recovery predicate isolated from producer: no ResearchRun/Owner constructed.
prod=next(n for n in ast.parse((C/'graph_ledger_continuation.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='produce')
check=next(n for n in prod.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and any(isinstance(a,ast.Constant) and a.value=='actual independently reviewed ledger recovery required' for a in n.value.args))
for recovery in ({},{'decision':'accepted'},{'decision':'accepted','ledger_byte_recovery':False}):
 try:exec(compile(ast.Module(body=[check],type_ignores=[]),'recovery_predicate','exec'),{'need':m.need,'recovery':recovery,'OLD':m.OLD,'p':p})
 except ValueError:pass
 else:raise AssertionError('absent actual recovery accepted')
assert not any(k in sys.modules for k in ['sqlite3','numpy','torch'])
print('PASS immutable source pins; original scientific AST/default inverse; unknown/fresh/recovery refusal; no database or scientific imports')
