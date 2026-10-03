"""Exact finite retained-format parser for four registered numerical refusals.

No matcher, array library, numerical authority or failed evidence is synthesized.
"""
import ast,hashlib,json,math,os,stat,struct
from pathlib import Path
from raw_receipts01 import body,require,digest
from refusal_evidence import canonical,key
FRAME=struct.Struct('<QB7xQdQ32s32s32s');TAIL=struct.Struct('<Qd32s');ZERO='0'*64
COUNTS={'wrong-purpose':(0,0),'wrong-ack':(1,0),'wrong-matrix':(64,64),'wrong-count':(64,64)}
def io_json(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def members(path,expected):
    info=path.lstat();require(stat.S_ISDIR(info.st_mode) and path.resolve()==path,'numerical evidence directory redirected')
    entries=os.scandir(path);primary=None
    try:
        names=[]
        for e in entries:
            require(len(names)<256,'numerical directory cardinality');names.append(e.name)
            st=e.stat(follow_symlinks=False);require(stat.S_ISDIR(st.st_mode) or (stat.S_ISREG(st.st_mode) and st.st_nlink==1),'numerical member type differs')
    except BaseException as error:primary=error;raise
    finally:
        try:entries.close()
        except BaseException:
            if primary is not None and (isinstance(primary,MemoryError) or not isinstance(primary,Exception)):pass
            else:raise
    require(set(names)==set(expected) and len(names)==len(expected),'numerical evidence membership differs')
def target_node_order(root,manifest_name,manifest,inputs):
    row=manifest['arrays']['node_ids'];relative=str(Path(manifest_name).parent/row['path'])
    require(any(v['path']==relative and v['sha256']==row['sha256'] for v in inputs.values()),'registered target node input absent')
    data=body(root,relative,65536);require(digest(data)==row['sha256'] and len(data)==row['bytes'],'registered target node body differs')
    require(data[:8]==b'\x93NUMPY\x01\x00' and len(data)>=10,'explicit tiny NPY header required')
    size=struct.unpack('<H',data[8:10])[0];require(size<=10000 and 10+size<=len(data),'bounded NPY header required')
    header=ast.literal_eval(data[10:10+size].decode('ascii').strip())
    require(set(header)=={'descr','fortran_order','shape'} and header['fortran_order'] is False and header['shape']==(2,) and type(header['descr']) is str and header['descr'].startswith('<U'),'registered two-node Unicode array required')
    width=int(header['descr'][2:]);require(0<width<=128 and len(data)==10+size+8*width,'bounded target node extent differs')
    values=[data[10+size+i*4*width:10+size+(i+1)*4*width].decode('utf-32-le').rstrip('\0') for i in range(2)]
    require(all(values) and len(set(values))==2,'distinct target nodes required');return key(values)

def authenticate_stage(root,stage,variant,owner,producer,policy,matching,context,source_files,numeric,execution,receipt_sha,node_order):
    pairs,acks=COUNTS[variant];files={};root=Path(root);stage=Path(stage)
    def raw(relative):
        value=body(root,str((stage/relative).relative_to(root)),65536);files[relative]=digest(value);return value
    def meta(relative):return json.loads(raw(relative))
    def exact(relative,expected):
        value=meta(relative);require(canonical(value)==canonical(expected),'numerical evidence differs: '+relative);return value
    members(stage,{'intent.json','matching','stream','checkpoints'});members(stage/'checkpoints',set())
    require(producer['dictionary_receipt_sha256']==receipt_sha and producer['dictionary_identity']==numeric['original_dictionary'],'producer original import receipt differs')
    scope=producer['scope'];require(scope['node_order']==node_order,'registered target node order differs');require(set(scope)=={'graph','node_order','dictionary','ordered_motifs','matching','workflow'},'numeric scope schema differs')
    require(scope['graph']==producer['graph_hash'] and scope['dictionary']==numeric['original_dictionary'] and scope['ordered_motifs']==key(numeric['ordered_motifs']) and scope['matching']==execution['execution_matching'],'numeric original scope differs')
    # Rebuild the registered typed imported workload from retained immutable inputs.
    workflow_record={'schema_version':2,'kind':'mcm-imported-original','workflow':context['namespace'],'backend':execution['backend'],'graph':scope['graph'],'node_order':scope['node_order'],'dictionary':scope['dictionary'],'ordered_motifs':numeric['ordered_motifs'],'matching':matching,'original_matching':numeric['original_matching'],'execution_matching':execution['execution_matching'],'import_execution_identity':key({'import_receipt':receipt_sha,'current':execution}),'dtype':'float32'}
    require(scope['workflow']==key(workflow_record),'typed imported workload differs')
    names=('matching_checkpoint','matching_annealing','matching_hardening','matching_sparse','matching_identity')
    components={n+'.py:onchain_replication':source_files['tradingagents/research/onchain_replication/'+n+'.py'] for n in names}
    matcher_scope={'workflow':scope['workflow'],'config':key(matching),'context':key(context),'policy':key({'pair':policy['pair'],'schedule':policy['schedule']}),'numerical_source':key(components)}
    # Fixed selected fixture has one64-cell score chunk and no progress snapshots.
    require(policy['score_chunk_cells']==64 and 'restart_retention' not in policy,'exact finite score policy differs')
    reservation=policy['log']['max_logical_bytes']+policy['schedule']['max_total_checkpoint_bytes']+88*64+8*8192+2*8192
    exact('intent.json',{'schema_version':1,'owner':owner,'stage':stage.name,'kind':'mcm','scope':matcher_scope,'pairs':64,'logical_reservation_bytes':reservation,'policy_sha256':key(policy)})
    start=exact('matching/start.json',{'schema_version':1,'owner':owner,'scope':matcher_scope,'limits':policy['log'],'max_iterations':matching['max_iterations'],'record_bytes':168,'format':'<QB7xQdQ32s32s32s32s'})
    start_sha=files['matching/start.json'];head=start_sha;payload=hashlib.sha256();completed=[];count=2*pairs;chunk_events=policy['log']['chunk_events'];require(type(chunk_events) is int and 0<chunk_events<=128,'event chunk bound differs')
    chunks=(count+chunk_events-1)//chunk_events;matching_members={'start.json','terminal.json'}|{f'events-{i:012d}.bin' for i in range(chunks)};members(stage/'matching',matching_members)
    events=[]
    for i in range(chunks):
        data=raw(f'matching/events-{i:012d}.bin');require(len(data)==min(chunk_events,count-i*chunk_events)*168,'event chunk extent differs');payload.update(data)
        for offset in range(0,len(data),168):
            frame=data[offset:offset+136];stored=data[offset+136:offset+168].hex();head=digest(bytes.fromhex(head)+frame);require(stored==head,'matching event chain differs');events.append(FRAME.unpack(frame))
    for i,event in enumerate(events):
        ordinal,kind,pair_index,score,iterations,purpose,identity,artifact=event
        require(ordinal==i and pair_index==i//2 and artifact.hex()==ZERO and purpose.hex()!=ZERO and identity.hex()!=ZERO,'matching event identity differs')
        if i%2==0:require(kind==0 and score==0 and iterations==0,'matching begin differs')
        else:
            require(kind in (1,2) and math.isfinite(score) and 0<=score<=1 and iterations<=matching['max_iterations'] and event[5:7]==events[i-1][5:7],'matching completion differs');completed.append((score,purpose.hex()))
    exact('matching/terminal.json',{'schema_version':1,'start_sha256':start_sha,'status':'failed','reason':'MCM producer failed','state':{'events':count,'started_pairs':pairs,'completed_pairs':pairs,'progress_events':0,'pending':None},'head':head,'chunks':chunks,'record_bytes':count*168,'payload_sha256':payload.hexdigest()})
    batch_start={'schema_version':1,'scope':scope,'owner':owner,'rows':2,'motifs':32,'chunk_cells':64,'dtype':'<f8','order':'row-major'}
    exact('stream/batches/start.json',batch_start);batch_sha=files['stream/batches/start.json']
    exact('stream/start.json',{'schema_version':1,'kind':'mcm-score-stream','scope':scope,'owner':owner,'rows':2,'motifs':32,'batch_start_sha256':batch_sha,'chunk_cells':64});stream_sha=files['stream/start.json']
    has_tail=variant!='wrong-purpose';sealed=acks==64;finished=variant=='wrong-count'
    members(stage/'stream',{'start.json','batches','tails'}|({'seal-000000000000.json'} if sealed else set())|({'complete.json'} if finished else set()))
    members(stage/'stream/tails',{'tail-000000000000'} if has_tail else set())
    batch_members={'start.json'}|({'chunk-000000000000.bin','chunk-000000000000.json'} if sealed else set())|({'terminal.json'} if finished else set());members(stage/'stream/batches',batch_members)
    if has_tail:
        tail='stream/tails/tail-000000000000';members(stage/tail,{'start.json','records.bin'}|({'terminal.json'} if sealed else set()))
        destination=digest(io_json({'directory':str(stage/'stream/batches'),'start_sha256':batch_sha,'index':0,'start_cell':0,'cells':64}))
        exact(tail+'/start.json',{'schema_version':1,'kind':'mcm-score-tail','scope':scope,'owner':owner,'start_cell':0,'cells':64,'destination':destination,'record_format':'<Qd32s32s','record_bytes':80})
        tail_head=files[tail+'/start.json'];records=raw(tail+'/records.bin');require(len(records)==acks*80,'tail acknowledged extent differs');values=[]
        for i in range(acks):
            frame=records[i*80:i*80+48];tail_head=digest(bytes.fromhex(tail_head)+frame);ordinal,score,purpose=TAIL.unpack(frame)
            require(records[i*80+48:(i+1)*80].hex()==tail_head and ordinal==i and (score,purpose.hex())==completed[i],'tail acknowledgement/matching differs');values.append(score)
        if sealed:
            exact(tail+'/terminal.json',{'schema_version':1,'start_sha256':files[tail+'/start.json'],'status':'complete','reason':'','acknowledged_cells':64,'head':tail_head,'records_bytes':5120,'records_sha256':digest(records)})
            data=raw('stream/batches/chunk-000000000000.bin');require(data==struct.pack('<64d',*values),'batch/tail scores differ')
            exact('stream/batches/chunk-000000000000.json',{'schema_version':1,'start_sha256':batch_sha,'previous':batch_sha,'index':0,'start_cell':0,'cells':64,'payload_sha256':digest(data)})
            header_sha=files['stream/batches/chunk-000000000000.json']
            exact('stream/seal-000000000000.json',{'schema_version':1,'start_sha256':stream_sha,'previous':stream_sha,'index':0,'start_cell':0,'cells':64,'tail_terminal_sha256':files[tail+'/terminal.json'],'batch_header_sha256':header_sha})
            if finished:
                exact('stream/batches/terminal.json',{'schema_version':1,'start_sha256':batch_sha,'head':header_sha,'status':'complete','cells':64,'chunks':1,'reason':'','pending':[]})
                exact('stream/complete.json',{'schema_version':1,'start_sha256':stream_sha,'head':files['stream/seal-000000000000.json'],'cells':64,'chunks':1,'batch_terminal_sha256':files['stream/batches/terminal.json']})
    return {'stage_count':1,'started_pairs':pairs,'completed_pairs':pairs,'matching_events':count,'progress_events':0,'acknowledged_cells':acks,'stream_complete':finished,'hashes':files}
