"""Unselected, local, single-pair restart scratch retention.

No scientific admission, stage population, aggregate budget or deletion authority
outside the freshly created root follows from this helper. Caller owns numerical
advance/score, original live authority and independently anchored completion.
Retired hashes are historical commitments, never recoverable checkpoints.
"""
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
from threading import Lock

from . import compact_matcher as snapshots, score_batches as io
from .provenance import freeze, thaw

VERSION='bounded-matching-restart-v1'
CONTROL=16384
GENERATION_CONTROL=8*CONTROL+3*snapshots.engine.LIMIT
LIMIT_KEYS={'max_generations','max_generation_bytes','max_control_bytes',
            'max_cumulative_bytes','max_replay_bytes','max_replays'}
require=io._require


def _raw(value):
    raw=io._json(thaw(value));require(len(raw)<=CONTROL,'retention metadata capacity');return raw


def _pin(path):
    info=path.lstat()
    require(path.resolve()==path and stat.S_ISDIR(info.st_mode),'retention canonical directory')
    return [info.st_dev,info.st_ino]


def _cleanup(actions,primary=None):
    errors=[]
    for action in actions:
        try:action()
        except BaseException as error:errors.append(error)
    if errors:
        if primary is not None and not isinstance(primary,Exception):
            for error in errors:primary.add_note('retention cleanup: '+repr(error))
            raise primary
        fatal=io.CleanupFailure('retention cleanup unresolved; worker must stop')
        for error in errors:fatal.add_note(repr(error))
        raise fatal from (primary if primary is not None else errors[0])


@contextmanager
def _directory(path,expected=None):
    root,fd=io._open(path)
    try:
        if expected is not None:require(list(io._signature(os.fstat(fd))[:2])==expected,'retention directory replaced')
        yield fd
        io._root(root,fd)
    finally:_cleanup((lambda:os.close(fd),),sys.exception())


def _sync(path):
    with _directory(path) as fd:os.fsync(fd)


def _write_bytes(path,raw):
    with _directory(path.parent) as parent:
        fd=os.open(path.name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=parent)
        try:
            offset=0
            while offset<len(raw):
                n=os.write(fd,raw[offset:]);require(n>0,'retention short write');offset+=n
            os.fsync(fd)
        finally:_cleanup((lambda:os.close(fd),),sys.exception())
        os.fsync(parent)
    return io._hash(raw)


def _read(path,limit):
    with _directory(path.parent) as fd:return io._read(fd,path.name,limit)


def _names(root,maximum):
    names=set()
    with _directory(root) as fd:
        with os.scandir(fd) as entries:
            for entry in entries:
                require(len(names)<maximum,'retention directory member bound')
                names.add(entry.name)
    return names


def _tree(root,cap):
    """Original inode inventory plus every body hash; bounded real descriptor reads."""
    device=_pin(root)[0];dirs={};files={};total=0
    def walk(path):
        nonlocal total
        with _directory(path) as fd:
            info=os.fstat(fd);require(info.st_dev==device,'retention crossed device')
            dirs[str(path.relative_to(root))]=[info.st_dev,info.st_ino]
            with os.scandir(fd) as entries:
                members=[]
                for entry in entries:
                    require(len(files)+len(dirs)+len(members)<16,'retention body inventory bound')
                    members.append(entry)
            for entry in sorted(members,key=lambda x:x.name):
                child=path/entry.name;info=entry.stat(follow_symlinks=False)
                require(info.st_dev==device,'retention body crossed device')
                if stat.S_ISDIR(info.st_mode):walk(child)
                else:
                    require(stat.S_ISREG(info.st_mode) and info.st_nlink==1,'retention regular exclusive body required')
                    require(total+info.st_size<=cap,'retention body byte bound')
                    raw=io._read(fd,entry.name,cap-total);total+=len(raw)
                    files[str(child.relative_to(root))]={'bytes':len(raw),'sha256':io._hash(raw),
                        'inode':[info.st_dev,info.st_ino]}
    walk(root)
    return {'directories':dirs,'files':files,'logical_bytes':total}


def _snapshot(root,sha,pair,policy,tree=None):
    snapshots._snapshot(root,sha,{'ordered_pair':thaw(pair)['numeric_identity']},thaw(policy))
    actual=_tree(root,policy['max_checkpoint_bytes'])
    if tree is not None:require(actual==tree,'retention original snapshot changed')
    return actual


def _retired_snapshot(root,tree,cap):
    """Retirement removes numeric bodies only; original engine metadata stays."""
    original=thaw(tree)
    metadata={name:item for name,item in original['files'].items() if name.endswith('.json')}
    expected={'directories':original['directories'],'files':metadata,
        'logical_bytes':sum(item['bytes'] for item in metadata.values())}
    require(_tree(root,cap)==expected,'retired metadata or heavy-body disposition differs')


@dataclass(frozen=True)
class EventRef:
    path: Path
    sha256: str


def _event(reference,expected):
    require(type(reference) is EventRef,'externally pinned durable event required')
    io._identity(reference.sha256)
    path=Path(reference.path);require(path.is_absolute() and path.resolve()==path,'canonical event path')
    raw=_read(path,CONTROL)
    require(io._hash(raw)==reference.sha256 and raw==_raw(expected),'durable event differs from external expectation')
    return {'sha256':reference.sha256,'event':thaw(expected)}


class Store:
    """A fresh one-pair authority; failures permanently revoke this instance."""
    def __init__(self,root,*,bindings,pair,policy,limits,replay_first,lease):
        require(set(bindings)=={'owner','stage','source','runtime','policy'},'retention bindings schema')
        for value in bindings.values():io._identity(value)
        require(set(pair)=={'ordinal','purpose_sha256','numeric_identity'}
            and type(pair['ordinal']) is int and pair['ordinal']>=0,'retention ordered pair')
        io._identity(pair['purpose_sha256'])
        require(set(pair['numeric_identity'])=={'left','right','configuration'},'retention numerical identity')
        for value in pair['numeric_identity'].values():io._identity(value)
        require(set(policy)==snapshots.engine.POLICY_FIELDS|{'max_checkpoint_bytes'}
            and all(type(v) is int and v>0 for v in policy.values()),'retention engine policy')
        require(set(limits)==LIMIT_KEYS and all(type(v) is int and 0<v<2**63 for v in limits.values()),'positive retention limits')
        require(type(replay_first) is bool and callable(lease),'explicit replay selector and lease')
        require(limits['max_control_bytes']>=2*CONTROL and limits['max_cumulative_bytes']>=2*CONTROL,'retention claim capacity')
        root=Path(root);require(root.is_absolute() and root.resolve()==root,'fresh canonical retention root')
        self.root=root;self.lease=lease;self.lock=Lock();self._original_lock=self.lock
        self.poisoned=False;self.closed=False
        self.pair=freeze(pair);self.policy=freeze(policy);self.limits=freeze(limits)
        self.generations=0;self.current=None;self.proofs=[];self.retired=[];self.replays={};self.expected={}
        self.spent={'generations':0,'control_bytes':2*CONTROL,'cumulative_bytes':2*CONTROL,'replay_bytes':0,'replays':0}
        lease();parent_pin=_pin(root.parent);root.mkdir();self.inode=_pin(root)
        require(self.inode[0]==parent_pin[0],'retention same-device root required');_sync(root.parent)
        self.claim=freeze({'schema_version':1,'version':VERSION,'root':str(root),'inode':self.inode,
            'bindings':bindings,'pair':pair,'policy':policy,'limits':limits,'replay_first':replay_first,
            'execution_admitted':False})
        self.claim_sha256=self._publish('claim.json',self.claim)
        self._guard()

    def _publish(self,name,value):
        raw=_raw(value);result=_write_bytes(self.root/name,raw);self.expected[name]=raw;return result

    def _local(self):
        require(_pin(self.root)==self.inode and io._hash(_raw(self.claim))==self.claim_sha256,'retention root/claim authority changed')
        allowed=set(self.expected)|{f'generation-{i:020d}' for i in range(self.generations)}|set(self.replays)
        require(_names(self.root,len(allowed)+1)==allowed,'retention root inventory differs')
        for name,raw in self.expected.items():require(_read(self.root/name,CONTROL)==raw,'retention immutable metadata changed')
        for proof in self.proofs:
            proof=thaw(proof)
            i=proof['generation'];path=self.root/f'generation-{i:020d}'
            require(_pin(path)==proof['generation_inode'],'retention generation replaced')
            if i in self.retired:_retired_snapshot(path/'state',proof['tree'],self.policy['max_checkpoint_bytes'])
            else:_snapshot(path/'state',proof['state_sha256'],self.pair,self.policy,thaw(proof['tree']))
        for name,proof in self.replays.items():
            _snapshot(self.root/name,proof['state_sha256'],self.pair,self.policy,proof['tree'])

    def _guard(self):
        require(not self.poisoned and not self.closed,'retention store terminal')
        require(self.lock is self._original_lock,'retention transition changed')
        self.lease()
        require(self.lock is self._original_lock,'retention transition changed during callback')
        self._local()

    @contextmanager
    def _operation(self):
        require(not self.closed and not self.poisoned,'retention store terminal')
        lock=self._original_lock
        require(self.lock is lock and lock.acquire(blocking=False),'concurrent or replaced retention transition')
        if self.closed or self.poisoned:
            _cleanup((lock.release,))
            raise ValueError('retention store terminal')
        try:
            self._guard();yield
            require(self.lock is lock and self._original_lock is lock,'captured retention transition changed')
        except BaseException as primary:
            self.poisoned=True
            try:
                if _pin(self.root)==self.inode and not (self.root/'failure.json').exists():
                    self._publish('failure.json',{'schema_version':1,'error_type':type(primary).__name__,
                        'spent':self.spent,'restart_permitted':False,'execution_admitted':False})
            except BaseException as failure:
                primary.add_note('retention failure evidence: '+repr(failure))
                if isinstance(primary,Exception) and not isinstance(failure,Exception):raise failure from primary
            raise
        finally:_cleanup((lock.release,),sys.exception())

    def _reserve(self,replay):
        size=self.policy['max_checkpoint_bytes'];control=GENERATION_CONTROL
        next_spent=dict(self.spent)
        for key,value in {'generations':1,'control_bytes':control,
            'cumulative_bytes':size+control+(size if replay else 0),
            'replay_bytes':size if replay else 0,'replays':int(replay)}.items():next_spent[key]+=value
        require(size<=self.limits['max_generation_bytes'],'retention single generation capacity')
        for key in next_spent:require(next_spent[key]<=self.limits['max_'+key],'retention cumulative capacity: '+key)
        self.spent=next_spent
        self._publish(f'reservation-{self.generations:020d}.json',{'schema_version':1,'generation':self.generations,'claim_sha256':self.claim_sha256,
            'predecessor':None if not self.proofs else io._hash(_raw(self.proofs[-1])),'spent':self.spent})

    def checkpoint(self,state,a,b,config,*,publish_progress):
        with self._operation():
            require(callable(publish_progress),'durable progress publisher required')
            snapshots.engine.check(state,a,b,config)
            require(snapshots.engine.ann.identity(a,b,config)==thaw(self.pair)['numeric_identity'],'retention pair changed')
            replay=self.generations==0 and self.claim['replay_first']
            self._reserve(replay);i=self.generations;self.generations+=1
            path=self.root/f'generation-{i:020d}';path.mkdir();_sync(self.root)
            sha=snapshots.engine.save(state,path/'state',a,b,config,max_checkpoint_bytes=self.policy['max_checkpoint_bytes'])
            tree=_snapshot(path/'state',sha,self.pair,self.policy)
            require(tree['logical_bytes']<=self.limits['max_generation_bytes'],'retention generation byte capacity')
            summary={'phase':state['phase'],'annealing_phase':state['annealing']['phase'],
                'cursor':state['annealing']['cursor'],'iterations':state['annealing']['iterations']}
            expected={'schema_version':1,'kind':'progress','pair':thaw(self.pair),'event_ordinal':i+1,
                'generation':i,'state_sha256':sha,'state':summary}
            event=_event(publish_progress(freeze(expected)),expected)
            self.lease();require(_pin(self.root)==self.inode,'retention root replaced at callback')
            _snapshot(path/'state',sha,self.pair,self.policy,tree)
            proof={'schema_version':1,'claim_sha256':self.claim_sha256,'generation':i,'generation_inode':_pin(path),'state_sha256':sha,
                'tree':tree,'event':event,'predecessor':None if not self.proofs else io._hash(_raw(self.proofs[-1])),
                'body_available':True,'restart_eligible':True,'execution_admitted':False}
            self._publish(f'progress-{i:020d}.json',proof);self.proofs.append(freeze(proof))
            if replay:self._copy_replay(proof)
            previous=self.current;self.current=i
            self._guard()
            if previous is not None:self._retire(previous,{'successor_proof':io._hash(_raw(proof))})
            self._guard()
            return freeze(proof)

    def _copy_replay(self,proof):
        name=f'replay-{proof["generation"]:020d}';target=self.root/name;target.mkdir();_sync(self.root)
        source=self.root/f'generation-{proof["generation"]:020d}'/'state'
        _snapshot(source,proof['state_sha256'],self.pair,self.policy,proof['tree'])
        for relative in sorted(proof['tree']['directories'],key=lambda x:(len(Path(x).parts),x)):
            if relative!='.':(target/relative).mkdir();_sync((target/relative).parent)
        for relative,item in proof['tree']['files'].items():
            raw=_read(source/relative,item['bytes']);require(io._hash(raw)==item['sha256'],'replay source changed')
            _write_bytes(target/relative,raw)
        tree=_snapshot(target,proof['state_sha256'],self.pair,self.policy)
        copied={'schema_version':1,'generation':proof['generation'],'state_sha256':proof['state_sha256'],
            'tree':tree,'source_proof_sha256':io._hash(_raw(proof)),'body_available':True,'restart_eligible':True}
        self._publish(name+'.json',copied);self.replays[name]=copied

    def _retire(self,i,reason):
        proof=self.proofs[i];path=self.root/f'generation-{i:020d}'/'state';tree=thaw(proof['tree'])
        self._guard()
        require(i not in self.retired and (i!=0 or not self.claim['replay_first'] or self.replays),
            'selected first checkpoint must be retained before retirement')
        intent={'schema_version':1,'generation':i,'proof_sha256':io._hash(_raw(proof)),
            'reason':reason,'tree':tree,'body_available':False,'restart_eligible':False}
        intent_sha=self._publish(f'retire-{i:020d}-intent.json',intent)
        self._guard()
        for relative in sorted(tree['files']):
            if relative.endswith('.json'):continue
            require(relative.endswith('.npy'),'retirement only owns numeric array bodies')
            item=tree['files'][relative];file=path/relative
            with _directory(file.parent,tree['directories'][str(file.parent.relative_to(path))]) as fd:
                raw=io._read(fd,file.name,item['bytes'])
                require(io._hash(raw)==item['sha256'] and list(io._signature(file.lstat())[:2])==item['inode'],
                    'retirement original member changed')
                os.unlink(file.name,dir_fd=fd);os.fsync(fd)
        _retired_snapshot(path,tree,self.policy['max_checkpoint_bytes'])
        self._publish(f'retire-{i:020d}-complete.json',{'schema_version':1,'generation':i,
            'intent_sha256':intent_sha,'body_available':False,'restart_eligible':False})
        self.retired.append(i)

    def finish(self,reference,*,expected):
        with self._operation():
            expected=thaw(expected)
            require(set(expected)=={'schema_version','kind','pair','event_ordinal','score','iterations','convergence'}
                and expected['schema_version']==1 and expected['kind']=='complete'
                and expected['pair']==thaw(self.pair) and expected['event_ordinal']==self.generations+1,
                'completion order/purpose/numeric identity differs')
            import math
            require(type(expected['score']) in (int,float) and math.isfinite(expected['score']) and 0<=expected['score']<=1
                and type(expected['iterations']) is int and expected['iterations']>=0
                and expected['convergence'] in ('temperature_complete','iteration_cap'),'completion numeric fields')
            require(self.spent['control_bytes']+3*CONTROL<=self.limits['max_control_bytes']
                and self.spent['cumulative_bytes']+3*CONTROL<=self.limits['max_cumulative_bytes'],'retention terminal capacity')
            self.spent['control_bytes']+=3*CONTROL;self.spent['cumulative_bytes']+=3*CONTROL
            event=_event(reference,expected);self._publish('completion.json',event)
            self._guard();_event(reference,expected)
            if self.current is not None:self._retire(self.current,{'completion_sha256':reference.sha256})
            self.current=None;self._guard()
            terminal={'schema_version':1,'version':VERSION,'claim_sha256':self.claim_sha256,
                'records':{name:io._hash(raw) for name,raw in self.expected.items()},
                'retired':self.retired,'replays':[v['generation'] for v in self.replays.values()],
                'generations':self.generations,'spent':self.spent,'completion':event,
                'first_checkpoint':('retained' if self.replays else 'completed_before_first_scheduled_checkpoint'
                    if self.claim['replay_first'] and not self.generations else 'unselected'),
                'execution_admitted':False}
            result=self._publish('terminal.json',terminal)
            self._local();verify(self.root,expected_claim=self.claim_sha256,expected_terminal=result)
            self.closed=True;return result

    def body_path(self,generation,*,inspect_failed=False):
        require(type(generation) is int and 0<=generation<len(self.proofs) and generation not in self.retired,
            'retired or unknown body is unavailable')
        require(not self.poisoned or inspect_failed,'failed store is inspection only')
        proof=self.proofs[generation];path=self.root/f'generation-{generation:020d}'/'state'
        _snapshot(path,proof['state_sha256'],self.pair,self.policy,thaw(proof['tree']));return path

    def replay_path(self,generation):
        name=f'replay-{generation:020d}';require(name in self.replays,'unselected replay body')
        proof=self.replays[name];path=self.root/name
        _snapshot(path,proof['state_sha256'],self.pair,self.policy,proof['tree']);return path


def _claim(root,expected):
    io._identity(expected);root=Path(root);raw=_read(root/'claim.json',CONTROL)
    require(io._hash(raw)==expected,'original retention claim differs');claim=json.loads(raw)
    require(claim['version']==VERSION and claim['execution_admitted'] is False
        and claim['root']==str(root) and claim['inode']==_pin(root),'original retention namespace differs')
    return claim


def verify(root,*,expected_claim,expected_terminal):
    """Callback-free terminal check; caller must anchor both original references."""
    root=Path(root);claim=_claim(root,expected_claim);raw=_read(root/'terminal.json',CONTROL)
    require(io._hash(raw)==expected_terminal,'original terminal reference differs');terminal=json.loads(raw)
    require(terminal['claim_sha256']==expected_claim and terminal['version']==VERSION
        and terminal['execution_admitted'] is False,'terminal claim differs')
    n=terminal['generations'];require(type(n) is int and 0<=n<=claim['limits']['max_generations']
        and terminal['retired']==list(range(n)),'terminal complete disposition chain required')
    replay=bool(claim['replay_first'] and n)
    require(terminal['replays']==([0] if replay else []),'frozen replay membership differs')
    record_names={'claim.json','completion.json'}
    for i in range(n):
        record_names.update({f'reservation-{i:020d}.json',f'progress-{i:020d}.json',
            f'retire-{i:020d}-intent.json',f'retire-{i:020d}-complete.json'})
    if replay:record_names.add('replay-00000000000000000000.json')
    require(set(terminal['records'])==record_names,'terminal exact admitted record set differs')
    records={}
    for name,digest in terminal['records'].items():
        data=_read(root/name,CONTROL);require(io._hash(data)==digest,'terminal record changed');records[name]=json.loads(data)
    require(terminal['records']['claim.json']==expected_claim,'terminal original claim differs')
    spent={'generations':0,'control_bytes':2*CONTROL,'cumulative_bytes':2*CONTROL,'replay_bytes':0,'replays':0}
    allowed=set(records)|{'terminal.json'};previous=None;size=claim['policy']['max_checkpoint_bytes']
    for i in range(n):
        name=f'generation-{i:020d}';allowed.add(name);proof=records[f'progress-{i:020d}.json']
        require(proof['generation']==i and proof['claim_sha256']==expected_claim and proof['predecessor']==previous
            and proof['generation_inode']==_pin(root/name),
            'terminal generation chain/retirement differs')
        _retired_snapshot(root/name/'state',proof['tree'],claim['policy']['max_checkpoint_bytes'])
        selected=bool(replay and i==0)
        for key,value in {'generations':1,'control_bytes':GENERATION_CONTROL,
            'cumulative_bytes':size+GENERATION_CONTROL+(size if selected else 0),
            'replay_bytes':size if selected else 0,'replays':int(selected)}.items():spent[key]+=value
        require(records[f'reservation-{i:020d}.json']=={'schema_version':1,'generation':i,
            'claim_sha256':expected_claim,'predecessor':previous,'spent':spent},'original monotone reservation differs')
        event=proof['event']['event']
        require(event['schema_version']==1 and event['kind']=='progress' and event['pair']==claim['pair']
            and event['generation']==i and event['event_ordinal']==i+1 and event['state_sha256']==proof['state_sha256']
            and proof['event']['sha256']==io._hash(_raw(event)),'progress durable event differs')
        previous=io._hash(_raw(proof));intent=records[f'retire-{i:020d}-intent.json'];done=records[f'retire-{i:020d}-complete.json']
        reason=({'successor_proof':io._hash(_raw(records[f'progress-{i+1:020d}.json']))} if i+1<n
            else {'completion_sha256':terminal['completion']['sha256']})
        require(intent['generation']==i and intent['proof_sha256']==previous and intent['tree']==proof['tree']
            and intent['reason']==reason and intent['body_available'] is False and intent['restart_eligible'] is False
            and done=={'schema_version':1,'generation':i,'intent_sha256':io._hash(_raw(intent)),
                'body_available':False,'restart_eligible':False},'retirement exact proof differs')
        if selected:
            name=f'replay-{i:020d}';allowed.add(name);r=records[name+'.json']
            require(r['source_proof_sha256']==previous and r['state_sha256']==proof['state_sha256']
                and r['generation']==i and r['body_available'] is True and r['restart_eligible'] is True,
                'replay original proof differs')
            _snapshot(root/name,r['state_sha256'],claim['pair'],claim['policy'],r['tree'])
    spent['control_bytes']+=3*CONTROL;spent['cumulative_bytes']+=3*CONTROL
    require(terminal['spent']==spent and all(value<=claim['limits']['max_'+key] for key,value in spent.items()),
        'terminal bounded monotone spending differs')
    require(_names(root,len(allowed)+1)==allowed,'terminal exact namespace differs')
    event=terminal['completion']['event']
    require(terminal['completion']==records['completion.json']
        and terminal['completion']['sha256']==io._hash(_raw(event))
        and event['schema_version']==1 and event['kind']=='complete' and event['pair']==claim['pair']
        and event['event_ordinal']==n+1,'terminal completion differs')
    disposition='retained' if replay else ('completed_before_first_scheduled_checkpoint'
        if claim['replay_first'] and not n else 'unselected')
    require(terminal['first_checkpoint']==disposition and _pin(root)==claim['inode'],'terminal final disposition/root differs')
    return freeze(terminal)


def reconcile(root,*,expected_claim,expected_progress=None):
    """Read-only crash observations. Original pins are required to verify bodies.

    No receipt is completed and no continuation/retry authority is manufactured.
    Unanchored on-disk progress remains an observation, not a trusted checkpoint.
    """
    root=Path(root);claim=_claim(root,expected_claim);items=[];last=None
    pins={} if expected_progress is None else dict(expected_progress)
    require(len(pins)<=claim['limits']['max_generations'],'reconciliation reference bound')
    for path_name in sorted(_names(root,5+claim['limits']['max_generations']*8)):
        path=root/path_name;info=path.lstat();item={'name':path.name,'directory':stat.S_ISDIR(info.st_mode),
            'symlink':stat.S_ISLNK(info.st_mode),'bytes':info.st_size,'restart_eligible':False}
        if path.name.startswith('generation-') and path.name[11:].isdigit():
            i=int(path.name[11:]);body=path/'state';item['body_present']=body.exists()
            item['body_verified']=False
            if i in pins:
                raw=_read(root/f'progress-{i:020d}.json',CONTROL)
                require(io._hash(raw)==pins[i],'reconciliation original progress differs');proof=json.loads(raw)
                require(proof['claim_sha256']==expected_claim and proof['generation']==i
                    and proof['generation_inode']==_pin(path),'reconciliation original generation differs')
                if body.exists():
                    try:_snapshot(body,proof['state_sha256'],claim['pair'],claim['policy'],proof['tree'])
                    except (ValueError,OSError):item['body_verified']=False
                    else:item['body_verified']=True;last=i if last is None else max(last,i)
        items.append(item)
    require(_pin(root)==claim['inode'],'reconciliation root changed')
    return {'claim_sha256':expected_claim,'observations':items,'last_available_verified_progress':last,
        'restart_permitted':False,'execution_admitted':False}
