"""Source-only genuine-reader -> opaque codec seam; no remote/release authority.

The generic cursor is byte machinery, not a capability. Public entrypoints require
already loaded original classes and actual admitted source/input pins. No project
module is imported here. Caller creates the fresh private LocalStore only after
genuine native preflight; this module neither starts nor admits a research run.
"""
import hashlib,json,os,stat,sys
from pathlib import Path

PREFIX='research/onchain-paper-replication-2026-09-24/full_sources/financial-batch-output-genuine-byte-bridge-preparation01-2026-10-04'
PKG='tradingagents.research.onchain_replication.'
GRANT='byte_bridge'
PART=1048576
META=262144
LIMIT=64*1024**2
BLOCK=65536
DENIED_SOURCE='0a2e7639b42b9423b90743feadcda4078aa21816'
PINS={
 'codec01':'f10f6803a637735bc490de8846056a34e9090451d92773d075a7025b19bd3d55',
 'local_store01':'ceec61446f678f8749fa1e24530b5b4e3e344a59cce75f7906e322f03dd8ad89',
 'owned_io':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb',
 'recovery04':'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a',
 'bounded_git01':'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'}

def require(ok,why):
    if not ok:raise ValueError(why)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def pin(v):return type(v) is str and len(v)==64 and all(c in '0123456789abcdef' for c in v)
def canonical(v,limit=META):
    raw=(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
    require(len(raw)<=limit,'bounded bridge metadata');return raw

class Cursor:
    """One-use concatenation of exact original members, with no numerical cast.

    rows are (name,byte_length,original_sha256) in original scientific order.
    read_part and check are utility callbacks, not authority; genuine wrappers
    supply them internally. A failed callback/hash/alignment permanently poisons.
    The original object owns all descriptors and is never closed by this cursor.
    """
    def __init__(self,rows,width,read_part,check):
        require(type(width) is int and width in (4,8),'original scalar byte width')
        require(type(rows) in (tuple,list) and 0<len(rows)<=32767,'finite original members')
        frozen=[];seen=set()
        for row in rows:
            require(type(row) in (tuple,list) and len(row)==3,'exact member descriptor')
            name,size,sha=row
            require(type(name) is str and Path(name).name==name and name not in ('','.','..') and name not in seen,'unique original member name')
            require(type(size) is int and 0<size<=9239969792 and size%width==0 and pin(sha),'aligned original extent/hash')
            frozen.append((name,size,sha));seen.add(name)
        self.rows=tuple(frozen);self.width=width;self._read=read_part;self._check=check
        self.index=self.offset=self.total=0;self.failed=self.finished=False
        self.member=hashlib.sha256();self.whole=hashlib.sha256()
        self._pin=canonical({'rows':self.rows,'width':width},4*1024**2)
    def _integrity(self):
        require(not self.failed and canonical({'rows':self.rows,'width':self.width},4*1024**2)==self._pin,'cursor terminal or descriptor changed')
    def read(self,count):
        try:
            self._integrity();require(type(count) is int and 0<count<=PART,'bounded codec read')
            self._check();self._integrity()
            if self.index==len(self.rows):
                require(count==1,'only codec EOF probe follows full payload')
                self.finished=True;return b''
            require(not self.finished and count%self.width==0,'aligned original payload read')
            parts=[];remaining=count
            while remaining and self.index<len(self.rows):
                name,size,expected=self.rows[self.index];n=min(remaining,size-self.offset)
                self._check();self._integrity()
                raw=self._read(name,self.offset,n)
                require(type(raw) is bytes and len(raw)==n,'exact original range length/type')
                self._check();self._integrity()
                self.member.update(raw);self.whole.update(raw);self.total+=n;self.offset+=n;remaining-=n;parts.append(raw)
                if self.offset==size:
                    require(self.member.hexdigest()==expected,'whole original member hash')
                    self.index+=1;self.offset=0;self.member=hashlib.sha256()
            return b''.join(parts)
        except BaseException:self.failed=True;raise
    def completion(self):
        self._integrity();require(self.finished and self.index==len(self.rows) and self.offset==0,'codec EOF required')
        return {'bytes':self.total,'sha256':self.whole.hexdigest(),'original_members':len(self.rows)}

def validate_grant(g,role,graphs,job_sha):
    require(type(g) is dict and set(g)=={'schema_version','kind','job_input','job_sha256','role','targets','max_logical_bytes','max_allocated_bytes','scientific_publication','transport','retirement'},'exact registered bridge grant')
    require(type(g['schema_version']) is int and g['schema_version']==1 and g['kind']=='two-imported-target-local-codec-v1','explicit tiny imported bridge grant')
    require(g['job_input']=='execution_job' and pin(job_sha) and g['job_sha256']==job_sha,'original job byte pin')
    require(role in ('score-batches','mcm-output') and g['role']==role,'separate f64/f32 registered alternatives')
    require(type(graphs) is dict and len(graphs)==2 and all(pin(k) and type(n) is int and n in (2,3) for k,n in graphs.items()),'original two tiny target population only')
    require(type(g['targets']) is dict and set(g['targets'])==set(graphs) and all(type(n) is int and n==graphs[k] for k,n in g['targets'].items()),'complete exact original target denominator')
    require(g['scientific_publication'] is False and g['transport'] is False and g['retirement'] is False,'no scientific or external authority')
    # Full two-target upper reservation: original metadata/payload, retained
    # original-copy provenance, codec files, directory/entry/scratch and summary.
    # No refund; finite fixed target paths cannot multiply this population.
    reserve=0
    for nodes in graphs.values():
        raw=nodes*32*(8 if role=='score-batches' else 4)
        reserve+=raw+META+2*META+65536+5*1024**2+12*BLOCK
    require(all(type(g[k]) is int and reserve<=g[k]<=LIMIT for k in ('max_logical_bytes','max_allocated_bytes')),'complete bridge reservation unavailable')
    canonical(g);return reserve

def _module(name):
    module=sys.modules.get(name)
    require(module is not None,'UNAVAILABLE: genuine already-loaded module '+name)
    return module

def original_cardinality(policy):
    require(type(policy) is dict and type(policy.get('sample_count')) is int and policy['sample_count']==512 and type(policy.get('motif_count')) is int and policy['motif_count']==32,'original exactly512 spent samples and32 motifs required')

def _authority(source,role):
    consumer=_module(PKG+'held_score_consumer')
    if role=='score-batches':
        api=_module('held_score_reader_selected');require(type(source) is api.HeldBatches,'actual original HeldBatches required')
    else:
        api=_module(PKG+'completed_f32');require(type(source) is api.CompletedF32,'actual original CompletedF32 required')
    source._checked()
    target,stage,held,value,owner,bound,run=source._objects
    require(type(target) is _module(PKG+'imported_mcm_identity').Target and type(owner) is _module(PKG+'compact_owner').Owner and type(stage) is _module(PKG+'compact_owner').Stage and type(held) is _module(PKG+'compact_owner')._HeldTransition,'genuine original handles')
    require(type(bound) is _module(PKG+'matching_owner').Binding and type(run) is _module('tradingagents.research.lifecycle').ResearchRun,'genuine current Binding/ResearchRun')
    require(run.admission.source!=DENIED_SOURCE,'UNAVAILABLE: unchanged Source339 has no bridge admission')
    bound.check();target.check();held.check(owner);consumer._sources(run)
    require(owner.bound is bound and bound._run is run and target.owner is owner,'original current authority identity')
    prepared=target.execution._stage.prepared
    original_policy=json.loads(run.read_input(prepared._input));original_cardinality(original_policy)
    require(original_policy==json.loads(prepared._cap._policy),'actual original import policy changed')
    target.check();held.check(owner)
    return consumer,target,stage,held,value,owner,bound,run

def _dependencies(consumer,run):
    result={}
    # Existing actual source admission owns the bridge self hash. No self hash is
    # embedded in the grant or the helper: source->grant hash cycles are avoided.
    self_path=run.admission.root/PREFIX/'byte_bridge01.py'
    require(Path(__file__)==self_path,'bridge must be installed at its admitted origin')
    required={PREFIX+'/'+n+'.py':h for n,h in PINS.items()}
    required[PREFIX+'/byte_bridge01.py']=run.admission.experiment['source_files'].get(PREFIX+'/byte_bridge01.py')
    for relative,h in required.items():
        require(pin(h) and run.admission.experiment['source_files'].get(relative)==h and digest(consumer._body(run.admission.root/relative))==h,'exact admitted bridge dependency')
    for name,h in PINS.items():
        # The genuine HeldBatches loader already owns the shared owned_io alias.
        # Reuse that exact accepted module instead of colliding with its origin.
        relative=(consumer.PREFIX+'/owned_io.py') if name=='owned_io' else PREFIX+'/'+name+'.py'
        m=_module(name);require(Path(m.__file__)==run.admission.root/relative and run.admission.experiment['source_files'].get(relative)==h and digest(consumer._body(run.admission.root/relative))==h,'dependency alias/origin differs');result[name]=m
    require(result['local_store01'].C is result['codec01'] and result['local_store01'].R is result['recovery04'] and result['local_store01']._cleanup is result['owned_io']._cleanup,'exact codec/store/reducer objects')
    return result

def _snapshot(source,role,target,stage,value,run):
    source._checked();target.check();rows=[];docs=[];total=0
    local=source._reader
    for name,p in local._pin:
        if name in local.members:rows.append((name,p[2],p[1]))
        else:
            _,raw=local._read(name,p[2],expected=p[1],extent=p[2],capture=True)
            total+=len(raw);require(total<=META,'complete original metadata bound')
            docs.append({'name':name,'bytes':len(raw),'sha256':digest(raw),'raw_hex':raw.hex()})
    if role=='score-batches':
        rows=sorted(rows,key=lambda x:x[0])
        require(tuple(x[0] for x in rows)==source.members,'original ordered f64 members')
        extra={'stage_intent_hex':stage.intent.hex(),'stream_completion_hex':source._completion[1].hex()}
        # Start body is read from its genuine pinned original path, not rebuilt.
        consumer=_module(PKG+'held_score_consumer');raw=consumer._body(value.root/'start.json')
        extra['stream_start_hex']=raw.hex()
    else:
        require(len(rows)==1 and rows[0][0]=='matrix.f32','exact completed raw member')
        consumer=_module(PKG+'held_score_consumer')
        extra={'stage_intent_hex':stage.intent.hex(),'producer_start_hex':consumer._body(value.directory/'start.json').hex(),'producer_complete_hex':consumer._body(value.directory/'complete.json').hex(),'producer_receipt_sha256':value.receipt_sha256}
        ticket=value.record['output'];receipt=consumer._body(Path(ticket['directory'])/'receipt.json')
        require(digest(receipt)==ticket['receipt_sha256'],'original publication receipt bytes')
        extra['publication_receipt_hex']=receipt.hex()
        extra['stage_complete_hex']=consumer._body(stage.root/'stage-complete.json').hex()
    original_input=target.execution._stage.prepared._input
    extra['original_import_policy_input']=original_input;extra['original_import_policy_hex']=run.read_input(original_input).hex()
    snapshot={'schema_version':1,'kind':'original-imported-local-byte-bridge-provenance','role':role,'source_commit':run.admission.source,'claim_sha256':run._claim_sha256,'owner':target.owner.identity,'stage':stage.name,'stage_intent_sha256':stage.intent_sha256,'original_root':str(local.root),'original_document_sha256':local.reference,'scope':target.derive_scope(),'original_members':[{'name':n,'bytes':p[2],'sha256':p[1],'mode':stat.S_IMODE(p[0][2])} for n,p in local._pin],'metadata':docs,'ancestry':extra,'scientific_publication':False,'representation_complete':False}
    body=canonical(snapshot,2*META);source._checked();target.check()
    return tuple(rows),body

def _write(R,IO,path,raw):
    # R4.new_file owns both descriptors and performs anchored namespace rejoin.
    # Its original finally reducer retains an active first fatal and closes all.
    with R.new_file(path) as fd:
        at=0
        while at<len(raw):
            n=os.write(fd,memoryview(raw)[at:at+65536]);require(n>0,'bridge write progress');at+=n
        os.fsync(fd)
    require(R.read(path.parent,path.name)==raw,'bridge durable readback')

def _codec_population(store,R):
    """Sample complete metadata through the owned directory; no byte authority."""
    store.check()
    root=os.fstat(store.fd)
    names=tuple(sorted(os.listdir(store.fd)))
    require(set(names)==store.names,'codec fingerprint complete membership')
    rows=[]
    for name in names:
        item=os.stat(name,dir_fd=store.fd,follow_symlinks=False)
        require(stat.S_ISREG(item.st_mode) and item.st_nlink==1 and stat.S_IMODE(item.st_mode)==0o600,'codec fingerprint member type/mode')
        rows.append((name,R.sig(item),item.st_blocks,item.st_blksize))
    current=os.fstat(store.fd)
    require(store.root.resolve()==store.root and R.sig(store.root.lstat())==R.sig(root)==R.sig(current) and tuple(sorted(os.listdir(store.fd)))==names,'codec fingerprint root/membership changed')
    return (R.sig(current),current.st_blocks,current.st_blksize,tuple(rows))

def _encode(source,role,store):
    consumer,target,stage,held,value,owner,bound,run=_authority(source,role)
    deps=_dependencies(consumer,run);C,L,R,IO=(deps[n] for n in ('codec01','local_store01','recovery04','owned_io'))
    require(type(store) is L.LocalStore,'actual retained LocalStore required')
    require(GRANT in run.admission.inputs,'UNAVAILABLE: absent separately registered byte_bridge grant')
    raw=run.read_input(GRANT);grant=json.loads(raw);require(canonical(grant)==raw,'canonical original bridge grant')
    job_raw=run.read_input('execution_job');job=json.loads(job_raw)
    require(job['kind']=='compact_resource','UNAVAILABLE: full financial population not this imported resource route')
    selected=target.execution._stage.prepared._selection_now()['selected']
    graphs=selected['descriptor']['resource_fixture']['target_nodes']
    reserve=validate_grant(grant,role,graphs,digest(job_raw))
    require(target.key in graphs and len(target.graph.node_ids)==graphs[target.key],'actual complete target nodes')
    base=run.directory/('byte-bridge-'+role+'-'+target.key)
    require(store.root==base/'codec' and base.resolve()==base and stat.S_IMODE(base.lstat().st_mode)==0o700 and set(os.listdir(base))=={'codec'},'fresh fixed owned bridge namespace; no retry')
    base_info=base.lstat();base_pin=(base_info.st_dev,base_info.st_ino,base_info.st_mode)
    require(base_info.st_blocks*512<=BLOCK,'initial bridge directory allocation')
    store.check();require(not store.names,'fresh empty codec store')
    limits=job['resources']['storage_budget']['limits']
    require(reserve<=min(limits['max_logical_bytes'],limits['max_allocated_bytes']),'bridge exceeds original whole-watch policy')
    rows,original=_snapshot(source,role,target,stage,value,run)
    dtype,width=('<f8',8) if role=='score-batches' else ('<f4',4)
    descriptor={'schema_version':1,'kind':'mcm-batch-output-bytes','role':role,'dtype':dtype,'shape':[graphs[target.key],32],'order':'C','scope':target.derive_scope(),'motifs':32,'spent_samples':512}
    require(sum(r[1] for r in rows)==C.descriptor(descriptor),'complete original payload denominator')
    published={}
    def boundary():
        _authority(source,role);_dependencies(consumer,run)
        require(run.read_input(GRANT)==raw and run.read_input('execution_job')==job_raw,'bridge grant/job changed')
        require(_snapshot(source,role,target,stage,value,run)==(rows,original),'original metadata/ancestry changed')
        info=base.lstat()
        require(base.resolve()==base and (info.st_dev,info.st_ino,info.st_mode)==base_pin and set(os.listdir(base))=={'codec'}|set(published),'bridge parent identity/membership changed')
        for name,body in published.items():require(R.read(base,name)==body,'retained bridge provenance/summary changed')
        require(L.shutil.disk_usage(base).free>=L.FLOOR+reserve,'bridge floor plus complete reservation')
        store.check()
    try:
        boundary();_write(R,IO,base/'original.json',original)
        published['original.json']=original
        cursor=Cursor(rows,width,source.read_part,boundary)
        terminal=C.encode_stream(cursor,descriptor,store.put)
        proof=store.verify(terminal,descriptor);done=cursor.completion();boundary()
        require(done['bytes']==proof['logical_bytes'] and done['sha256']==proof['raw_sha256'],'whole original->codec raw hash')
        result={'schema_version':1,'kind':'genuine-imported-local-codec-byte-proof-only','original_sha256':digest(original),'grant_sha256':digest(raw),'terminal_sha256':terminal,'descriptor':descriptor,'original_raw':done,'codec':proof,'complete_population_reservation':reserve,'transport_authority':False,'retirement_authority':False,'local_bytes_retired':0,'representation_complete':False}
        body=canonical(result,65536);boundary();_write(R,IO,base/'complete.json',body);published['complete.json']=body;boundary()
        codec_before=_codec_population(store,R)
        final_proof=store.verify(terminal,descriptor)
        require(final_proof==proof and final_proof['logical_bytes']==done['bytes'] and final_proof['raw_sha256']==done['sha256'],'post-summary complete codec/original byte join')
        boundary()
        require(_codec_population(store,R)==codec_before,'post-verification codec population changed')
        return result
    except BaseException as primary:
        owner.poisoned=True;store.poisoned=True
        def mark():_write(R,IO,base/'failed.json',canonical({'status':'FAILED','error_type':type(primary).__name__,'original_sha256':digest(original),'local_bytes_retired':0}))
        IO._cleanup((mark,),primary=primary)
        raise

def encode_held(source,store):return _encode(source,'score-batches',store)
def encode_completed(source,store):return _encode(source,'mcm-output',store)
def release(*args,**kwargs):raise ValueError('UNAVAILABLE: no transport, retirement, scientific publication or numerical release authority')
