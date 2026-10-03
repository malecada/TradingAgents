"""Independent exact static local-import and dependency readback; source only."""
import ast,hashlib,json,pathlib
D=pathlib.Path(__file__).resolve().parent;ROOT=D.parents[3]
man=json.loads((D/'MANIFEST01.json').read_text())
for row in man['dependencies']:
 raw=(ROOT/row['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256']
inv=json.loads((D/'source_inventory01.json').read_text());rows={r['target']:r for r in inv['source_inventory']};mods={k[:-3].replace('/','.') if not k.endswith('/__init__.py') else k[:-12].replace('/','.') for k in rows if k.endswith('.py')};edges=0;missing=[]
for target,row in rows.items():
 if not target.startswith('tradingagents/') or not target.endswith('.py'):continue
 package=target[:-3].replace('/','.');package=package.rsplit('.',1)[0]
 for node in ast.walk(ast.parse((ROOT/row['origin']).read_bytes())):
  if isinstance(node,ast.ImportFrom):
   if node.level:
    bits=package.split('.');base='.'.join(bits[:len(bits)-node.level+1]);base+='.'+node.module if node.module else ''
   else:base=node.module or ''
   if not base.startswith('tradingagents'):continue
   if base not in mods:missing.append([target,node.lineno,base])
   edges+=1
   if node.module is None:
    for alias in node.names:
     if base+'.'+alias.name not in mods:missing.append([target,node.lineno,base+'.'+alias.name])
  elif isinstance(node,ast.Import):
   for alias in node.names:
    if alias.name.startswith('tradingagents'):
     edges+=1
     if alias.name not in mods:missing.append([target,node.lineno,alias.name])
assert not missing,missing
print(json.dumps({'source_entries':len(rows),'package_entries':sum(k.startswith('tradingagents/') for k in rows),'static_local_import_statements':edges,'missing':missing,'qualification':'Static package import closure; selected dynamic helpers joined by dedicated admitted hash checks, not executed.'},sort_keys=True))
