import dataclasses as D,io,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent;A=H.parent/'financial-batch-output-codec-spool-integration-preparation02-2026-10-04';sys.path.insert(0,str(A));import router05 as R
assert R.sha((A/'router05.py').read_bytes())=='5d13a47c3f8997b215be50d8bee165b8d3d5f7fc4e292689f90a16d6e32b8acc'
def mkdir(n):p=H/n;p.mkdir(mode=0o700);return p
source=mkdir('source');d=dict(schema_version=1,kind='mcm-batch-output-bytes',role='mcm-output',dtype='<f4',shape=[1,32],order='C',scope={k:'a'*64 for k in R.C.SCOPE},motifs=32,spent_samples=512)
with R.L.LocalStore(source) as s:tp=R.C.encode_stream(io.BytesIO(bytes(range(128))),d,s.put,chunk_bytes=32)
i=R.inspect(source,'b'*64,d,tp);route=R.route((i,),4);router=R.Router(mkdir('ledger'),route,*R.estimate(route));sp=tuple(mkdir('spool-%d'%p.index) for p in route.partitions);rr=(mkdir('recovered'),);memory={};events=[]
f=route.partitions[0].files[1];badf=D.replace(f,raw_offset=f.raw_offset+4);badpart=D.replace(route.partitions[0],files=(route.partitions[0].files[0],badf)+route.partitions[0].files[2:]);badroute=D.replace(route,partitions=(badpart,)+route.partitions[1:]);assert badroute.pin()==route.pin()
def send(env,b):
 if not events:router.route=badroute;events.append('replaced public router.route with changed partition raw_offset')
 memory[env.pin()]=b;m=env.spool_member;return R.RoutedAck(env.pin(),R.S.Ack(env.spool_plan_sha256,m.page,m.chunk,m.size,m.sha256,'c'*64))
def recover(env,a):return R.RoutedRecovery(env.pin(),a.ack,memory[env.pin()])
router.run(sp,rr,send,recover);assert router.finished and not router.failed;router.check()
try:R.validate_route(router.route)
except ValueError as e:reason=str(e)
else:raise AssertionError('mutated route should fail full reconstruction')
out={'router_finished':router.finished,'final_check_accepted':True,'current_full_reconstruction_refuses':reason,'encoded_route_pin_unchanged':route.pin()==badroute.pin(),'original_offset':f.raw_offset,'mutated_partition_offset':badf.raw_offset,'no_private_field_mutation':True,'callback_actions':events,'actual_payload_bytes_changed':False,'no_research_authority':True};router.close();(H/'IR3_WITNESS01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps(out,sort_keys=True))
