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
