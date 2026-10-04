import dataclasses as D
import io,json,os
from pathlib import Path
import router06 as A
C=A.C;L=A.L;S=A.S
P=Path(__file__).resolve().parent
checks=[]
def ok(value,label):
 assert value,label
 checks.append(label)
def refused(label,fn,kind=ValueError):
 try:fn()
 except BaseException as e:
  ok(isinstance(e,kind),label+' category');return e
 raise AssertionError(label+' accepted')
def mkdir(name):
 p=P/('successor-'+name);p.mkdir(mode=0o700);return p
def source(name,rows=1,dtype='<f4',chunk=16):
 root=mkdir(name);raw=bytes(range(128))*(rows*(2 if dtype=='<f8' else 1))
 desc={'schema_version':1,'kind':'mcm-batch-output-bytes','role':'mcm-output' if dtype=='<f4' else 'score-batches','dtype':dtype,'shape':[rows,32],'order':'C','scope':{k:A.sha(k.encode()) for k in C.SCOPE},'motifs':32,'spent_samples':512}
 with L.LocalStore(root) as store:
  pin=C.encode_stream(io.BytesIO(raw),desc,store.put,chunk_bytes=chunk)
  store.verify(pin,desc)
 inv=A.inspect(root,A.sha(name.encode()),desc,pin)
 return inv,raw,desc

def outputs(label,route):
 return (tuple(mkdir(label+'-spool-%03d'%p.index) for p in route.partitions),tuple(mkdir(label+'-recovered-%02d'%i) for i in range(len(route.inventories))))
def callbacks():
 memory={};calls=[]
 def send(env,body):
  assert env.pin() not in memory
  memory[env.pin()]=body;calls.append(env.file.name);m=env.spool_member
  ack=S.Ack(env.spool_plan_sha256,m.page,m.chunk,m.size,m.sha256,A.sha(b'engineering receipt'+body))
  return A.RoutedAck(env.pin(),ack)
 def recover(env,ack):return A.RoutedRecovery(env.pin(),ack.ack,memory[env.pin()])
 return send,recover,memory,calls

one,raw1,d1=source('source-one',rows=9)
two,raw2,d2=source('source-two',dtype='<f8')
route=A.route((one,two),members_per_plan=7)
limits=A.estimate(route)
router=A.Router(mkdir('ledger-complete'),route,*limits)
sroots,rroots=outputs('complete',route);send,recover,memory,calls=callbacks()
router.run(sroots,rroots,send,recover)
ok(router.finished and not router.failed,'real complete two-target pipeline')
ok(router.consumed==limits,'shared full accounting never refunded')
ok(router.completed==tuple(range(len(route.partitions))),'all partitions ordered')
ok(len(calls)==len(one.files)+len(two.files),'every actual codec member once')
ok(calls==[f.name for inv in (one,two) for f in inv.files],'exact emission order retained')
ok(len(one.files)==76 and len(two.files)==19,'actual start frames pages footer membership')
for inv,raw,desc,root in zip((one,two),(raw1,raw2),(d1,d2),rroots):
 parts=[];result=C.verify_stream(lambda n:A.R.read(root,n),inv.terminal_sha256,desc,parts.append)
 ok(b''.join(parts)==raw and result['raw_sha256']==A.sha(raw),'raw exact reassembly '+inv.target_key)
 ok(A.inspect(root,inv.target_key,desc,inv.terminal_sha256).files==inv.files,'all file/mode/offset/scope joins')
refused('completed retry',lambda:router.run(sroots,rroots,send,recover))
refused('release unavailable',router.release,RuntimeError);refused('production unavailable',A.production,RuntimeError)
router.close()
for n,(lo,al) in enumerate(((limits[0]-1,limits[1]),(limits[0],limits[1]-1),(True,limits[1]))):
 refused('reservation-'+str(n),lambda n=n,lo=lo,al=al:A.Router(mkdir('budget-'+str(n)),route,lo,al))
for cap in (True,0,33,4097):refused('partition cap-'+str(cap),lambda cap=cap:A.route((one,),cap))
for label,bad in (
 ('missing',D.replace(route,partitions=route.partitions[:-1])),
 ('duplicate',D.replace(route,partitions=route.partitions+(route.partitions[0],))),
 ('reorder',D.replace(route,partitions=tuple(reversed(route.partitions)))),
 ('dtype',D.replace(route,inventories=(D.replace(one,descriptor=C.canonical({**d1,'dtype':'<f8'})),two))),
 ('scope',D.replace(route,inventories=(D.replace(one,descriptor=C.canonical({**d1,'scope':{**d1['scope'],'graph':'f'*64}})),two))),
 ('offset',D.replace(route,inventories=(D.replace(one,files=(one.files[0],D.replace(one.files[1],raw_offset=4))+one.files[2:]),two)))):
 refused(label,lambda bad=bad:A.validate_route(bad))
small=A.route((two,),4)
for label in ('partial','wrong-envelope','wrong-recovery','fatal','cleanup-fatal'):
 router=A.Router(mkdir('ledger-'+label),small,*A.estimate(small));sr,rr=outputs(label,small);send,recover,memory,calls=callbacks();original=router.consumed
 primary=MemoryError('original transport fatal');later=SystemExit('later cleanup fatal');counter=[0]
 def wrapped_send(env,body):
  counter[0]+=1
  if counter[0]==2:
   if label=='partial':return None
   if label=='wrong-envelope':return D.replace(send(env,body),envelope_sha256='f'*64)
   if label in ('fatal','cleanup-fatal'):raise primary
  return send(env,body)
 def wrapped_recover(env,ack):
  response=recover(env,ack)
  return D.replace(response,body=b'wrong') if label=='wrong-recovery' and counter[0]==2 else response
 def cleanup():
  if label=='cleanup-fatal' and counter[0]==2:raise later
 err=refused(label,lambda:router.run(sr,rr,wrapped_send,wrapped_recover,cleanup),MemoryError if label in ('fatal','cleanup-fatal') else ValueError)
 if label in ('fatal','cleanup-fatal'):ok(err is primary,label+' first fatal identity')
 ok(router.failed and not router.finished and router.consumed==original,label+' terminal nonrefunded')
 ok((router.root/'failed.json').is_file() and not (router.root/'complete.json').exists(),label+' actual failed vs absent complete')
 count=counter[0];refused(label+' retry',lambda:router.run(sr,rr,wrapped_send,wrapped_recover));ok(counter[0]==count,label+' no replay callback')
 router.close()
for label in ('extra','missing','corrupt'):
 inv,raw,d=source('mutant-'+label)
 if label=='extra':(Path(inv.root)/'unknown.bin').write_bytes(b'x')
 elif label=='missing':(Path(inv.root)/'page-0000.json').rename(Path(inv.root)/'retained-missing-page.json')
 else:
  # New owned corrupt fixture; no original/predecessor evidence changed.
  f=Path(inv.root)/'chunk-00000.bin';rawframe=f.read_bytes();f.write_bytes(rawframe[:-1]+bytes([rawframe[-1]^1]))
 refused(label+' actual source',lambda inv=inv:A.current(inv))
# Denominators are metadata-only, not an observed genuine Target population.
count=(C.MAX_BYTES+C.CHUNK-1)//C.CHUNK;pages=(count+C.PAGE-1)//C.PAGE
ok((count,pages,count+pages+2)==(8812,138,8952),'unchanged default whole aggregate metadata count')
ok((8952+31)//32==280,'finite metadata partition count without repacking')
(P/'RESULT01.json').write_text(json.dumps({'checks':checks,'count':len(checks),'actual_members':len(one.files)+len(two.files),'actual_partitions':len(route.partitions),'logical_and_allocated_accounting':limits,'default_aggregate_metadata_only':{'frames':count,'pages':pages,'members':count+pages+2,'32_member_partitions':280},'production_available':False,'remote_origin_observed':False},indent=2)+'\n')
print(len(checks),'controls passed')
