"""Engineering-only binary batch journal; no old stream/authority receipt credit."""
import hashlib,json,math,os,stat,struct
from pathlib import Path
RECORD=struct.Struct('>Q32sdIB') # ordinal, purpose SHA, exact f64, iterations, status
HEADER=struct.Struct('>8sIQQ32s32s') # magic, width, range, pending SHA, actual purpose aggregate
MAGIC=b'MCMBAT03'
STATUS={'temperature_complete':0,'iteration_cap':1}
def body(value):return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def sig(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def require(ok,message):
    if not ok:raise ValueError(message)

class BatchJournal:
    def __init__(self,root,*,batch_cells,max_cells,max_bytes,max_body_bytes,boundary):
        require(all(type(v) is int and v>0 for v in (batch_cells,max_cells,max_bytes,max_body_bytes)),'positive bounds required')
        require(batch_cells<=4096 and max_cells<2**64 and 1024<=max_body_bytes<=1024**2,'format bounds exceeded')
        require(callable(boundary),'boundary callback required')
        self.root=Path(root).absolute();require(self.root.parent.resolve()==self.root.parent,'nonsymlink parent required')
        self.root.mkdir(exist_ok=False)
        self.fd=None;parent=None
        try:
            self.fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
            s=os.fstat(self.fd);self.pin=(s.st_dev,s.st_ino)
            parent=os.open(self.root.parent,os.O_RDONLY|os.O_DIRECTORY)
            os.fsync(parent)
            closing=parent;parent=None;os.close(closing)
            self.batch_cells=batch_cells;self.max_cells=max_cells;self.max_bytes=max_bytes;self.max_body=max_body_bytes
            self.boundary=boundary;self.cells=0;self.bytes=0;self.batch=0;self.poisoned=False;self.closed=False
        except BaseException as primary:
            # A constructor which has not returned still owns every acquired FD.
            for descriptor in (parent,self.fd):
                if descriptor is not None:
                    try:os.close(descriptor)
                    except BaseException as failure:primary.add_note('Journal acquisition cleanup failed: '+repr(failure))
            self.closed=True
            raise
    def _root(self):
        s=self.root.lstat();f=os.fstat(self.fd)
        require(stat.S_ISDIR(s.st_mode) and (s.st_dev,s.st_ino)==self.pin==(f.st_dev,f.st_ino) and self.root.resolve()==self.root,'journal root replaced')
    def _read(self,name,expected=None,*,links=1,pin=None):
        self._root();fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=self.fd)
        try:
            before=os.fstat(fd);entry=os.stat(name,dir_fd=self.fd,follow_symlinks=False)
            require(stat.S_ISREG(before.st_mode) and stat.S_IMODE(before.st_mode)==0o600 and before.st_nlink==links and sig(before)==sig(entry),'journal file identity/mode/links differs')
            require(pin is None or (before.st_dev,before.st_ino)==pin,'journal inode replaced')
            require(before.st_size<=max(self.max_body,HEADER.size+self.batch_cells*RECORD.size),'journal extent exceeded')
            raw=b''
            while len(raw)<=before.st_size:
                block=os.read(fd,min(65536,before.st_size+1-len(raw)))
                if not block:break
                raw+=block
            require(len(raw)==before.st_size and sig(os.fstat(fd))==sig(before)==sig(os.stat(name,dir_fd=self.fd,follow_symlinks=False)),'journal changed while reading')
            require(expected is None or raw==expected and digest(raw)==digest(expected),'journal readback differs')
            result=(raw,(before.st_dev,before.st_ino))
        finally:os.close(fd)
        self._root();return result
    def _write(self,name,raw,limit):
        self._root();require(len(raw)<=limit and self.bytes+len(raw)<=self.max_bytes,'journal byte allowance exceeded')
        fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=self.fd)
        try:
            os.fchmod(fd,0o600);s=os.fstat(fd);pin=(s.st_dev,s.st_ino);self.bytes+=len(raw)
            view=memoryview(raw)
            while view:
                n=os.write(fd,view);require(n>0,'zero write');view=view[n:]
            os.fsync(fd)
        finally:os.close(fd)
        self._read(name,raw,pin=pin);os.fsync(self.fd);return pin
    def _publish(self,tmp,final,raw,pin):
        self._read(tmp,raw,pin=pin);self._root()
        os.link(tmp,final,src_dir_fd=self.fd,dst_dir_fd=self.fd,follow_symlinks=False)
        self._read(tmp,raw,links=2,pin=pin);self._read(final,raw,links=2,pin=pin);os.fsync(self.fd)
        os.unlink(tmp,dir_fd=self.fd);os.fsync(self.fd);self._read(final,raw,pin=pin)
    def _pending(self,stem,raw,pin):self._read(stem+'.pending.json',raw,pin=pin)
    def read_complete(self,ordinal):
        require(not self.closed and not self.poisoned,'journal unavailable')
        try:return self._read_complete(ordinal)
        except BaseException:self.poisoned=True;raise
    def _read_complete(self,ordinal):
        """Validate pending/header/payload/metadata closure; no empirical authority."""
        require(type(ordinal) is int and 0<=ordinal<2**64,'invalid batch ordinal')
        stem=f'{ordinal:08d}'
        pending,pp=self._read(stem+'.pending.json');meta,mp=self._read(stem+'.complete.json');payload,bp=self._read(stem+'.records.bin')
        p=json.loads(pending);m=json.loads(meta)
        require(set(p)=={'schema','kind','start','stop','workload_sha256','disposition'} and p['schema']==3 and p['kind']=='engineering_pending' and p['disposition']=='attempted_unknown_without_complete','pending schema differs')
        require(type(p['start']) is int and type(p['stop']) is int and 0<=p['start']<p['stop']<=self.max_cells and p['stop']-p['start']<=self.batch_cells,'pending range differs')
        require(type(p['workload_sha256']) is str and len(p['workload_sha256'])==64 and all(c in '0123456789abcdef' for c in p['workload_sha256']),'workload commitment differs')
        require(type(m) is dict and set(m)=={'schema','kind','pending_sha256','payload_sha256','payload_bytes','record_bytes','purposes_sha256'},'completion schema differs')
        require(m=={'schema':3,'kind':'engineering_complete','pending_sha256':digest(pending),'payload_sha256':digest(payload),'payload_bytes':len(payload),'record_bytes':RECORD.size,'purposes_sha256':m['purposes_sha256']},'completion commitment differs')
        require(len(payload)==HEADER.size+(p['stop']-p['start'])*RECORD.size,'binary extent differs')
        require(HEADER.unpack_from(payload)==(MAGIC,RECORD.size,p['start'],p['stop'],bytes.fromhex(digest(pending)),bytes.fromhex(m['purposes_sha256'])),'binary header differs')
        aggregate=hashlib.sha256();records=[]
        for offset in range(p['stop']-p['start']):
            row=RECORD.unpack_from(payload,HEADER.size+offset*RECORD.size)
            require(row[0]==p['start']+offset and math.isfinite(row[2]) and 0<=row[2]<=1 and row[4] in STATUS.values(),'binary record differs')
            aggregate.update(row[1]);records.append(row)
        require(aggregate.hexdigest()==m['purposes_sha256'],'ordered purpose aggregate differs')
        self._read(stem+'.pending.json',pending,pin=pp);self._read(stem+'.complete.json',meta,pin=mp);self._read(stem+'.records.bin',payload,pin=bp)
        return records
    def _purpose_body(self,purpose):
        # Exact JSON types cannot hide a retained graph in subclass attributes.
        todo=[(purpose,0)];seen=0
        while todo:
            value,depth=todo.pop();seen+=1
            require(seen<=256 and depth<=16,'purpose structure exceeded')
            if type(value) is dict:
                require(len(value)<=256 and all(type(k) is str for k in value),'plain purpose keys required')
                todo.extend((v,depth+1) for v in value.values())
            elif type(value) is list:
                require(len(value)<=256,'purpose list exceeded');todo.extend((v,depth+1) for v in value)
            else:require(type(value) in (str,int,float,bool,type(None)),'plain purpose values required')
        raw=body(purpose);require(len(raw)<=8192,'purpose extent exceeded');return raw
    def _purposes(self,retained,workload,workload_raw):
        require(body(workload)==workload_raw,'workload descriptor mutated')
        for offset,(purpose,raw) in enumerate(retained):
            require(type(purpose) is dict and type(purpose.get('ordinal')) is int and purpose['ordinal']==self.cells+offset and self._purpose_body(purpose)==raw,'purpose changed after computation')
    def run_batch_stream(self,count,tasks,executor,workload):
        """Consume a finite batch iterator; exhaustion probe never executes a score."""
        require(not self.closed and not self.poisoned,'journal unavailable')
        iterator=None;iterator_closed=False;primary=None
        try:
            require(type(count) is int and 0<count<=self.batch_cells and self.cells+count<=self.max_cells,'batch cell allowance exceeded')
            require(type(workload) is dict,'plain workload descriptor required')
            workload_raw=body(workload);require(len(workload_raw)<=8192,'workload extent exceeded')
            payload_limit=HEADER.size+count*RECORD.size
            require(self.bytes+2*self.max_body+payload_limit<=self.max_bytes,'batch byte reservation exceeded')
            self._root();self.boundary();self._root()
            require(body(workload)==workload_raw,'workload descriptor mutated')
            stem=f'{self.batch:08d}';pending=body({'schema':3,'kind':'engineering_pending','start':self.cells,'stop':self.cells+count,'workload_sha256':digest(workload_raw),'disposition':'attempted_unknown_without_complete'})
            pp=self._write(stem+'.pending.json',pending,self.max_body)
            # Creation and first next occur only after pending is durable.
            iterator=iter(tasks);retained=[];aggregate=hashlib.sha256();records_raw=bytearray()
            for offset in range(count):
                try:task=next(iterator)
                except StopIteration as error:raise ValueError('short batch iterator') from error
                require(type(task) is tuple and len(task)==3,'typed task tuple required')
                purpose,a,b=task;del task
                require(type(purpose) is dict and type(purpose.get('ordinal')) is int and purpose['ordinal']==self.cells+offset,'fresh ordered purpose required')
                raw=self._purpose_body(purpose);key=hashlib.sha256(raw).digest()
                try:score,iterations,status=executor(a,b,key.hex())
                finally:del a,b
                require(type(score) is float and math.isfinite(score) and 0<=score<=1 and type(iterations) is int and 0<=iterations<2**32 and status in STATUS,'invalid result')
                require(self._purpose_body(purpose)==raw,'purpose changed during computation')
                retained.append((purpose,raw));aggregate.update(key)
                records_raw.extend(RECORD.pack(self.cells+offset,key,score,iterations,STATUS[status]))
                del purpose,raw,key
            # An extra item is refused without invoking executor. Batch wrappers
            # must be finite; shared upstream-generator cleanup remains caller-owned.
            sentinel=object();extra=next(iterator,sentinel)
            if extra is not sentinel:
                del extra
                raise ValueError('extra batch iterator item')
            closer=getattr(iterator,'close',None)
            if closer is not None:closer()
            iterator_closed=True
            self._purposes(retained,workload,workload_raw);self._pending(stem,pending,pp)
            self.boundary();self._pending(stem,pending,pp);self._purposes(retained,workload,workload_raw)
            actual=aggregate.digest()
            payload=HEADER.pack(MAGIC,RECORD.size,self.cells,self.cells+count,bytes.fromhex(digest(pending)),actual)+records_raw
            del records_raw
            bp=self._write(stem+'.records.tmp',payload,payload_limit)
            self._purposes(retained,workload,workload_raw);self._pending(stem,pending,pp)
            self._publish(stem+'.records.tmp',stem+'.records.bin',payload,bp)
            meta=body({'schema':3,'kind':'engineering_complete','pending_sha256':digest(pending),'payload_sha256':digest(payload),'payload_bytes':len(payload),'record_bytes':RECORD.size,'purposes_sha256':actual.hex()})
            mp=self._write(stem+'.complete.tmp',meta,self.max_body)
            self._pending(stem,pending,pp);self._read(stem+'.records.bin',payload,pin=bp)
            self._purposes(retained,workload,workload_raw)
            self._publish(stem+'.complete.tmp',stem+'.complete.json',meta,mp)
            records=self.read_complete(self.batch)
            self._pending(stem,pending,pp);self._read(stem+'.records.bin',payload,pin=bp);self._read(stem+'.complete.json',meta,pin=mp);self._root()
            self._purposes(retained,workload,workload_raw)
            self.cells+=count;self.batch+=1;return records
        except BaseException as error:self.poisoned=True;primary=error;raise
        finally:
            if iterator is not None and not iterator_closed:
                try:
                    closer=getattr(iterator,'close',None)
                    if closer is not None:closer()
                except BaseException as cleanup:
                    self.poisoned=True
                    if primary is not None:primary.add_note('iterator cleanup failed: '+repr(cleanup))
                    else:raise
    def close(self):
        if not self.closed:os.close(self.fd);self.closed=True
