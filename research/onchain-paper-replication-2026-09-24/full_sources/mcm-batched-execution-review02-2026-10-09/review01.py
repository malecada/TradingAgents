import copy,hashlib,importlib.util,json,os,resource,signal,struct,sys
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(30)
R=Path.cwd();H=Path(__file__).resolve().parent;P=H.parent/'mcm-batched-execution02-2026-10-09';sys.path.insert(0,str(R));checks=[]
def ck(n,v):
 assert v,n
 checks.append(n)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(fn):
 spec=importlib.util.spec_from_file_location(fn,P/(fn+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
bj=load('batch_journal');ck('journal_pin',sha(P/'batch_journal.py')=='c862508a062eafb3a2c21bd3e05bc774a0839248415e8de3ec500a70328a0a7f');ck('executor_unchanged',sha(P/'pair_executor.py')=='6d1ad3a720eec15f63c7fd6423a9f0c92b4e5020c0d9962ef825f8b5cf73d34a')
limits=dict(batch_cells=2,max_cells=4,max_bytes=16384,max_body_bytes=2048)
for case in ['pending','root','purpose','throw','symlink']:
 root=H/case;calls=[];purpose={'ordinal':0};primary=RuntimeError('boundary')
 def boundary():
  calls.append(1)
  if len(calls)==2:
   if case=='pending':(root/'00000000.pending.json').write_bytes(b'{}\n')
   elif case in ('root','symlink'):
    moved=H/(case+'-moved');root.rename(moved)
    if case=='root':root.mkdir()
    else:root.symlink_to(moved,target_is_directory=True)
   elif case=='throw':raise primary
 def execute(*args):
  if case=='purpose':purpose['ordinal']=99
  return .5,3,'iteration_cap'
 j=bj.BatchJournal(root,boundary=boundary,**limits)
 try:
  try:j.run_batch([(purpose,None,None)],execute)
  except (ValueError,RuntimeError) as e:
   if case=='throw':assert e is primary
  else:raise AssertionError('fault credited '+case)
  ck('reproducer_refused_'+case,j.poisoned and j.cells==0)
 finally:j.close()
# Binary status and signed-zero bit preservation; fresh next occurrence.
j=bj.BatchJournal(H/'roundtrip',boundary=lambda:None,**limits)
for ordinal,score,status in [(0,0.,'temperature_complete'),(1,-0.,'iteration_cap')]:
 purpose={'ordinal':ordinal};rows=j.run_batch([(purpose,None,None)],lambda *args:(score,7,status));back=j.read_complete(ordinal)
 ck('record_roundtrip_'+str(ordinal),rows==back and rows[0][0]==ordinal and rows[0][1]==hashlib.sha256(bj.body(purpose)).digest() and struct.pack('>d',rows[0][2])==struct.pack('>d',score) and rows[0][4]==bj.STATUS[status])
 ck('framing_'+str(ordinal),(H/'roundtrip'/f'{ordinal:08d}.records.bin').stat().st_size==60+53 and bj.HEADER.size==60 and bj.RECORD.size==53)
ck('no_temp_success',not list((H/'roundtrip').glob('*.tmp')));j.close()
for case in ['payload','metadata','mode','links']:
 root=H/('consumer-'+case);j=bj.BatchJournal(root,boundary=lambda:None,**limits);j.run_batch([({'ordinal':0},None,None)],lambda *a:(.25,1,'iteration_cap'))
 p=root/'00000000.records.bin'
 if case=='payload':raw=bytearray(p.read_bytes());raw[-1]^=1;p.write_bytes(raw)
 elif case=='metadata':(root/'00000000.complete.json').write_text('{}')
 elif case=='mode':p.chmod(0o644)
 else:os.link(p,root/'extra-link')
 try:
  try:j.read_complete(0)
  except ValueError:pass
  else:raise AssertionError('corruption consumed')
  ck('consumer_refused_'+case,j.poisoned)
 finally:j.close()
for case,kw,tasks in [('bytes',{'max_bytes':1},[({'ordinal':0},None,None)]),('cells',{'max_cells':1},[({'ordinal':0},None,None),({'ordinal':1},None,None)]),('ordinal',{},[({'ordinal':1},None,None)])]:
 j=bj.BatchJournal(H/('limit-'+case),boundary=lambda:None,**{**limits,**kw})
 try:
  try:j.run_batch(tasks,lambda *a:(_ for _ in ()).throw(AssertionError('numeric reached')))
  except ValueError:pass
  else:raise AssertionError('bound missed')
  ck('limit_'+case,j.poisoned and j.cells==0)
 finally:j.close()
try:bj.BatchJournal(H/'roundtrip',boundary=lambda:None,**limits)
except FileExistsError:checks.append('namespace_exclusive')
else:raise AssertionError('existing namespace accepted')
# Independent original nested engine loop, tiny synthetic graph, once.
import numpy as np
from tradingagents.research.onchain_replication.contracts import AttributedGraph
from tradingagents.research.onchain_replication.matching_reference import match_reference
pe=load('pair_executor');c=dict(beta0=.2,beta_final=.5,beta_rate=.1,max_iterations=3,alpha=.7,max_pair_entries=10000,normalization_iterations=1,solver='algorithm1_literal');policy=dict(max_state_bytes=65536,normalization_chunk_entries=8,hardening_chunk_entries=8,hardening_buffer_bytes=65536,max_score_buffer_bytes=65536,chunk_edges=8,max_checkpoint_bytes=262144,max_publications=100,total_checkpoint_bytes=1048576);schedule=dict(max_checkpoints=100,calls_per_checkpoint=2,operations_per_call=3,max_total_checkpoints=1000,max_total_checkpoint_bytes=500000000)
a=AttributedGraph(('a','b'),np.array([[0.],[1.]]),np.array([[0,1],[1,0]],dtype=np.int64),np.array([[.2],[.3]]),'a'*64,'a');key='a'*64;trace=[];s=pe.engine.create(a,a,c,**{k:policy[k] for k in pe.pair.ENGINE_FIELDS})
try:
 for ordinal in range(schedule['max_checkpoints']):
  for _ in range(2):
   trace.append(('advance',s['phase'],s['annealing']['phase'],s['annealing']['cursor']));pe.engine.advance(s,a,a,c,max_operations=3)
   if s['phase']=='done':break
  if s['phase']=='done':
   result=pe.engine.score_only(s,a,a,c,max_buffer_bytes=65536,chunk_edges=8);expected=(result.score,result.iterations,result.convergence);break
  trace.append(('checkpoint',ordinal,s['phase'],s['annealing']['cursor']))
finally:pe.engine.close(s)
seen=[];closed=[];advance=pe.engine.advance;close=pe.engine.close
def spy(s,*args,**kw):seen.append(('advance',s['phase'],s['annealing']['phase'],s['annealing']['cursor']));return advance(s,*args,**kw)
def closer(s):closed.append(s);return close(s)
def checkpoint(k,i,s,*args):assert k==key;seen.append(('checkpoint',i,s['phase'],s['annealing']['cursor']))
pe.engine.advance=spy;pe.engine.close=closer
try:
 executor=pe.PairExecutor(c,policy,schedule,checkpoint);answer=executor(a,a,key)
 ck('original_numeric_loop_trace',answer==expected and seen==trace and sum(r[0]=='advance' for r in trace)==12 and sum(r[0]=='checkpoint' for r in trace)==5)
 ck('reference_tolerance',abs(answer[0]-match_reference(a,a,c).score)<=1e-12)
 ck('success_cleanup',len(closed)==1 and closed[0]['annealing'] is None)
 for case in ['callback','exhaustion','cumulative']:
  closed.clear();primary=RuntimeError('checkpoint-primary');cb=(lambda *args:(_ for _ in ()).throw(primary)) if case=='callback' else (lambda *a:None);ss={**schedule,'max_checkpoints':1,'calls_per_checkpoint':1}
  if case=='cumulative':ss['max_total_checkpoint_bytes']=1
  ex=pe.PairExecutor(c,policy,ss,cb)
  try:ex(a,a,key)
  except (RuntimeError,ValueError) as e:
   if case=='callback':assert e is primary
  else:raise AssertionError('failure absent')
  ck('executor_failure_'+case,ex.poisoned and (not closed if case=='cumulative' else len(closed)==1 and closed[0]['annealing'] is None))
  if case!='cumulative':ck('reservation_charged_'+case,ex.checkpoints==1 and ex.reserved_bytes==policy['max_checkpoint_bytes']+2*pe.pair.LIMIT)
finally:pe.engine.advance=advance;pe.engine.close=close
out={'decision':'accepted-source-only-bounded-engineering-domain','source_sha256':{'batch_journal.py':sha(P/'batch_journal.py'),'pair_executor.py':sha(P/'pair_executor.py')},'checks':checks,'framing':{'header_bytes':60,'record_bytes':53},'qualification':'Version01 remains permanently withheld. Binary chunk/root/pending/current purpose joins refuse tested callback corruption and symlink replacement before credit; consumer validates exact pending/header/payload/metadata closure. Original engine result/iteration/convergence and12advance5checkpoint order independently verified with synthetic fixture;1e-12 reference tolerance. Deliberately changed batch control trace, not old per-pair authority. Explicit descriptor close remains caller responsibility; partial failed files retained, publication may exist after later error but zero in-memory credit/poison prevents continued use. Exclusive single-process namespace/immutable graph ownership and unchanged numerical runtime required; arbitrary concurrent hostile writes or monkeypatched OS guarantees not certified. No full capacity, genuine Owner/admission, numerical population, benchmark, source installation or launch claim.'}
(H/'SOURCE_REVIEW01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'checks':len(checks),'sha256':sha(H/'SOURCE_REVIEW01.json')}))
