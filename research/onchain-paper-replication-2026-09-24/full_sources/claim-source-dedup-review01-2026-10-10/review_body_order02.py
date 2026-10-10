"""Actual per-body versus aggregate limit order; in-memory synthetic source text."""
import builtins,hashlib,importlib.util,json,os,resource,signal,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;C=P.with_name('claim-source-dedup-candidate01-2026-10-10')
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2));signal.alarm(15)
assert os.sched_getaffinity(0)=={3}
started=time.perf_counter_ns();original_import=builtins.__import__
def restricted(name,*a,**kw):
 assert name.split('.')[0] not in {'numpy','scipy','torch','ctypes'}
 return original_import(name,*a,**kw)
builtins.__import__=restricted
spec=importlib.util.spec_from_file_location('candidate_body_order',C/'verify.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
a=b'source-first'*17;b=b'b'*(v._GIT_BODY+1)
ha=b'a'*40+b' blob '+str(len(a)).encode()+b'\n';hb=b'b'*40+b' blob '+str(len(b)).encode()+b'\n'
metadata=ha+ha+hb;full=ha+a+b'\n'+ha+a+b'\n'+hb+b+b'\n';requests=b'c:a\nc:alias\nc:oversize\n'
assert len(full)<=v._GIT_BODY+128*v._GIT_PARTS
actual=v._git_transport;cases=[]
for firstwrong in (True,False):
 events=[]
 def transport(root,req,**kw):
  events.append({'metadata':bool(kw.get('_source_check')),'request_matches_original':req==requests})
  return metadata if kw.get('_source_check') else full
 v._git_transport=transport
 rows=[('a','c','0'*64 if firstwrong else hashlib.sha256(a).hexdigest()),('alias','c',hashlib.sha256(a).hexdigest()),('oversize','c','0'*64)]
 try:v._verify_source_flush(None,requests,rows)
 except ValueError as e:
  expected='registered source/charter/selection hash mismatch' if firstwrong else 'Git blob body ceiling exceeded'
  assert str(e)==expected and len(events)==2 and all(x['request_matches_original'] for x in events)
  cases.append({'first_hash_wrong':firstwrong,'exception':str(e),'events':events})
 else:raise AssertionError('oversize source accepted')
v._git_transport=actual
result={'checks':2,'logical_response_bytes':len(full),'actual_aggregate_cap':v._GIT_BODY+128*v._GIT_PARTS,'oversize_body_bytes':len(b),'actual_body_cap':v._GIT_BODY,'cases':cases,'elapsed_ns':time.perf_counter_ns()-started,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'actual_git_transport_used':False,'original_candidate_parser_used':True}
(P/'RESULT02.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
