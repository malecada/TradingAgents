import pathlib,json,hashlib,os,stat,struct,math,ast,types,datetime
ROOT=pathlib.Path.cwd();R=pathlib.Path(__file__).resolve().parent;F=R.parent;E=F/'real-data-pilot-full28-entry01-2026-10-09';h=lambda b:hashlib.sha256(b).hexdigest();evidence={}
def sig(s):return(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def stable(p,cap):
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  before=os.fstat(fd);assert stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size<=cap and sig(before)==sig(p.lstat())
  raw=os.read(fd,cap+1);assert len(raw)==before.st_size and sig(before)==sig(os.fstat(fd))==sig(p.lstat())
 finally:os.close(fd)
 evidence[str(p.relative_to(ROOT))]=h(raw);return raw,before
obsraw,_=stable(E/'FIRST_BATCH_OBSERVATION01.json',20000);obs=json.loads(obsraw)
sraw,_=stable(ROOT/obs['original_numeric_summary']['path'],4096);summary=json.loads(sraw);assert h(sraw)==obs['original_numeric_summary']['sha256'];capt,_=stable(E/'FIRST_NUMERIC_SUMMARY01.json',4096);assert capt==sraw
meta_path=ROOT/obs['original_matching_closure']['path'];root=meta_path.parent;stage=root.parent;cache={}
for suffix,cap in (('.pending.json',4096),('.records.bin',217180),('.complete.json',4096)):
 path=root/('00000000'+suffix);cache[path.name]=stable(path,cap)
assert h(cache[meta_path.name][0])==obs['original_matching_closure']['sha256']
# Exact existing pure validation body, with a cached read adapter; no journal/Owner constructor.
source=ROOT/'tradingagents/research/onchain_replication/batched_journal.py';raw,_=stable(source,100000);tree=ast.parse(raw);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='BatchJournal');method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_read_complete');ns={'json':json,'hashlib':hashlib,'math':math,'RECORD':struct.Struct('>Q32sdIB'),'HEADER':struct.Struct('>8sIQQ32s32s'),'MAGIC':b'MCMBAT03','STATUS':{'temperature_complete':0,'iteration_cap':1},'digest':h}
def require(ok,msg):
 if not ok:raise ValueError(msg)
ns['require']=require;exec(compile(ast.Module(body=[method],type_ignores=[]),str(source),'exec'),ns)
class Snapshot:
 max_cells=415968128;batch_cells=4096
 def _read(self,name,expected=None,pin=None):
  raw,st=cache[name];assert sig((root/name).lstat())==sig(st)
  if expected is not None:assert raw==expected
  actual=(st.st_dev,st.st_ino)
  if pin is not None:assert pin==actual
  return raw,actual
records=ns['_read_complete'](Snapshot(),0);assert len(records)==4096
pending=json.loads(cache['00000000.pending.json'][0]);assert [pending['start'],pending['stop']]==[0,4096]
# One bounded first-batch prefix read for each actively appendable stream.
streams={};prefixes={}
for name,n in [('scores.f32',16384),('closure-tokens.bin',168),('numeric-origins.bin',36864)]:
 p=stage/'stream'/name;fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  before=os.fstat(fd);assert stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size>=n
  body=os.pread(fd,n,0);after=os.fstat(fd);entry=p.lstat();assert len(body)==n and (before.st_dev,before.st_ino)==(after.st_dev,after.st_ino)==(entry.st_dev,entry.st_ino) and before.st_size<=after.st_size<=entry.st_size
  if before.st_size==after.st_size:assert sig(before)==sig(after)
 finally:os.close(fd)
 prefixes[name]=body;streams[name]={'path':str(p.relative_to(ROOT)),'prefix_bytes':n,'prefix_sha256':h(body),'before_extent':before.st_size,'after_extent':after.st_size,'entry_extent':entry.st_size,'whole_file_hash_claimed':False}
for index,suffix in enumerate(('.pending.json','.records.bin','.complete.json')):
 dev,ino,n,digest=struct.Struct('>QQQ32s').unpack_from(prefixes['closure-tokens.bin'],index*56);raw,st=cache['00000000'+suffix];assert (dev,ino,n,digest)==(st.st_dev,st.st_ino,len(raw),hashlib.sha256(raw).digest())
assert h(prefixes['numeric-origins.bin'])==summary['origin_sha256']=='5afd467f7936579c7aa3bb9023503c57ec0555977f6bf3c7b894f233ba84cc8c'
assert summary['computed']==4000 and summary['reused']==96 and summary['computed']+summary['reused']==summary['stop']-summary['start']==len(records)
c=summary['counters'];assert c['authority_poll_calls']==28795 and c['authority_poll_failures']==0 and c['authority_poll_ns']==1602536835417
elapsed=summary['elapsed_seconds'];callback=c['authority_poll_ns']/1e9;assert elapsed==3360.272647872902
claimraw,_=stable(ROOT/'research_runs'/obs['identity']/'claim.json',1500000);claim=json.loads(claimraw);assert claim['experiment']['source_files'][str(source.relative_to(ROOT))]==h(raw if False else source.read_bytes())
for filename in ('batched_driver.py','batched_numeric_execution.py','batched_numeric_reuse.py'):
 p=source.parent/filename;body,_=stable(p,200000);assert claim['experiment']['source_files'][str(p.relative_to(ROOT))]==h(body)
v={'decision':'accepted_first_engineering_batch_partial_progress_only','identity':obs['identity'],'source':claim['source'],'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'evidence':evidence,'journal':{'exact_existing_parser':'BatchJournal._read_complete AST body with stable cached read adapter; no constructor or authority','header_bytes':92,'record_bytes':53,'records':4096,'range':[0,4096],'payload_bytes':217180,'ordered_ordinals_and_purpose_aggregate_valid':True,'finite_score_range_and_status_valid':True,'closed_record_token_triplet_matches_original_inodes_extents_hashes':True},'streams':streams,'numeric_summary':summary,'timing':{'elapsed_seconds':elapsed,'inclusive_callback_seconds':callback,'callback_share_percent':100*callback/elapsed,'residual_noncallback_elapsed_seconds':elapsed-callback,'qualification':'Inclusive measured callback wall/bookkeeping time; residual includes noncallback work and waits, not pure solverCPU. Counters do not identify causal system bottleneck.'},'qualifications':['No per-cell score values emitted; parser validates actual53-byte records but does not prove graph-purpose semantic equivalence or recompute scores.','Opaque origins authenticated first-batch prefix; receipt_sha256 cannot be recomputed without original provisional receipt stream.','Appendable streams read once at bounded prefix; unchangedinode/nondecreasingextent checked. Prefix snapshot and journal token joins do not prove future byte immutability or writer exclusion.','No capturepost_sink/group/offload/wholegraph/MCM/training or final scientific completion credited. Run remains active; no terminal cleanup/accounting/release assertion.','No numerical imports, original graph arrays, empirical recomputation, network, Main/Git/cap/claim/process changes.']}
(R/'PROGRESS_REVIEW01.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps({'sha256':h((R/'PROGRESS_REVIEW01.json').read_bytes()),'timing':v['timing']}))
