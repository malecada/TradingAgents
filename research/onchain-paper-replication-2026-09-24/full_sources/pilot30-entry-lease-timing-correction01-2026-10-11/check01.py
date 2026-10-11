"""Finite real-scheduler clock model; no real Target/Owner or research execution."""
import ast,json,math
from pathlib import Path
ROOT=Path.cwd().resolve();H=Path(__file__).resolve().parent;P=ROOT/'tradingagents/research/onchain_replication'
def main():
 scope={};scheduler=P/'imported_authority_interval.py';exec(compile(scheduler.read_bytes(),str(scheduler),'exec'),scope)
 selected=json.loads((H.parent/'real-data-pilot-fixed13-metadata-successor01-2026-10-06/candidate/imported_authority_lease.json').read_bytes());assert selected['max_stale_ms']==60000
 Interval=scope['Interval']
 class Clock:
  def __init__(self):self.t=0.0
  def __call__(self):return self.t
  def advance(self,d):self.t+=d
 def start():
  c=Clock();i=Interval(selected,clock=c);events=[]
  i.validate(lambda:events.append('initial_full'),lambda:events.append('initial_finger'),lambda:events.append('initial_live'),boundary=True)
  return c,i,events
 cost=8.756164185004309;age=52.08589645799657
 c,i,events=start();c.advance(age)
 def full():events.append('full');c.advance(cost)
 try:i.validate(full,lambda:events.append('finger'),lambda:events.append('live'),boundary=True)
 except ValueError as e:
  red={'error':str(e),'notes':getattr(e,'__notes__',[]),'closed':i.closed,'full':i.full,'time':c.t};assert i.closed and i.full==0 and math.isclose(c.t,age+cost)
 else:raise AssertionError('original exact recorded age must expire')
 # A possible finite split only, NOT an attribution of real unmeasured phases.
 c,i,events=start();segments=[10.0,12.0,20.0,age-42.0]
 for index,duration in enumerate(segments):
  c.advance(duration)
  def full(index=index):events.append('full_phase_'+str(index));c.advance(cost)
  i.validate(full,lambda:events.append('finger'),lambda:events.append('live'),boundary=True)
 assert not i.closed and events.count('finger')==4 and all('full_phase_'+str(k) in events for k in range(4))
 green={'closed':i.closed,'full':i.full,'time':c.t,'segments':segments,'events':events}
 refusals={}
 for name,initial,callback in [('already_stale',60.000001,0.0),('indivisible_group',61.0,0.0),('callback_crosses_expiry',52.0,8.000001)]:
  c,i,events=start();c.advance(initial)
  def full():events.append('full');c.advance(callback)
  try:i.validate(full,lambda:events.append('finger'),lambda:events.append('live'),boundary=True)
  except ValueError as e:assert i.closed and i.full==0;refusals[name]={'error':str(e),'events':events,'full_unchanged':True}
  else:raise AssertionError(name)
 for role in ('live','full','finger'):
  c,i,events=start();c.advance(10);primary=RuntimeError('synthetic '+role+' authority refusal')
  def denied():raise primary
  callbacks={k:(denied if k==role else lambda:None) for k in ('live','full','finger')}
  try:i.validate(callbacks['full'],callbacks['finger'],callbacks['live'],boundary=True)
  except RuntimeError as e:assert e is primary and i.closed and i.full==0;refusals[role]={'primary_identity':True,'closed':True,'full_unchanged':True}
  else:raise AssertionError(role)
 old=ast.parse((P/'compact_mcm_batched.py').read_bytes());new=ast.parse((H/'compact_mcm_batched.py').read_bytes())
 helper=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='_entry_lease');assert any(isinstance(n,ast.ImportFrom) and n.module=='imported_authority_lease' for n in ast.walk(helper))
 delegate=next(n for n in ast.walk(helper) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='target_lease');assert len(delegate.keywords)==1 and delegate.keywords[0].arg=='boundary' and delegate.keywords[0].value.value is True
 new.body.remove(helper);produce=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='produce');block=next(n for n in produce.body if isinstance(n,ast.Try));extra=[n for n in block.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='_entry_lease'];assert len(extra)==3
 block.body=[n for n in block.body if n not in extra];assert ast.dump(old,include_attributes=False)==ast.dump(new,include_attributes=False)
 text=(H/'compact_mcm_batched.py').read_text();assert "normalization=_compiled_inputs(b['execution'],owner.bound._run)\n        _entry_lease(target,b['execution'])\n        owner.boundary();target.check()" in text
 helper_scope={};exec(compile(ast.Module(body=[helper],type_ignores=[]),'<entry helper>','exec'),helper_scope)
 # Inactive branches return before importing/delegating any genuine authority.
 helper_scope['_entry_lease'](None,{})
 class Plain:
  execution=None
 helper_scope['_entry_lease'](Plain(),{'compiled_normalization_policy':{}})
 result={'status':'PASS_FOCUSED_SYNTHETIC_SCHEDULER','recorded_age_RED':red,'hypothetical_segmented_GREEN':green,'refusals':refusals,'source_ast_inverse':True,'new_complete_boundaries':3,'inactive_route_noop':True,'scheduler_and_policy_unchanged':True,'qualification':'Clock/callback fixtures are synthetic, not fake genuine authority. Actual phase times and end-to-end success remain unmeasured; indivisible >60s work still refuses.'}
 (H/'RESULT01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({'status':result['status'],'RED_age':red['time'],'GREEN_explicit_split':True,'refusals':len(refusals),'AST_inverse':True}))
if __name__=='__main__':main()
