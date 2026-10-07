import ast, importlib.util, json, hashlib
from pathlib import Path
OUT=Path(__file__).resolve().parent;ROOT=Path.cwd()
def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
old=load(ROOT/'tradingagents/research/onchain_replication/archive_control_history.py','original_history')
new=load(OUT/'candidate/archive_control_history.py','candidate_history')
p={'schema_version':1,'format':new.FORMAT,'assumption':new.ASSUMPTION,'success_control_bytes':1024,'success_diagnostic_bytes':1024,'shard_bytes':4096,'full_interval_ms':10000,'max_stale_ms':60000,'max_callbacks_between_full':100}
class Clock:
 def __init__(self):self.t=0.
 def __call__(self):return self.t
rows=[]
def refusal(fn,text):
 try:fn()
 except ValueError as error:
  assert text in str(error),(text,str(error));return str(error)
 raise AssertionError('expected refusal '+text)
def case(name):
 c=Clock();i=new.Interval(p,c);calls=[]
 def audit():calls.append(c.t)
 i.check(audit,force=True)
 return c,i,calls,audit
def record(name,**values):rows.append({'case':name,'passed':True,**values})
c=Clock();i=old.Interval(p,c);calls=[];i.check(lambda:calls.append(c.t),force=True);c.t=317
reason=refusal(lambda:i.check(lambda:calls.append(c.t),force=True),'history audit stale');assert len(calls)==1 and i.failed
record('RED original forced boundary after idle',reason=reason,audit_calls=len(calls))
for consumer in ('dispatch._outer','reservation._evidence'):
 c,i,calls,audit=case(consumer);c.t=317;i.check(audit,force=True)
 assert calls==[0.,317] and i.last==317 and i.observed==317 and i.calls==0 and not i.failed
 c.t=317.001;i.check(audit);assert len(calls)==2
 record('GREEN '+consumer+' forced audit then sampled')
c,i,calls,audit=case('sampled');c.t=60
refusal(lambda:i.check(audit),'history audit stale');assert len(calls)==1 and i.failed and i.last==0
refusal(lambda:i.check(audit,force=True),'history audit poisoned');assert len(calls)==1
record('sampled exact 60 seconds stale never audits and forced retry stays poisoned')
for duration in (60.,60.001):
 c,i,calls,audit=case('slow');c.t=317
 def slow():calls.append(c.t);c.t+=duration
 refusal(lambda:i.check(slow,force=True),'expired during check');assert i.failed and i.last==0
 record('forced duration rejected',duration=duration)
c,i,calls,audit=case('near');c.t=317
# Full successful audit just below the unchanged strict duration limit.
def near():calls.append(c.t);c.t+=59.999
i.check(near,force=True);assert i.last==c.t and not i.failed
record('forced duration below 60 accepted')
c,i,calls,audit=case('sampledslow');c.t=59
# Nonforced full callback retains the ORIGINAL observation origin.
def over():calls.append(c.t);c.t+=1
refusal(lambda:i.check(over),'expired during check');assert i.failed and i.last==0
record('nonforced audit cannot renew old observation past 60')
for mode in ('backward-entry','backward-audit','nonfinite-entry','nonfinite-audit','policy','clock','audit-exception'):
 c,i,calls,audit=case(mode);c.t=317
 if mode=='backward-entry':c.t=-1
 if mode=='nonfinite-entry':c.t=float('nan')
 if mode=='policy':i.p['max_stale_ms']=61000
 if mode=='clock':i.clock=lambda:317
 def callback():
  calls.append(c.t)
  if mode=='backward-audit':c.t=316
  if mode=='nonfinite-audit':c.t=float('nan')
  if mode=='audit-exception':raise ValueError('actual audit failure')
 refusal(lambda:i.check(callback,force=True),{'backward-entry':'backward','backward-audit':'backward','nonfinite-entry':'finite','nonfinite-audit':'backward','policy':'replaced','clock':'replaced','audit-exception':'actual audit failure'}[mode]);assert i.failed and i.last==0
 record('sticky refusal '+mode)
# Real bounded local control journals, no fake Run/Owner/admission.
fixtures=OUT/'fixtures';fixtures.mkdir()
for mode in ('intact','closed-bytes','foreign-name','counter'):
 c=Clock();j=new.Journal(fixtures/mode,record_bytes=1024,total_bytes=8192,records=4,shard_bytes=1320)
 j.append('one.json',b'{"original":1}');j.append('two.json',b'{"original":2}')
 i=new.Interval(p,c);i.check(j.audit,force=True);c.t=317
 if mode=='closed-bytes':
  path=j._path(0);raw=path.read_bytes();path.write_bytes(raw.replace(b'original',b'changed!'));j.pins[0]=new.signature(path.lstat())
 if mode=='foreign-name':(j.root/'foreign').write_bytes(b'foreign')
 if mode=='counter':j.count+=1
 if mode=='intact':i.check(j.audit,force=True);assert i.last==317 and not i.failed
 else:refusal(lambda:i.check(j.audit,force=True),{'closed-bytes':'chain changed','foreign-name':'membership differs','counter':'history differs'}[mode]);assert i.failed and i.last==0
 record('real journal '+mode)
# Actual consumers keep passing their ORIGINAL complete audit callbacks; extract
# and execute just their literal invocation to test dispatch flag routing.
for filename,method,attr,callbackname in [('archive_dispatch.py','_outer','_history','_full_history'),('archive_owner_operations.py','_evidence','_history','_full_evidence')]:
 path=ROOT/'tradingagents/research/onchain_replication'/filename;tree=ast.parse(path.read_text())
 fn=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==method)
 node=next(n for n in ast.walk(fn) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='check' and isinstance(n.value.func.value,ast.Attribute) and n.value.func.value.attr==attr)
 assert ast.unparse(node)==f'self._history.check(self.{callbackname}, force=not sampled)'
 for sampled in (False,True):
  c,i,calls,audit=case(filename);c.t=317
  class Shell:pass
  shell=Shell();shell._history=i;setattr(shell,callbackname,audit)
  def invoke():exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),{'self':shell,'sampled':sampled})
  if sampled:refusal(invoke,'history audit stale');assert len(calls)==1
  else:invoke();assert len(calls)==2 and i.last==317
 record('actual consumer callsite routing '+filename)
print(json.dumps({'status':'passed','cases':rows,'count':len(rows),'scope':'synthetic original-source scheduler, real tiny control journal audits and extracted actual consumer invocation; no Run/Owner/claim/data/numerical execution'},sort_keys=True))
