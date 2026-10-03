"""Static dated-source graph. Never imports selected package/numerical modules."""
import ast,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];FULL=HERE.parent
OLD=FULL/'neural-cold-feature-handoff-proof-source-composition01-2026-10-03'
CORRECT=FULL/'imported-source-cleanup-composition-correction01-2026-10-03/compact_mcm.py'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def scalar(node,env):
 if isinstance(node,ast.Constant) and type(node.value) in (str,int):return node.value
 if isinstance(node,ast.Name):return env[node.id]
 if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Div):return Path(scalar(node.left,env))/scalar(node.right,env)
 if isinstance(node,ast.Attribute) and node.attr in ('parent','parents'):return getattr(scalar(node.value,env),node.attr)
 if isinstance(node,ast.Subscript):return scalar(node.value,env)[scalar(node.slice,env)]
 if isinstance(node,ast.Call):
  if isinstance(node.func,ast.Name) and node.func.id=='Path' and len(node.args)==1:return Path(scalar(node.args[0],env))
  if isinstance(node.func,ast.Attribute) and node.func.attr=='resolve' and not node.args:return scalar(node.func.value,env).resolve()
 raise ValueError('not a static path expression')
def edges(target,raw):
 tree=ast.parse(raw);env={'__file__':str(ROOT/target),'HERE':(ROOT/target).parent,'ROOT':ROOT};found=set();calls=[]
 for node in tree.body:
  if isinstance(node,ast.Assign):
   try:v=scalar(node.value,env)
   except (ValueError,KeyError,TypeError,AttributeError,IndexError):continue
   for t in node.targets:
    if isinstance(t,ast.Name):env[t.id]=v
 for node in ast.walk(tree):
  values=[]
  if isinstance(node,ast.Constant) and type(node.value) is str and node.value.endswith('.py') and node.value.startswith('research/'):values=[ROOT/node.value]
  if isinstance(node,ast.BinOp):
   try:v=scalar(node,env)
   except (ValueError,KeyError,TypeError,AttributeError,IndexError):pass
   else:
    if isinstance(v,Path) and v.suffix=='.py':values.append(v)
  if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='spec_from_file_location':
   try:value=scalar(node.args[1],env)
   except (ValueError,KeyError,TypeError,AttributeError,IndexError):calls.append({'line':node.lineno,'expression':ast.unparse(node.args[1]),'static':False})
   else:
    values.append(Path(value));calls.append({'line':node.lineno,'expression':ast.unparse(node.args[1]),'static':True,'target':str(Path(value).relative_to(ROOT))})
  for value in values:
   value=value.resolve()
   if not value.is_relative_to(ROOT) or not value.is_file():raise ValueError('external declared source absent/escaped: '+str(value))
   if 'full_sources' in value.parts:found.add(str(value.relative_to(ROOT)))
 return sorted(found),calls

def discover():
 old=json.loads((OLD/'source_inventory01.json').read_bytes());rows={r['target']:{k:v for k,v in r.items() if k!='snapshot'} for r in old['source_inventory']};pin='6673fa484f37c0c3556c3d158035bb0c7f1db8f4a9f834ca50374c57c1e21b81';assert sha(CORRECT.read_bytes())==pin
 target='tradingagents/research/onchain_replication/compact_mcm.py';rows[target].update(origin=str(CORRECT.relative_to(ROOT)),sha256=pin,bytes=CORRECT.stat().st_size,git_commit=None,git_path=None)
 pending=sorted(n for n in rows if n.endswith('.py'));done=set();graph={};dynamic={}
 while pending:
  target=pending.pop(0)
  if target in done:continue
  done.add(target);row=rows[target];raw=(ROOT/row['origin']).read_bytes();assert sha(raw)==row['sha256']
  outgoing,calls=edges(target,raw);graph[target]=outgoing;dynamic[target]=calls
  for name in outgoing:
   if name not in rows:
    p=ROOT/name;b=p.read_bytes();assert len(b)<=4194304
    rows[name]={'target':name,'origin':name,'sha256':sha(b),'bytes':len(b),'git_commit':None,'git_path':None};pending.append(name)
 return rows,graph,dynamic
if __name__=='__main__':
 rows,graph,dynamic=discover();out={'source_count':len(rows),'external_count':sum(n.startswith('research/') for n in rows),'added':sorted(set(rows)-{r['target'] for r in json.loads((OLD/'source_inventory01.json').read_bytes())['source_inventory']}),'dynamic_unresolved':[{'source':n,**c} for n,calls in dynamic.items() for c in calls if not c['static']]};print(json.dumps(out,indent=2))
