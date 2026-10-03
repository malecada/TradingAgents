"""Interpret source-path declarations only; no selected module is imported.

Module proxies represent source names, never runtime/Owner/graph authority.
Only literal path operations, finite containers/comprehensions, dynamic-loader
path arguments and actual required_sources function expressions are evaluated.
"""
import ast
from pathlib import Path
from discover_source01 import ROOT
class Symbols:
 def __init__(self,rows):self.rows=rows;self.modules={};self.functions=[]
 def module(self,path):
  path=str(Path(path).relative_to(ROOT)) if Path(path).is_absolute() else str(path)
  if path not in self.rows:raise ValueError('source declaration missing: '+path)
  if path not in self.modules:self.modules[path]=Module(self,path)
  return self.modules[path]
class Module:
 def __init__(self,world,path):
  self.world=world;self.path=path;self.tree=ast.parse((ROOT/world.rows[path]['origin']).read_bytes());self.cache={'__file__':str(ROOT/path),'Path':Path,'set':set,'tuple':tuple,'str':str,'sorted':sorted,'frozenset':frozenset};self.active=set();self.before=len(self.tree.body);self.values={}
 def __getattr__(self,name):return self.get(name)
 def evaluate(self,node,local=None):
  local={} if local is None else local
  e=lambda n:self.evaluate(n,local)
  if isinstance(node,ast.Constant):return node.value
  if isinstance(node,ast.Name):return local[node.id] if node.id in local else self.get(node.id)
  if isinstance(node,ast.Attribute):return getattr(e(node.value),node.attr)
  if isinstance(node,ast.Subscript):return e(node.value)[e(node.slice)]
  if isinstance(node,ast.BinOp):
   if isinstance(node.op,ast.Div):return Path(e(node.left))/e(node.right)
   if isinstance(node.op,ast.BitOr):return e(node.left)|e(node.right)
  if isinstance(node,(ast.Tuple,ast.List,ast.Set)):
   values=[e(x) for x in node.elts];return tuple(values) if isinstance(node,ast.Tuple) else set(values) if isinstance(node,ast.Set) else values
  if isinstance(node,(ast.GeneratorExp,ast.SetComp,ListComp)):
   if len(node.generators)!=1 or node.generators[0].ifs:raise ValueError('nonfinite source declaration')
   g=node.generators[0]
   if not isinstance(g.target,ast.Name):raise ValueError('source binding pattern unsupported')
   values=[self.evaluate(node.elt,local|{g.target.id:v}) for v in e(g.iter)]
   return set(values) if isinstance(node,ast.SetComp) else values
  if isinstance(node,ast.Call):
   spelling=ast.unparse(node.func)
   if spelling.endswith('spec_from_file_location') or spelling in ('_load','load'):return self.world.module(e(node.args[1]))
   if spelling.endswith('module_from_spec'):return e(node.args[0])
   if spelling in ('Path','set','tuple','str','sorted','frozenset'):return self.get(spelling)(*[e(x) for x in node.args])
   if isinstance(node.func,ast.Attribute) and node.func.attr in ('resolve','relative_to'):
    value=e(node.func.value)
    if not isinstance(value,Path):raise ValueError('path declaration receiver differs')
    return getattr(value,node.func.attr)(*[e(x) for x in node.args])
   raise ValueError('source declaration call not allowed: '+spelling)
  raise ValueError('source declaration unsupported: '+ast.dump(node))
 def get(self,name):
  if name in self.cache:return self.cache[name]
  key=(name,self.before)
  if key in self.values:return self.values[key]
  if key in self.active:raise ValueError('recursive source declaration '+self.path+':'+name)
  self.active.add(key);before=self.before;result=None;found=False
  try:
   if name=='_api' and self.path.endswith('/compact_native_features.py'):
    value=lambda:self.world.module(self.get('NATIVE'));self.cache[name]=value;return value
   for i,node in enumerate(self.tree.body[:before]):
    if isinstance(node,ast.ImportFrom) and (node.level or node.module and node.module.startswith('tradingagents')):
     for alias in node.names:
      if (alias.asname or alias.name)!=name:continue
      if node.level:
       parent=Path(self.path).parent
       for _ in range(node.level-1):parent=parent.parent
       base=parent.joinpath(*(node.module.split('.') if node.module else []))
      else:base=Path(*node.module.split('.'))
      candidate=str(base/alias.name)+'.py'
      if candidate in self.world.rows:value=self.world.module(candidate);self.cache[name]=value;return value
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets):
     # SOURCES may deliberately be extended by a later top-level assignment.
     self.before=i
     try:result=self.evaluate(node.value);found=True
     finally:self.before=before
    if isinstance(node,ast.FunctionDef) and node.name==name and name=='required_sources':
     env=Lazy(self);env.update({'__builtins__':{},'Path':Path,'set':set,'str':str})
     exec(compile(ast.Module(body=[node],type_ignores=[]),self.path,'exec'),env)
     self.cache[name]=env[name];self.world.functions.append(self.path+':required_sources')
   if found:self.values[key]=result;return result
   if name in self.cache:return self.cache[name]
   raise AttributeError(self.path+':'+name)
  finally:self.active.remove(key);self.before=before
class Lazy(dict):
 def __init__(self,module):super().__init__();self.module=module
 def __missing__(self,key):value=self.module.get(key);self[key]=value;return value
ListComp=ast.ListComp
