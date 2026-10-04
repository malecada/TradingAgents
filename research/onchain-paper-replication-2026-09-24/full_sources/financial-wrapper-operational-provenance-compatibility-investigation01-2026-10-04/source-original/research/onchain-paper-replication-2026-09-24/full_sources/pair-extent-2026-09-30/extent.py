"""Policy-bound saved pair extent checks; no numerical body reads or admission.

Call reservation_bytes before allocation. A sole admitted writer/guard must hold
ownership across reservation, save, verification and publication. Array contents
are verified by the numerical loader separately; this helper checks their extents.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat

from tradingagents.research.onchain_replication.matching_pair import POLICY_FIELDS, ENGINE_FIELDS, BACKEND

LIMIT=65536


def require(value, message):
    if not value:raise ValueError(message)


def hash_value(value):
    require(isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value), 'hash identity')


def same(left,right):
    return json.dumps(left,sort_keys=True,separators=(',',':'),allow_nan=False)==json.dumps(right,sort_keys=True,separators=(',',':'),allow_nan=False)


def reservation_bytes(policy):
    """Whole pair publication upper envelope, excluding separately charged owner."""
    require(isinstance(policy,dict) and set(policy)==POLICY_FIELDS,'pair policy schema')
    require(all(type(v) is int and v>0 for v in policy.values()),'positive integer policy')
    require(policy['chunk_edges']<=65536 and policy['hardening_chunk_entries']<=65536,'bounded chunk policy')
    envelope=policy['max_checkpoint_bytes']+LIMIT
    require(policy['total_checkpoint_bytes']>=LIMIT+envelope,'session reservation insufficient')
    return envelope


def stamp(info):
    return (info.st_dev,info.st_ino,info.st_mode,info.st_nlink,info.st_size,info.st_mtime_ns,info.st_ctime_ns,info.st_blocks)


def regular(path, device):
    try:value=path.lstat()
    except OSError as error:raise ValueError('missing or inaccessible extent') from error
    require(stat.S_ISREG(value.st_mode),'regular nonsymlink file required')
    require(value.st_nlink==1,'multiply-linked file forbidden')
    require(value.st_dev==device,'cross-device artifact forbidden')
    return value


def inventory(base, device):
    """Fixed schema-sized walk; reject extra files before any large inventory."""
    pending=[base];files={};directories={};entries=0
    while pending:
        current=pending.pop();info=current.lstat()
        require(stat.S_ISDIR(info.st_mode) and info.st_dev==device,'regular same-device directory required')
        directories[str(current.relative_to(base))]=stamp(info)
        with os.scandir(current) as children:
            for item in children:
                entries+=1
                require(entries<=11,'artifact inventory exceeds fixed schema')
                path=Path(item.path);value=item.stat(follow_symlinks=False)
                require(value.st_dev==device,'cross-device artifact forbidden')
                if stat.S_ISDIR(value.st_mode):
                    require(len(path.relative_to(base).parts)<=2,'artifact inventory directory depth')
                    pending.append(path)
                else:
                    info=regular(path,device);files[str(path.relative_to(base))]=stamp(info)
    return files,directories


def verify(reference,*,root,owner,identity,policy,parent,declared_artifact_bytes):
    reserved=reservation_bytes(policy)
    require(type(declared_artifact_bytes) is int and declared_artifact_bytes==reserved,'exact policy-derived reservation required')
    hash_value(owner)
    require(isinstance(identity,dict) and same(identity.get('backend'),BACKEND),'backend identity differs')
    root=Path(root).absolute()
    require(root.is_dir() and root.resolve()==root,'existing nonsymlink root required')
    require(isinstance(reference,dict) and set(reference)=={'path','sha256'},'pair reference schema')
    hash_value(reference['sha256'])
    outer=Path(reference['path'])
    require(outer.is_absolute() and outer.resolve()==outer and outer.is_relative_to(root)
            and outer.name=='manifest.json','pair reference containment')
    require(outer.parent.parent.parent==root
            and re.fullmatch('artifact-[0-9]{6}',outer.parent.name)
            and re.fullmatch('[A-Za-z0-9_-]{1,100}',outer.parent.parent.name), 'pair session/artifact root layout differs')
    base=outer.parent;device=root.stat().st_dev
    before,dirs_before=inventory(base,device)
    owner_path=base.parent/'owner.json';owner_stat=stamp(regular(owner_path,device))
    metadata={}
    def read(path,expected=None):
        before_stat=regular(path,device)
        require(before_stat.st_size<=LIMIT,'compact metadata limit')
        fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
        with os.fdopen(fd,'rb') as file:
            require(stamp(os.fstat(file.fileno()))==stamp(before_stat),'metadata changed before read')
            raw=file.read(LIMIT+1)
            require(stamp(os.fstat(file.fileno()))==stamp(before_stat),'metadata changed during read')
        require(len(raw)<=LIMIT and len(raw)==before_stat.st_size,'metadata extent changed')
        digest=hashlib.sha256(raw).hexdigest()
        if expected is not None:
            hash_value(expected);require(digest==expected,'metadata hash differs')
        metadata[str(path)]=digest
        return json.loads(raw)
    meta=read(outer,reference['sha256'])
    keys={'schema_version','kind','owner','identity','policy','state_sha256','result','parent'}
    require(isinstance(meta,dict) and set(meta)==keys and type(meta['schema_version']) is int
            and meta['schema_version']==1,'pair manifest schema')
    require(meta['owner']==owner and same(meta['identity'],identity) and same(meta['policy'],policy)
            and same(meta['parent'],parent),'pair owner/identity/policy/parent differs')
    own=read(owner_path)
    require(same(own,{'schema_version':1,'owner':owner,'identity':identity,'policy':policy,'parent':parent})
            and type(own['schema_version']) is int,'session owner differs')
    expected_files={'manifest.json'};expected_dirs={'.'};array_paths=[]
    if meta['kind']=='complete':
        require(meta['state_sha256'] is None and isinstance(meta['result'],dict),'completed pair metadata')
    else:
        require(meta['kind']=='progress' and meta['result'] is None,'pair phase')
        state=read(base/'state/manifest.json',meta['state_sha256'])
        require(set(state)=={'version','phase','policy','matrix_sha256','annealing_sha256','hardening_sha256'}
                and type(state['version']) is int and state['version']==3,'combined checkpoint schema')
        require(same(state['policy'],{k:policy[k] for k in ENGINE_FIELDS}),'checkpoint policy differs')
        require(state['phase'] in ('annealing','hardening','done'),'checkpoint phase')
        anneal=read(base/'state/annealing/manifest.json',state['annealing_sha256'])
        require(set(anneal)=={'schema_version','identity','phase','cursor','iterations','beta','shape','safe','max_chunk_entries','files'}
                and type(anneal['schema_version']) is int and anneal['schema_version']==3,'annealing schema')
        require(same(anneal['identity'],identity['ordered_pair']) and same(anneal['max_chunk_entries'],policy['normalization_chunk_entries'])
                and anneal['safe'] is True,'annealing identity/policy differs')
        shape=anneal['shape']
        require(isinstance(shape,list) and len(shape)==2 and all(type(v) is int and v>0 for v in shape),'matrix shape')
        n,m=shape
        require(32*n*m<=policy['max_state_bytes'] and 32*n*m+512+3*LIMIT<=policy['max_checkpoint_bytes'],'matrix policy envelope')
        require(isinstance(anneal['files'],dict) and set(anneal['files'])=={'V','M','Q'},'annealing inventory')
        expected_dirs.update({'state','state/annealing'})
        expected_files.update({'state/manifest.json','state/annealing/manifest.json'})
        for name,info in anneal['files'].items():
            path=base/f'state/annealing/{name}.npy'
            require(isinstance(info,dict) and set(info)=={'sha256','bytes'},'array extent schema')
            hash_value(info['sha256'])
            require(type(info['bytes']) is int and info['bytes']==8*n*m+128
                    and regular(path,device).st_size==info['bytes'],'array extent differs')
            array_paths.append(path);expected_files.add(str(path.relative_to(base)))
        if state['hardening_sha256'] is None:
            require(state['phase']=='annealing' and state['matrix_sha256'] is None,'missing hardening state')
        else:
            require(state['phase'] in ('hardening','done') and anneal['phase']=='done','hardening phase differs')
            hard=read(base/'state/hardening/manifest.json',state['hardening_sha256'])
            require(set(hard)=={'version','safe','phase','shape','input_sha256','max_pair_entries','max_explicit_bytes','cursor','pairs','order_sha256','order_bytes'}
                    and type(hard['version']) is int and hard['version']==1,'hardening schema')
            hash_value(state['matrix_sha256']);hash_value(hard['order_sha256'])
            require(same(hard['shape'],shape) and hard['input_sha256']==state['matrix_sha256']
                    and same(hard['max_explicit_bytes'],policy['hardening_buffer_bytes']) and hard['safe'] is True,'hardening identity/policy differs')
            path=base/'state/hardening/order.npy'
            require(type(hard['order_bytes']) is int and hard['order_bytes']==8*n*m+128
                    and regular(path,device).st_size==hard['order_bytes'],'rank extent differs')
            array_paths.append(path);expected_dirs.add('state/hardening')
            expected_files.update({'state/hardening/manifest.json','state/hardening/order.npy'})
    require(set(before)==expected_files and set(dirs_before)==expected_dirs,'artifact inventory differs')
    after,dirs_after=inventory(base,device)
    require(after==before and dirs_after==dirs_before and stamp(regular(owner_path,device))==owner_stat,'artifact changed during extent check')
    total=sum(info[4] for info in before.values())
    state_bytes=sum(info[4] for name,info in before.items() if name.startswith('state/'))
    require(state_bytes<=policy['max_checkpoint_bytes'] and total<=reserved,'saved extent exceeds reservation')
    return {'schema_version':1,'reference':dict(reference),'owner':owner,'kind':meta['kind'],
            'reserved_artifact_bytes':reserved,'publication_logical_bytes':total,
            'state_logical_bytes':state_bytes,'owner_logical_bytes':owner_stat[4],
            'publication_allocated_file_bytes':sum(info[7]*512 for info in before.values()),
            'owner_allocated_file_bytes':owner_stat[7]*512,
            'array_files':len(array_paths),'metadata_files':len(metadata)-1,
            'metadata_sha256':metadata,'array_contents_verified':False,
            'qualification':'Complete fixed publication inventory and file extents only; sole-owner guard/admission and numerical array verification remain separate.'}


def reserve_pair(journal,purpose,identity,policy):
    """Reserve the pinned policy envelope before the caller allocates a session."""
    from tradingagents.research.onchain_replication.matching_pair import digest
    budget=reservation_bytes(policy)
    require(isinstance(identity,dict) and same(identity.get('backend'),BACKEND),'backend identity differs')
    target=journal.target(purpose)
    return journal.reserve(purpose,target['path'],digest(identity),budget)


def publish_pair(journal,reference,*,identity,policy):
    """Verify complete saved extents before the durable publication event.

    Verification failure preserves both pending reservation and artifact. It
    does not reconcile or authorize starting another numerical pair.
    """
    from tradingagents.research.onchain_replication.matching_pair import digest
    journal.active()
    pending=journal.state['pending']
    require(pending is not None,'no pending reservation')
    require(pending['identity_sha256']==digest(identity) and reference['path']==pending['path'],'pending publication identity differs')
    report=verify(reference,root=journal.root/'pairs',owner=pending['artifact_owner'],
        identity=identity,policy=policy,parent=pending['session_parent'],
        declared_artifact_bytes=pending['declared_artifact_bytes'])
    journal.publish(reference)
    return report
