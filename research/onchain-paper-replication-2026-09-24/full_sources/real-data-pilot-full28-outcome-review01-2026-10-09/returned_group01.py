from pathlib import Path
import ast,io,json,math,struct,hashlib,tarfile,os,stat,resource,signal
R=Path.cwd();D=Path(__file__).resolve().parent;F=D.parent;T=F/'real-data-pilot-full28-group-fresh-return01-2026-10-09'
os.sched_setaffinity(0,{3});os.nice(10)
for k,v in [(resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_FSIZE,4*1024**2),(resource.RLIMIT_CPU,30)]:resource.setrlimit(k,(v,v))
signal.alarm(30);(D/'RETURN_LIMITER01.json').write_text(json.dumps({'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'AS':resource.getrlimit(resource.RLIMIT_AS),'FSIZE':resource.getrlimit(resource.RLIMIT_FSIZE),'CPU':resource.getrlimit(resource.RLIMIT_CPU),'alarm':30})+'\n')
evidence={};readbytes=0;memberbytes=0;sha=lambda b:hashlib.sha256(b).hexdigest();sig=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def read(p,cap=1048576):
 global readbytes
 p=Path(p);fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  st=os.fstat(fd);assert stat.S_ISREG(st.st_mode) and st.st_nlink==1 and st.st_size<=cap and sig(st)==sig(p.lstat());data=os.read(fd,cap+1);assert len(data)==st.st_size and sig(st)==sig(os.fstat(fd))==sig(p.lstat())
 finally:os.close(fd)
 readbytes+=len(data);assert readbytes+memberbytes<=12*1024**2;evidence[str(p.relative_to(R))]=sha(data);return data
load=lambda p:json.loads(read(p))
prior=load(D/'OUTCOME_REVIEW01.json');ret=load(T/'RETURN01.json');transport=load(T/'original-group-return01.tar.transport.json');assert transport['status']=='complete' and transport['returncode']==0 and transport['received_bytes']==transport['expected_bytes']==ret['returned_bytes']==3532800
ob=read(R/ret['original_offload_path']);assert sha(ob)==ret['original_offload_sha256'];off=json.loads(ob);manifest=off['manifest'];assert off['receipt']['transport_identity']==ret['transport_identity'] and off['receipt']['member']==ret['remote_member'];archive=read(R/ret['returned_path'],4*1024**2);assert sha(archive)==ret['returned_sha256']==manifest['archive_sha256']==off['receipt']['source_sha256']
source=R/'tradingagents/research/onchain_replication/batched_journal.py';sb=read(source);claim=load(R/'research_runs'/prior['identity']/'claim.json');assert sha(sb)==claim['experiment']['source_files'][str(source.relative_to(R))]
tree=ast.parse(sb);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='BatchJournal');method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_read_complete');ns={'json':json,'math':math,'hashlib':hashlib,'struct':struct,'digest':sha,'RECORD':struct.Struct('>Q32sdIB'),'HEADER':struct.Struct('>8sIQQ32s32s'),'MAGIC':b'MCMBAT03','STATUS':{'temperature_complete':0,'iteration_cap':1}}
def require(ok,message):
 if not ok:raise ValueError(message)
ns['require']=require;exec(compile(ast.Module(body=[method],type_ignores=[]),str(source),'exec'),ns)
cache={};members=[];tokens=bytes.fromhex(off['binding']['source_tokens'])
with tarfile.open(fileobj=io.BytesIO(archive),mode='r:') as tar:
 roster=tar.getmembers();assert len(roster)==48
 for i,(m,row) in enumerate(zip(roster,manifest['members'])):
  assert m.isfile() and not m.issym() and not m.islnk() and m.name==row['member']==f'files/{i:08d}' and m.size==row['bytes']
  b=tar.extractfile(m).read();memberbytes+=len(b);assert len(b)==row['bytes'] and sha(b)==row['expected_sha256'];dev,ino,size,h=struct.unpack_from('>QQQ32s',tokens,i*56);assert size==len(b) and h.hex()==sha(b)
  suffix=('.pending.json','.records.bin','.complete.json')[i%3];name=f'{i//3:08d}'+suffix;assert Path(row['source_path']).name==name;cache[name]=(b,(dev,ino));members.append({'name':m.name,'original_name':name,'bytes':len(b),'sha256':sha(b),'mode':m.mode,'type':'regular'})
assert memberbytes==manifest['raw_bytes']==3483544
class Snapshot:
 max_cells=415968128;batch_cells=4096
 def _read(self,name,expected=None,pin=None):
  b,p=cache[name]
  if expected is not None:assert b==expected
  if pin is not None:assert p==pin
  return b,p
stage=Path(off['binding']['root']).parent;origin=read(stage/'stream/numeric-origins.bin');scores=read(stage/'stream/scores.f32');streamtokens=read(stage/'stream/closure-tokens.bin');assert streamtokens==tokens and len(origin)==65536*9 and len(scores)==65536*4
cursor=0;computed=reused=0;ranges=[]
for i in range(16):
 rows=ns['_read_complete'](Snapshot(),i);assert len(rows)==4096 and rows[0][0]==cursor and rows[-1][0]+1==cursor+4096
 summary=load(stage/f'stream/numeric-batches/{i:012d}.json');segment=origin[cursor*9:(cursor+4096)*9];assert sha(segment)==summary['origin_sha256'];nc=nr=0
 for offset,(mode,sourceordinal) in enumerate(struct.iter_unpack('>BQ',segment)):
  ordinal=cursor+offset;assert (mode==0 and sourceordinal==ordinal) or (mode==1 and sourceordinal<ordinal);nc+=mode==0;nr+=mode==1
 assert (nc,nr)==(summary['computed'],summary['reused']);computed+=nc;reused+=nr;ranges.append([cursor,cursor+4096]);cursor+=4096
assert cursor==65536 and computed==63904 and reused==1632 and readbytes+memberbytes<=12*1024**2
out={'decision':'accepted_fresh_original_group_byte_and_journal_semantic_return','identity':prior['identity'],'evidence':evidence,'returned_archive_sha256':sha(archive),'archive_bytes':len(archive),'members':members,'member_payload_bytes':memberbytes,'actual_disk_read_bytes':readbytes,'logical_read_plus_member_parse_bytes':readbytes+memberbytes,'read_cap_bytes':12*1024**2,'journal_semantics':{'parser':'Exact original pinned BatchJournal._read_complete AST on immutable archive-member bytes with original token identities; no constructor/Owner','ranges':ranges,'record_width':53,'header_width':92,'records':65536,'finite_score_status_and_ordered_purpose_digest_verified':True},'origin_metadata':{'computed':computed,'reused':reused,'ordinal_mode_rules_and_batch_hashes_verified':True,'bytes':len(origin)},'spool':{'bytes':len(scores),'sha256':sha(scores),'qualification':'Opaque bytes and exact extent only; no numerical f64-to-f32 recomputation or score interpretation.'},'unchanged_disposition':{'run':'FAILED','confirmed_post_sink_cells':61440,'journal_cells':65536,'whole_MCMs':0,'training':None,'no_retry':True},'qualifications':['Fresh returned bytes hash-match original typed receipt/manifest and transport reports complete/exit0; not merely archive existence.','Original fixed journal semantics parsed independently for all16 batches; actual source-token/member binding and original first-three review evidence retained.','Purpose digests are authenticated, but purpose-to-original-graph semantic reconstruction, numeric solver correctness and cache equivalence are not recomputed.','No final grouped spool-cast/full graph/model completion, POSIX restoration, current/future remote availability guarantee, deletion authority or new scientific claim.','Original OUTCOME_REVIEW01 remains unchanged; this is its pending archive-proof supplement.']}
p=D/'RETURNED_GROUP_REVIEW01.json';p.write_text(json.dumps(out,indent=2)+'\n');print(sha(p.read_bytes()),readbytes+memberbytes)
