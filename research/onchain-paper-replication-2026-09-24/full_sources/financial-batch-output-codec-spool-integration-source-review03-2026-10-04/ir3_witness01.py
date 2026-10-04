import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.with_name("financial-batch-output-codec-spool-integration-preparation03-2026-10-04")))
import dataclasses as D,importlib.util,io,json,sys
from pathlib import Path
import router06 as new
P=Path(__file__).resolve().parent;oldpath=P.with_name('financial-batch-output-codec-spool-integration-preparation02-2026-10-04')/'router05.py'
spec=importlib.util.spec_from_file_location('old05',oldpath);old=importlib.util.module_from_spec(spec);sys.modules[spec.name]=old;spec.loader.exec_module(old)
def mkdir(n):p=P/n;p.mkdir(mode=0o700);return p
rows=[]
for label,A in (('old',old),('new',new)):
 src=mkdir('ir3-'+label+'-source');desc={'schema_version':1,'kind':'mcm-batch-output-bytes','role':'mcm-output','dtype':'<f4','shape':[1,32],'order':'C','scope':{k:'a'*64 for k in A.C.SCOPE},'motifs':32,'spent_samples':512}
 with A.L.LocalStore(src) as store:tp=A.C.encode_stream(io.BytesIO(bytes(range(128))),desc,store.put,chunk_bytes=32)
 inv=A.inspect(src,'b'*64,desc,tp);route=A.route((inv,),4);router=A.Router(mkdir('ir3-'+label+'-ledger'),route,*A.estimate(route))
 sp=tuple(mkdir('ir3-'+label+'-spool-'+str(i)) for i in range(len(route.partitions)));rr=(mkdir('ir3-'+label+'-recovery'),)
 f=route.partitions[0].files[1];badfile=D.replace(f,raw_offset=f.raw_offset+4);badpart=D.replace(route.partitions[0],files=(route.partitions[0].files[0],badfile)+route.partitions[0].files[2:]);badroute=D.replace(route,partitions=(badpart,)+route.partitions[1:])
 encoded_error=None
 try:same_pin=badroute.pin()==route.pin()
 except ValueError as e:encoded_error=str(e);same_pin=None
 assert same_pin is True if label=='old' else encoded_error=='partition inventory/spool derivative differs'
 memory={};actions=[];recoveries=[];consumed=router.consumed
 def send(env,body):
  if not actions:router.route=badroute;actions.append('replace public route with frozen derivative raw_offset0->4')
  memory[env.pin()]=body;m=env.spool_member
  return A.RoutedAck(env.pin(),A.S.Ack(env.spool_plan_sha256,m.page,m.chunk,m.size,m.sha256,'c'*64))
 def recover(env,ack):recoveries.append(env.file.name);return A.RoutedRecovery(env.pin(),ack.ack,memory[env.pin()])
 error=None
 try:router.run(sp,rr,send,recover)
 except BaseException as e:error=e
 assert len(actions)==1 and router.consumed==consumed
 if label=='old':
  assert error is None and router.finished and not router.failed;router.check()
  try:A.validate_route(router.route)
  except ValueError as e:independent=str(e)
  else:raise AssertionError('old reconstruction should refuse')
  proof=A.C.verify_stream(lambda n:A.R.read(rr[0],n),tp,desc);assert proof['raw_sha256']==A.sha(bytes(range(128)))
 else:
  assert isinstance(error,ValueError) and str(error)=='original immutable route reference replaced'
  assert router.failed and not router.finished and not recoveries
  assert (router.root/'failed.json').exists() and not (router.root/'complete.json').exists()
  independent=None
 rows.append({'source':label,'invalid_pin_equals_original':same_pin,'encoded_refusal':encoded_error,'finished':router.finished,'failed':router.failed,'exception':None if error is None else str(error),'callback_actions':actions,'recovery_callbacks':len(recoveries),'full_validate_refusal':independent,'complete':(router.root/'complete.json').exists(),'consumed_unchanged':True,'raw_payload_changed':False});router.close()
(P/'IR3_WITNESS01.json').write_text(json.dumps(rows,sort_keys=True,indent=2)+'\n');print('exact IR3 oldRED/newGREEN passed')
