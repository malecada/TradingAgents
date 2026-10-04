import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.with_name("financial-batch-output-codec-spool-integration-preparation03-2026-10-04")))
import dataclasses as D,json
from pathlib import Path
import router06 as A
P=Path(__file__).resolve().parent;src=P/'ir3-new-source';desc=A.C.parse(A.R.read(src,'start.json'))['descriptor'];terminal=A.sha(A.R.read(src,'terminal.json'));inv=A.inspect(src,'b'*64,desc,terminal);route=A.route((inv,),4);rows=[]
def refuse(label,fn):
 try:fn()
 except ValueError as e:rows.append({'case':label,'refusal':str(e)})
 else:raise AssertionError(label)
p=route.partitions[0];f=p.files[1]
for field,value in [('raw_offset',4),('raw_size',16),('raw_sha256','f'*64),('mode',0o600),('sha256','f'*64),('name','chunk-00009.bin'),('ordinal',9),('size',f.size+1)]:
 if value==getattr(f,field):continue
 badfile=D.replace(f,**{field:value});badpart=D.replace(p,files=(p.files[0],badfile)+p.files[2:]);bad=D.replace(route,partitions=(badpart,)+route.partitions[1:]);refuse('derived-file-'+field,bad.pin)
for label,badpart in [('plan-reservation',D.replace(p,plan=D.replace(p.plan,logical_reservation=p.plan.logical_reservation+1))),('plan-quantum',D.replace(p,plan=D.replace(p.plan,allocation_quantum=8192,allocated_reservation=p.plan.allocated_reservation*2))),('reordered-files',D.replace(p,files=tuple(reversed(p.files)))),('duplicated-file',D.replace(p,files=(p.files[0],p.files[0])+p.files[2:])),('wrong-start',D.replace(p,start=1))]:
 refuse(label,D.replace(route,partitions=(badpart,)+route.partitions[1:]).pin)
for label,parts in [('missing',route.partitions[:-1]),('extra',route.partitions+(route.partitions[0],)),('reordered',tuple(reversed(route.partitions)))]:refuse(label,D.replace(route,partitions=parts).pin)
# Genuine compact format remains unchanged for a valid route; no payload or
# previously encoded JSON field is introduced by derivative validation.
expected=A.encode({'inventories':[D.asdict(i) for i in route.inventories],'members_per_plan':route.members_per_plan,'partitions':[{'target':p.target,'index':p.index,'start':p.start,'count':len(p.files),'spool_plan_sha256':A.sha(p.plan.encoded())} for p in route.partitions]})
assert route.encoded()==expected;rows.append({'case':'unchanged-valid-compact-format','equal':True})
def mkdir(n):p=P/n;p.mkdir(mode=0o700);return p
for boundary in ('send','recover','cleanup'):
 ledger=A.Router(mkdir('snapshot-'+boundary+'-ledger'),route,*A.estimate(route));sp=tuple(mkdir('snapshot-'+boundary+'-spool-'+str(p.index)) for p in route.partitions);rr=(mkdir('snapshot-'+boundary+'-recovery'),);memory={};events=[];saved=ledger.consumed
 def replace():
  if not events:
   clone=D.replace(route);assert clone==route and clone is not route and clone.pin()==route.pin();ledger.route=clone;events.append('replace with equal but different immutable route')
 def send(env,body):
  if boundary=='send':replace()
  memory[env.pin()]=body;m=env.spool_member;return A.RoutedAck(env.pin(),A.S.Ack(env.spool_plan_sha256,m.page,m.chunk,m.size,m.sha256,'c'*64))
 def recover(env,ack):
  if boundary=='recover':replace()
  return A.RoutedRecovery(env.pin(),ack.ack,memory[env.pin()])
 def cleanup():
  if boundary=='cleanup':replace()
 try:ledger.run(sp,rr,send,recover,cleanup)
 except ValueError as e:assert str(e)=='original immutable route reference replaced'
 else:raise AssertionError(boundary)
 assert ledger.failed and not ledger.finished and ledger.consumed==saved and events and (ledger.root/'failed.json').exists() and not (ledger.root/'complete.json').exists()
 rows.append({'case':'immutable-reference-'+boundary,'failed':True,'consumed_unchanged':True});ledger.close()
(P/'DERIVATIVE01.json').write_text(json.dumps({'count':len(rows),'rows':rows},sort_keys=True,indent=2)+'\n');print(len(rows),'derivative/boundary controls passed')
