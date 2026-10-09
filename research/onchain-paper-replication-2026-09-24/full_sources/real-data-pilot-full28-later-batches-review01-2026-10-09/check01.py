import pathlib,json,hashlib,os,stat,struct,math,ast,resource,signal,datetime
ROOT=pathlib.Path.cwd();R=pathlib.Path(__file__).resolve().parent;F=R.parent;E=F/'real-data-pilot-full28-entry01-2026-10-09';os.sched_setaffinity(0,{3});os.nice(10)
for k,v in ((resource.RLIMIT_AS,512*1024**2),(resource.RLIMIT_CPU,30),(resource.RLIMIT_FSIZE,4*1024**2)):resource.setrlimit(k,(v,v))
signal.setitimer(signal.ITIMER_REAL,30)
(R/'LIMITS01.json').write_text(json.dumps({'affinity':list(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'AS':resource.getrlimit(resource.RLIMIT_AS),'CPU':resource.getrlimit(resource.RLIMIT_CPU),'FSIZE':resource.getrlimit(resource.RLIMIT_FSIZE),'wall_remaining':signal.getitimer(signal.ITIMER_REAL)[0]})+'\n')
h=lambda b:hashlib.sha256(b).hexdigest();ev={};readbytes=0
sig=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def stable(p,cap):
 global readbytes
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  st=os.fstat(fd);assert stat.S_ISREG(st.st_mode) and st.st_nlink==1 and st.st_size<=cap and sig(st)==sig(p.lstat());raw=os.read(fd,cap+1);readbytes+=len(raw);assert len(raw)==st.st_size and sig(st)==sig(os.fstat(fd))==sig(p.lstat())
 finally:os.close(fd)
 assert readbytes<=3*1024**2;ev[str(p.relative_to(ROOT))]=h(raw);return raw,st
priorpath=F/'real-data-pilot-full28-first-batch-review01-2026-10-09/PROGRESS_REVIEW01.json';raw,_=stable(priorpath,100000);assert h(raw)=='25f072d0c1cc3b0c27da1cbe98a625db6edb8260893d9db1558cada3831a4b9a';prior=json.loads(raw)
raw,_=stable(E/'BATCH_PROGRESS_OBSERVATION02.json',30000);obs=json.loads(raw);assert len(obs['entries'])==3
source=ROOT/'tradingagents/research/onchain_replication/batched_journal.py';raw,_=stable(source,100000);assert h(raw)==prior['evidence'][str(source.relative_to(ROOT))]
tree=ast.parse(raw);cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='BatchJournal');method=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='_read_complete');ns={'json':json,'hashlib':hashlib,'math':math,'RECORD':struct.Struct('>Q32sdIB'),'HEADER':struct.Struct('>8sIQQ32s32s'),'MAGIC':b'MCMBAT03','STATUS':{'temperature_complete':0,'iteration_cap':1},'digest':h}
def require(ok,message):
 if not ok:raise ValueError(message)
ns['require']=require;exec(compile(ast.Module(body=[method],type_ignores=[]),str(source),'exec'),ns)
cache={};summaries={};root=None
for row in obs['entries'][1:]:
 p=ROOT/row['path'];raw,_=stable(p,4096);assert h(raw)==row['sha256'] and json.loads(raw)==row['summary'];summary=json.loads(raw);batch=summary['batch'];assert batch in (1,2);summaries[batch]=summary
 complete=ROOT/row['matching_closure']['path'];root=complete.parent
 for suffix,cap in (('.pending.json',4096),('.complete.json',4096),('.records.bin',217180)):
  p=root/(f'{batch:08d}'+suffix);cache[p.name]=stable(p,cap)
 assert h(cache[complete.name][0])==row['matching_closure']['sha256']
class Snapshot:
 max_cells=415968128;batch_cells=4096
 def _read(self,name,expected=None,pin=None):
  raw,st=cache[name];assert sig((root/name).lstat())==sig(st);actual=(st.st_dev,st.st_ino)
  if expected is not None:assert raw==expected
  if pin is not None:assert actual==pin
  return raw,actual
for batch in (1,2):
 rows=ns['_read_complete'](Snapshot(),batch);assert len(rows)==4096;pending=json.loads(cache[f'{batch:08d}.pending.json'][0]);assert [pending['start'],pending['stop']]==[batch*4096,(batch+1)*4096];del rows
streams={};prefixes={}
for name,n in [('scores.f32',3*16384),('closure-tokens.bin',3*168),('numeric-origins.bin',3*36864)]:
 p=root.parent/'stream'/name;fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  st=os.fstat(fd);assert stat.S_ISREG(st.st_mode) and st.st_nlink==1 and st.st_size>=n;raw=os.pread(fd,n,0);readbytes+=len(raw);after=os.fstat(fd);entry=p.lstat();assert len(raw)==n and (st.st_dev,st.st_ino)==(after.st_dev,after.st_ino)==(entry.st_dev,entry.st_ino) and st.st_size<=after.st_size<=entry.st_size
  if st.st_size==after.st_size:assert sig(st)==sig(after)
 finally:os.close(fd)
 prefixes[name]=raw;streams[name]={'path':str(p.relative_to(ROOT)),'read_prefix_bytes':n,'before_extent':st.st_size,'after_extent':after.st_size,'entry_extent':entry.st_size,'whole_file_hash_claimed':False}
results=[];previous=obs['entries'][0]['summary']
for batch in (1,2):
 summary=summaries[batch];assert summary['computed']+summary['reused']==4096 and summary['start']==batch*4096 and summary['stop']==(batch+1)*4096
 for offset,suffix in enumerate(('.pending.json','.records.bin','.complete.json')):
  actual=struct.Struct('>QQQ32s').unpack_from(prefixes['closure-tokens.bin'],batch*168+offset*56);raw,st=cache[f'{batch:08d}'+suffix];assert actual==(st.st_dev,st.st_ino,len(raw),hashlib.sha256(raw).digest())
 origin=prefixes['numeric-origins.bin'][batch*36864:(batch+1)*36864];assert h(origin)==summary['origin_sha256']
 nsdelta=summary['counters']['authority_poll_ns']-previous['counters']['authority_poll_ns'];calls=summary['counters']['authority_poll_calls']-previous['counters']['authority_poll_calls'];assert nsdelta>=0 and calls>=0 and summary['counters']['authority_poll_failures']==0
 results.append({'batch':batch,'range':[summary['start'],summary['stop']],'records':4096,'record_bytes':53,'header_bytes':92,'payload_bytes':217180,'ordered_purpose_digest_valid':True,'token_inodes_extents_hashes_match':True,'computed':summary['computed'],'reused':summary['reused'],'opaque_origin_segment_sha256':h(origin),'opaque_score_segment_sha256':h(prefixes['scores.f32'][batch*16384:(batch+1)*16384]),'opaque_token_segment_sha256':h(prefixes['closure-tokens.bin'][batch*168:(batch+1)*168]),'elapsed_seconds':summary['elapsed_seconds'],'callback_delta_calls':calls,'callback_delta_seconds':nsdelta/1e9,'callback_share_percent':100*nsdelta/1e9/summary['elapsed_seconds'],'noncallback_residual_seconds':summary['elapsed_seconds']-nsdelta/1e9});previous=summary
assert readbytes<=3*1024**2
v={'decision':'accepted_partial_engineering_batches1_and2_only','identity':obs['identity'] if 'identity' in obs else prior['identity'],'source':prior['source'],'evidence':ev,'batches':results,'new_partial_cells_authenticated':8192,'first_batch_reused_cells':4096,'total_first_three_engineering_cells':12288,'streams':streams,'actual_read_bytes':readbytes,'read_cap_bytes':3*1024**2,'parser_scope':'Exact original pure BatchJournal._read_complete AST with stable single-read cached bodies, no constructor/Owner; validates finite scores/status/range/ordered purpose aggregate without emitting per-cell values.','qualifications':['Prefix reads bounded through batch2 regardless of current append extent; monotonic size and inode checks are observations, not writer exclusion or future immutability. First-batch binary not parsed again.','Opaque origin and score byte segments only; no numerical recomputation or original graph/feature reads. Token joins do not grant post_sink/group/offload proof.','Cumulative timing counters differenced; callback wall intervals inclusive, residual not pure solverCPU and no population ETA.','No whole graph/MCM/training, terminal cleanup/accounting, capacity/release/claim/native execution or network assertion.','Provisional receipt stream hash and purpose-to-original-graph semantics not independently reconstructed.'],'at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(R/'PROGRESS_REVIEW01.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps({'sha256':h((R/'PROGRESS_REVIEW01.json').read_bytes()),'read_bytes':readbytes}))
