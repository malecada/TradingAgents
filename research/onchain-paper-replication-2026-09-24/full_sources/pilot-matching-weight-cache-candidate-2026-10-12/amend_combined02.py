from pathlib import Path
import shutil
P=Path(__file__).resolve().parent;I=P/'iteration01';I.mkdir()
for name in ('matching_numeric_policy.py','matching_immutable_session.py','numeric_harness.py','benchmark01.py','SOURCE_MANIFEST01.json'):shutil.copy2(P/name,I/name)
p=P/'matching_numeric_policy.py';s=p.read_text();s=s.replace('    # Original selected helper checks are repeated even on an all-hit chunk.','    # Fresh structural/runtime domain; numeric row domain is proved by original\n    # successful miss evaluation and immutable pair pins for already-valid hits.')
s=s.replace("    a=left[il];b=right[ir]\n    return bool(np.isfinite(a).all() and np.isfinite(b).all()\n        and not np.any(np.abs(a)>256.) and not np.any(np.abs(b)>256.))",'    return True')
a=s.index('    if adapter._cache_pair is None:\n        pins=',s.index('def _cache_fill'))
b=s.index('    out[:count]=adapter._cache_weights[positions]',a)
s=s[:a]+'''    initial=adapter._cache_pair is None
    if initial:
        pins=(_feature_pin(left),_feature_pin(right))
        if any(pin is None for pin in pins):return None
    else:
        if np.shares_memory(out,adapter._cache_weights) or np.shares_memory(out,adapter._cache_valid):return False
    adapter._counts['index_bytes']+=16*count
    positions=il*len(right)+ir
    missing=None if initial else np.flatnonzero(~adapter._cache_valid[positions])
    misses=count if initial else len(missing)
    if misses:
        ml=il if initial else np.frombuffer(il[missing].tobytes(),dtype=np.int64)
        mr=ir if initial else np.frombuffer(ir[missing].tobytes(),dtype=np.int64)
        computed=np.empty(misses,dtype=np.float64)
        # Original helper validates actual miss rows BEFORE any initial cache
        # allocation or validity update. Refusal leaves out/progress untouched.
        if not kernel.fill_agreement(left,right,ml,mr,computed,0,misses):return False
        computed*=.5
    if initial:
        weights=np.empty(total,dtype=np.float64);valid=np.zeros(total,dtype=np.bool_)
        adapter._cache_weights=weights;adapter._cache_valid=valid
        adapter._cache_storage=(weights,valid);adapter._cache_pair=pins
        adapter._cache_storage_pins=tuple((a.dtype.str,tuple(a.shape),tuple(a.strides),a.nbytes,
            a.__array_interface__['data'][0],id(a.base)) for a in (weights,valid))
        adapter._counts.update(cache_reserved_bytes=reserved,cache_weight_bytes=weights.nbytes,
            cache_validity_bytes=valid.nbytes,cache_peak_retained_bytes=reserved)
        adapter._counts['cache_allocations']+=1;adapter._counts['cache_allocated_bytes']+=reserved
        phase_timing.add_count('cache_allocations',1)
        phase_timing.add_count('cache_allocated_bytes',reserved)
    if misses:
        locations=positions if initial else positions[missing]
        adapter._cache_weights[locations]=computed
        adapter._cache_valid[locations]=True
'''+s[b:];p.write_text(s)
p=P/'matching_immutable_session.py';s=p.read_text();a=s.index('        if matching_numeric_policy.cache_selected(');b=s.index('\n    def _edge_current',a);old=s[a:b];lines=old.splitlines(True)
# Capture acquired backend cleanup before the newly fallible selector/setup.
new='        prior_cleanup=self._normalizer_cleanup\n        try:\n'+''.join('    '+line if line.strip() else line for line in lines if line.strip()!='prior_cleanup=self._normalizer_cleanup')
new+='''        except BaseException as primary:
            try:prior_cleanup()
            except BaseException as cleanup:
                try:BaseException.add_note(primary,'numeric cleanup setup failed: '+repr(cleanup))
                except BaseException:pass
            raise
'''
s=s[:a]+new+s[b:];p.write_text(s)
p=P/'numeric_harness.py';s=p.read_text();a=s.index('def solve(');b=s.index('\ndef compare',a)
s=s[:a]+'''def solve(a,b,c,version,*,checkpoint=None,budget=1024):
 if type(budget) is not int or budget<=0:raise ValueError('positive original operation budget required')
 selected=dict(policy.CACHE_POLICY if version==2 else policy.POLICY)
 progress=[];counts=[];reloaded=False;totals=phase.PhaseTotals()
 state=session=None;start=time.perf_counter()
 try:
  with phase.activate(totals):
   state=engine.create(a,b,c,max_state_bytes=16*1024**2,hardening_buffer_bytes=4*1024**2)
   session=Session(a,b,c,engine=engine,annealing=ann,numeric_kernel_policy=selected,
       edge_cache_policy=dict(ann.ADAPTIVE_EDGE_POLICY))
   while state['phase']!='done':
    used=session.advance(state,max_operations=budget);inner=state['annealing']
    progress.append((used,state['phase'],inner['phase'],inner['cursor'],inner['iterations']))
    if checkpoint is not None and not reloaded and inner['iterations']>=2:
     pin=engine.save(state,checkpoint,a,b,c,max_checkpoint_bytes=16*1024**2)
     session.close();counts.append(session._numeric_adapter.snapshot());engine.close(state)
     state=engine.load(checkpoint,a,b,c,expected_sha256=pin,max_state_bytes=16*1024**2,hardening_buffer_bytes=4*1024**2)
     session=Session(a,b,c,engine=engine,annealing=ann,numeric_kernel_policy=selected,
         edge_cache_policy=dict(ann.ADAPTIVE_EDGE_POLICY));reloaded=True
   score=engine.score_only(state,a,b,c,max_buffer_bytes=4*1024**2)
   # Diagnostic copies only; no dense all-edge-product score computation.
   assignment=np.zeros(state['annealing']['M'].shape,dtype=np.int8)
   for u,i in state['hardening']['pairs']:assignment[u,i]=1
   result=ann.MatchResult(assignment,score.score,score.convergence,score.iterations,state['annealing']['M'].copy())
   session.close();counts.append(session._numeric_adapter.snapshot());session=None
   engine.close(state);state=None
  elapsed=time.perf_counter()-start
  return result,progress,{'adapter_lifetimes':counts,'phases':totals.snapshot(),'wall_seconds':elapsed,
      'timing_interval':'cold create + session + advances/hardening + production score_only + diagnostic copies + session/state cleanup',
      'operation_budget':budget,'checkpoint_reloaded':reloaded}
 finally:
  primary=sys.exception()
  for closer in ((session.close if session is not None else lambda:None),
                  (lambda:engine.close(state)) if state is not None else lambda:None):
   try:closer()
   except BaseException as error:
    if primary is None:primary=error
    else:
     try:BaseException.add_note(primary,'fixture cleanup failed: '+repr(error))
     except BaseException:pass
  if primary is not None and sys.exception() is None:raise primary
'''+s[b:];p.write_text(s)
p=P/'benchmark01.py';s=p.read_text().replace("p.add_argument('--config-sha256',required=True);args=p.parse_args()", "p.add_argument('--config-sha256',required=True);p.add_argument('--budget',type=int,default=1000000);args=p.parse_args()")
s=s.replace('old=solve(a,b,c,1);new=solve(a,b,c,2)','old=solve(a,b,c,1,budget=args.budget);new=solve(a,b,c,2,budget=args.budget)');p.write_text(s)
