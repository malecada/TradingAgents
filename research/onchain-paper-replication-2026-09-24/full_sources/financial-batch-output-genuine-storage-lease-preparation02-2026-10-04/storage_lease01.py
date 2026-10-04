"""Uninstalled retained-tree lease; metadata enforcement, never a kernel quota.

No scientific imports or authority construction. Generic OwnedLease is an opaque
engineering utility. GenuineLease requires existing original handles and an exact
admitted grant at each boundary. There is no reopen, refund, retirement or delete.
All producers must reserve exact prospective paths before writing and call check
at bounded callback boundaries. Uninstrumented/blocked writers remain outside a
sampled guarantee and still require the original native whole-root watch.
"""
import hashlib,json,os,stat,sys,threading,time
from pathlib import Path,PurePosixPath
from contextlib import contextmanager
from owned_io import _cleanup

MIB=1024**2
FILE=4*MIB
MAXIMUM=1024*MIB
FLOOR=10*1024**3
BLOCK=65536
DIRECTORY=MIB
SCRATCH=4*MIB
EVENT=65536
EVENTS=128
ENTRIES=32768
PKG='tradingagents.research.onchain_replication.'
PREFIX='research/onchain-paper-replication-2026-09-24/full_sources/financial-batch-output-genuine-storage-lease-preparation02-2026-10-04'
DENIED_SOURCE='0a2e7639b42b9423b90743feadcda4078aa21816'
IO_SHA='09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb'
ROLES=('producer','batches','outputs','codec','spool','recovered','diagnostic','journal','scratch')
FORBIDDEN=frozenset(('keys','apis','.env','hf_token.txt'))

def require(ok,why):
    if not ok:raise ValueError(why)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def canonical(v):
    raw=(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
    require(len(raw)<=FILE,'bounded metadata');return raw
def relative(s):
    require(type(s) is str and 0<len(s)<=4096 and not s.startswith('/') and str(PurePosixPath(s))==s and all(p not in ('','.','..') and p not in FORBIDDEN for p in s.split('/')),'contained canonical nonsecret path')
    return s
def pin(s):return type(s) is str and len(s)==64 and all(c in '0123456789abcdef' for c in s)
def round_block(n):return ((n+BLOCK-1)//BLOCK)*BLOCK
def sig(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_nlink,s.st_size,s.st_blocks,s.st_mtime_ns,s.st_ctime_ns)
def identity(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_uid)

def _anchor(path):
    path=Path(path)
    require(path.is_absolute() and str(path)==str(Path(os.path.abspath(path))) and path.resolve()==path,'canonical absolute root')
    fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        for part in path.parts[1:]:
            require(part not in FORBIDDEN,'no secret traversal')
            child=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=fd)
            previous=fd;fd=child
            _cleanup((lambda:os.close(previous),))
        require(identity(os.fstat(fd))==identity(path.lstat()),'root descriptor join')
        result=fd;fd=None;return result
    finally:
        if fd is not None:_cleanup((lambda:os.close(fd),))

def _rejoin(root,fd,root_id,rows,deadline):
    """One final metadata fingerprint sweep after measured IO cleanup.

    No new file/dir descriptor, iterator, callback or deferred close is created.
    Directory signatures cover sampled membership; every recorded child joins
    its full signature. No body hash or atomic/continuous immutability is claimed.
    Concurrent changes after their final stat remain outside this sampled proof.
    """
    require(time.monotonic()<deadline and root.resolve()==root and identity(root.lstat())==root_id and identity(os.fstat(fd))==root_id,'final sampled root identity')
    for path,row in sorted(rows.items()):
        require(time.monotonic()<deadline,'final sampled fingerprint deadline')
        current=os.fstat(fd) if path=='' else os.stat(path,dir_fd=fd,follow_symlinks=False)
        require(sig(current)==tuple(row['signature']),'final sampled metadata fingerprint changed')
    require(root.resolve()==root and identity(root.lstat())==root_id and identity(os.fstat(fd))==root_id,'final sampled lexical root rejoin')

def census(root,fd,root_id,*,deadline,file_limit=FILE):
    """No body reads: complete anchored metadata census, all retained descendants.

    Symlinks, hardlinked files, foreign UID/device and special types refuse. No
    subtree is excluded. Directory size/allocation is counted separately. A later
    namespace change cannot redirect retained descriptors; final lexical joins
    must still match. This does not make concurrent filesystem writes atomic.
    """
    rows={};dev=root_id[0]
    require(Path(root).resolve()==root and identity(root.lstat())==root_id and identity(os.fstat(fd))==root_id,'retained root namespace changed')
    def walk(dfd,prefix,depth):
        require(time.monotonic()<deadline and depth<=32,'bounded census deadline/depth')
        before=os.fstat(dfd);require(before.st_dev==dev and before.st_uid==os.getuid(),'owned same-filesystem tree')
        rows[prefix]={'kind':'directory','identity':identity(before),'size':before.st_size,'allocated':before.st_blocks*512,'signature':sig(before)}
        it=os.scandir(dfd)
        try:
            names=[]
            for entry in it:
                require(len(names)+len(rows)<ENTRIES,'finite tree cardinality')
                require(entry.name not in FORBIDDEN,'secret subtree refused')
                names.append(entry.name)
        finally:_cleanup((it.close,))
        for name in sorted(names):
            require(time.monotonic()<deadline,'census deadline')
            p=name if not prefix else prefix+'/'+name;relative(p)
            before_child=os.stat(name,dir_fd=dfd,follow_symlinks=False)
            require(before_child.st_dev==dev and before_child.st_uid==os.getuid(),'owned same-filesystem member')
            isdir=stat.S_ISDIR(before_child.st_mode)
            require(isdir or stat.S_ISREG(before_child.st_mode),'symlink/special member refused')
            require(isdir or before_child.st_nlink==1,'hardlinked file refused')
            flags=os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC|(os.O_DIRECTORY if isdir else 0)
            child=os.open(name,flags,dir_fd=dfd)
            try:
                require(sig(os.fstat(child))==sig(before_child),'open member changed')
                if isdir:walk(child,p,depth+1)
                else:
                    require(before_child.st_size<=file_limit,'per-file cap')
                    rows[p]={'kind':'file','identity':identity(before_child),'size':before_child.st_size,'allocated':before_child.st_blocks*512,'signature':sig(before_child)}
                require(sig(os.fstat(child))==sig(before_child) and sig(os.stat(name,dir_fd=dfd,follow_symlinks=False))==sig(before_child),'member changed during census')
            finally:_cleanup((lambda:os.close(child),))
        require(sig(os.fstat(dfd))==sig(before),'directory changed during census')
    walk(fd,'',0)
    require(Path(root).resolve()==root and identity(root.lstat())==root_id and identity(os.fstat(fd))==root_id,'final root rejoin')
    require(len(rows)<=ENTRIES,'finite total tree')
    _rejoin(root,fd,root_id,rows,deadline)
    return rows

class OwnedLease:
    """One live process/thread, one root and one immutable ledger namespace.

    Reservation counters include baseline, all issued tickets, all finite journal
    slots, per-entry rounding, directory growth and scratch. Never reduced. Each
    path ticket is one-use, including absent copies. A failed operation poisons
    the lease; close only relinquishes descriptors and cannot enable reuse.
    """
    def __init__(self,root,ledger,roles,logical,allocated,check):
        self.fd=self.ledger_fd=None;self.failed=False;self.closed=False;self._busy=threading.Lock();self.thread=threading.get_ident()
        self.root=Path(root);self.ledger=relative(ledger)
        require('/' not in ledger,'ledger must be direct root child')
        require(type(roles) is dict and set(roles)==set(ROLES),'complete declared workflow roles')
        self.roles=tuple((r,relative(roles[r])) for r in ROLES)
        require(all(not (p==ledger or p.startswith(ledger+'/')) for _,p in self.roles),'lease namespace separate from writer roles')
        require(type(logical) is int and type(allocated) is int and 0<logical<=MAXIMUM and 0<allocated<=MAXIMUM,'bounded registered maxima')
        require(callable(check),'engineering boundary callback')
        self.logical_cap=logical;self.allocated_cap=allocated;self._callback=check;self._callback_identity=check
        self.deadline=time.monotonic()+1800;self.tickets={};self.serial=0;self.seen={};self.records=[];self.failures=[];self.failure_journal_attempted=False
        self._config=(str(self.root),self.ledger,self.roles,logical,allocated,self.thread,self.deadline)
        self._stamp=None
        try:
            check();self.fd=_anchor(self.root);self.root_id=identity(os.fstat(self.fd))
            initial=census(self.root,self.fd,self.root_id,deadline=min(self.deadline,time.monotonic()+5))
            require(self.ledger not in initial,'fresh one-use lease namespace required')
            # Budget all future journal files and directory overhead up front.
            self.logical_reserved=sum(r['size'] for r in initial.values())+DIRECTORY+EVENTS*EVENT+SCRATCH
            self.allocated_reserved=sum(r['allocated'] for r in initial.values())+DIRECTORY+EVENTS*(BLOCK+BLOCK)+SCRATCH
            self._bounds(initial);self._space(self.allocated_reserved-sum(r['allocated'] for r in initial.values()))
            self.seen=initial
            os.mkdir(self.ledger,0o700,dir_fd=self.fd)
            self.ledger_fd=os.open(self.ledger,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=self.fd)
            st=os.fstat(self.ledger_fd);require(stat.S_IMODE(st.st_mode)==0o700,'private ledger mode');self.ledger_id=identity(st)
            self._stamp=self._state();self._write('start',{'roles':self.roles,'logical_reserved':self.logical_reserved,'allocated_reserved':self.allocated_reserved,'sampled':True,'authority':False})
            self.check()
        except BaseException as error:
            self.failed=True;self.failures.append(error)
            self._close_resources();raise
    def _state(self):
        return digest(canonical({'config':self._config,'tickets':self.tickets,'serial':self.serial,'logical':self.logical_reserved,'allocated':self.allocated_reserved,'records':self.records,'seen':self.seen,'root_id':self.root_id,'ledger_id':getattr(self,'ledger_id',None)}))
    def _integrity(self):
        require(not self.failed and not self.closed and threading.get_ident()==self.thread,'lease terminal/thread')
        require(self._callback is self._callback_identity and (str(self.root),self.ledger,self.roles,self.logical_cap,self.allocated_cap,self.thread,self.deadline)==self._config,'lease configuration changed')
        require(self._stamp==self._state(),'retained lease state changed')
        require(time.monotonic()<self.deadline,'whole lease deadline')
    def _boundary(self):
        self._integrity();self._callback();self._integrity()
    def _space(self,remaining):
        v=os.fstatvfs(self.fd);free=v.f_bavail*v.f_frsize
        require(free>=FLOOR+max(0,remaining),'10GiB free floor plus remaining committed growth')
        return free
    def _bounds(self,rows):
        logical=sum(r['size'] for r in rows.values());allocated=sum(r['allocated'] for r in rows.values())
        require(logical<=self.logical_reserved<=self.logical_cap and allocated<=self.allocated_reserved<=self.allocated_cap,'whole logical/allocated reservation exceeded')
        return logical,allocated
    def _write(self,kind,details):
        require(self.serial<EVENTS,'finite journal exhausted; no reset')
        name='event-%04d.json'%self.serial;raw=canonical({'sequence':self.serial,'kind':kind,'details':details})
        require(len(raw)<=EVENT,'event bound')
        require(identity(os.fstat(self.ledger_fd))==self.ledger_id and identity(os.stat(self.ledger,dir_fd=self.fd,follow_symlinks=False))==self.ledger_id,'ledger namespace changed')
        # Reserve sequence before any write; failures never make the name reusable.
        self.serial+=1;self._stamp=self._state()
        fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=self.ledger_fd)
        try:
            view=memoryview(raw)
            while view:
                n=os.write(fd,view[:65536]);require(n>0,'journal write progress');view=view[n:]
            os.fsync(fd);st=os.fstat(fd)
            require(st.st_nlink==1 and stat.S_IMODE(st.st_mode)==0o600 and st.st_size==len(raw) and sig(os.stat(name,dir_fd=self.ledger_fd,follow_symlinks=False))==sig(st),'journal owned path join')
        finally:_cleanup((lambda:os.close(fd),))
        os.fsync(self.ledger_fd)
        self.records.append((name,len(raw),digest(raw)));self._stamp=self._state()
    def _sample(self):
        rows=census(self.root,self.fd,self.root_id,deadline=min(self.deadline,time.monotonic()+5))
        for path,old in self.seen.items():
            require(path in rows,'retained member disappeared; no retirement')
            new=rows[path];require(new['identity']==old['identity'] and new['size']>=old['size'] and new['allocated']>=old['allocated'],'retained identity/extent/allocation decreased')
            if old['kind']=='file' and path not in self.tickets:
                require(new['signature']==old['signature'],'unreserved existing file mutation')
        for path,row in rows.items():
            if path==self.ledger:require(row['identity']==self.ledger_id,'ledger identity')
            elif path.startswith(self.ledger+'/'):
                require(path.count('/')==1 and any(path==self.ledger+'/'+x[0] and row['size']==x[1] for x in self.records),'unknown or partial journal body')
            elif path not in self.seen:
                require(path in self.tickets,'unreserved new member')
            if path in self.tickets:
                ticket=self.tickets[path]
                require(row['kind']==ticket['kind'] and row['size']<=ticket['size'] and row['allocated']<=ticket['allocated'],'projected path reservation exceeded')
                # Final extent seals only the sampled stat fingerprint, never bytes.
                if ticket.get('final') is not None:require(tuple(row['signature'])==tuple(ticket['final']),'sealed reserved file changed')
                if row['kind']=='file' and row['size']==ticket['size']:ticket['final']=row['signature']
        logical,allocated=self._bounds(rows);free=self._space(self.allocated_reserved-allocated)
        # Floor/statvfs and census descriptor cleanup precede this final sweep.
        _rejoin(self.root,self.fd,self.root_id,rows,min(self.deadline,time.monotonic()+5))
        self.seen=rows;self._stamp=self._state()
        return {'logical_bytes':logical,'allocated_bytes':allocated,'members':len(rows),'free_bytes':free,'logical_reserved':self.logical_reserved,'allocated_reserved':self.allocated_reserved}
    @contextmanager
    def _operation(self):
        if not self._busy.acquire(False):
            error=ValueError('recursive/concurrent lease operation refused');self.abort(error);raise error
        try:
            self._boundary();final={};yield final;self._boundary()
            # Exactly one final census after the actual trailing callback.
            # Its cleanup/floor IO is followed by a descriptor-free rejoin.
            final['sample']=self._sample()
        except BaseException as error:
            self.abort(error);raise
        finally:self._busy.release()
    def check(self):
        with self._operation() as final:self._sample()
        return final['sample']
    def reserve(self,role,paths,*,scratch_bytes=0):
        """Reserve exact new/growing destinations before any external write.

        paths is ordered [(relative_path,'file'|'directory',final_logical_size)].
        Directory projections must be1MiB. Scratch is retained commitment only;
        any actual scratch file ALSO requires its own path ticket. No deletion.
        """
        with self._operation() as final:
            self._sample();require(role in ROLES and type(paths) in (list,tuple) and 0<len(paths)<=256,'bounded declared copy plan')
            require(type(scratch_bytes) is int and 0<=scratch_bytes<=SCRATCH,'bounded additional scratch')
            prefix=dict(self.roles)[role];planned={};logical=scratch_bytes;allocated=round_block(scratch_bytes)
            for row in paths:
                require(type(row) in (list,tuple) and len(row)==3,'path projection shape');path,kind,size=row;relative(path)
                require((path==prefix or path.startswith(prefix+'/')) and path not in self.tickets and path not in planned,'role-contained one-use path')
                require(kind in ('file','directory') and type(size) is int and 0<=size<=(FILE if kind=='file' else DIRECTORY) and (kind!='directory' or size==DIRECTORY),'bounded final path extent')
                old=self.seen.get(path)
                require(old is None or (old['kind']==kind and kind=='file' and size>old['size']),'new path or monotone existing file growth')
                parent=str(PurePosixPath(path).parent)
                require(parent=='.' or (parent in self.seen and self.seen[parent]['kind']=='directory') or (parent in planned and planned[parent]['kind']=='directory'),'declare missing parents before child')
                amount=(DIRECTORY if kind=='directory' else round_block(size)+BLOCK)
                planned[path]={'kind':kind,'size':size,'allocated':amount,'final':None}
                logical+=size;allocated+=amount # full copies, no credit for prior allocation
            require(self.logical_reserved+logical<=self.logical_cap and self.allocated_reserved+allocated<=self.allocated_cap,'cumulative prospective capacity exhausted')
            self._space(self.allocated_reserved+allocated-sum(r['allocated'] for r in self.seen.values()))
            # Spend before journaling; no finally rollback on failure.
            self.logical_reserved+=logical;self.allocated_reserved+=allocated;self.tickets.update(planned);self._stamp=self._state()
            self._write('reserve',{'role':role,'paths':paths,'scratch_bytes':scratch_bytes,'logical_reserved':self.logical_reserved,'allocated_reserved':self.allocated_reserved})
            self._sample()
        return final['sample']
    def perform(self,role,paths,write,*,scratch_bytes=0):
        """Bounded utility callback; genuine caller supplies the real writer.

        reserve/check complete before calling writer. No internal lock is held
        during writer, so writer's nonrecursive periodic lease.check is allowed.
        Writer failure permanently poisons; all original bytes remain retained.
        """
        self.reserve(role,paths,scratch_bytes=scratch_bytes)
        try:
            self.check();result=write(self.check);self.check();return result
        except BaseException as error:self.abort(error);raise
    def abort(self,error):
        self.failed=True;self.failures.append(error)
        def diagnostic():
            if self.ledger_fd is None or self.failure_journal_attempted:return
            self.failure_journal_attempted=True
            self._space(0)
            self._write('failed',{'error_type':type(error).__name__,'logical_reserved':self.logical_reserved,'allocated_reserved':self.allocated_reserved,'no_refund':True})
        def retain(action):
            def call():
                try:return action()
                except BaseException as later:self.failures.append(later);raise
            return call
        _cleanup((retain(diagnostic),retain(self._close_resources)),primary=error)
    def _close_resources(self):
        actions=[]
        for attr in ('ledger_fd','fd'):
            fd=getattr(self,attr,None);setattr(self,attr,None)
            if fd is not None:actions.append(lambda fd=fd:os.close(fd))
        _cleanup(tuple(actions))
    def close(self):
        if self.closed:return
        try:
            if not self.failed:
                self.check();self._write('closed',self._sample());self.check()
        except BaseException as error:self.failed=True;self.failures.append(error);raise
        finally:
            self.closed=True;self._close_resources()

# Genuine entrypoints below never create handles or import project packages.
def module(name):
    value=sys.modules.get(name);require(value is not None,'UNAVAILABLE: genuine loaded module '+name);return value

def validate_grant(g,job_sha,roles,graphs):
    keys={'schema_version','kind','execution_job_sha256','roles','max_logical_bytes','max_allocated_bytes','max_file_bytes','free_floor_bytes','root_scope','targets','publication','transport','retirement'}
    require(type(g) is dict and set(g)==keys and type(g['schema_version']) is int and g['schema_version']==1,'exact storage grant')
    require(g['kind']=='two-imported-target-retained-lease-v1' and pin(job_sha) and g['execution_job_sha256']==job_sha,'separate resource engineering grant')
    require(type(graphs) is dict and len(graphs)==2 and all(pin(k) and type(n) is int and n in (2,3) for k,n in graphs.items()) and type(g['targets']) is dict and g['targets']==graphs and all(type(n) is int for n in g['targets'].values()),'exact original two tiny targets')
    require(g['roles']==roles and g['root_scope']=='entire-admission-root','complete exact retained scope')
    require(g['max_file_bytes']==FILE and type(g['max_file_bytes']) is int and g['free_floor_bytes']==FLOOR and type(g['free_floor_bytes']) is int,'original file/floor policy')
    require(all(type(g[k]) is int and 0<g[k]<=MAXIMUM for k in ('max_logical_bytes','max_allocated_bytes')),'whole registered storage maxima')
    require(all(g[k] is False for k in ('publication','transport','retirement')),'no additional authority')
    return g

class GenuineLease:
    """Composes existing held Target boundaries; never reacquires Owner's lock.

    Create while a genuine held transition is active. Rebind the SAME Owner/Run
    at later genuine target transitions using boundary(); the core is never
    reset. Every byte callback must occur inside that boundary. It deliberately
    cannot operate as a financial grant or an asynchronous transport authority.
    """
    def __init__(self,target,held):
        self.context=None;self.core=None;self.owner=None;self.run=None;self.closed=False
        self._set(target,held)
        try:
            self._genuine();run=self.run;owner=self.owner
            job_raw=run.read_input('execution_job');job=json.loads(job_raw)
            require(job.get('kind')=='compact_resource','UNAVAILABLE: financial/source grant unsupported')
            require('storage_lease' in run.admission.inputs,'UNAVAILABLE: separately registered storage lease absent')
            grant_raw=run.read_input('storage_lease');grant=json.loads(grant_raw)
            require(canonical(grant)==grant_raw,'canonical registered storage grant')
            self.grant_raw=grant_raw;self.job_raw=job_raw
            root=run.admission.root;record=owner.bound.record
            roles={
              'producer':str((root/'research_artifacts/onchain_compact_mcm'/record['workflow_identity']/record['experiment']).relative_to(root)),
              'batches':str(owner.root.relative_to(root)),
              'outputs':str((root/'research_artifacts/onchain_compact_outputs'/record['workflow_identity']/record['experiment']).relative_to(root)),
              'codec':str(run.directory.relative_to(root)),
              'spool':str((run.directory/'retained-spool').relative_to(root)),
              'recovered':str((run.directory/'retained-recovered').relative_to(root)),
              'diagnostic':str(run.directory.relative_to(root)),
              'journal':str(Path(record['journal_directory']).relative_to(root)),
              'scratch':str((run.directory/'retained-scratch').relative_to(root))}
            graphs=target.execution._stage.prepared._selection_now()['selected']['descriptor']['resource_fixture']['target_nodes']
            validate_grant(grant,digest(job_raw),roles,graphs)
            require(target.key in graphs and len(target.graph.node_ids)==graphs[target.key],'actual original target denominator')
            require(owner.bound.record.get('resource_only') is True,'genuine original resource-only Owner')
            limits=job['resources']['storage_budget']['limits']
            require(grant['max_logical_bytes']<=limits['max_logical_bytes'] and grant['max_allocated_bytes']<=limits['max_allocated_bytes'],'unchanged original whole-watch caps')
            self.graphs=tuple(sorted(graphs.items()))
            require(grant['max_logical_bytes']<=owner.maximum,'lease cannot enlarge original Owner maximum')
            # Every new source body joins actual admission, not a hash in its own grant.
            consumer=module(PKG+'held_score_consumer');consumer._sources(run)
            for relative_path in (PREFIX+'/storage_lease01.py',PREFIX+'/owned_io.py'):
                h=run.admission.experiment['source_files'].get(relative_path)
                require(pin(h) and digest(consumer._body(root/relative_path))==h,'actual admitted lease source')
                if relative_path.endswith('/owned_io.py'):require(h==IO_SHA,'unchanged first-fatal reducer')
            require(Path(__file__)==root/PREFIX/'storage_lease01.py','installed lease origin')
            io_origin=consumer.PREFIX+'/owned_io.py'
            require(_cleanup is module('owned_io')._cleanup and Path(module('owned_io').__file__)==root/io_origin and run.admission.experiment['source_files'].get(io_origin)==IO_SHA and digest(consumer._body(root/io_origin))==IO_SHA,'genuine admitted unchanged reducer alias')
            self.core=OwnedLease(root,'retained-lease-'+record['workflow_identity'],roles,grant['max_logical_bytes'],grant['max_allocated_bytes'],self._genuine)
        finally:self.context=None
    def _set(self,target,held):
        require(self.context is None and not self.closed,'one held boundary at a time')
        require(type(target) is module(PKG+'imported_mcm_identity').Target,'actual original Target before attribute access')
        owner=target.owner
        require(type(owner) is module(PKG+'compact_owner').Owner and type(held) is module(PKG+'compact_owner')._HeldTransition,'actual original Target/Owner/held only')
        bound=owner.bound;run=bound._run
        require(type(bound) is module(PKG+'matching_owner').Binding and type(run) is module('tradingagents.research.lifecycle').ResearchRun,'actual original Binding/Run only')
        require(run.admission.source!=DENIED_SOURCE,'UNAVAILABLE: Source339 has no shared lease admission')
        require(self.owner is None or (self.owner is owner and self.run is run),'no cross-owner/source lease reuse')
        self.owner=owner;self.run=run;self.context=(target,held)
    def _genuine(self):
        require(self.context is not None,'genuine held boundary unavailable');target,held=self.context
        held.check(self.owner);self.owner.bound.check();target.check()
        if hasattr(self,'grant_raw'):
            require(self.run.read_input('storage_lease')==self.grant_raw and self.run.read_input('execution_job')==self.job_raw,'registered grant/job changed')
        if hasattr(self,'graphs'):
            graphs=target.execution._stage.prepared._selection_now()['selected']['descriptor']['resource_fixture']['target_nodes']
            require(tuple(sorted(graphs.items()))==self.graphs and target.key in graphs and len(target.graph.node_ids)==graphs[target.key],'same complete target denominator')
        module(PKG+'compact_owner').verify_current(self.owner);held.check(self.owner)
        prepared=target.execution._stage.prepared;policy=json.loads(self.run.read_input(prepared._input))
        require(policy==json.loads(prepared._cap._policy) and type(policy.get('sample_count')) is int and policy['sample_count']==512 and type(policy.get('motif_count')) is int and policy['motif_count']==32,'unchanged actual original512/32 policy')
    @contextmanager
    def boundary(self,target,held):
        self._set(target,held)
        try:
            self.core.check();yield self.core;self.core.check()
        except BaseException as error:
            self.core.abort(error);raise
        finally:self.context=None
    def close_held(self,target,held):
        self._set(target,held)
        try:self.core.close()
        finally:self.context=None;self.closed=True
