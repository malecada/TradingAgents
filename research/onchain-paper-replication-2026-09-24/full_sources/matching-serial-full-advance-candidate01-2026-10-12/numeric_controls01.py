"""ROOT ONLY numerical fault/domain controls. Synthetic instrumentation, no authority."""
from pathlib import Path
import argparse,importlib.util,sys,json,hashlib
P=Path(__file__).resolve().parent

def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);parser.add_argument('--config-sha256',required=True);args=parser.parse_args()
 harness=P.parent/'pilot-matching-weight-cache-candidate-2026-10-12/numeric_harness.py'
 assert hashlib.sha256(harness.read_bytes()).hexdigest()=='fdc0940ca0b18d75cb933bbaa58c4a0fd38824b638f6ed09d0d1adc3ad3729e8'
 h=load(harness,'serial_fault_harness');s=load(P/'serial_advance.py','serial_fault_candidate');c=h.config(args.config,args.config_sha256)
 a,b=h.graph(16),h.graph(16,.031);n,m=len(a.node_ids),len(b.node_ids)
 def fresh():return h.ann.create(a,b,c,max_state_bytes=1024*1024)
 def same(x,y):
  for key in x:
   if key in h.ann.NAMES:assert x[key].tobytes()==y[key].tobytes(),key
   else:assert x[key]==y[key],key
 class Recorder:
  def __init__(self,fail=None):self.calls=[];self.fail=fail
  def lse(self,block,*,axis,keepdims,fallback):
   self.calls.append((block.shape,block.strides,axis,keepdims))
   if len(self.calls)==self.fail:raise KeyboardInterrupt('injected normalization fatal')
   return fallback(block,axis=axis,keepdims=keepdims)
 for failure in (None,1,2,3):
  states=[fresh(),fresh()];logs=[]
  for state,function in zip(states,(s.ORIGINAL,s.advance_checked)):
   recorder=Recorder(failure);error=None
   try:function(state,a,b,c,max_operations=1000000,normalizer=recorder,edge_cache_policy=dict(h.ann.ADAPTIVE_EDGE_POLICY))
   except KeyboardInterrupt as exc:error=(type(exc).__name__,exc.args)
   logs.append((recorder.calls,error))
  assert logs[0]==logs[1];same(*states)
 # Inject a scalar edge failure after the validated entry, solely as a synthetic
 # failure-prefix fixture. Runtime guard is instrumented here, never authority.
 original_agreement=h.ann.agreement;original_runtime=h.ann._reuse_runtime
 try:
  states=[fresh(),fresh()]
  for state,function in zip(states,(s.ORIGINAL,s.advance_checked)):
   calls=[0]
   def fail(x,y):
    calls[0]+=1
    if calls[0]==n*m+4:raise SystemExit('injected agreement fatal')
    return original_agreement(x,y)
   h.ann.agreement=fail;h.ann._reuse_runtime=lambda:True
   try:function(state,a,b,c,max_operations=1000000)
   except SystemExit as error:assert error.args==('injected agreement fatal',)
   else:raise AssertionError('fatal not propagated')
  same(*states)
 finally:h.ann.agreement=original_agreement;h.ann._reuse_runtime=original_runtime
 # Unsupported array subclass must return sentinel before numerical writes.
 class Subclass(h.np.ndarray):pass
 state=fresh();original=a.node_features
 object.__setattr__(a,'node_features',original.view(Subclass))
 try:assert s.try_advance_checked(state,a,b,c,max_operations=1000000) is None
 finally:object.__setattr__(a,'node_features',original)
 assert state['phase']=='nodes' and state['cursor']==0 and state['safe'] is True
 # Mutable graph features likewise delegate; no typed immutable proof shortcut.
 object.__setattr__(a,'node_features',original.copy())
 try:assert s.try_advance_checked(state,a,b,c,max_operations=1000000) is None
 finally:object.__setattr__(a,'node_features',original)
 print(json.dumps({'normalizer_call_and_fatal_controls':4,'edge_failure_prefix':True,'subclass_and_mutable_fallback':True,'scope':'synthetic only; no genuine authority'},sort_keys=True))
if __name__=='__main__':main()
