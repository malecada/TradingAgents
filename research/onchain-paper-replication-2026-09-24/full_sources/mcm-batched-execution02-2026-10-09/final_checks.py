import importlib.util,json,os,resource,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
assert resource.getrlimit(resource.RLIMIT_AS)[0]==268435456 and resource.getrlimit(resource.RLIMIT_FSIZE)[0]==4194304 and len(os.sched_getaffinity(0))==2
import batch_journal as m
# Third historical RED kept independently; no mutation of01 directory.
q=P.parent/'mcm-batched-execution01-2026-10-09/batch_journal.py';spec=importlib.util.spec_from_file_location('old',q);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
bounds=dict(batch_cells=2,max_cells=4,max_bytes=100000,max_body_bytes=8192)
tasks=[({'ordinal':0},None,None)]
j=old.BatchJournal(P/'red01-purpose',boundary=lambda:None,**bounds)
def change(*args):tasks[0][0]['ordinal']=999;return 0.,1,'iteration_cap'
j.run_batch(tasks,change);assert j.cells==1;j.close()
# Final consumer poison guard, plus metadata/aggregate closure refusal.
tasks=[({'ordinal':0},None,None)]
for mode in ['payload','pending','metadata','mode','links']:
 root=P/('final-'+mode);j=m.BatchJournal(root,boundary=lambda:None,**bounds);j.run_batch(tasks,lambda *args:(0.,1,'iteration_cap'))
 if mode=='payload':(root/'00000000.records.bin').write_bytes(b'bad')
 if mode=='pending':(root/'00000000.pending.json').write_bytes(b'{}')
 if mode=='metadata':(root/'00000000.complete.json').write_bytes(b'{}')
 if mode=='mode':(root/'00000000.records.bin').chmod(0o644)
 if mode=='links':os.link(root/'00000000.records.bin',root/'extra-link')
 try:j.read_complete(0)
 except (ValueError,KeyError):pass
 else:raise AssertionError(mode+' accepted')
 assert j.poisoned;j.close()
# Exact encoded-byte arithmetic, no graph inputs or numerical runtime.
N=415968128;B=4096;batch_count=(N+B-1)//B;metadata=0;payload=0
for start in range(0,N,B):
 stop=min(N,start+B);extent=m.HEADER.size+(stop-start)*m.RECORD.size
 pending=m.body({'schema':2,'kind':'engineering_pending','start':start,'stop':stop,'purposes_sha256':'0'*64,'disposition':'attempted_unknown_without_complete'})
 complete=m.body({'schema':2,'kind':'engineering_complete','pending_sha256':'0'*64,'payload_sha256':'0'*64,'payload_bytes':extent,'record_bytes':m.RECORD.size})
 metadata+=len(pending)+len(complete);payload+=extent
result={'status':'PASS','historical_purpose_defect_reproduced':True,'consumer_poison_refusals':['payload','pending','metadata','mode','links'],'cells':N,'batch_cells':B,'batches':batch_count,'record_bytes':m.RECORD.size,'record_payload_bytes':N*m.RECORD.size,'header_bytes_per_batch':m.HEADER.size,'binary_bytes_with_headers':payload,'json_metadata_bytes':metadata,'total_logical_ledger_bytes':payload+metadata,'qualification':'Conditional encoded bodies only; excludes allocation rounding/inodes/directories, checkpoints, graphs, outputs, transport, source controls, other receipts and failures. SHA contents have fixed width; ranges/last-batch extent evaluated exactly.'}
(P/'FINAL_CHECKS01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
