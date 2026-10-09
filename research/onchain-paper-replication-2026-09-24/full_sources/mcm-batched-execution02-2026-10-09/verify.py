import json,os,resource,struct,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));sys.path.insert(0,str(P.parents[3]))
assert resource.getrlimit(resource.RLIMIT_AS)[0]==268435456 and resource.getrlimit(resource.RLIMIT_FSIZE)[0]==4194304
assert len(os.sched_getaffinity(0))==2 and os.getpriority(os.PRIO_PROCESS,0)==10
import batch_journal as bj
bounds=dict(batch_cells=2,max_cells=4,max_bytes=100000,max_body_bytes=8192)
results={}
# Actual reviewed defects: pending/root/purpose mutation; also boundary exceptions.
for mode in ['pending','root','purpose','boundary_throw']:
 root=P/('green-'+mode);calls=[];tasks=[({'ordinal':0},None,None)]
 def boundary():
  calls.append(1)
  if len(calls)==2:
   if mode=='pending':(root/'00000000.pending.json').write_bytes(b'forged\n')
   if mode=='root':root.rename(P/'green-moved');root.mkdir()
   if mode=='boundary_throw':raise RuntimeError('boundary-stop')
 def executor(*args):
  if mode=='purpose':tasks[0][0]['ordinal']=999
  return 0.,1,'iteration_cap'
 j=bj.BatchJournal(root,boundary=boundary,**bounds)
 try:
  try:j.run_batch(tasks,executor)
  except (ValueError,RuntimeError) as e:results[mode]={'refused':True,'error':str(e)}
  else:raise AssertionError('defect accepted '+mode)
  assert j.cells==0 and j.poisoned
 finally:j.close()
# Exact fixed binary records, positive/negative zero, both status tags and closure.
j=bj.BatchJournal(P/'roundtrip',boundary=lambda:None,**bounds)
values=iter([(0.,1,'temperature_complete'),(-0.,2,'iteration_cap')]);tasks=[({'ordinal':i,'motif':i},None,None) for i in range(2)]
rows=j.run_batch(tasks,lambda *args:next(values));assert rows==j.read_complete(0)
assert [struct.pack('>d',r[2]).hex() for r in rows]==['0000000000000000','8000000000000000']
assert [r[4] for r in rows]==[0,1] and [r[0] for r in rows]==[0,1]
assert bj.RECORD.size==53 and bj.HEADER.size==60
payload=(P/'roundtrip/00000000.records.bin').read_bytes();assert len(payload)==166
assert list((P/'roundtrip').iterdir()).__len__()==3
encoded=sum(x.stat().st_size for x in (P/'roundtrip').iterdir());j.close()
try:bj.BatchJournal(P/'roundtrip',boundary=lambda:None,**bounds)
except FileExistsError:pass
else:raise AssertionError('namespace reused')
# Interrupted computation retains pending only; forged payload fails consumer.
j=bj.BatchJournal(P/'partial',boundary=lambda:None,**bounds);calls=[]
def fail(*args):
 calls.append(1)
 if len(calls)==2:raise RuntimeError('primary')
 return 0.,1,'iteration_cap'
try:j.run_batch(tasks,fail)
except RuntimeError as e:assert str(e)=='primary'
else:raise AssertionError('failure missing')
assert j.cells==0 and j.poisoned and [x.name for x in (P/'partial').iterdir()]==['00000000.pending.json'];j.close()
j=bj.BatchJournal(P/'tamper',boundary=lambda:None,**bounds);j.run_batch(tasks,lambda *args:(0.,1,'iteration_cap'))
f=P/'tamper/00000000.records.bin';raw=bytearray(f.read_bytes());raw[-1]=9;f.write_bytes(raw)
try:j.read_complete(0)
except ValueError:pass
else:raise AssertionError('forged payload accepted')
j.close()
for mode,changes in [('cells',{'max_cells':1}),('bytes',{'max_bytes':1})]:
 j=bj.BatchJournal(P/mode,boundary=lambda:None,**(bounds|changes))
 try:j.run_batch(tasks,lambda *args:(_ for _ in ()).throw(AssertionError('numeric entered')))
 except ValueError:pass
 else:raise AssertionError('cap ignored')
 assert j.poisoned and j.cells==0;j.close()
# Numeric/checkpoint trace once, using the retained first candidate test prefix.
text=(P.parent/'mcm-batched-execution01-2026-10-09/verify.py').read_text()
prefix=text[text.index('import numpy as np'):text.index('# Batches retain exact order/hash/f64 bits;')]
exec(compile(prefix,'original_numeric_focused_test','exec'))
result={'status':'PASS','defects':results,'record_bytes':bj.RECORD.size,'header_bytes':bj.HEADER.size,'two_cell_total_encoded_bytes':encoded,'float64_signed_zero_bits_preserved':True,'partial_pending_only':True,'forged_payload_consumer_refused':True,'numeric_trace_advance_calls':sum(x[0]=='advance' for x in trace),'numeric_trace_checkpoint_callbacks':sum(x[0]=='checkpoint' for x in trace),'affinity':sorted(os.sched_getaffinity(0))}
(P/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
