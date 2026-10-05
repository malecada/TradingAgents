from pathlib import Path
import ast,hashlib,json,sys
D=Path(__file__).resolve().parent;F=D.parent;P=Path('tradingagents/research/onchain_replication');C=F/'real-data-pilot-model-entry-composition01-2026-10-05';h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert h(C/'MANIFEST01.json')=='685c890108acf6d3d51ab3846e9fe462a79297ce266a12c729c92ec0e2e89ffd'
m=json.loads((C/'MANIFEST01.json').read_text())
for r in m['members']:
 p=C/r['path'];assert h(p)==r['sha256'] and p.stat().st_size==r['bytes']
r=json.loads((C/'COMPOSITION01.json').read_text());caller=C/'candidate'/P/'real_pilot_import_caller.py'
assert h(caller)=='e3e5bd544d470e870780305a9ed3bfdb8b669c703a921a34baf9175552272593'
for b in r['baselines']:
 assert h(Path(b['manifest']))==b['manifest_sha256'] and h(Path(b['origin']))==b['sha256'];lines=caller.read_text().splitlines(True)
 for e in reversed(b['edits']):assert lines[e['new_start']:e['new_end']]==e['new'];lines[e['new_start']:e['new_end']]=e['old']
 assert ''.join(lines).encode()==Path(b['origin']).read_bytes()
assert h(C/'candidate'/P/'real_pilot_population.py')==r['helper']['sha256']==h(Path(r['helper']['path']))=='e4671b48754c8f56d989d1905e7803d8111c10334f1110ff07cfcc79a1fb45db'
for b in r['native_policy_reuse']:assert h(Path(b['path']))==b['sha256']
def fs(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
a=fs(C/'baseline/full-size-policy.py');b=fs(caller)
changed=[k for k in a if a[k]!=b[k]];assert set(changed)=={'validate_plan','execute'}
assert not {'numpy','torch','scipy','networkx'}&set(sys.modules)
print(json.dumps({'decision':'pass','composition_manifest_members':len(m['members']),'both_exact_parent_inverses':True,'helper_unchanged':True,'native_policy_bodies_reused':3,'changed_caller_functions':changed,'numerical_imports':False,'authority_or_native_execution':False},sort_keys=True,indent=2))
