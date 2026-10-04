import dataclasses as D,io,json,os
from pathlib import Path
import router04 as A
P=Path(__file__).resolve().parent;rows=[]
def mkdir(name):
 p=P/name;p.mkdir(mode=0o700);return p
source=mkdir('adversarial-source');desc={'schema_version':1,'kind':'mcm-batch-output-bytes','role':'mcm-output','dtype':'<f4','shape':[1,32],'order':'C','scope':{k:A.sha(k.encode()) for k in A.C.SCOPE},'motifs':32,'spent_samples':512}
with A.L.LocalStore(source) as store:terminal=A.C.encode_stream(io.BytesIO(bytes(range(128))),desc,store.put)
inv=A.inspect(source,'1'*64,desc,terminal);route=A.route((inv,),2)
for attack in ('retained-change','readonly-reservation','cross-envelope','cleanup-only'):
 ledger=A.Router(mkdir('adversarial-ledger-'+attack),route,*A.estimate(route))
 spools=tuple(mkdir('adversarial-'+attack+'-spool-'+str(i)) for i in range(2));rec=(mkdir('adversarial-'+attack+'-recovery'),)
 memory={};count=[0];first=[];original=ledger.consumed;marker=SystemExit('actual cleanup fatal')
 def send(env,body):
  count[0]+=1
  if attack=='readonly-reservation':ledger.consumed=(0,0)
  m=env.spool_member;ack=A.RoutedAck(env.pin(),A.S.Ack(env.spool_plan_sha256,m.page,m.chunk,m.size,m.sha256,'a'*64));memory[env.pin()]=body
  if not first:first.append(ack)
  if attack=='cross-envelope' and count[0]==2:return first[0]
  if attack=='retained-change' and count[0]==3:
   # Earlier plan is closed and retained. Change only an owned tiny fixture.
   path=spools[0]/'body-0000';fd=os.open(path,os.O_WRONLY|os.O_NOFOLLOW)
   try:os.pwrite(fd,b'!',0)
   finally:os.close(fd)
  return ack
 def recover(env,ack):return A.RoutedRecovery(env.pin(),ack.ack,memory[env.pin()])
 def cleanup():
  if attack=='cleanup-only':raise marker
 error=None
 try:ledger.run(spools,rec,send,recover,cleanup)
 except BaseException as e:error=e
 assert error is not None and ledger.failed and not ledger.finished and ledger.consumed==original
 assert (ledger.root/'failed.json').exists() and not (ledger.root/'complete.json').exists()
 if attack=='cleanup-only':assert error is marker
 if attack=='readonly-reservation':assert isinstance(error,AttributeError)
 if attack=='retained-change':assert 'closed retained spool body changed' in str(error)
 rows.append({'attack':attack,'error':type(error).__name__,'message':str(error),'consumed_unchanged':True,'attempted':ledger.attempted,'completed':ledger.completed,'calls':count[0]});ledger.close()
(P/'ADVERSARIAL01.json').write_text(json.dumps(rows,sort_keys=True,indent=2)+'\n');print(len(rows),'passed')
