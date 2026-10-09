"""Explicit numeric-reuse occurrence closure; no Owner or scientific authority."""
import hashlib,json,math,os,stat,struct,time
from pathlib import Path
from . import batched_numeric_reuse as reuse

RECORD=struct.Struct('>BQ')
SUMMARY_LIMIT=8192
FORMAT='numeric-reuse-origins-v1'
def require(ok,message):
    if not ok:raise ValueError(message)
def raw(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def sig(st):return tuple(getattr(st,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'))
def regular(st):require(stat.S_ISREG(st.st_mode) and stat.S_IMODE(st.st_mode)==0o600 and st.st_nlink==1,'numeric file type/mode/links')
def write_all(fd,body):
    view=memoryview(body)
    while view:
        n=os.write(fd,view);require(n>0,'numeric write made no progress');view=view[n:]
def read_file(fd,name,limit):
    child=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
    primary=None
    try:
        before=os.fstat(child);regular(before);require(0<=before.st_size<=limit,'numeric file extent')
        body=b''
        while len(body)<=limit:
            block=os.read(child,min(65536,limit+1-len(body)))
            if not block:break
            body+=block
        require(len(body)==before.st_size and sig(os.fstat(child))==sig(before)==sig(os.stat(name,dir_fd=fd,follow_symlinks=False)),'numeric body changed')
        return body,sig(before)
    except BaseException as error:
        primary=error;raise
    finally:
        try:os.close(child)
        except BaseException as cleanup:
            if primary is None:raise
            primary.add_note('numeric read cleanup: '+repr(cleanup))
def counters(memo):
    value=dict(memo.counters)
    require(all(type(k) is str and type(v) is int and 0<=v<2**127 for k,v in value.items()),'numeric counters invalid')
    return value

class NumericExecution:
    def __init__(self,stream_root,config,policy,schedule,checkpoint,*,cells,batch_cells,max_origin_bytes,max_summary_bytes,max_entries,max_retained_bytes,max_key_bytes,authority_poll=None):
        self.fd=self.origins_fd=self.batches_fd=None;self.memo=None;self.closed=False;self.poisoned=False;self.finished=False
        self.root=Path(stream_root).absolute();self.cells=cells;self.batch_cells=batch_cells
        self.max_origin_bytes=max_origin_bytes;self.max_summary_bytes=max_summary_bytes
        self.ordinal=0;self.batch=0;self.computed=0;self.reused=0;self.summary_bytes=0;self.elapsed_seconds=0.0
        self.buffer=bytearray();self.receipts=hashlib.sha256();self.summary_hash=hashlib.sha256();self.summary_inventory=hashlib.sha256();self.origin_hash=hashlib.sha256()
        self.batch_computed=self.batch_reused=0;self.batch_elapsed=0.0
        try:
            require(type(cells) is int and 0<cells<2**63 and type(batch_cells) is int and 0<batch_cells<=4096,'finite numeric range required')
            require(type(max_origin_bytes) is int and 9*cells<=max_origin_bytes<2**63 and type(max_summary_bytes) is int and 0<max_summary_bytes<2**63,'numeric storage reservation required')
            self.batches=(cells+batch_cells-1)//batch_cells
            self.fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);self.root_pin=sig(os.fstat(self.fd))[:2];self._root()
            os.mkdir('numeric-batches',mode=0o700,dir_fd=self.fd)
            self.batches_fd=os.open('numeric-batches',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=self.fd);self.batches_pin=sig(os.fstat(self.batches_fd))[:2]
            self.origins_fd=os.open('numeric-origins.bin',os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=self.fd)
            self.origin_sig=sig(os.fstat(self.origins_fd));os.fsync(self.fd)
            self.memo=reuse.NumericReuseExecutor(config,policy,schedule,checkpoint,max_entries=max_entries,max_retained_bytes=max_retained_bytes,max_key_bytes=max_key_bytes,authority_poll=authority_poll)
        except BaseException as primary:
            self.poisoned=True
            try:self.close()
            except BaseException as cleanup:primary.add_note('numeric constructor cleanup: '+repr(cleanup))
            raise
    def _root(self):
        require(self.root.resolve()==self.root and sig(os.stat(self.root,follow_symlinks=False))[:2]==self.root_pin==sig(os.fstat(self.fd))[:2],'numeric stream root changed')
        if self.batches_fd is not None:require(sig(os.stat('numeric-batches',dir_fd=self.fd,follow_symlinks=False))[:2]==self.batches_pin==sig(os.fstat(self.batches_fd))[:2],'numeric batch root changed')
    def _origin_current(self):
        self._root();st=os.fstat(self.origins_fd);regular(st)
        require(sig(st)==self.origin_sig==sig(os.stat('numeric-origins.bin',dir_fd=self.fd,follow_symlinks=False)),'numeric origin file changed')
    def _poison(self):
        self.poisoned=True
        if self.memo is not None:self.memo._poison()
    def __call__(self,a,b,purpose):
        require(not self.closed and not self.poisoned and not self.finished and self.ordinal<self.cells,'numeric execution unavailable')
        try:
            self._origin_current()
            if not self.buffer:self.memo.begin_batch()
            started=time.perf_counter();result=self.memo(a,b,purpose);elapsed=time.perf_counter()-started
            require(math.isfinite(elapsed) and elapsed>=0,'numeric timing invalid')
            receipt=self.memo.last_receipt
            expected={'schema_version','kind','ordinal','purpose_sha256','mode','origin_purpose_sha256','origin_ordinal','score_f64_be','iterations','convergence','cached','checkpoint_attempt_delta','checkpoint_reserved_byte_delta','retained_cache_bytes','old_per_occurrence_execution_credit','boundary_validated_batch_complete'}
            require(type(receipt) is dict and set(receipt)==expected and receipt['schema_version']==2 and receipt['kind']=='engineering_numeric_occurrence' and type(receipt['ordinal']) is int and receipt['ordinal']==self.ordinal and receipt['purpose_sha256']==purpose,'fresh provisional occurrence required')
            require(type(result) is tuple and len(result)==3 and type(result[0]) is float and receipt['score_f64_be']==struct.pack('>d',result[0]).hex() and receipt['iterations']==result[1] and receipt['convergence']==result[2],'numeric receipt/result differs')
            require(receipt['old_per_occurrence_execution_credit'] is False and receipt['boundary_validated_batch_complete'] is False and receipt['mode'] in ('computed','reused'),'numeric receipt authority differs')
            origin=receipt['origin_ordinal'];mode=int(receipt['mode']=='reused')
            require(type(origin) is int and (0<=origin<self.ordinal if mode else origin==self.ordinal) and (mode or receipt['origin_purpose_sha256']==purpose),'numeric origin invalid')
            require(type(receipt['cached']) is bool and all(type(receipt[k]) is int and receipt[k]>=0 for k in ('checkpoint_attempt_delta','checkpoint_reserved_byte_delta','retained_cache_bytes','iterations')) and type(receipt['origin_purpose_sha256']) is str and len(receipt['origin_purpose_sha256'])==64 and all(c in '0123456789abcdef' for c in receipt['origin_purpose_sha256']) and math.isfinite(result[0]) and 0<=result[0]<=1 and receipt['convergence'] in ('temperature_complete','iteration_cap'),'numeric provisional field types')
            encoded=raw(receipt);require(len(encoded)<=SUMMARY_LIMIT,'numeric receipt extent')
            self.receipts.update(struct.pack('>Q',len(encoded)));self.receipts.update(encoded)
            self.buffer.extend(RECORD.pack(mode,origin));self.ordinal+=1;self.computed+=1-mode;self.reused+=mode;self.batch_computed+=1-mode;self.batch_reused+=mode
            self.batch_elapsed+=elapsed
            if len(self.buffer)==9*self.batch_cells or self.ordinal==self.cells:self._complete_batch()
            return result
        except BaseException:
            self._poison();raise
    def _complete_batch(self):
        self.memo.end_batch() # Genuine full guard precedes any summary credit.
        start=self.ordinal-len(self.buffer)//9
        summary={'format':FORMAT,'batch':self.batch,'start':start,'stop':self.ordinal,'computed':self.batch_computed,'reused':self.batch_reused,'origin_sha256':hashlib.sha256(self.buffer).hexdigest(),'receipt_sha256':self.receipts.hexdigest(),'receipt_framing':'u64be-length/canonical-json-newline','counters':counters(self.memo),'elapsed_seconds':self.batch_elapsed,'old_per_occurrence_execution_credit':False}
        body=raw(summary);require(len(body)<=SUMMARY_LIMIT and self.summary_bytes+len(body)<=self.max_summary_bytes and 9*self.ordinal<=self.max_origin_bytes,'numeric retained byte cap')
        self._origin_current();write_all(self.origins_fd,self.buffer);os.fsync(self.origins_fd)
        self.origin_sig=sig(os.fstat(self.origins_fd));self._origin_current()
        require(os.pread(self.origins_fd,len(self.buffer),9*start)==self.buffer,'numeric origin write readback differs')
        name=f'{self.batch:012d}.json';child=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=self.batches_fd)
        primary=None
        try:write_all(child,body);os.fsync(child)
        except BaseException as error:
            primary=error;raise
        finally:
            try:os.close(child)
            except BaseException as cleanup:
                if primary is None:raise
                primary.add_note('numeric summary cleanup: '+repr(cleanup))
        readback,file_signature=read_file(self.batches_fd,name,SUMMARY_LIMIT);require(readback==body,'numeric summary readback differs');os.fsync(self.batches_fd);self._root()
        self.summary_inventory.update(raw({'name':name,'signature':file_signature}));self.origin_hash.update(self.buffer);self.summary_hash.update(struct.pack('>Q',len(body)));self.summary_hash.update(body);self.summary_bytes+=len(body);self.batch+=1
        self.elapsed_seconds+=self.batch_elapsed;self.buffer.clear();self.receipts=hashlib.sha256();self.batch_computed=self.batch_reused=0;self.batch_elapsed=0.0
    def finish(self):
        require(not self.closed and not self.poisoned and not self.finished,'numeric finish unavailable')
        try:
            require(self.ordinal==self.cells and self.batch==self.batches and not self.buffer and not self.memo.active,'numeric range incomplete')
            self._origin_current();os.fsync(self.origins_fd)
            binding={'format':FORMAT,'cells':self.cells,'batch_cells':self.batch_cells,'batches':self.batches,'computed':self.computed,'reused':self.reused,'origin_bytes':9*self.cells,'origin_sha256':self.origin_hash.hexdigest(),'origin_signature':list(self.origin_sig),'stream_inode':list(self.root_pin),'batches_inode':list(self.batches_pin),'batches_signature':list(sig(os.fstat(self.batches_fd))),'summary_bytes':self.summary_bytes,'summary_sha256':self.summary_hash.hexdigest(),'summary_inventory_sha256':self.summary_inventory.hexdigest(),'max_origin_bytes':self.max_origin_bytes,'max_summary_bytes':self.max_summary_bytes,'counters':counters(self.memo),'elapsed_seconds':self.elapsed_seconds,'old_per_occurrence_execution_credit':False,'independent_key_equivalence_recomputed':False,'resume_supported':False}
            verify(self.root,binding);self.finished=True;return binding
        except BaseException:self._poison();raise
    def close(self):
        if self.closed:return
        primary=None
        actions=[]
        if self.memo is not None:
            if not self.finished:actions.append(self._poison) # Never attest/credit a partial cache batch on close.
            actions.append(self.memo.close)
        for key in ('origins_fd','batches_fd','fd'):
            value=getattr(self,key)
            if value is not None:actions.append(lambda value=value:os.close(value));setattr(self,key,None)
        for action in actions:
            try:action()
            except BaseException as error:
                if primary is None:primary=error
                else:primary.add_note('additional numeric cleanup: '+repr(error))
        self.buffer=bytearray();self.closed=True
        if primary is not None:raise primary
    def __enter__(self):return self
    def __exit__(self,kind,primary,tb):
        try:self.close()
        except BaseException as cleanup:
            if primary is None:raise
            primary.add_note('numeric cleanup: '+repr(cleanup))
        return False

def verify(stream_root,binding):
    """Storage/range closure only; does not recompute numeric key equivalence."""
    root=Path(stream_root).absolute();fd=bd=origin=None;primary=None
    try:
        require(binding['format']==FORMAT and type(binding['cells']) is int and 0<binding['cells']<2**63 and type(binding['batch_cells']) is int and 0<binding['batch_cells']<=4096,'numeric binding format/range')
        cells=binding['cells'];batch_cells=binding['batch_cells'];batches=(cells+batch_cells-1)//batch_cells
        require(binding['batches']==batches and binding['origin_bytes']==cells*9<=binding['max_origin_bytes'] and binding['summary_bytes']<=binding['max_summary_bytes'] and binding['old_per_occurrence_execution_credit'] is False and binding['independent_key_equivalence_recomputed'] is False and binding['resume_supported'] is False,'numeric binding closure')
        fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);require(root.resolve()==root and sig(os.fstat(fd))[:2]==tuple(binding['stream_inode'])==sig(root.lstat())[:2],'numeric stream identity')
        bd=os.open('numeric-batches',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);bst=sig(os.fstat(bd));require(bst==tuple(binding['batches_signature']) and bst[:2]==tuple(binding['batches_inode']),'numeric summary directory identity')
        count=0
        with os.scandir(bd) as entries:
            for entry in entries:
                require(entry.name.endswith('.json') and len(entry.name)==17 and entry.name[:12].isdigit() and 0<=int(entry.name[:12])<batches,'unexpected numeric summary name');count+=1;require(count<=batches,'numeric summary count')
        require(count==batches,'missing numeric summary')
        origin=os.open('numeric-origins.bin',os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd);st=os.fstat(origin);regular(st);require(sig(st)==tuple(binding['origin_signature']) and st.st_size==cells*9,'numeric origins signature/extent')
        oh=hashlib.sha256();sh=hashlib.sha256();ih=hashlib.sha256();summary_bytes=computed=reused=0;elapsed=0.0;last_counters=None
        for index in range(batches):
            start=index*batch_cells;stop=min(cells,start+batch_cells);body,signature=read_file(bd,f'{index:012d}.json',SUMMARY_LIMIT);s=json.loads(body)
            require(raw(s)==body and s['format']==FORMAT and s['batch']==index and s['start']==start and s['stop']==stop and s['old_per_occurrence_execution_credit'] is False and s['receipt_framing']=='u64be-length/canonical-json-newline' and len(s['receipt_sha256'])==64 and all(c in '0123456789abcdef' for c in s['receipt_sha256']),'numeric summary range/framing')
            chunk=os.pread(origin,9*(stop-start),9*start);require(len(chunk)==9*(stop-start) and hashlib.sha256(chunk).hexdigest()==s['origin_sha256'],'numeric origin range hash')
            nc=nr=0
            for ordinal,(mode,source) in enumerate(RECORD.iter_unpack(chunk),start):
                require((mode==0 and source==ordinal) or (mode==1 and source<ordinal),'numeric origin semantics');nc+=mode==0;nr+=mode==1
            require(type(s['computed']) is int and type(s['reused']) is int and nc==s['computed'] and nr==s['reused'],'numeric mode counts');computed+=nc;reused+=nr
            require(type(s['elapsed_seconds']) is float and math.isfinite(s['elapsed_seconds']) and s['elapsed_seconds']>=0 and type(s['counters']) is dict and all(type(k) is str and type(v) is int and 0<=v<2**127 for k,v in s['counters'].items()),'numeric summary measurements');elapsed+=s['elapsed_seconds']
            ih.update(raw({'name':f'{index:012d}.json','signature':signature}));oh.update(chunk);sh.update(struct.pack('>Q',len(body)));sh.update(body);summary_bytes+=len(body);last_counters=s['counters']
        require(oh.hexdigest()==binding['origin_sha256'] and sh.hexdigest()==binding['summary_sha256'] and summary_bytes==binding['summary_bytes'] and computed==binding['computed'] and reused==binding['reused'] and computed+reused==cells and last_counters==binding['counters'] and elapsed==binding['elapsed_seconds'] and ih.hexdigest()==binding['summary_inventory_sha256'],'numeric aggregate differs')
        require(sig(os.fstat(origin))==tuple(binding['origin_signature'])==sig(os.stat('numeric-origins.bin',dir_fd=fd,follow_symlinks=False)) and sig(os.fstat(bd))==bst==sig(os.stat('numeric-batches',dir_fd=fd,follow_symlinks=False)) and sig(root.lstat())[:2]==tuple(binding['stream_inode']),'numeric final currentness differs')
        current_inventory=hashlib.sha256()
        for index in range(batches):
            name=f'{index:012d}.json';current_inventory.update(raw({'name':name,'signature':sig(os.stat(name,dir_fd=bd,follow_symlinks=False))}))
        require(current_inventory.hexdigest()==binding['summary_inventory_sha256'],'numeric summary inventory changed')
        return {'cells':cells,'computed':computed,'reused':reused,'origin_bytes':9*cells,'summary_bytes':summary_bytes}
    except BaseException as error:
        primary=error;raise
    finally:
        cleanup_error=None
        for value in (origin,bd,fd):
            if value is not None:
                try:os.close(value)
                except BaseException as error:
                    if primary is not None:primary.add_note('numeric verifier cleanup: '+repr(error))
                    elif cleanup_error is None:cleanup_error=error
                    else:cleanup_error.add_note('additional numeric verifier cleanup: '+repr(error))
        if primary is None and cleanup_error is not None:raise cleanup_error
