import resource
resource.setrlimit(resource.RLIMIT_AS,(384*1024**2,384*1024**2));resource.setrlimit(resource.RLIMIT_CPU,(30,30));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2))
from pathlib import Path
import hashlib,json,os,stat,struct,tarfile,io,math,datetime
P=Path(__file__).resolve().parent;F=P.parent;R=P.parents[3];A=F/'pilot29-first-group-actual-recovery01-2026-10-10';V=F/'pilot29-first-group-review01-2026-10-10'
reads={};nread=0;checks=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def raw(v):return (json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def ck(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def read(p,limit=4*1024**2,prefix=None):
 global nread
 p=Path(p)
 with p.open('rb') as h:
  a=os.fstat(h.fileno());b=h.read((limit+1) if prefix is None else prefix);z=os.fstat(h.fileno())
 ck(len(b)<=limit and (a.st_dev,a.st_ino)==(z.st_dev,z.st_ino),'bounded body and inode '+p.name)
 ck(a.st_size==z.st_size==len(b) if prefix is None else len(b)==prefix and a.st_size>=prefix and z.st_size>=prefix,'body/prefix extent '+p.name)
 nread+=len(b);ck(nread<=16*1024**2,'input aggregate bound '+p.name)
 reads[str(p.relative_to(R))]={'bytes':len(b),'sha256':sha(b),'prefix':prefix is not None,'before_size':a.st_size,'after_size':z.st_size,'device':z.st_dev,'inode':z.st_ino}
 return b
def js(p):return json.loads(read(p))
manb=read(A/'MANIFEST01.json');ck(sha(manb)=='69402c432696dd0d203f3e11ea4cdffc48ce843ddd9813fa9fc7a9e2760b54c3','external fresh recovery manifest anchor');man=json.loads(manb);bodies={}
for name,d in man['files'].items():
 b=read(A/name);ck(len(b)==d['bytes'] and sha(b)==d['sha256'],'actual fresh output manifest '+name);bodies[name]=b
req=json.loads(bodies['REQUEST01.json']);res=json.loads(bodies['RESULT01.json']);archive=bodies['returned-first-group.tar']
ck(res['actual_exit']==0 and res['actual_error'] is None and res['exact_match'] is True and len(bodies['ssh.stderr'])==0,'recorded actual SSH result')
prior=js(V/'REVIEW01.json');ck(sha(read(V/'REVIEW01.json'))=='0b3020957edb0f5de31529f7d10e7473af0ca7042797e15f8dacac528e4ded90','prior accepted narrow review anchor')
o_path=next(k for k in prior['inventory'] if k.endswith('/offload.json'));ob=read(R/o_path);o=json.loads(ob);m=o['manifest'];receipt=o['receipt'];tokens=bytes.fromhex(o['binding']['source_tokens']);stage=Path(o['binding']['root']).parent
ck(sha(ob)==req['offload_sha256']==prior['offload_sha256'] and req['receipt']==receipt,'fresh request original offload/receipt anchor')
ck(req['transport_identity']==receipt['transport_identity']=='553a31d3776219f2ef54ba0eef449dba08746d0ea8cc6c68ca120a37fe86ac84','recorded original connection identity')
argv=req['argv'];ck(argv[0]=='ssh' and argv[-1]=='cat '+receipt['member'] and 'StrictHostKeyChecking=yes' in argv and 'BatchMode=yes' in argv and 'IdentitiesOnly=yes' in argv,'exact one-member authenticated request metadata')
ck(receipt['member']==receipt['remote']+'/payload.bin','exact receipt member')
ck(len(archive)==res['returned_bytes']==res['expected_bytes']==receipt['bytes']==m['archive_bytes']==3532800,'actual archive exact byte denominator')
ck(sha(archive)==res['returned_sha256']==res['expected_sha256']==receipt['source_sha256']==m['archive_sha256']=='8a3b369dff972bed939fade9a32084200a7781722310f458adf736db99f1eb4e','actual recovered archive digest')
source=read(R/'tradingagents/research/onchain_replication/batched_journal.py');ck(sha(source)=='0d96f0f3fbe7a320161d8bd16ee7d0d0b0de0384cfbce22459dcf9a8aa9e92a4','unchanged accepted original journal parser')
ck(read(stage/'stream/closure-tokens.bin',prefix=2688)==tokens,'current append-only closure prefix joins original')
HEADER=struct.Struct('>8sIQQ32s32s');RECORD=struct.Struct('>Q32sdIB');TOKEN=struct.Struct('>QQQ32s')
ck((HEADER.size,RECORD.size,TOKEN.size)==(92,53,56),'original explicit framing widths')
memberdata=[];memberchecks=[]
with tarfile.open(fileobj=io.BytesIO(archive),mode='r:') as tar:
 members=tar.getmembers();ck(len(members)==48==m['files'],'actual exact archive roster count')
 for i,t in enumerate(members):
  d=m['members'][i];dev,ino,size,digest=TOKEN.unpack_from(tokens,56*i)
  ck(t.isfile() and not t.issym() and not t.islnk() and t.name==d['member']==f'files/{i:08d}' and t.mode==0o600 and t.linkname=='','actual member regular/name/mode '+str(i))
  ck(t.size==d['bytes']==size,'actual member size '+str(i))
  with tar.extractfile(t) as f:b=f.read(size+1)
  ck(len(b)==size and sha(b)==d['expected_sha256']==digest.hex(),'actual member original body hash '+str(i))
  nread+=len(b);ck(nread<=16*1024**2,'decoded cumulative input cap '+str(i));memberdata.append(b)
  memberchecks.append({'member':t.name,'bytes':len(b),'sha256':sha(b),'mode':t.mode,'uid':t.uid,'gid':t.gid,'mtime':t.mtime})
ck(sum(map(len,memberdata))==m['raw_bytes']==3483544,'all original recovered member byte sum')
converted=bytearray();batchchecks=[];scope=None;iterations=0;statuses={0:0,1:0}
for batch in range(16):
 pending,payload,complete=memberdata[3*batch:3*batch+3];p=json.loads(pending);c=json.loads(complete)
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
ck(scope==prior['next_pending']['workload_sha256'],'recovered workload joins independently retained next batch scope')
spool=read(stage/'stream/scores.f32',prefix=262144);ck(bytes(converted)==spool,'all 65536 recovered f64 values cast by stdlib match observed little-endian f32 prefix')
# Repeat only the live observed prefix, because later appends are allowed.
ck(read(stage/'stream/scores.f32',prefix=262144)==spool,'same f32 prefix observed twice')
(P/'observed-scores-prefix.f32').write_bytes(spool)
result={'disposition':'ACCEPT_ACTUAL_FIRST_GROUP_RECOVERED_BYTES_AND_JOURNAL_PREFIX_CONSISTENCY','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'input_bytes_including_decoded_members_and_repeat_reads':nread,'input_cap_bytes':16*1024**2,'resources':{'address_space_bytes':384*1024**2,'cpu_seconds':30,'max_output_file_bytes':4*1024**2,'affinity':[3],'nice':10},'read_inventory':reads,'request_sha256':sha(bodies['REQUEST01.json']),'result_sha256':sha(bodies['RESULT01.json']),'archive_sha256':sha(archive),'original_offload_sha256':sha(ob),'member_checks':memberchecks,'batch_checks':batchchecks,'cells':65536,'workload_sha256':scope,'f32_prefix':{'bytes':len(spool),'sha256':sha(spool),'matches_all_recovered_f64_casts':True,'observed_twice':True,'whole_spool_integrity_claimed':False},'not_tested':['mathematical/scientific correctness of scores or convergence','graph-derived original purpose preimages or cache key equivalence','per-cell provisional receipt stream','full current or future remote availability beyond this recovered object at Root observation','whole-MCM completion, neural training, financial performance or admission','independent private host/key configuration inspection; none read'],'limitations':['SSH execution and authenticated-host selection are recorded Root evidence; reviewer performed no network action','result JSON does not itself hash request; the externally supplied manifest authenticates both request and result and the actual body joins receipt','purpose digest integrity checked against original headers and complete records; graph-purpose reconstruction excluded','f32 comparison is an observed prefix only, not a permanent seal or immutable complete spool']}
(P/'REVIEW01.json').write_bytes(raw(result));print(json.dumps({'disposition':result['disposition'],'checks':len(checks),'read_bytes':nread,'review_sha256':sha(raw(result))}))
