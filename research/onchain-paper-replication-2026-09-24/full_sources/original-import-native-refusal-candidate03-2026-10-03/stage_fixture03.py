"""Fabricated retained-format bytes; no real Owner, matcher, unit or claim."""
import hashlib,json,struct
from pathlib import Path
from refusal_evidence import key,canonical
POLICY={'score_chunk_cells':64,'pair':{'fixture':1},'schedule':{'max_total_checkpoint_bytes':1000},'log':{'max_logical_bytes':100000,'chunk_events':64}}
def populate(root,journal,variant,write):
 compact=journal/'compact';stage=next(p for p in compact.iterdir() if p.name.startswith('mcm-'));(stage/'checkpoints').mkdir()
 read=lambda p:json.loads(p.read_bytes());rawhash=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 owner=read(compact/'owner.json');ownerid=key(owner);receipt=read(compact/'dictionary-import/import-complete.json');receiptsha=rawhash(compact/'dictionary-import/import-complete.json');numeric=receipt['numeric'];execution=receipt['execution'];claim=read(root/'research_runs'/journal.name/'claim.json');job=read(root/claim['inputs']['execution_job']['path']);selected=next(iter(job['payload']['representation_jobs'].values()));matching=selected['descriptor']['configs']['matching']
 scope={'graph':stage.name[4:],'node_order':key(['a','b']),'dictionary':numeric['original_dictionary'],'ordered_motifs':key(numeric['ordered_motifs']),'matching':execution['execution_matching']}
 record={'schema_version':2,'kind':'mcm-imported-original','workflow':owner['context']['namespace'],'backend':execution['backend'],'graph':scope['graph'],'node_order':scope['node_order'],'dictionary':scope['dictionary'],'ordered_motifs':numeric['ordered_motifs'],'matching':matching,'original_matching':numeric['original_matching'],'execution_matching':execution['execution_matching'],'import_execution_identity':key({'import_receipt':receiptsha,'current':execution}),'dtype':'float32'};scope['workflow']=key(record)
 producer=next((root/'research_artifacts/onchain_compact_mcm').glob('*/*/*'));v=read(producer/'start.json');v.update(scope=scope,dictionary_receipt_sha256=receiptsha,dictionary_identity=numeric['original_dictionary']);write(producer/'start.json',v)
 components={n+'.py:onchain_replication':'a'*64 for n in ('matching_checkpoint','matching_annealing','matching_hardening','matching_sparse','matching_identity')}
 ps={'workflow':scope['workflow'],'config':key(matching),'context':key(owner['context']),'policy':key({'pair':POLICY['pair'],'schedule':POLICY['schedule']}),'numerical_source':key(components)}
 reservation=100000+1000+88*64+10*8192
 write(stage/'intent.json',{'schema_version':1,'owner':ownerid,'stage':stage.name,'kind':'mcm','scope':ps,'pairs':64,'logical_reservation_bytes':reservation,'policy_sha256':key(POLICY)})
 log=stage/'matching';write(log/'start.json',{'schema_version':1,'owner':ownerid,'scope':ps,'limits':POLICY['log'],'max_iterations':matching['max_iterations'],'record_bytes':168,'format':'<QB7xQdQ32s32s32s32s'})
 pairs={'wrong-purpose':0,'wrong-ack':1,'wrong-matrix':64,'wrong-count':64}[variant];start=rawhash(log/'start.json');head=start;payload=b'';purposes=[]
 for i in range(pairs):
  purpose=hashlib.sha256(str(i).encode()).digest();purposes.append(purpose)
  for kind,score,iters in ((0,0.,0),(1,.5,3)):
   frame=struct.pack('<QB7xQdQ32s32s32s',2*i+kind,kind,i,score,iters,purpose,b'a'*32,b'\0'*32);head=hashlib.sha256(bytes.fromhex(head)+frame).hexdigest();payload+=frame+bytes.fromhex(head)
 for i in range(0,2*pairs,64):write(log/f'events-{i//64:012d}.bin',payload[i*168:(i+64)*168])
 write(log/'terminal.json',{'schema_version':1,'start_sha256':start,'status':'failed','reason':'MCM producer failed','state':{'events':2*pairs,'started_pairs':pairs,'completed_pairs':pairs,'progress_events':0,'pending':None},'head':head,'chunks':(2*pairs+63)//64,'record_bytes':len(payload),'payload_sha256':hashlib.sha256(payload).hexdigest()})
 stream=stage/'stream';batch=stream/'batches';(stream/'tails').mkdir(parents=True)
 write(batch/'start.json',{'schema_version':1,'scope':scope,'owner':ownerid,'rows':2,'motifs':32,'chunk_cells':64,'dtype':'<f8','order':'row-major'});bs=rawhash(batch/'start.json')
 write(stream/'start.json',{'schema_version':1,'kind':'mcm-score-stream','scope':scope,'owner':ownerid,'rows':2,'motifs':32,'batch_start_sha256':bs,'chunk_cells':64});ss=rawhash(stream/'start.json')
 if variant!='wrong-purpose':
  tail=stream/'tails/tail-000000000000';destination=hashlib.sha256(canonical({'directory':str(batch),'start_sha256':bs,'index':0,'start_cell':0,'cells':64})+b'\n').hexdigest()
  write(tail/'start.json',{'schema_version':1,'kind':'mcm-score-tail','scope':scope,'owner':ownerid,'start_cell':0,'cells':64,'destination':destination,'record_format':'<Qd32s32s','record_bytes':80});ts=rawhash(tail/'start.json');th=ts;records=b''
  if pairs==64:
   for i in range(64):
    frame=struct.pack('<Qd32s',i,.5,purposes[i]);th=hashlib.sha256(bytes.fromhex(th)+frame).hexdigest();records+=frame+bytes.fromhex(th)
  write(tail/'records.bin',records)
  if pairs==64:
   write(tail/'terminal.json',{'schema_version':1,'start_sha256':ts,'status':'complete','reason':'','acknowledged_cells':64,'head':th,'records_bytes':5120,'records_sha256':hashlib.sha256(records).hexdigest()})
   payload=struct.pack('<64d',*([.5]*64));write(batch/'chunk-000000000000.bin',payload);write(batch/'chunk-000000000000.json',{'schema_version':1,'start_sha256':bs,'previous':bs,'index':0,'start_cell':0,'cells':64,'payload_sha256':hashlib.sha256(payload).hexdigest()});bh=rawhash(batch/'chunk-000000000000.json')
   write(stream/'seal-000000000000.json',{'schema_version':1,'start_sha256':ss,'previous':ss,'index':0,'start_cell':0,'cells':64,'tail_terminal_sha256':rawhash(tail/'terminal.json'),'batch_header_sha256':bh})
   if variant=='wrong-count':
    write(batch/'terminal.json',{'schema_version':1,'start_sha256':bs,'head':bh,'status':'complete','cells':64,'chunks':1,'reason':'','pending':[]})
    write(stream/'complete.json',{'schema_version':1,'start_sha256':ss,'head':rawhash(stream/'seal-000000000000.json'),'cells':64,'chunks':1,'batch_terminal_sha256':rawhash(batch/'terminal.json')})
 return stage
