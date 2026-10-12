import ast,json,hashlib,difflib
from pathlib import Path
F=Path('research/onchain-paper-replication-2026-09-24/full_sources');H=F/'real-data-pilot-full24-preparation-increment01-2026-10-09';D=H/'full39outcome37';B=H/'full38outcome35';h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((D/'HELPERS_MANIFEST01.json').read_text())
for path,digest in m.items():assert h(Path(path))==digest,path
class Normalize(ast.NodeTransformer):
 def visit_Constant(self,n):
  return ast.Constant('<string>') if isinstance(n.value,str) else n
 def visit_Assign(self,n):
  if len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in {'baseline_pins','selected_pins','reused_pins','helper_names','closed_directory_roster'}:n.value=ast.Constant('<finite_scope>');return n
  return self.generic_visit(n)
 def visit_Dict(self,n):
  # Only finite descriptive selection fields; runtime fields remain compared.
  pairs=[(k,v) for k,v in zip(n.keys,n.values) if not(isinstance(k,ast.Constant) and k.value in {'exact_prior33_34_rows_reused','exact_prior36_rows_reused','prior36_baseline_pins','exact_prior36_baseline_reused','closed_scopes'})];n.keys=[k for k,v in pairs];n.values=[v for k,v in pairs];return self.generic_visit(n)
changes={};patch='';inverse=''
for tool in ['select','capture','recover']:
 a=(B/f'{tool}35.py').read_text();b=(D/f'{tool}37.py').read_text();aa=ast.parse(a);bb=ast.parse(b)
 assert ast.dump(Normalize().visit(aa))==ast.dump(Normalize().visit(bb)),tool
 patch+=''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=f'{tool}35.py',tofile=f'{tool}37.py'))
 inverse+=''.join(difflib.unified_diff(b.splitlines(True),a.splitlines(True),fromfile=f'{tool}37.py',tofile=f'{tool}35.py'))
 changes[tool]=h(D/f'{tool}37.py')
assert patch==(D/'LITERAL_PATCH01.diff').read_text()
assert inverse==(D/'LITERAL_INVERSE01.diff').read_text()
t=ast.parse((D/'select37.py').read_text());sel=next(n.value for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='selection' for x in n.targets));fields={ast.literal_eval(k):v for k,v in zip(sel.keys,sel.values)}
assert 'exact_prior33_34_rows_reused' not in fields
scope=json.loads((D/'TOOL_SCOPE01.json').read_text());assert ast.literal_eval(fields['closed_scopes'])==scope['closed_scopes'];assert ast.literal_eval(fields['exact_prior36_baseline_reused'])==scope['baseline_pins']
assert not (D/'SELECTION37.json').exists()
print(json.dumps({'status':'PASS','helper_manifest_sha256':h(D/'HELPERS_MANIFEST01.json'),'tool_sha256':changes,'accepted35_algorithm_ast_preserved':True,'literal_inverse':True,'stale_prior_field_removed':True,'qualification':'Finite data/namespace change only; no helper executed, no capture/remote/recovery proven.'},indent=2))
