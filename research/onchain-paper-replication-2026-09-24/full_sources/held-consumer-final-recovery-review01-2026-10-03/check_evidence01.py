import ast,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parent;A=R.parent/'held-consumer-final-recovery-preparation01-2026-10-03';H=lambda b:hashlib.sha256(b).hexdigest()
e=json.loads((A/'SOURCE_EVIDENCE01.json').read_bytes())
for row in e['implementation_sources']:
 b=(A/row['path']).read_bytes();assert len(b)==row['bytes'] and H(b)==row['sha256']
for row in e['origins']:
 b=Path(row['path']).read_bytes();assert len(b)==row['bytes'] and H(b)==row['sha256']
assert (A/'owned_io.py').read_bytes()==Path(e['origins'][1]['path']).read_bytes()
original=ast.parse(Path(e['origins'][2]['path']).read_bytes());subset=ast.parse((A/'bounded_git01.py').read_bytes());defs={n.name:n for n in original.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
for node in subset.body:
 if isinstance(node,(ast.FunctionDef,ast.ClassDef)):assert ast.dump(node)==ast.dump(defs[node.name]),node.name
(R/'SOURCE_READBACK01.json').write_text(json.dumps({'source_evidence':e,'owned_io_exact_bytes':True,'bounded_git_exact_ast':True,'capsule_scan_archive_or_history_lookup_performed':False},indent=2,sort_keys=True)+'\n')
print('PASS exact IO origin bytes, bounded Git selected AST, all three origins and implementation hashes')
