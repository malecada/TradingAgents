"""Tiny local semantic composition only. No Owner, transport, or admission."""
from pathlib import Path
H=Path(__file__).resolve().parent
# Reuse only fixture setup; no previous test execution or native authority imports.
setup=(H/'functional01.py').read_text().split("root=H/'tiny-stage'")[0]
exec(compile(setup,str(H/'functional01.py'),'exec'))
semantic=load(package+'.batched_offload_semantics',candidate('batched_offload_semantics.py'))
from tradingagents.research.onchain_replication import preservation
consume_fn=actual_function(candidate('registered_offload.py'),'_consume_recovered',{'os':os,'require':io._require})
work=H/'recovery-fixture';work.mkdir();j=mods['journal'].BatchJournal(work/'matching',batch_cells=48,max_cells=64,max_bytes=200000,max_body_bytes=1024,boundary=lambda:None)
spool=bytearray();captured=[];trace=[]
def sink(ordinal,center,motif,payload):
 assert ordinal*4==len(spool);spool.extend(payload)
def post(journal,batch,token,original):
 trace.append(('post',batch));rows=[]
 for i,suffix in enumerate(mods['driver'].SUFFIXES):
  p=journal.root/(f'{batch:08d}'+suffix);st=p.stat();_,_,size,digest=mods['driver'].TOKEN.unpack_from(token,i*56)
  rows.append({'source_path':str(p),'resolved_path':str(p),'bytes':size,'mtime_ns':st.st_mtime_ns,'expected_sha256':digest.hex()})
 archive=work/f'batch-{batch}.tar';manifest=preservation.build_bundle(rows,archive,allowed_roots=[journal.root],start_index=batch*3)
 evidence=semantic.recover(archive.read_bytes(),manifest,journal,batch,token,work/f'first-{batch}')
 # Synthetic local fixture retirement only, after actual original-byte recovery.
 for suffix in semantic.SUFFIXES:(journal.root/(f'{batch:08d}'+suffix)).unlink()
 captured.append((archive,manifest,bytes(token)))
def compare(batch,rows):
 expected=np.asarray([r[2] for r in rows],dtype='<f8').astype('<f4').tobytes()
 assert spool[4*rows[0][0]:4*(rows[-1][0]+1)]==expected
 trace.append(('compare',batch))
def final(journal,tokens,count,original):
 for batch,(archive,manifest,token) in enumerate(captured):
  directory=work/f'final-{batch}'
  evidence=semantic.recover(archive.read_bytes(),manifest,journal,batch,token,directory)
  consume_fn(journal,evidence,batch,directory,compare)
  assert bytes(tokens[batch*168:(batch+1)*168])==token
 trace.append(('final',count))
config={'rows':2,'cells':64,'motifs':32,'graph_hash':graph_hash(g),'node_order_hash':node_order_hash(g.node_ids),'workload_sha256':'d'*64,'purpose_schema_version':2}
result=mods['driver'].drive(g,dictionary,descriptor=config,policy={'max_buffer_bytes':100000,'edge_chunk':2,'extraction_limit':3},journal=j,executor=Executor(None,None,None,None),consumer=sink,max_chunk_bytes=128,max_closure_token_bytes=336,post_batch=post,final_batches=final)
assert result['completed_cells']==64 and j.closed and not list(j.root.iterdir()) and trace==[('post',0),('post',1),('compare',0),('compare',1),('final',2)]
# Changed consumer seam must rejoin recovered files after the callback.
batch=1;archive,manifest,token=captured[batch];directory=work/'mutated';evidence=semantic.recover(archive.read_bytes(),manifest,j,batch,token,directory)
def corrupt(b,rows):(directory/'tree'/f'{b:08d}.records.bin').write_bytes(b'bad')
try:consume_fn(j,evidence,batch,directory,corrupt)
except ValueError:pass
else:raise AssertionError('consumer mutation admitted')
# Exact class identity is substantive: duplicate journal module cannot bind.
duplicate=load('different_journal_class',candidate('batched_journal.py'));other=duplicate.BatchJournal(work/'different',batch_cells=48,max_cells=64,max_bytes=200000,max_body_bytes=1024,boundary=lambda:None)
try:semantic.binding(other,0,token,manifest)
except ValueError:pass
else:raise AssertionError('duplicate class admitted')
finally:other.close()
# Policy4 is explicit; old3 cannot silently select the new route.
assert m.selected({'schema_version':4}) and not m.selected({'schema_version':3})
report={'synthetic_only':True,'cells':64,'actual_apis':['driver hooks','journal03','preservation.build_bundle/verify_bundle','semantic.recover','registered_offload._consume_recovered'],'trace':trace,'post_consumer_corruption_refused':True,'duplicate_journal_class_refused':True,'genuine_owner_or_transport_executed':False,'affinity':sorted(os.sched_getaffinity(0))}
(H/'RECOVERY_RESULT01.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
