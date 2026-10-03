"""Bounded source-only capsule export. Does not admit, commit or execute research."""
import hashlib,json,os,stat,subprocess
from pathlib import Path
MAX_FILE=4*1024**2
MAX_TOTAL=32*1024**2
MAX_FILES=256

def require(value,message):
    if not value:raise ValueError(message)

class SourceCleanupFailure(BaseException):pass

def close_owned(fd,primary):
    try:os.close(fd)
    except BaseException as later:
        if primary is not None and (isinstance(primary,MemoryError) or not isinstance(primary,Exception)):return
        if isinstance(later,MemoryError) or not isinstance(later,Exception):raise
        failure=SourceCleanupFailure('source descriptor close uncertain; retained partial export')
        failure.errors=(primary,later)
        raise failure from primary


def relative(name):
    p=Path(name)
    require(type(name) is str and name and not p.is_absolute() and all(x not in ('..','.env','keys','apis','hf_token.txt','.git','.venv') and not x.startswith('.env.') for x in p.parts),'unsafe capsule source path')
    require(str(p)==name and '\n' not in name and '\x00' not in name,'noncanonical source path')
    return p

def read(root,name,expected,size):
    root=Path(root);p=root/relative(name);before=p.lstat()
    require(p.resolve()==p and stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size==size and 0<size<=MAX_FILE,'source type/link/extent differs')
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW);primary=None
    try:
        opened=os.fstat(fd);require((opened.st_dev,opened.st_ino)==(before.st_dev,before.st_ino),'source replaced before read')
        raw=b''
        while len(raw)<=size:
            block=os.read(fd,min(65536,size+1-len(raw)))
            if not block:break
            raw+=block
        after=p.lstat();require((after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)==(before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns),'source changed during read')
        require(len(raw)==size and hashlib.sha256(raw).hexdigest()==expected,'source hash differs')
        return raw
    except BaseException as error:primary=error;raise
    finally:
        close_owned(fd,primary)

def validated_sources(spec,root):
    rows=spec['source_inventory'];require(type(rows) is list and 1<=len(rows)<=MAX_FILES,'source inventory cardinality')
    seen=set();total=0;result=[]
    for row in rows:
        require(set(row)=={'target','origin','sha256','bytes','git_commit','git_path'},'source row schema differs')
        name=str(relative(row['target']));require(name not in seen,'duplicate install target');seen.add(name)
        require(type(row['bytes']) is int and row['bytes']>0,'source extent differs');total+=row['bytes'];require(total<=MAX_TOTAL,'capsule source total exceeds bound')
        raw=read(root,row['origin'],row['sha256'],row['bytes'])
        if row['git_commit'] is not None:
            require(type(row['git_commit']) is str and len(row['git_commit'])==40,'source commit differs')
            ref=row['git_commit']+':'+str(relative(row['git_path']))
            env={**os.environ,'GIT_NO_LAZY_FETCH':'1'}
            extent=int(subprocess.check_output(['git','cat-file','-s',ref],cwd=root,env=env,timeout=10))
            require(extent==len(raw),'Git source extent differs')
            body=subprocess.check_output(['git','cat-file','blob',ref],cwd=root,env=env,timeout=10)
            require(body==raw,'committed source body differs')
        result.append((name,raw))
    require(set(spec['required_package_sources'])<=seen,'package closure omitted')
    return result

def export_sources(spec,root,destination):
    """Coordinator may call after source review; no .git/runtime/input birth here."""
    require(spec['status']=='reviewed-source-export-only','unreviewed capsule export refused')
    result=validated_sources(spec,root)
    destination=Path(destination);require(destination.is_absolute() and destination.parent.resolve()==destination.parent and not destination.exists(),'fresh absolute capsule directory required')
    destination.mkdir(mode=0o700)
    # Every byte was validated before first population; any partial tree is retained.
    for name,raw in result:
        p=destination/name;p.parent.mkdir(parents=True,exist_ok=True)
        fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);primary=None
        try:
            offset=0
            while offset<len(raw):
                count=os.write(fd,raw[offset:]);require(count>0,'short source write');offset+=count
            os.fsync(fd)
        except BaseException as error:primary=error;raise
        finally:
            close_owned(fd,primary)
    for directory in sorted({destination}|{p for name,_ in result for p in (destination/name).parents if p==destination or p.is_relative_to(destination)},key=lambda p:len(p.parts),reverse=True):
        fd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);primary=None
        try:os.fsync(fd)
        except BaseException as error:primary=error;raise
        finally:close_owned(fd,primary)
    return {'files':len(result),'logical_bytes':sum(len(raw) for _,raw in result),'committed':False,'registered':False}


def export_original_objects(index,source_root,capsule_root):
    """After coordinator-created local .git; does not create any new source commit."""
    capsule_root=Path(capsule_root)
    require((capsule_root/'.git').is_dir() and not (capsule_root/'.git').is_symlink(),'local owned Git object store required')
    require(not (capsule_root/'.git/objects/info/alternates').exists(),'external Git alternates forbidden')
    rows=index['objects'];require(type(rows) is list and len(rows)<=128,'bounded original object count')
    total=0;pending=[];seen=set();env={**os.environ,'GIT_NO_LAZY_FETCH':'1'}
    for row in rows:
        oid=row['oid'];require(type(oid) is str and len(oid)==40 and all(x in '0123456789abcdef' for x in oid) and oid not in seen,'original object identity differs');seen.add(oid)
        require(row['type'] in ('commit','tree','blob') and type(row['bytes']) is int and 0<row['bytes']<=MAX_FILE,'original object type/extent')
        total+=row['bytes'];require(total<=4*1024**2,'original object total bound')
        size=int(subprocess.check_output(['git','cat-file','-s',oid],cwd=source_root,env=env,timeout=10));require(size==row['bytes'],'original Git extent differs')
        raw=subprocess.check_output(['git','cat-file',row['type'],oid],cwd=source_root,env=env,timeout=10)
        require(hashlib.sha256(raw).hexdigest()==row['body_sha256'],'original Git object body differs');pending.append((row,raw))
    for row,raw in pending:
        result=subprocess.run(['git','hash-object','-w','-t',row['type'],'--stdin'],cwd=capsule_root,input=raw,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=10)
        require(result.stdout.decode().strip()==row['oid'],'original object import differs')
    return {'objects':len(pending),'bytes':total,'historical_claim_reopened':False}

# Separate held-resource metadata route. Legacy exporter remains unchanged.
HELD_COUNTS=(199,148)
HELD_S2='fb9fad1d93836b4f92f2be8111da4adf22b7e069'
HELD_SOURCE04_ANCHOR='0cfc2c03200880534b7c91c2f16ac659a265a35b'
HELD_SOURCE04='fa9712c36daf2896ef3f6a8a8a5d99ec696cfdf4'
HELD_SOURCE04_LINEAGE=((HELD_SOURCE04,HELD_SOURCE04_ANCHOR),(HELD_SOURCE04_ANCHOR,'903488c49ad25e8026ec849a1c8b30ca5f90bcff'),('903488c49ad25e8026ec849a1c8b30ca5f90bcff','76a4bd766722e0f5177412f6945117d9c2b5fc45'),('76a4bd766722e0f5177412f6945117d9c2b5fc45','b8c6c280fb229ffaa5195c95baf3f57485e972b0'),('b8c6c280fb229ffaa5195c95baf3f57485e972b0',HELD_S2))
HELD_SOURCE04_PACKAGE_CHANGES={'resource_fixture.py':'3ea9902ec4067edc59bc897081c5ad5f6738350ccd3a339b0b423c863212a97e'}
HELD_OLD_INVENTORY='e8d8594d1c7aabe4076bf2b4bab7454cb0fad48ec8f46b754e06fc3f3ddb6773'
HELD_IO='09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb'
HELD_PACKAGE_CHANGES={'compact_mcm.py':'6661a8668d04bdff4afa84161932e12daa351d2654c5c481eba5faafcd938a4c','mcm_score_stream.py':'ee7931cea3d28ad0719b5f3db171a5d5d3ab95db9ff7cad0cc8379101948b79e','held_score_consumer.py':'35da29691a5ef6c23f4bbdf178a55fd51bb6779214c1d38fb5a162e712ea0d41'}
HELD_READER='research/onchain-paper-replication-2026-09-24/full_sources/neural-cold-feature-handoff-held-score-reader-preparation01-2026-10-03/'
HELD_ADDITIONS={HELD_READER+'held_score_reader.py':'3836bbcdc8b5b1be6a08c47a6d97c76c7c0875eeba7e91e6d363bdc6b4ade209',HELD_READER+'exact_members02.py':'ea1ffcef833344ff1a5fbd89bc2f79ade1414c90a3159329c1f3bdee86bfe0cb',HELD_READER+'owned_io.py':HELD_IO,'tradingagents/research/onchain_replication/held_score_consumer.py':HELD_PACKAGE_CHANGES['held_score_consumer.py']}
HELD_SUCCESSOR_HELPERS={'fixture_tools/capsule_builder01.py','fixture_tools/generate_inputs01.py','proof_tools/build_release_draft01.py'}

def _held_io(root):
    # Bootstrap uses the pre-existing bounded descriptor read/first-fatal close.
    name='tradingagents/research/onchain_replication/owned_io.py'
    raw=read(root,name,HELD_IO,3099);namespace={'__name__':'held_metadata_owned_io'}
    exec(compile(raw,name,'exec'),namespace)
    return namespace['_cleanup']

def held_document(root,reference):
    """Bounded metadata/source bytes only; no decoding of array/pickle files."""
    require(type(reference) is dict and set(reference)=={'path','sha256','bytes'},'held document reference fields')
    name=str(relative(reference['path']));require(not name.endswith(('.npy','.npz','.pt','.pkl','.pickle')),'numerical body is not a metadata role')
    require(type(reference['bytes']) is int and 0<reference['bytes']<=MAX_FILE and type(reference['sha256']) is str and len(reference['sha256'])==64,'held document extent/hash')
    root=Path(root);path=root/name;cleanup=_held_io(root);parent_fd=fd=None
    sig=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_blocks)
    try:
        require(root.is_absolute() and root.resolve()==root and path.resolve()==path,'held metadata path redirected')
        parent_fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);parent=sig(os.fstat(parent_fd))
        require(sig(path.parent.lstat())==parent,'held metadata parent changed')
        before=os.stat(path.name,dir_fd=parent_fd,follow_symlinks=False);pin=sig(before)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size==reference['bytes'],'held metadata extent/type differs')
        fd=os.open(path.name,os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent_fd)
        require(sig(os.fstat(fd))==pin,'held metadata replaced before open')
        chunks=[];count=0
        while True:
            block=os.read(fd,min(65536,before.st_size-count+1))
            if not block:break
            count+=len(block);require(count<=before.st_size,'held metadata grew');chunks.append(block)
        raw=b''.join(chunks)
        require(count==reference['bytes'] and hashlib.sha256(raw).hexdigest()==reference['sha256'],'held metadata hash differs')
        require(sig(os.fstat(fd))==pin==sig(os.stat(path.name,dir_fd=parent_fd,follow_symlinks=False))==sig(path.lstat()) and path.resolve()==path,'held metadata changed during read')
        require(sig(os.fstat(parent_fd))==parent==sig(path.parent.lstat()) and path.parent.resolve()==path.parent,'held metadata parent changed during read')
        return raw
    finally:cleanup((() if fd is None else (lambda:os.close(fd),))+(() if parent_fd is None else (lambda:os.close(parent_fd),)))

def _held_git(root,*args):
    return subprocess.check_output(['git','-c','protocol.allow=never',*args],cwd=root,env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_OPTIONAL_LOCKS':'0','GIT_NO_REPLACE_OBJECTS':'1'},stderr=subprocess.PIPE,timeout=10)

def held_source_plan(root,source,anchor,rows):
    """Authenticate current199/anchor148 bodies; result is NOT admission."""
    root=Path(root)
    for x in (source,anchor):require(type(x) is str and len(x)==40 and all(c in '0123456789abcdef' for c in x),'genuine full source/anchor required')
    require(_held_git(root,'rev-parse','HEAD').decode().strip()==source,'held current HEAD differs')
    require((root/'.git').is_dir() and not (root/'.git').is_symlink(),'owned local Git required')
    for name in ('objects/info/alternates','info/grafts','refs/replace'):
        require(not os.path.lexists(root/'.git'/name),'Git indirection refused')
    _held_git(root,'merge-base','--is-ancestor',anchor,source)
    parents=_held_git(root,'show','-s','--format=%P',anchor).decode().strip().split()
    source04=anchor==HELD_SOURCE04_ANCHOR
    if source04:
        for child,parent in HELD_SOURCE04_LINEAGE:
            actual=_held_git(root,'show','-s','--format=%P',child).decode().strip().split()
            require(actual==[parent],'accepted held Source04 lineage differs')
        _held_git(root,'merge-base','--is-ancestor',HELD_SOURCE04,source)
    else:
        require(parents==[HELD_S2],'held anchor must genuinely descend directly from original S2')
    old_path='cold_prep/source_inventory.json';old_raw=read(root,old_path,HELD_OLD_INVENTORY,124011);old=json.loads(old_raw)
    require(old['source_count']==195 and old['package_count']==147,'historical source denominator differs')
    baseline={x['target']:x['sha256'] for x in old['source_inventory']};require(len(baseline)==195,'historical source inventory duplicates')
    require(type(rows) is list and len(rows)==199 and all(type(x) is dict and set(x)=={'path','sha256','bytes'} for x in rows),'held199 source rows required')
    names=[x['path'] for x in rows];require(names==sorted(set(names)) and set(names)==set(baseline)|set(HELD_ADDITIONS),'complete held source membership differs')
    registered={x['path']:x['sha256'] for x in rows};expected={**baseline,**HELD_ADDITIONS}
    expected.update({'tradingagents/research/onchain_replication/'+k:v for k,v in HELD_PACKAGE_CHANGES.items()})
    if source04:expected.update({'tradingagents/research/onchain_replication/'+k:v for k,v in HELD_SOURCE04_PACKAGE_CHANGES.items()})
    expected['tradingagents/research/verify.py']='1f14343c7918e3464991b9b57ecdf74425130de5c049a4e401d896116881efce'
    for name in set(expected)-HELD_SUCCESSOR_HELPERS:require(registered[name]==expected[name],'undeclared held source replacement')
    package=sorted(n for n in names if n=='tradingagents/__init__.py' or (n.endswith('.py') and str(Path(n).parent) in ('tradingagents/research','tradingagents/research/onchain_replication')))
    require(len(package)==148,'held complete package denominator differs')
    if source04:
        for commit in (anchor,source):
            anchored=_held_git(root,'ls-tree','-r','--name-only',commit).decode().splitlines()
            anchored_package=sorted(n for n in anchored if n=='tradingagents/__init__.py' or (n.endswith('.py') and str(Path(n).parent) in ('tradingagents/research','tradingagents/research/onchain_replication')))
            require(anchored_package==package,'accepted Source04 complete148 anchor/current roster differs')
    total=0;origins=[]
    for row in rows:
        raw=held_document(root,row);total+=len(raw);require(total<=MAX_TOTAL,'held source aggregate exceeds limit')
        for commit in ([source,anchor] if row['path'] in package else [source]):
            ref=commit+':'+row['path'];require(int(_held_git(root,'cat-file','-s',ref))==len(raw),'held Git source extent differs')
            require(_held_git(root,'cat-file','blob',ref)==raw,'held Git/source body differs')
        origins.append({'path':row['path'],'sha256':row['sha256'],'bytes':len(raw),'git_commit':source,'git_path':row['path']})
    return {'schema_version':1,'kind':'held-resource-source-metadata-v1','status':'source-only-unregistered','root':str(root),'source':source,'anchor':anchor,'source_count':199,'package_count':148,'source_files':registered,'package_files':{n:registered[n] for n in package},'source_origins':origins,'logical_bytes':total,'execution_admitted':False}

def _held_interpreter(root,path,expected,size):
    """Hash only the pinned runtime executable, with a separate64MiB ceiling.

    Source/native writable caps remain4MiB. No executable bytes are accumulated.
    """
    path=Path(path);cleanup=_held_io(root);parent_fd=fd=None
    sig=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_blocks)
    try:
        require(type(size) is int and 0<size<=64*1024**2 and type(expected) is str and len(expected)==64 and all(c in '0123456789abcdef' for c in expected),'finite pinned runtime executable extent/hash')
        require(path.is_absolute() and path.resolve()==path and path.name not in ('','.','..'),'runtime executable redirected')
        parent=path.parent
        parent_fd=os.open(parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
        parent_pin=sig(os.fstat(parent_fd))
        require(stat.S_ISDIR(os.fstat(parent_fd).st_mode) and parent.resolve()==parent and sig(parent.lstat())==parent_pin,'runtime executable parent changed')
        before=os.stat(path.name,dir_fd=parent_fd,follow_symlinks=False);pin=sig(before)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_size==size,'runtime executable type/link/extent differs')
        fd=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=parent_fd)
        require(sig(os.fstat(fd))==pin,'runtime executable replaced before open')
        digest=hashlib.sha256();total=0
        while True:
            block=os.read(fd,min(65536,size-total+1))
            if not block:break
            total+=len(block);require(total<=size,'runtime executable grew');digest.update(block)
        require(total==size and digest.hexdigest()==expected,'runtime executable hash/extent differs')
        require(sig(os.fstat(fd))==pin==sig(os.stat(path.name,dir_fd=parent_fd,follow_symlinks=False))==sig(path.lstat()) and path.resolve()==path,'runtime executable changed during read')
        require(sig(os.fstat(parent_fd))==parent_pin==sig(parent.lstat()) and parent.resolve()==parent,'runtime executable parent changed during read')
        return {'bytes':total,'sha256':digest.hexdigest()}
    finally:cleanup((() if fd is None else (lambda:os.close(fd),))+(() if parent_fd is None else (lambda:os.close(parent_fd),)))

def held_runtime_metadata(root,expected):
    """Read actual installed RECORD bytes using stdlib only; no native authority."""
    import importlib.metadata,platform,sys
    require(type(expected) is dict and type(expected.get('distribution_records')) is list and len(expected['distribution_records'])==251,'complete runtime metadata required')
    require(sys.executable==expected['executable'] and sys.prefix==expected['prefix'] and platform.python_version()==expected['python'],'current locked interpreter differs')
    executable=Path(sys.executable).resolve();require(str(executable)==expected['resolved_executable'],'resolved interpreter differs')
    _held_interpreter(root,executable,expected['executable_sha256'],expected['executable_bytes'])
    prefix=Path(sys.prefix).resolve();rows=[];total=0
    for row in expected['distribution_records']:
        require(type(row) is dict and type(row.get('record')) is str and importlib.metadata.version(row['name'])==row['version'],'installed distribution version/record differs')
        p=Path(row['record']);require(p.resolve()==p and p.is_relative_to(prefix),'runtime RECORD outside pinned prefix')
        size=p.stat().st_size;total+=size;require(total<=32*1024**2,'runtime RECORD aggregate bound')
        read(prefix,str(p.relative_to(prefix)),row['record_sha256'],size)
        rows.append({'name':row['name'],'version':row['version'],'path':str(p),'sha256':row['record_sha256'],'bytes':size})
    require(len({x['name'] for x in rows})==251,'runtime distribution uniqueness')
    lock=Path(root)/'uv.lock';read(root,'uv.lock',expected['lock_sha256'],lock.stat().st_size)
    return {'kind':'actual-stdlib-runtime-record-readback','distribution_records':rows,'record_count':251,'record_bytes':total,'all_installed_package_bodies_rehashed':False,'native_controls_verified':False,'execution_admitted':False}


# Explicit full202 metadata route; original prefix remains byte-identical.
import selectors,time
MAX=4*1024**2
META=8192
class CleanupFailure(BaseException):pass

def sha(raw):return hashlib.sha256(raw).hexdigest()

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()

def equal(a,b):return canonical(a)==canonical(b)

def fatal(e):return isinstance(e,MemoryError) or (not isinstance(e,Exception) and not isinstance(e,CleanupFailure))

def cleanup(actions,primary=None):
    failures=[]
    for action in actions:
        try:action()
        except BaseException as error:failures.append(error)
    errors=([primary] if primary is not None else [])+failures
    chosen=next((e for e in errors if fatal(e)),None)
    if chosen is not None:raise chosen
    if failures:raise CleanupFailure('owned read/process cleanup uncertain') from (primary or failures[0])
    if primary is not None:raise primary

def signature(s):return (s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)

def parse(raw):
    def pairs(items):
        out={}
        for k,v in items:require(k not in out,'duplicate JSON key');out[k]=v
        return out
    def constant(value):raise ValueError('nonfinite JSON constant')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)

class Reader:
    def __init__(self,root):
        self.root=Path(root);require(self.root.is_absolute() and self.root.resolve()==self.root,'canonical original root required')
        self.total=0;self.files={};self.deadline=time.monotonic()+120
    def body(self,relative,limit=MAX):
        require(time.monotonic()<self.deadline,'bounded semantic read deadline')
        require(type(relative) is str and relative and not Path(relative).is_absolute() and all(p not in ('','.','..') for p in relative.split('/')) and '\\' not in relative,'finite relative original member')
        require(not any(p.lower() in ('keys','apis','.env','.ssh') or p.lower().endswith(('.pem','.key')) or p.lower()=='hf_token.txt' for p in relative.split('/')),'protected path refused before IO')
        require(type(limit) is int and 0<limit<=MAX,'finite per-file bound')
        path=self.root/relative;fds=[];parents=[];primary=None;result=None
        try:
            fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);fds.append(fd);parent=self.root
            parents.append((parent,fd,signature(os.fstat(fd))))
            for part in Path(relative).parts[:-1]:
                fd=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=fd);fds.append(fd);parent=parent/part;parents.append((parent,fd,signature(os.fstat(fd))))
            name=Path(relative).name;before=os.stat(name,dir_fd=fd,follow_symlinks=False);pin=signature(before)
            require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and 0<=before.st_size<=limit,'original file type/link/extent')
            child=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=fd);fds.append(child)
            require(signature(os.fstat(child))==pin,'original member changed before read')
            chunks=[];count=0
            while True:
                part=os.read(child,min(65536,before.st_size-count+1))
                if not part:break
                count+=len(part);require(count<=before.st_size and count<=limit,'original member grew during read');chunks.append(part)
            require(count==before.st_size and signature(os.fstat(child))==pin and signature(os.stat(name,dir_fd=fd,follow_symlinks=False))==pin and signature(path.lstat())==pin and path.resolve()==path,'original member changed during read')
            for parent,parentfd,expected in parents:require(parent.resolve()==parent and signature(parent.lstat())==expected==signature(os.fstat(parentfd)),'original parent redirected/replaced')
            result=b''.join(chunks);self.total+=len(result);require(self.total<=64*1024**2 and len(self.files)<4096,'aggregate semantic read ceiling')
            row=(pin,sha(result));require(relative not in self.files or self.files[relative]==row,'retained member changed between checks');self.files[relative]=row
        except BaseException as error:primary=error
        cleanup([lambda fd=fd:os.close(fd) for fd in reversed(fds)],primary)
        return result
    def json(self,name,limit=MAX):return parse(self.body(name,limit))
    def exact_members(self,relative,names):
        root=self.root/relative;require(root.resolve()==root,'member directory redirected');fd=None;it=None;primary=None
        try:
            fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);pin=signature(os.fstat(fd));it=os.scandir(fd);seen=set()
            for row in it:
                require(row.name not in seen and row.name in names,'unexpected original member');s=row.stat(follow_symlinks=False);require(stat.S_ISREG(s.st_mode) and s.st_nlink==1,'nonregular original member');seen.add(row.name)
            require(seen==set(names) and root.resolve()==root and signature(root.lstat())==pin==signature(os.fstat(fd)),'missing/replaced original member directory')
        except BaseException as error:primary=error
        cleanup(([] if it is None else [it.close])+([] if fd is None else [lambda:os.close(fd)]),primary)
    def recheck(self):
        saved=dict(self.files)
        for name in sorted(saved):self.body(name)
        require(self.files==saved,'evidence changed during final readback')

def git(root,args,request=b'',cap=8*1024**2):
    """Fresh offline Git process; bounded pipes/cleanup, no fetch or mutation."""
    env={'PATH':'/usr/bin:/bin','LC_ALL':'C','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_TERMINAL_PROMPT':'0'}
    require(len(request)<=65536,'Git request bound');child=None;poll=None;primary=None;out=bytearray();err=bytearray();offset=0
    try:
        child=subprocess.Popen(['git','-c','protocol.allow=never',*args],cwd=root,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        poll=selectors.DefaultSelector()
        for stream,event in ((child.stdin,selectors.EVENT_WRITE),(child.stdout,selectors.EVENT_READ),(child.stderr,selectors.EVENT_READ)):os.set_blocking(stream.fileno(),False);poll.register(stream,event)
        deadline=time.monotonic()+10
        while poll.get_map():
            require(time.monotonic()<deadline,'Git bounded deadline')
            for key,event in poll.select(.1):
                if key.fileobj is child.stdin:
                    if offset<len(request):offset+=os.write(child.stdin.fileno(),request[offset:offset+16384])
                    else:poll.unregister(child.stdin);child.stdin.close()
                else:
                    data=os.read(key.fileobj.fileno(),65536)
                    if not data:poll.unregister(key.fileobj)
                    else:
                        buf=out if key.fileobj is child.stdout else err;buf.extend(data);require(len(buf)<=(cap if buf is out else 65536),'Git response bound')
        require(child.wait(timeout=1)==0,'Git source lookup failed')
    except BaseException as error:primary=error
    actions=[]
    if child is not None:
        # Popen.kill is harmless after reap; avoid optional poll/closed reads
        # outside the reducer. Stream.close is idempotent for closed stdin.
        actions.extend([lambda:child.kill(),lambda:child.wait(timeout=5)])
        actions.extend(lambda name=name:getattr(child,name).close() for name in ('stdin','stdout','stderr'))
    if poll is not None:actions.append(lambda:poll.close())
    cleanup(actions,primary);return bytes(out)
FULL_MODE="completed-f32-and-held-f64-source-closure-v1"
FULL_HELPERS=('fixture_tools/capsule_builder01.py', 'fixture_tools/generate_inputs01.py', 'proof_tools/build_release_draft01.py')
FULL_FIXED_SOURCES={'.python-version': '56c16a411e41fec3219e828087f312d9891641e3b29093c69d08a05ec1e5d693', 'fixture_tools/controller01.py': '87d64a8ad54d687e4438c0421567f16e90612463182b294fd4610f152f18a743', 'fixture_tools/outer_controller01.py': '93a7b8bc57d3733018045e4d6743cc2fb6c0da0143b7f6be05d3f39ce08b7ca5', 'fixture_tools/raw_receipts01.py': '47e025bb5e6c1a442ab8c03d9d19d95d6f9f5541377f8c7e753584dbfa2077b4', 'fixture_tools/runtime_gate01.py': '8a60c8746d3d54e609f96c09e2560741ed8edfd32426279ee92068e7b13d5cdc', 'proof_tools/proof_outer01.py': '1ba69376298e19843dc6721b5a4ac204aff34fc6156bc60a2318d7f3e02b3aa1', 'proof_tools/proof_raw01.py': '19cee43d920881c08065913373079c96fe261c3f46692c438a022377a211406d', 'proof_tools/proof_release01.py': '53c2294b7b38f340e9160e4484a6b7506942ce36e2dff12694a47f9b72206812', 'proof_tools/proof_supervise01.py': 'e0c8c13c4502faba07e226d4e82329c4c6677d57a8324d44d8094233512f67de', 'proof_tools/runtime_gate01.py': '8a60c8746d3d54e609f96c09e2560741ed8edfd32426279ee92068e7b13d5cdc', 'pyproject.toml': 'fa319e95452e538ac22d78584f87f5f13a24d4b8bb83064b51d015706ef594b9', 'research/onchain-paper-replication-2026-09-24/full_sources/dictionary-artifact-route-2026-10-01/route.py': '1d98c4bec261ced5a5ed7357aabe6c8b27a26b2edbb07380d3fbbd2e870fffad', 'research/onchain-paper-replication-2026-09-24/full_sources/dictionary-publication-2026-10-01/driver.py': '487da65650c7905a8c27fd7adab76084aa572f800959299077e034918a0e55aa', 'research/onchain-paper-replication-2026-09-24/full_sources/dictionary-publication-2026-10-01/publication.py': '95ccbaa8224a48848618c9ff63a428586a441337c4377a1d428d1d01e9d4fdea', 'research/onchain-paper-replication-2026-09-24/full_sources/graph-feature-artifact-route-2026-10-01/route.py': 'e7d34cb08a457b402d28d75dcb1a804579c6b1bf8a9b9bd68d56c695d8004806', 'research/onchain-paper-replication-2026-09-24/full_sources/graph-feature-boundary-2026-10-01/boundary.py': '792deafa7270a686c923dcd2f6b26bf16de14d1a86608bda620c608d1e4c20c5', 'research/onchain-paper-replication-2026-09-24/full_sources/graph-feature-publication-2026-10-01/encoded_hashes.py': '302922b0c403817ccbb6665942ca9d28950a6fe13a8bb41fcc9a744ee77d6f2b', 'research/onchain-paper-replication-2026-09-24/full_sources/graph-feature-publication-2026-10-01/publication.py': 'e0ce2673fcca7d7fdb544ac3ed113b09e3d116fd44750ab1292eaf56028284da', 'research/onchain-paper-replication-2026-09-24/full_sources/graph-feature-route-2026-10-01/route.py': 'e9908a3687823af56c5088f7e377c58f89632eb1d8d1efc7ba3f25430f3eced5', 'research/onchain-paper-replication-2026-09-24/full_sources/mcm-array-kernel-2026-10-01/kernel.py': '4a870113be59f55913ffb91ee79c89438f3a43b53de280fa049467a1781fa047', 'research/onchain-paper-replication-2026-09-24/full_sources/mcm-artifact-route-2026-10-01/route.py': '88482b62d4bdb86ea9fabba2da0b4e36955084c03866766d16300d98da508070', 'research/onchain-paper-replication-2026-09-24/full_sources/mcm-publication-2026-10-01/driver.py': 'd76d2c01777c6f71c6a6295a55b94da82d3bd699f30d44102fc4b5c22c9bac75', 'research/onchain-paper-replication-2026-09-24/full_sources/mcm-publication-2026-10-01/publication.py': 'f76fc7ec93eb0cefb886d32fe301a09c28fb4ae447b268b0077bfc21017f87d6', 'research/onchain-paper-replication-2026-09-24/full_sources/neural-cold-feature-handoff-held-score-reader-preparation01-2026-10-03/exact_members02.py': 'ea1ffcef833344ff1a5fbd89bc2f79ade1414c90a3159329c1f3bdee86bfe0cb', 'research/onchain-paper-replication-2026-09-24/full_sources/neural-cold-feature-handoff-held-score-reader-preparation01-2026-10-03/held_score_reader.py': '3836bbcdc8b5b1be6a08c47a6d97c76c7c0875eeba7e91e6d363bdc6b4ade209', 'research/onchain-paper-replication-2026-09-24/full_sources/neural-cold-feature-handoff-held-score-reader-preparation01-2026-10-03/owned_io.py': '09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb', 'research/onchain-paper-replication-2026-09-24/full_sources/original-import-fixture-bridge-candidate-2026-10-02/imported_kernel.py': '8d810af1448893858504a90537a0a76b6ba70306427d3385f9571b0677a99287', 'research/onchain-paper-replication-2026-09-24/full_sources/pair-component-reader-2026-10-01/reader.py': '3f9ebf731b5027f3282e8d4c7ae8a66c8d25f4aa8a989e2a8cfbd44d3d27cc50', 'research/onchain-paper-replication-2026-09-24/full_sources/pair-consumer-route-2026-10-01/route.py': '0e8e2e34fcd1a98660f7dbe6aa7ebd0ebf94fb8ff6a3e555c0d44f5ad8799da0', 'research/onchain-paper-replication-2026-09-24/full_sources/pair-extent-2026-09-30/extent.py': 'c62c743c67490e37b9aca2e6722d143e02df009c5398bb2fd246e9051f1ac3ac', 'research/onchain-paper-replication-2026-09-24/full_sources/pair-owner-route-2026-09-30/journal.py': 'e51d087c49651e12867dc6297d366d5839cc675923839be75193c37e2bb03421', 'research/onchain-paper-replication-2026-09-24/full_sources/pair-owner-route-2026-09-30/ownership.py': '43198ef10c3cc5f9b457edc5d37a9c1bcf1e34deb603d973ced2cd788d3508bb', 'research/onchain-paper-replication-2026-09-24/full_sources/pair-serial-composition-2026-09-30/serial.py': 'c23d2d709385de7a9d241ea48d993655785c7304c9e542e8e565765a698970ee', 'research/onchain-paper-replication-2026-09-24/full_sources/pair-workload-2026-09-30/workload.py': '30a957ad48997a3236203e1af2ccf9e0874b172ffac73773c31efc6bece9fc67', 'research/onchain-paper-replication-2026-09-24/full_sources/pair-workload-route-2026-09-30/route.py': 'a71d890fae6681c29bd2a4b49241068fbf1936001bc4392880025ca1fd2f668c', 'research/onchain-paper-replication-2026-09-24/full_sources/representation-closure-route-2026-10-01/closure.py': 'c56bcb63f8ca3b412b50b24e14638c20ea2a133da744ad973bc20981f282e301', 'research/onchain-paper-replication-2026-09-24/full_sources/representation-denominator-2026-10-01/denominator.py': 'e3ffddacc03011fb6e1b5f446c6820ac491a6e7b84c8ffef01b7f507530c1bd8', 'research/onchain-paper-replication-2026-09-24/full_sources/representation-denominator-route-2026-10-01/route.py': '3671b1c9efc042e55fdd2b2807f955d01317bc9cd5844b77b7a4e19b699eba56', 'research/onchain-paper-replication-2026-09-24/full_sources/representation-seal-2026-10-01/publication.py': 'd621f59f18e368badce7a60779c7c801502af231fe5c483171c80a28ed78392c', 'research/onchain-paper-replication-2026-09-24/full_sources/representation-seal-2026-10-01/records.py': '85dcf606ca0fc97ea4cfa3974cebccbe3f1f3fd1aae0b3af1134900e58ead6ee', 'research/onchain-paper-replication-2026-09-24/full_sources/sample-artifact-route-2026-10-01/route.py': 'e049307f0acd01e4646cba2d7b7e79d4f634db058faafe87e0591c986ffea7d3', 'research/onchain-paper-replication-2026-09-24/full_sources/sampler-leased-core-2026-10-01/core.py': '07428fc777ec7224f199d245aee10658b8f4e74520732f6c85dcc7d8d2a37bc6', 'research/onchain-paper-replication-2026-09-24/full_sources/sampler-proof-route-2026-10-01/producer.py': 'f5703eea849b94707c750695f1bdd97512ed428e39033b013420043568762305', 'research/onchain-paper-replication-2026-09-24/full_sources/sampler-proof-route-2026-10-01/route.py': 'e7d7db3a20bf37da88047a12ea1e90a66c848f066b5078caaac41478a414d1be', 'research/onchain-paper-replication-2026-09-24/full_sources/terminal-output-lifetime-2026-10-01/native_map.py': '0462c2eb5cb8991b35e631b1ea45669afd70f9df97656cd4d8ec1e2abfcb7ef7', 'research/onchain-paper-replication-2026-09-24/full_sources/terminal-output-lifetime-2026-10-01/outputs.py': 'a0d44a625cebf30060764c2515f23dae150671c2ade221a11c17ec91d533d727', 'research/onchain-paper-replication-2026-09-24/full_sources/terminal-output-lifetime-2026-10-01/seal.py': 'a85fe1fa35859acbf948162e60e45cb33e6e76aaedb7532340eacd902c52d1ec', 'tradingagents/__init__.py': 'f3f6f89f20f49a016e061266fa802b73fa95720d060a2642573d4227646ad4e5', 'tradingagents/research/__init__.py': 'b34ced6fb4b6dd9dc1ae15645c40d62687ae7fa85f104ff77a6f1f49f874d2af', 'tradingagents/research/__main__.py': 'd5d7664ed30f9905a4911c70d69a756e5260e534365d68968808d4f5079cd70e', 'tradingagents/research/admission.py': '585d66f526d88f8488c6efcc4989a09328006e393566a596fe9e95c6c7f60cfd', 'tradingagents/research/budget_extensions.py': '59d22880e9ff7909508db6b0c15a7a833df30be365af4e31d643ed64afabb25a', 'tradingagents/research/examples.py': '0c4e4e901d14455b6742627a3c0bd42ffe65f5cf8eea7b64afbd0010dcbcbdc1', 'tradingagents/research/lifecycle.py': '88589c2dab53954711a66a22f2bf7e134a6e7d21072c5b7b508d11f04c6490dc', 'tradingagents/research/onchain_replication/__init__.py': '905f63046b02552c4d7cd90014328a48d77bcdb336b4a1f3351b453b83878fd1', 'tradingagents/research/onchain_replication/aggregation.py': '768c2ca743b2146fcc6bf606e4fa0bf41273ac15d06344d3a25a6aac78e8038f', 'tradingagents/research/onchain_replication/archive_chunks.py': 'f26f1cb62334497494f9b02579f53be9e2238889a81f56c04fd4e781542b38fe', 'tradingagents/research/onchain_replication/archive_consume.py': '9cfa242b77e42c2385e3c4cb8e51086965cc7d42768f2c52364fa3fd4ec77dc5', 'tradingagents/research/onchain_replication/archive_dispatch.py': 'eb4dcdafe5deb5c6acba1fdf20610efc9b4ca990c3e3c81f404d8ff8ba4a56b0', 'tradingagents/research/onchain_replication/archive_non_tail.py': 'c62e1521969b7665baca6d29b3125be9214d4eb8c4f42f980622d9d670e56fac', 'tradingagents/research/onchain_replication/archive_owner_operations.py': '5882578d065e94af588511356071b8f575aa1e8a1bbd7a9ab116e5853eb4c83f', 'tradingagents/research/onchain_replication/archive_owner_policy.py': '81b0e2fa4220c45461ffad850209e92819b65a56a7037887d1d7ba92c97956c9', 'tradingagents/research/onchain_replication/archive_owner_seal.py': '7c8c01ce43756605e4765f8e04e1cbbf1665d651d076b36eab74340acb0b07fa', 'tradingagents/research/onchain_replication/archive_owner_stage.py': '21a1f134c4ed0d4f57c266f21d4dd130d61241117b11e7f66a6466db3ddec39c', 'tradingagents/research/onchain_replication/archive_owner_writer.py': '7980139206c4b2a0e8b11763f44d23a73c4e9f067d9c10799a081664c42135d1', 'tradingagents/research/onchain_replication/archive_pair_reader.py': '11aedf0b9e5e8698831854952033f36db185c0cb4948f226912731ffc68d16df', 'tradingagents/research/onchain_replication/archive_pair_writer.py': 'c714c350f372be1b4e3c7840b5187deb7f72ee80549edfed4e48450e2d0ca052', 'tradingagents/research/onchain_replication/archive_transport.py': 'ef0fdc052a354af5b83e487cbc2d2cf92170149d64f90117adcb5ee37e3b572d', 'tradingagents/research/onchain_replication/archived_pair_log.py': 'e01d267c54be8bc786478d5647c90505f75f66dd96e1d57349ba3f76e6259b3f', 'tradingagents/research/onchain_replication/archived_stage.py': '1e4b09210a0a9384b778a71e1573298cb923711bcf7c7dcd3b464460001dc407', 'tradingagents/research/onchain_replication/array_neighborhoods.py': '4130af3869fb6615ba0898c5b25f1297f236e2df6b4dbe37d705dc2459982d6d', 'tradingagents/research/onchain_replication/baselines.py': '8ad95719b412aa633607f966e72e3246cceeceffb68e6ced90b4289637b3954a', 'tradingagents/research/onchain_replication/btc.py': '775838b3fc00534849d747f38c942f13187762b81c35ef5b1af52d67882a2dd0', 'tradingagents/research/onchain_replication/btc_source.py': 'deb5f4003ab63a69f945756f1e40fdd6212733331b2ef0133bab2ba0f69acead', 'tradingagents/research/onchain_replication/btc_store.py': '79f78d1bfc46d3e975f506407f3fcea102835235b5aa5b68cf6b1d7674c10452', 'tradingagents/research/onchain_replication/btc_subsets.py': '79f1cc4de5b5bf52e491201d05941bbe0ff29555d814f343294411f4591ed736', 'tradingagents/research/onchain_replication/btc_weekly.py': '6d52650e2bc6225c73da9841e51ab03be33ba8f3dd32a5ae504d6b76908c4aed', 'tradingagents/research/onchain_replication/cache.py': '5fbbe0df14cfc1802dd1df4da6c8bdbd1153a9fcbb4c89dd202e791d1811ddba', 'tradingagents/research/onchain_replication/calendar.py': 'c96e984a7d3482500a3a98231d859da1678cae4ca63960f33515a06dbda760f2', 'tradingagents/research/onchain_replication/cells.py': '1a15e33377030b6f3c533fd498bf75825778a59c35f2b0b8702cfaf79bb9bcfd', 'tradingagents/research/onchain_replication/census_production.py': '37ec0a081edaf2928146fab3984e362f1241809af43009eb05de307f247665b1', 'tradingagents/research/onchain_replication/checkpoints.py': '74e7bd16d4331cbac45143884e1f35a52687b19280c214457834b0cf19a457bc', 'tradingagents/research/onchain_replication/coinmetrics_prices.py': '5e14eae6fafccdfe562ab07c73ac3854f5e86751d74e468807b82be0a3a0a62f', 'tradingagents/research/onchain_replication/cold_files.py': '3740b149a69ed10448ae0d4f177f8d93c3300765b9e20846d4cbda5aec75ca85', 'tradingagents/research/onchain_replication/compact_closure.py': '87a145ec3ad7b44ce5a4e40ba2f610d8d8f4d715b1e70b767cece835abf9390e', 'tradingagents/research/onchain_replication/compact_cold_features.py': '9231e784a2085cbe4130568d748cbacb63d61e41fc955f3f0685831853ebd2c0', 'tradingagents/research/onchain_replication/compact_cold_proof.py': 'd3e401618b214647d27387d18182153ab493e69177394823e483546b44a6a153', 'tradingagents/research/onchain_replication/compact_cold_proof_inputs.py': 'cae64e3531207a9c3d62031a6e0969af72a0b0f8eb93814e643bfbe16ad8c42a', 'tradingagents/research/onchain_replication/compact_cold_proof_native.py': 'efbda343637395a88d6349aacbb77421430d59bbad745a375aad989b107e0aba', 'tradingagents/research/onchain_replication/compact_denominator.py': '6579c4aa57804ecfd35010beb81df0e81f722285bea9fda856d1a7f8e466b372', 'tradingagents/research/onchain_replication/compact_dictionary.py': '1c2618cc3706f4bdbfaba0ec957e1fb908f63857403bbdcc9341181effe313dc', 'tradingagents/research/onchain_replication/compact_features.py': '584268806ac6b6ea713737e4f54a6ba0bd923397165c089f2f359dfb3d916752', 'tradingagents/research/onchain_replication/compact_graph_artifacts.py': 'fd1395b0c274b1b51dc26365fd0c2954f904492cf77ddb3d553ce40c6dc6bf8a', 'tradingagents/research/onchain_replication/compact_matcher.py': '6a7e6e0c1918db7a42edc8fe8737f2b77497c0e32583c184e338e286fa47ad70', 'tradingagents/research/onchain_replication/compact_mcm.py': '35aba737220f1b5772b31138ea2c4cd920e842ae888425bfecbfd0ee151c5181', 'tradingagents/research/onchain_replication/compact_mcm_output.py': '4e31d1f241fc7c1f1ef4b7fc163d27a332ff057378a254e56667d2e7f6d29b11', 'tradingagents/research/onchain_replication/compact_mcm_publication.py': 'f32449d58b9bd3ecc71a6078cd0213fcb27217964de77964d74a41653b05d80a', 'tradingagents/research/onchain_replication/compact_native_features.py': '34a6f63125ac048df2d0f4a2b354ff2c6808ee8fc0dcc4b6a04bff1eeeb6e136', 'tradingagents/research/onchain_replication/compact_native_producer.py': '36cb548d012ee9a143fd65118d7540193406fd16002711b9f9e2899a9131d336', 'tradingagents/research/onchain_replication/compact_owner.py': 'c1f4f1b70ab5e955d5302cda5a1fd2dfc1c02a9df15589acabc7a36c80873171', 'tradingagents/research/onchain_replication/compact_pair_log.py': 'e7b38cbc4a0b13733e0018db897489acab5f7324368c7938addb20f8a9d2392d', 'tradingagents/research/onchain_replication/compact_policy.py': '4f4e4f91df881249540e8f7b0e33029f21e680bf7595fb0bbe075a8d8aee9d7d', 'tradingagents/research/onchain_replication/compact_publication.py': 'b2b999c40c38b286a6e24f319089998099306979da1e7d75b86d692b537216d8', 'tradingagents/research/onchain_replication/compact_sample_proof.py': 'cb94729af806f10b1c719cc240ec8c2546a1aa2a79591ef62cbf852c29256893', 'tradingagents/research/onchain_replication/compact_sampler.py': '7820254d9a9ac287e55b0d20d2c26e1907b625dd743e194fae0602110593a608', 'tradingagents/research/onchain_replication/compact_samples.py': 'f14a11212edd281901aab69fbe9b1164251988472baa65da6b319d50ff436d7b', 'tradingagents/research/onchain_replication/compact_stage.py': '3e35d200bcd04efa169ec64745ae54bb81ef1a58f3ae160157f00f40f60aad3e', 'tradingagents/research/onchain_replication/compact_terminal.py': 'b06ccedcfc6e3bb8356dec48fc2ea49092da2c1e18f23e32aeb8f58ca0e3c0b5', 'tradingagents/research/onchain_replication/compact_training.py': 'ef70263e79cf743aff6a389866a7fd86615b5bcdbd5b834ebe922ffd420bebd3', 'tradingagents/research/onchain_replication/comparison.py': 'b157f41b2b98517c67152209bac46fbedf3a2eb9471fd27f9c588a41e60c8c23', 'tradingagents/research/onchain_replication/completed_f32.py': 'ba739fb8711287f365abca061544a712bfdb0fd65a52836188da1c959ac9f266', 'tradingagents/research/onchain_replication/component_store.py': 'ba0cf44dd7cf5af8c0b99cbe129f107ef7b40833a76b8162ae9d91512b566b68', 'tradingagents/research/onchain_replication/contracts.py': '3f88e9e56f2bfca059e2ef9da2b01ae593444b05e1067154653ea6a5479fea1a', 'tradingagents/research/onchain_replication/dataset.py': 'c8d701b5646395bb94e5037aefcc2d0d29a55de95cca05e019ce35d3f53561df', 'tradingagents/research/onchain_replication/dictionary.py': '32e27a4a17dc2aa993d1440d6486c75b0d4dcff341969dbf99bdff412dd7e446', 'tradingagents/research/onchain_replication/environment.py': '8b3d09acbce94502f58f5d595c0018e45e9854b8f04241705c50fb21051b8a28', 'tradingagents/research/onchain_replication/eth_source.py': '78e0731e16d2751534e3530dde7313e94950bd852f99b30cec4661dbf7db1487', 'tradingagents/research/onchain_replication/evaluation.py': 'b3af7cf6b71f8adcdd762eb471abb66d8fdd00f20087aeff377447d51a854b29', 'tradingagents/research/onchain_replication/feature_journal.py': '00f157d8a2e0d1e1b8d657a7030ab1fe8e43bf4b113a1ca29288a5635d524665', 'tradingagents/research/onchain_replication/feature_pipeline.py': '19ebe96275095ded92743a1a1bcadc4178f85cd5d39f1ed23786fba279b5fa41', 'tradingagents/research/onchain_replication/feature_residency.py': '4ea5370958b65edf0d37950f12d358ab562291c786f28a287514c77c3838ddcd', 'tradingagents/research/onchain_replication/gat.py': 'c2292bb164869bb4202a2af028a453f547d8e2930cd9d58ee4a59ffcb72913d6', 'tradingagents/research/onchain_replication/graph_baselines.py': 'f284a85a0ce3aa5dee24c748c6a376d9d44a2d775409b874540215ff0e594907', 'tradingagents/research/onchain_replication/graph_production.py': 'ef5ee5e2c8f6438e4e334d1a468397ad6f60e176d157e7849b7132737c7c85e8', 'tradingagents/research/onchain_replication/graph_residency.py': '1ded72ad7c25135780a718455b430eafa020e8f3de6ca608b04e005b798609a6', 'tradingagents/research/onchain_replication/graph_store.py': 'dcea4265fab07e26fba1c94f56c3fb74b12d872a7378065ed6d4ae431e9e54bd', 'tradingagents/research/onchain_replication/held_score_consumer.py': '8c66189bd61a715c5f06b33b5fa9195a7185237c571529135d46f8ee1d7710ae', 'tradingagents/research/onchain_replication/hub_census_production.py': 'b9c406f19c32f2b78409b9a3260edebcad0ced042e9e4d187ff44e574d763d2a', 'tradingagents/research/onchain_replication/hub_edges.py': 'e5858170437f6d9f0a994315e2b2aa30d502844cf0a1c1b8ec782a1e693887e9', 'tradingagents/research/onchain_replication/import_metadata.py': '1c9455bc80b8f424bf63d6fdd5b94338ce54c14ead720990a2f787aef9e93dfe', 'tradingagents/research/onchain_replication/imported_mcm_identity.py': '8b062eaf6a9a4d7315591c3b1d96f3fd8de52fae873f4cf31769cf3224fcf5a1', 'tradingagents/research/onchain_replication/job.py': '6ee38bb578d1e6cdd38aa276ec31313aeb6636ad191194a55458559604dc502b', 'tradingagents/research/onchain_replication/job_payload.py': 'c57db123a7c1a951a37656d5a19173e47fb71dcee62f87b69cbc58b8ec0069ea', 'tradingagents/research/onchain_replication/journal_recovery.py': '1f5a280789572a01d943e80081930e324e621127b742ef67b6d93b6041ed009d', 'tradingagents/research/onchain_replication/mapped_graph.py': 'c5e93b325599a82bf65e5b31074e9c76a73b25d479ddea7d3ff3687e75f7b197', 'tradingagents/research/onchain_replication/matching.py': 'e5a4cb7966a53522532158a13ef7293d4d081a26cffba56c2eb0761a628c72a6', 'tradingagents/research/onchain_replication/matching_ancestry.py': '51221522256e3f1babb03512a8dad4d293d12638c4579d4bddcf92945db5e4bc', 'tradingagents/research/onchain_replication/matching_annealing.py': '602636b8311431bd2f7d4d28ed59627e9ac576341b0dbcc6f0d41225dc79b7d1', 'tradingagents/research/onchain_replication/matching_checkpoint.py': '6ef36f12a8e601177c0dde507f99d80853df80ad46cfd7f0321e5c0d655ab9df', 'tradingagents/research/onchain_replication/matching_death.py': 'f76a96274e77d4f728d9d7e0b93db2a8bb4e663654ae59c0480f6c66192c3ff8', 'tradingagents/research/onchain_replication/matching_hardening.py': '3ed02e0df1508a7f963d3652cfea252b759c701235589ea5855cdd560e520f80', 'tradingagents/research/onchain_replication/matching_identity.py': 'f011658abf3b56b04a0ec33a7bdfed2c68e2e2e79791aa96c5ca7f8fd1653f89', 'tradingagents/research/onchain_replication/matching_owner.py': '22afd3f3a0c52221d43a2fa87d285db4874e08a21adf7c5ac336270e0ece0751', 'tradingagents/research/onchain_replication/matching_pair.py': '3fc8a0666b2b4bf334411a85decd7dbf484b038827255714c6727ffe3846621c', 'tradingagents/research/onchain_replication/matching_policy.py': '5d552673fb772f61344d212606a5d9d2c22c91c8de44dfa501d57422c9b4e739', 'tradingagents/research/onchain_replication/matching_reference.py': '75e3269a94cf0d840c299f52c7b138b58dd138251bde6048e52e6c1149934332', 'tradingagents/research/onchain_replication/matching_sparse.py': '06f2d312a1527f335decc8e0c4d1283448a28e783d5e64018d70e9bf3416883e', 'tradingagents/research/onchain_replication/mcm.py': 'd2527cdc34f1032f6ed9a3ff175fd1e7c21412e19e1d449ac53f773bd582f9df', 'tradingagents/research/onchain_replication/mcm_score_stream.py': 'ee7931cea3d28ad0719b5f3db171a5d5d3ab95db9ff7cad0cc8379101948b79e', 'tradingagents/research/onchain_replication/metrics.py': '9476c2052e02be278c01360fa598a3a136a791ffaa90d90f1fde992c8a27c84b', 'tradingagents/research/onchain_replication/model.py': '2f55b04d3a707e212b2a1d9e0fb591eb3ec2b4828614edcc1a5a5d8f313d3b8e', 'tradingagents/research/onchain_replication/model_registry.py': 'c0e2202578ae708e2fc0406ece5726541952bf40f29df9dc81812c177c334543', 'tradingagents/research/onchain_replication/native_producer.py': '5b7dff71ffe2b1e6c0570b859020d82af337d753665ae77cbea95ff07d1914ed', 'tradingagents/research/onchain_replication/native_reuse.py': 'a84274b035278fb5d840f58420cdc4d70eb7c5d8ca2ee5247392cf6bb29b2bbb', 'tradingagents/research/onchain_replication/neighborhood_census.py': 'be4704d1b19028c2ce734c35483986d6b49d7eecd6f6bd9048c96208b51c02a9', 'tradingagents/research/onchain_replication/neighborhood_policy.py': 'f86e19de0bedd4c12ef73fe2ba243990256f592c604c083d8e772ce8131bc12a', 'tradingagents/research/onchain_replication/neighborhoods.py': 'b53901125dc20dbb8a38b6e0e539866fb04109053afbcba0d75b2a2a8dc38271', 'tradingagents/research/onchain_replication/neural_authority.py': 'eed5f79f4c34819fb64ac2d79069ff56e4b24d175f2d391da9856f9d50186fb2', 'tradingagents/research/onchain_replication/neural_phases.py': '11af32f66fa1d9289c713da0304a5c7e0d6dd7a0623f783597bd0f9368988d71', 'tradingagents/research/onchain_replication/neural_physical.py': '8891e3ed52142f23ae987b8985cd4ee8e09caf86658623e43a37df7140dfe190', 'tradingagents/research/onchain_replication/neural_resource.py': 'ae7cd7ff76b0ddfd5e55645ea7a36a56d12089388add620a99fc70b1bc6759b9', 'tradingagents/research/onchain_replication/original_dictionary.py': 'cbe571a3758695b2ff63a45031c90840a7358538f9a2c0bad31077db8439a6d9', 'tradingagents/research/onchain_replication/original_import_preparation.py': 'cfae656ca4684271e5f9bc36f4ec4f09ff0da77436a5133b5f2a743c80ffe9e5', 'tradingagents/research/onchain_replication/original_import_stage.py': '7e1596c76e2af76eede19f5d9a6fd368c4f87eaf92156b4ac7be9def069d717a', 'tradingagents/research/onchain_replication/owned_io.py': '09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb', 'tradingagents/research/onchain_replication/parquet_ranges.py': '482c0686e552aae3157bf6cf12f802e0d284c68ce14d879000253b895450b044', 'tradingagents/research/onchain_replication/pooling.py': '054845bed22c44294ce41f2263155df0397c42b0b306755e36791ae5a3960303', 'tradingagents/research/onchain_replication/population_assembly.py': 'da65f5168c9d03cf8518f8dac1717482ff48c047ac451563f8728a7afe5c528f', 'tradingagents/research/onchain_replication/preservation.py': '2849670dcf847a97274cf590a2c6732cd7749e0e9e3e64e802cb2e415f08a410', 'tradingagents/research/onchain_replication/price_source.py': '66af531218352999667f2cac88c8393e70ddcf956b8e9f05db16a52c6b2f6e74', 'tradingagents/research/onchain_replication/prices.py': '5f44f1e689b614121c4b9cab5da75e17322074a9ec9f2a30a174ac353093798f', 'tradingagents/research/onchain_replication/provenance.py': 'd29f7f5c2fc5d0def6538d3a1eb13dc051c672d8ea38257af333930f87b9ff1b', 'tradingagents/research/onchain_replication/range_source.py': '5f1e004a89e2339d1f21c941415dc3976e9523f509a1d1591f23a8ea7a836bd7', 'tradingagents/research/onchain_replication/registered_features.py': '8a79c459336773bd139f377fe44fe1006796378651d30a8eb22c966c72f7b267', 'tradingagents/research/onchain_replication/replay.py': '37cb3925ac1e4a453ed385fd560b463e88f1ddb91cf00af338c08230ed244691', 'tradingagents/research/onchain_replication/resource_binding.py': '06db541c97a122b911c91106daef524cd1e69a33c8a44b4d3abde77f7eb4fb5d', 'tradingagents/research/onchain_replication/resource_fixture.py': '4bcef0f71fc228e7ae7379aac2ea3a49ef24dc379f86a67719682e4192db9587', 'tradingagents/research/onchain_replication/resources.py': 'e1d305e41938815d60ae2f465fcb2b543768c6862d176f4f6075ced53c8069c7', 'tradingagents/research/onchain_replication/restart_retention.py': '15e7b2090ce87081b0cd6e2338b4d62d348d779082947729cacf0210d3c6dc7d', 'tradingagents/research/onchain_replication/run.py': 'd44fa28991f05bedf228de22975399847dd97404b1f3dba8390be7bd720f73de', 'tradingagents/research/onchain_replication/sampling_policy.py': '79d1253009e6ba5e8815f82fdf3422113d5559b92e5e0e36bfec84fc2963354d', 'tradingagents/research/onchain_replication/sampling_weights.py': '5f1837f93fe0523d7c851654390584fc6c04fb803f2025fd027e74a5da8318d1', 'tradingagents/research/onchain_replication/score_batches.py': '4018ad121fcf7b6abf0ec93afe7b78857a1254611a02791965974437558c7a45', 'tradingagents/research/onchain_replication/score_tail.py': 'd18681b36e16bbca604346469d1cb79e14d2ebb1649108334c62356d9f6eb91e', 'tradingagents/research/onchain_replication/selected_non_tail_transport.py': 'e3cea797bb51eab1d423399686dfb331b2e4697242f42c7cec1f3f4f026eb7c8', 'tradingagents/research/onchain_replication/serialization.py': 'f711a0a931fe9fb91aadf0ad7ba6e68b638f3874e736790e05edd21acdefc65b', 'tradingagents/research/onchain_replication/source_footers.py': '65005ceca3072760befb09680f9c7aa469d5aaa5ab3f2af6a741d4ed2fef660e', 'tradingagents/research/onchain_replication/source_inventory.py': '6d868efe77d4d84af97fdb1657585ad86fda15866b44541f111656d3e09759db', 'tradingagents/research/onchain_replication/stage_retention.py': '2f608ba1735fd07fdf18eab8969854f61e9769603b84b16869a008cde108b478', 'tradingagents/research/onchain_replication/stage_retention_reader.py': 'c2ae559de8721bea87a3520d9d13591f6c47ee6cad9971c7166c2c63937736f5', 'tradingagents/research/onchain_replication/streamed_gat.py': 'e8355dc4443dc40b64fe2fd0d22f764d47280c655f921e9f1705042e348ec21f', 'tradingagents/research/onchain_replication/subsets.py': '59a17cb12711d8ec518f6f25ec4518f143647b79c3ef3286399dada114b7a22c', 'tradingagents/research/onchain_replication/temporal.py': 'd8adafb5a50716ce472848df05e8bbb804525ed8003958c7f9a25c82d81ad226', 'tradingagents/research/onchain_replication/training.py': '5c0380de62c670d356ea3546c7b81eed4ccab55a886bc27b6a1bbfd75c2c3369', 'tradingagents/research/onchain_replication/verification.py': 'c492cc9be2eb0956035800c26bde5d6cc2999844cd7466eb151bd3ea82815873', 'tradingagents/research/onchain_replication/weekly.py': '079a427f212738759109b31da23933549a8b7751851e3033703cdd03dc5f054a', 'tradingagents/research/onchain_replication/workflow_storage.py': 'bf52b9408008ac3616f867ebef8130e2f315f8c8febf00ab1815557d68684554', 'tradingagents/research/verify.py': '1f14343c7918e3464991b9b57ecdf74425130de5c049a4e401d896116881efce', 'uv.lock': 'f7a1829c0ae554fb00923eb07c3c5e5370c1eadb52698ea657446c64d6c83b9a'}

def full_mode(mode):
    require(type(mode) is dict and set(mode)=={'schema_version','kind','helper_source_files'} and type(mode['schema_version']) is int and mode['schema_version']==1 and mode['kind']==FULL_MODE,'explicit supported full source mode required')
    pins=mode['helper_source_files']
    require(type(pins) is dict and set(pins)==set(FULL_HELPERS) and all(type(h) is str and len(h)==64 and all(c in '0123456789abcdef' for c in h) for h in pins.values()),'exact three externally frozen helper pins required')
    return dict(sorted({**FULL_FIXED_SOURCES,**pins}.items()))

def full_package(name):
    return name=='tradingagents/__init__.py' or (name.endswith('.py') and str(Path(name).parent) in ('tradingagents/research','tradingagents/research/onchain_replication'))

def full_rows(rows,mode):
    expected=full_mode(mode)
    require(type(rows) is list and len(rows)==202 and all(type(r) is dict and set(r)=={'path','sha256','bytes'} for r in rows),'exact full202 source rows required')
    names=[r['path'] for r in rows]
    require(names==sorted(set(names)) and set(names)==set(expected),'complete full202 selected paths required')
    require(all(type(r['bytes']) is int and 0<r['bytes']<=MAX and type(r['sha256']) is str and r['sha256']==expected[r['path']] for r in rows),'unknown full source replacement/extent')
    require(sum(r['bytes'] for r in rows)<=32*1024**2,'full source aggregate bound')
    package={n:h for n,h in expected.items() if full_package(n)}
    require(len(package)==151,'exact full151 package closure required')
    return expected,package

def full_git_bodies(reader,commit,rows):
    require(type(commit) is str and len(commit)==40 and all(c in '0123456789abcdef' for c in commit),'real complete source commit required')
    for offset in range(0,len(rows),128):
        group=rows[offset:offset+128];request=''.join(commit+':'+r['path']+'\n' for r in group).encode()
        response=git(reader.root,['cat-file','--batch'],request);position=0
        for row in group:
            end=response.index(b'\n',position);header=response[position:end].split()
            require(len(header)==3 and header[1]==b'blob' and header[2].isdigit(),'missing/nonblob genuine source object')
            size=int(header[2]);require(size==row['bytes'] and size<=MAX,'actual Git source extent differs')
            start=end+1;body=response[start:start+size]
            require(len(body)==size and sha(body)==row['sha256'] and body==reader.body(row['path']) and response[start+size:start+size+1]==b'\n','genuine Git/current source body differs')
            position=start+size+1
        require(position==len(response),'extra Git response body')

def full_source_plan(root,source,anchor,rows,mode,*,design_source):
    expected,package=full_rows(rows,mode);reader=Reader(root)
    require(Path(__file__).resolve()==reader.root/'fixture_tools/capsule_builder01.py','actual selected builder source origin required')
    for commit in (source,anchor,design_source):require(type(commit) is str and len(commit)==40 and all(c in '0123456789abcdef' for c in commit),'genuine current/design/151 anchor required')
    require(source!=anchor,'fresh genuine151 anchor must precede current metadata commit')
    require((reader.root/'.git').is_dir() and not (reader.root/'.git').is_symlink(),'owned local Git required')
    for path in ('objects/info/alternates','info/grafts','refs/replace'):require(not os.path.lexists(reader.root/'.git'/path),'Git indirection refused')
    require(git(reader.root,['rev-parse','HEAD'],cap=128).decode().strip()==source,'actual current source HEAD differs')
    for parent in (anchor,design_source):git(reader.root,['merge-base','--is-ancestor',parent,source],cap=128)
    # The new anchor must descend from the preserved genuine Source07 lineage.
    git(reader.root,['merge-base','--is-ancestor','d443208795f59292c156c5b81b687594efacea4d',anchor],cap=128)
    for commit in dict.fromkeys((source,design_source,anchor)):
        roster=git(reader.root,['ls-tree','-r','--name-only',commit],cap=65536).decode().splitlines()
        require(sorted(n for n in roster if full_package(n))==sorted(package),'current/design/anchor151 package roster differs')
    for row in rows:
        raw=reader.body(row['path']);require(len(raw)==row['bytes'] and sha(raw)==row['sha256'],'current full source differs')
    full_git_bodies(reader,source,rows);full_git_bodies(reader,design_source,rows)
    full_git_bodies(reader,anchor,[r for r in rows if r['path'] in package]);reader.recheck()
    return {'schema_version':1,'kind':'full202-resource-source-metadata-v1','status':'source-only-unregistered','closure_mode':mode,'root':str(reader.root),'source':source,'design_source':design_source,'anchor':anchor,'source_count':202,'package_count':151,'source_files':expected,'package_files':package,'source_origins':[dict(r,git_commit=source,git_path=r['path']) for r in rows],'logical_bytes':sum(r['bytes'] for r in rows),'execution_admitted':False,'route_blocker':'selected f64 worker currently requires201/206; raw caller and full202 registration/native release not integrated'}

_legacy_held_source_plan=held_source_plan

def held_source_plan(root,source,anchor,rows,*,closure_mode=None,design_source=None):
    if closure_mode is None:return _legacy_held_source_plan(root,source,anchor,rows)
    return full_source_plan(root,source,anchor,rows,closure_mode,design_source=design_source)
