import resource
resource.setrlimit(resource.RLIMIT_AS,(384*1024**2,384*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2))
from pathlib import Path
import hashlib,json,os,stat,struct,tarfile,io,math,datetime
P=Path(__file__).resolve().parent;F=P.parent;R=P.parents[3];A=F/'pilot29-third-group-actual-recovery01-2026-10-10';V=F/'pilot29-second-group-recovery-review01-2026-10-10'
reads={};nread=0;checks=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def raw(v):return (json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def ck(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def read(p,limit=4*1024**2,prefix=None,offset=0):
 global nread
 p=Path(p)
 with p.open('rb') as h:
  a=os.fstat(h.fileno());h.seek(offset);b=h.read((limit+1) if prefix is None else prefix);z=os.fstat(h.fileno())
 ck(len(b)<=limit and (a.st_dev,a.st_ino)==(z.st_dev,z.st_ino),'bounded body and inode '+p.name)
 ck(a.st_size==z.st_size==len(b) if prefix is None else len(b)==prefix and a.st_size>=offset+prefix and z.st_size>=offset+prefix,'body/prefix extent '+p.name)
 nread+=len(b);ck(nread<=16*1024**2,'input aggregate bound '+p.name)
 reads[str(p.relative_to(R))]={'bytes':len(b),'sha256':sha(b),'segment':prefix is not None,'offset':offset,'before_size':a.st_size,'after_size':z.st_size,'device':z.st_dev,'inode':z.st_ino}
 return b
def js(p):return json.loads(read(p))
manb=read(A/'MANIFEST01.json');ck(sha(manb)=='6e2f137755b85d0595fe66f5d559a542683c4ea7aec9aed36f6d4967eaeb4b2a','external fresh recovery manifest anchor');man=json.loads(manb);bodies={}
for d in man['files']:
 name=d['path'];b=read(A/name);ck(len(b)==d['bytes'] and sha(b)==d['sha256'],'actual fresh output manifest '+name);bodies[name]=b
req=json.loads(bodies['REQUEST01.json']);res=json.loads(bodies['RESULT01.json']);archive=bodies['returned-third-group.tar']
ck(res['actual_exit']==0 and res['actual_error'] is None and res['exact_match'] is True and len(bodies['ssh.stderr'])==0,'recorded actual SSH result')
prior=js(V/'REVIEW01.json');ck(sha(read(V/'REVIEW01.json'))=='f13a006dd79d21a0eb1815b983f9c870c9ecc6dd5709d60ed86f896377ab7e76','prior accepted narrow review anchor')
o_path='research_artifacts/onchain_batched_offload/c64f82cdaebfcadd2c0227b40ac26bfdf7c53705c0d8f56903f3183c0ea49cc2/mcm-0114d61904938208c75497bdabe82c5dae32b7d2110a4e460d1942f84dc473ba/preserve/00000002/offload.json';ob=read(R/o_path);o=json.loads(ob);m=o['manifest'];receipt=o['receipt'];tokens=bytes.fromhex(o['binding']['source_tokens']);stage=Path(o['binding']['root']).parent
ck(sha(ob)==req['offload_sha256']=='f624da9e33cfa1ad8f2085569dbbad884e3b72c50ae73ac1d6601c9c65b769c0' and req['receipt']==receipt,'fresh request original offload/receipt anchor')
ck(req['transport_identity']==receipt['transport_identity']=='553a31d3776219f2ef54ba0eef449dba08746d0ea8cc6c68ca120a37fe86ac84','recorded original connection identity')
argv=req['argv'];ck(argv[0]=='ssh' and argv[-1]=='cat '+receipt['member'] and 'StrictHostKeyChecking=yes' in argv and 'BatchMode=yes' in argv and 'IdentitiesOnly=yes' in argv,'exact one-member authenticated request metadata')
ck(receipt['member']==receipt['remote']+'/payload.bin','exact receipt member')
ck(len(archive)==res['returned_bytes']==res['expected_bytes']==receipt['bytes']==m['archive_bytes']==3532800,'actual archive exact byte denominator')
ck(sha(archive)==res['returned_sha256']==res['expected_sha256']==receipt['source_sha256']==m['archive_sha256']=='e8ca86cafcd9ef003bd21946e6bbf139f125faeacebde1a6775a1d82cbae0607','actual recovered archive digest')

ck((o['first_batch'],o['batches'],o['start'],o['stop'],o['cells'],o['retired_files'])==(32,16,131072,196608,65536,48),'third-group exact new coverage')
ck(sha(raw(m))==o['binding']['manifest_sha256']=='d759fc4fb00380fff803850d830006f2b181b19c27039b2df82c5492a014df49','third-group original manifest external anchor')
ck(len(tokens)==2688 and o['binding']['first_batch']==32 and o['binding']['batches']==16,'third-group token roster')
h=o['history'];ledger=Path(h['directory']);op=h['intent_sha256'];intentb=read(ledger/h['intent']);completeb=read(ledger/h['complete']);intent=json.loads(intentb);done=json.loads(completeb)
ck(sha(intentb)==op and sha(completeb)==h['complete_sha256'] and intent['binding']==o['binding'] and done['operation_sha256']==op,'third-group actual typed history anchors')
ck(intent['owner']=='c64f82cdaebfcadd2c0227b40ac26bfdf7c53705c0d8f56903f3183c0ea49cc2' and intent['stage']==stage.name and intent['kind']=='mcm-batched-bundle-v3','same actual selected owner/stage')
part=js(ledger/f'typed-part-{op}-000000000000.json');retired=js(ledger/f'typed-grouped-retired-{op}.json')
ck(part['receipt']==receipt and part['receipt_sha256']==sha(raw(receipt)) and part['fresh_full_recovery'] is True and part['operation_sha256']==op and done['parts']==1 and done['parts_sha256']==sha(bytes.fromhex(sha(raw(part)))),'third-group actual typed recovered part')
ck(retired['binding']==o['binding'] and retired['operation_sha256']==op and retired['files']==48 and retired['receipt_sha256']==sha(raw(receipt)),'third-group actual retired completion')
ck(receipt['scope']==sha(raw({'operation':op,'index':0,'bytes':3532800,'sha256':m['archive_sha256']})),'third-group exact receipt scope')

source=read(R/'tradingagents/research/onchain_replication/batched_journal.py');ck(sha(source)=='0d96f0f3fbe7a320161d8bd16ee7d0d0b0de0384cfbce22459dcf9a8aa9e92a4','unchanged accepted original journal parser')
ck(read(stage/'stream/closure-tokens.bin',prefix=2688,offset=5376)==tokens,'current append-only closure segment joins original')
HEADER=struct.Struct('>8sIQQ32s32s');RECORD=struct.Struct('>Q32sdIB');TOKEN=struct.Struct('>QQQ32s')
ck((HEADER.size,RECORD.size,TOKEN.size)==(92,53,56),'original explicit framing widths')
memberdata=[];memberchecks=[]
with tarfile.open(fileobj=io.BytesIO(archive),mode='r:') as tar:
 members=tar.getmembers();ck(len(members)==48==m['files'],'actual exact archive roster count')
 for i,t in enumerate(members):
  d=m['members'][i];dev,ino,size,digest=TOKEN.unpack_from(tokens,56*i)
  ck(t.isfile() and not t.issym() and not t.islnk() and t.name==d['member']==f'files/{96+i:08d}' and t.mode==0o600 and t.linkname=='','actual member regular/name/mode '+str(i))
  ck(t.size==d['bytes']==size,'actual member size '+str(i))
  with tar.extractfile(t) as f:b=f.read(size+1)
  ck(len(b)==size and sha(b)==d['expected_sha256']==digest.hex(),'actual member original body hash '+str(i))
  nread+=len(b);ck(nread<=16*1024**2,'decoded cumulative input cap '+str(i));memberdata.append(b)
  memberchecks.append({'member':t.name,'bytes':len(b),'sha256':sha(b),'mode':t.mode,'uid':t.uid,'gid':t.gid,'mtime':t.mtime})
ck(sum(map(len,memberdata))==m['raw_bytes'],'all original recovered member byte sum')
converted=bytearray();batchchecks=[];scope=None;iterations=0;statuses={0:0,1:0}
for local_batch in range(16):
 batch=32+local_batch
 pending,payload,complete=memberdata[3*local_batch:3*local_batch+3];p=json.loads(pending);c=json.loads(complete)
 ck(raw(p)==pending and raw(c)==complete,'actual canonical journal metadata '+str(batch))
 ck(set(p)=={'schema','kind','start','stop','workload_sha256','disposition'} and p['schema']==3 and p['kind']=='engineering_pending' and p['disposition']=='attempted_unknown_without_complete','actual pending format '+str(batch))
 ck((p['start'],p['stop'])==(4096*batch,4096*(batch+1)),'actual ordered batch range '+str(batch))
 if scope is None:scope=p['workload_sha256']
 ck(p['workload_sha256']==scope and len(scope)==64 and all(x in '0123456789abcdef' for x in scope),'actual shared workload commitment '+str(batch))
 ck(c=={'schema':3,'kind':'engineering_complete','pending_sha256':sha(pending),'payload_sha256':sha(payload),'payload_bytes':len(payload),'record_bytes':53,'purposes_sha256':c['purposes_sha256']},'actual original complete commitments '+str(batch))
 ck(len(payload)==92+4096*53 and HEADER.unpack_from(payload)==(b'MCMBAT03',53,p['start'],p['stop'],bytes.fromhex(sha(pending)),bytes.fromhex(c['purposes_sha256'])),'actual journal binary header '+str(batch))
 purposes=hashlib.sha256()
 for k in range(4096):
  ordinal,purpose,score,it,status=RECORD.unpack_from(payload,92+53*k)
  if not (ordinal==p['start']+k and math.isfinite(score) and 0<=score<=1 and status in (0,1)):raise AssertionError('record framing/range '+str(ordinal))
  purposes.update(purpose);converted.extend(struct.pack('<f',score));iterations+=it;statuses[status]+=1
 ck(purposes.hexdigest()==c['purposes_sha256'],'actual ordered purpose aggregate '+str(batch))
 batchchecks.append({'batch':batch,'start':p['start'],'stop':p['stop'],'purposes_sha256':purposes.hexdigest(),'payload_sha256':sha(payload)})
ck(scope==prior['workload_sha256'],'third-group workload joins accepted preceding-group scope')
spool=read(stage/'stream/scores.f32',prefix=262144,offset=524288);ck(bytes(converted)==spool,'all 65536 recovered f64 values cast by stdlib match observed little-endian f32 segment')
# Repeat only the live observed prefix, because later appends are allowed.
ck(read(stage/'stream/scores.f32',prefix=262144,offset=524288)==spool,'same f32 segment observed twice')
(P/'observed-scores-segment.f32').write_bytes(spool)
result={'disposition':'ACCEPT_ACTUAL_THIRD_GROUP_RECOVERED_BYTES_AND_JOURNAL_SEGMENT_CONSISTENCY','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'input_bytes_including_decoded_members_and_repeat_reads':nread,'input_cap_bytes':16*1024**2,'resources':{'address_space_bytes':384*1024**2,'cpu_seconds':30,'max_output_file_bytes':4*1024**2,'affinity':[3],'nice':10},'read_inventory':reads,'request_sha256':sha(bodies['REQUEST01.json']),'result_sha256':sha(bodies['RESULT01.json']),'archive_sha256':sha(archive),'original_offload_sha256':sha(ob),'member_checks':memberchecks,'batch_checks':batchchecks,'cells':65536,'workload_sha256':scope,'f32_segment':{'start_cell':131072,'stop_cell':196608,'byte_offset':524288,'bytes':len(spool),'sha256':sha(spool),'matches_all_recovered_f64_casts':True,'observed_twice':True,'whole_spool_integrity_claimed':False},'not_tested':['mathematical/scientific correctness of scores or convergence','graph-derived original purpose preimages or cache key equivalence','per-cell provisional receipt stream','full current or future remote availability beyond this recovered object at Root observation','whole-MCM completion, neural training, financial performance or admission','independent private host/key configuration inspection; none read'],'limitations':['SSH execution and authenticated-host selection are recorded Root evidence; reviewer performed no network action','result JSON does not itself hash request; the externally supplied manifest authenticates both request and result and the actual body joins receipt','purpose digest integrity checked against original headers and complete records; graph-purpose reconstruction excluded','f32 comparison is an observed segment only, not a permanent seal or immutable complete spool']}
(P/'REVIEW01.json').write_bytes(raw(result));print(json.dumps({'disposition':result['disposition'],'checks':len(checks),'read_bytes':nread,'review_sha256':sha(raw(result))}))
