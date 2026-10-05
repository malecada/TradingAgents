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
HELD_CANONICAL_ANCHOR='55e7d50431654aba952b4541ca506524d9feece1'
HELD_CANONICAL_PARENT='d443208795f59292c156c5b81b687594efacea4d'
HELD_CANONICAL_DICTIONARY='e05aa225b6bcf8f4e14a644d0a03f2a9aff6cb36ae4a5b02a3dded72d94580b9'
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
    canonical=anchor==HELD_CANONICAL_ANCHOR
    if canonical:
        require(parents==[HELD_CANONICAL_PARENT],'canonical anchor sole parent differs')
        _held_git(root,'merge-base','--is-ancestor',HELD_SOURCE04,HELD_CANONICAL_PARENT)
    source04=anchor==HELD_SOURCE04_ANCHOR or canonical
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
    if canonical:expected['tradingagents/research/onchain_replication/original_dictionary.py']=HELD_CANONICAL_DICTIONARY
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
