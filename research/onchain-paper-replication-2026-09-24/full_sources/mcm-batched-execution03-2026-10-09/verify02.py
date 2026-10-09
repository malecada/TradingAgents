import json,os,resource,struct,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
assert resource.getrlimit(resource.RLIMIT_AS)[0]==268435456 and resource.getrlimit(resource.RLIMIT_FSIZE)[0]==4194304 and len(os.sched_getaffinity(0))==2 and os.getpriority(os.PRIO_PROCESS,0)==10
import batch_journal as m
OUTPUT=P/'RESULT02.json';P=P/'fixtures02';P.mkdir()
bounds=dict(batch_cells=8,max_cells=100,max_bytes=200000,max_body_bytes=8192)
workload={'kind':'synthetic-routing-only','centers':3,'motifs':2}
class Local:
 live=0;peak=0
 def __init__(self,center):
  self.center=center;Local.live+=1;Local.peak=max(Local.peak,Local.live)
 def __del__(self):Local.live-=1
closed=[];root=P/'stream'
def tasks():
 try:
  assert (root/'00000000.pending.json').exists()
  for center in range(3):
   local=Local(center)
   try:
    for motif in range(2):yield ({'ordinal':center*2+motif,'center':center,'motif':motif},local,motif)
   finally:del local
 finally:closed.append(1)
def compute(local,motif,key):return (-0. if motif else 0.),local.center,('iteration_cap' if motif else 'temperature_complete')
j=m.BatchJournal(root,boundary=lambda:None,**bounds);rows=j.run_batch_stream(6,tasks(),compute,workload)
assert Local.peak==1 and Local.live==0 and closed==[1] and j.cells==6 and rows==j.read_complete(0)
assert [r[0] for r in rows]==list(range(6)) and [struct.pack('>d',r[2]).hex() for r in rows]==['0000000000000000','8000000000000000']*3
p=json.loads((root/'00000000.pending.json').read_text());assert 'purposes_sha256' not in p and p['workload_sha256']==m.digest(m.body(workload))
meta=json.loads((root/'00000000.complete.json').read_text());assert len(meta['purposes_sha256'])==64;j.close()
results={}
for mode in ['short','extra','misordered','purpose','prior_purpose','workload','pending','root','boundary','iterator_failure']:
 root=P/mode;calls=[];boundaries=[];closed=[];purposes=[];w=dict(workload)
 def boundary():
  boundaries.append(1)
  if len(boundaries)==2:
   if mode=='workload':w['centers']=999
   if mode=='pending':(root/'00000000.pending.json').write_bytes(b'bad')
   if mode=='root':root.rename(P/'moved');root.mkdir()
   if mode=='boundary':raise RuntimeError('boundary-fail')
 def gen():
  try:
   for ordinal in range(1 if mode=='short' else 3 if mode=='extra' else 2):
    if mode=='iterator_failure' and ordinal==1:raise RuntimeError('iterator-fail')
    purpose={'ordinal':999 if mode=='misordered' else ordinal};purposes.append(purpose)
    yield purpose,None,None
  finally:closed.append(1)
 def executor(a,b,key):
  calls.append(1)
  if mode=='purpose':purposes[-1]['ordinal']=999
  if mode=='prior_purpose' and len(calls)==2:purposes[0]['ordinal']=999
  return 0.,1,'iteration_cap'
 j=m.BatchJournal(root,boundary=boundary,**bounds)
 try:j.run_batch_stream(2,gen(),executor,w)
 except (ValueError,RuntimeError) as error:results[mode]=str(error)
 else:raise AssertionError('accepted '+mode)
 assert j.poisoned and j.cells==0 and closed==[1]
 if mode=='extra':assert len(calls)==2 # Extra task never receives a numeric call.
 j.close()
# One concrete returned-chunk tampering refusal remains exercised with schema03.
root=P/'tamper';j=m.BatchJournal(root,boundary=lambda:None,**bounds)
j.run_batch_stream(1,iter([({'ordinal':0},None,None)]),lambda *args:(0.,1,'iteration_cap'),workload)
f=root/'00000000.records.bin';raw=bytearray(f.read_bytes());raw[-1]=9;f.write_bytes(raw)
try:j.read_complete(0)
except ValueError:pass
else:raise AssertionError('consumer accepted tamper')
assert j.poisoned;j.close()
# Exact conditional encoding arithmetic only; no numerical inputs or benchmark.
N=415968128;B=4096;metadata=0;payload=0
for start in range(0,N,B):
 stop=min(N,start+B);extent=m.HEADER.size+(stop-start)*m.RECORD.size
 p=m.body({'schema':3,'kind':'engineering_pending','start':start,'stop':stop,'workload_sha256':'0'*64,'disposition':'attempted_unknown_without_complete'})
 c=m.body({'schema':3,'kind':'engineering_complete','pending_sha256':'0'*64,'payload_sha256':'0'*64,'payload_bytes':extent,'record_bytes':m.RECORD.size,'purposes_sha256':'0'*64})
 metadata+=len(p)+len(c);payload+=extent
r={'status':'PASS','source03_streaming':True,'centers':3,'scores':6,'peak_live_local':Local.peak,'remaining_live_local':Local.live,'failure_refusals':results,'exact_record_bytes':m.RECORD.size,'header_bytes':m.HEADER.size,'numerical_tests_repeated':False,'full_cells':N,'batch_cells':B,'batches':(N+B-1)//B,'final_files':3*((N+B-1)//B),'one_journal_directory':1,'binary_bytes':payload,'metadata_bytes':metadata,'total_encoded_bytes':payload+metadata,'retained_canonical_purpose_bytes_upper':8192*B,'retained_record_bytes_upper':53*B,'qualification':'Encoded bodies and namespace arithmetic only, not allocation/RAM/process/transport/full-capacity proof; purpose dict objects remain bounded by encoded extent convention, Python overhead separate.'}
OUTPUT.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
