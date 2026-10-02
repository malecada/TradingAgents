"""Explicit archived-stage restart retention; no run or scientific admission.

Binary frames commit pre-event descriptors. The later Store receipts refer to
separate exact JSON event views, avoiding a frame/proof hash cycle. Stage limits
reserve all retained controls and replay bodies cumulatively; numeric scratch,
physical allocation and elapsed time remain the enclosing guard's obligations.
"""
import hashlib
import io as memory_io
import json
from pathlib import Path
import struct
from weakref import WeakKeyDictionary

import numpy as np
from . import restart_retention as store, score_batches as io, compact_pair_log as events
from .cache import cache_key
from .matching_identity import graph_identity
from .provenance import freeze, thaw

require=io._require
FORMAT='archived-restart-retention-v1'
FIELDS={'schema_version','format','max_stores','max_generations','max_control_bytes',
    'max_cumulative_bytes','max_live_bytes','max_replay_bytes','max_input_bytes','max_replays'}
_AUTH=WeakKeyDictionary()


def validate(policy,pair=None):
    require(type(policy) is dict and set(policy)==FIELDS and policy['schema_version']==1
        and type(policy['schema_version']) is int and policy['format']==FORMAT,'explicit stage retention policy')
    require(all(type(policy[k]) is int and 0<policy[k]<2**63 for k in FIELDS-{'schema_version','format'}),
        'positive finite stage retention limits')
    require(policy['max_replays']>=2 and policy['max_control_bytes']>=8*store.CONTROL,
        'stage replay/control allowance')
    if pair is not None:
        require(policy['max_live_bytes']>=policy['max_control_bytes']+policy['max_input_bytes']
            +policy['max_replay_bytes']+2*pair['max_checkpoint_bytes'],'current candidate controls and replay live allowance')
    return policy


def dictionary_selection(samples,settings):
    n=len(samples.graphs);indices=list(range(n))
    if n>settings['partition_threshold']:
        shuffled=np.random.Generator(np.random.PCG64(samples.seed)).permutation(indices)
        groups=[sorted(map(int,shuffled[i:i+settings['partition_size']]))
            for i in range(0,n,settings['partition_size'])]
    else:groups=[indices]
    eligible=[g for g in groups if len(g)>1]
    members=[] if not eligible else [[eligible[0][1],eligible[0][0]],[eligible[-1][-2],eligible[-1][-1]]]
    members=[v for i,v in enumerate(members) if v not in members[:i]]
    return {'kind':'dictionary','population':{'sample_hash':samples.identity,'sample_count':n,
        'seed':samples.seed,'configuration':settings,'initial_blocks_sha256':cache_key(groups)},'members':members}


def mcm_selection(graph,dictionary):
    n=len(graph.node_ids);k=len(dictionary.representatives)
    return {'kind':'mcm','population':{'nodes':n,'motifs':k},
        'members':[[0,0]] if n*k==1 else [[0,0],[n-1,k-1]]}


def _selection(value):
    require(type(value) is dict and set(value)=={'kind','population','members'}
        and value['kind'] in ('dictionary','mcm') and type(value['members']) is list
        and len(value['members'])<=2 and len({tuple(x) for x in value['members']})==len(value['members']),
        'fixed replay selector schema')
    for member in value['members']:
        require(type(member) is list and len(member)==2 and all(type(v) is int and v>=0 for v in member),
            'ordered replay selector')
    if value['kind']=='mcm':
        p=value['population'];require(set(p)=={'nodes','motifs'} and all(type(x) is int and x>0 for x in p.values()),'MCM replay population')
        expected=[[0,0]] if p['nodes']*p['motifs']==1 else [[0,0],[p['nodes']-1,p['motifs']-1]]
        require(value['members']==expected,'MCM fixed endpoints differ')
    return value


def _digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def _read(path):return json.loads(store._read(path,store.CONTROL))
def _write(path,value):return store._write_bytes(path,store._raw(value))
def _inventory(root):
    result={}
    for directory in (root,root/'bridges',root/'events',root/'inputs'):
        for path in sorted(directory.iterdir()):
            if path.is_dir():continue
            if path.name=='seal.json' and directory==root:continue
            raw=store._read(path,max(store.CONTROL,path.stat().st_size))
            result[str(path.relative_to(root))]=io._hash(raw)
    return result


class Controller:
    def __init__(self,matcher,*,policy,selection,stage):
        from .archive_pair_writer import ArchivePairLog
        require(type(matcher.log) is ArchivePairLog,'restart retention requires explicit archived event route')
        validate(policy,matcher.policy);_selection(selection);io._identity(stage)
        self.matcher=matcher;self.root=matcher.root;self.policy=freeze(policy);self.selection=freeze(selection)
        self.inode=store._pin(self.root);self.expected={};self.active=None;self.selections={};self.stores={}
        self.spent={'stores':0,'generations':0,'control_bytes':8*store.CONTROL,'cumulative_bytes':8*store.CONTROL,
            'replay_bytes':0,'input_bytes':0,'replays':0};self.closed=False;self.poisoned=False
        self.current_frame=None
        self.claim={'schema_version':1,'format':FORMAT,'root':str(self.root),'inode':self.inode,
            'owner':matcher.log.start['owner'],'stage':stage,'log_start_sha256':matcher.log.start_sha,
            'scope':matcher.log.start['scope'],'policy':thaw(self.policy),'selection':thaw(self.selection),
            'pair_policy':matcher.policy,'context':matcher.context,'config':matcher.config,'schedule':matcher.schedule}
        for name in ('stores','bridges','events','inputs'):(self.root/name).mkdir()
        store._sync(self.root);self._write('claim.json',self.claim)
        _AUTH[self]={'root':self.root,'inode':self.inode,'failed':False};self._refresh()
        self.live()

    def _state(self):
        return _digest({'claim':self.claim,'expected':self.expected,'spent':self.spent,
            'selection':thaw(self.selection),'policy':thaw(self.policy),'closed':self.closed,'poisoned':self.poisoned,
            'active':None if self.active is None else {k:v for k,v in self.active.items() if k!='store'},
            'stores':self.stores,'selections':self.selections,'frame':None if self.current_frame is None else
                [self.current_frame[0],self.current_frame[1],self.current_frame[2].hex()]})
    def _refresh(self):
        if self in _AUTH:_AUTH[self]['state']=self._state()
    def _authority(self):
        pin=_AUTH[self];require(not pin['failed'] and not self.poisoned and not self.closed
            and self.root==pin['root'] and self.inode==pin['inode'] and self._state()==pin['state'],
            'original stage retention authority changed')
    def _write(self,name,value):
        ref=_write(self.root/name,value);self.expected[name]=ref;self._refresh();return ref
    def _integrity(self):
        require(store._pin(self.root)==self.inode,'retention stage namespace changed')
        for name,sha in self.expected.items():
            require(io._hash(store._read(self.root/name,store.CONTROL))==sha,'retention stage record changed')
    def live(self):
        self._authority();before=self._state();self.matcher._check()
        require(self._state()==before,'stage retention callback changed authority');self._authority();self._integrity()
        if self.current_frame is not None:self.matcher._ack_check(self.current_frame)
    def _reserve(self,**values):
        self.live();next_spent=dict(self.spent)
        for key,value in values.items():next_spent[key]+=value
        for key,value in next_spent.items():require(value<=self.policy['max_'+key],'stage retention cumulative capacity: '+key)
        self.spent=next_spent;self._refresh()
    def _member(self,purpose):
        return purpose['sample_indices'] if self.selection['kind']=='dictionary' else [purpose['center_index'],purpose['motif_index']]
    def begin(self,purpose,a,b,identity,expected):
        self.current_frame=expected;self._refresh();self.live()
        ordinal=self.matcher.log.state['pending']['ordinal'];member=self._member(purpose)
        selected=next((i for i,v in enumerate(self.selection['members']) if list(v)==member and i not in self.selections),None)
        self.active={'ordinal':ordinal,'purpose':thaw(purpose),'identity':thaw(identity),'selected':selected,'store':None}
        self._refresh()
        if selected is not None:
            self._inputs(selected,a,b)
            self.selections[selected]={'ordinal':ordinal,'purpose_sha256':cache_key(purpose),'member':member}
            self._refresh()
    def _inputs(self,index,a,b):
        encoded=[];graphs=[]
        for direction,g in enumerate((a,b)):
            item={'node_ids':list(g.node_ids),'parent_hash':g.parent_hash,'center_id':g.center_id,
                'typed_identity':graph_identity(g),'files':{}}
            for name in ('node_features','edge_index','edge_features'):
                output=memory_io.BytesIO();np.save(output,getattr(g,name),allow_pickle=False);raw=output.getvalue()
                relative=f'input-{index:012d}-{direction}-{name}.npy'
                encoded.append((relative,raw));item['files'][name]={'path':relative,'bytes':len(raw),'sha256':io._hash(raw)}
            graphs.append(item)
        meta={'schema_version':1,'graphs':graphs};raw=store._raw(meta)
        size=sum(len(v) for _,v in encoded)+len(raw)
        self._reserve(input_bytes=size,cumulative_bytes=size,control_bytes=2*store.CONTROL)
        for name,body in encoded:store._write_bytes(self.root/'inputs'/name,body)
        self._write(f'inputs/input-{index:012d}.json',meta);self.live()
    def checkpoint(self,state,a,b,identity,purpose):
        require(self.active is not None,'retention matching pair absent')
        selected=self.active['selected'];obj=self.active['store']
        replay=obj is None and selected is not None
        control=store.GENERATION_CONTROL+3*store.CONTROL
        self._reserve(generations=1,control_bytes=control,cumulative_bytes=control+self.matcher.policy['max_checkpoint_bytes']*(1+int(replay)),
            replay_bytes=self.matcher.policy['max_checkpoint_bytes']*int(replay),replays=int(replay))
        if obj is None:
            self._reserve(stores=1,control_bytes=5*store.CONTROL,cumulative_bytes=5*store.CONTROL)
            policy={k:self.matcher.policy[k] for k in store.snapshots.engine.POLICY_FIELDS|{'max_checkpoint_bytes'}}
            limits={'max_generations':self.matcher.schedule['max_checkpoints'],'max_generation_bytes':policy['max_checkpoint_bytes'],
                'max_control_bytes':self.policy['max_control_bytes'],'max_cumulative_bytes':self.policy['max_cumulative_bytes'],
                'max_replay_bytes':self.policy['max_replay_bytes'],'max_replays':1}
            pair={'ordinal':self.active['ordinal'],'purpose_sha256':cache_key(purpose),'numeric_identity':identity['ordered_pair']}
            obj=store.Store(self.root/'stores'/f'pair-{pair["ordinal"]:012d}',bindings={'owner':self.claim['owner'],
                'stage':self.claim['stage'],'source':cache_key(self.matcher.components),'runtime':self.matcher.context['runtime_hash'],
                'policy':cache_key(thaw(self.policy))},pair=pair,policy=policy,limits=limits,replay_first=replay,lease=self.live)
            self.active['store']=obj;self.active['claim_sha256']=obj.claim_sha256;self._refresh()
        def publish(value):
            self.live();event=self.matcher.log.events
            eventname=f'events/progress-{event:012d}.json';sha=self._write(eventname,thaw(value))
            bridge={'schema_version':1,'format':FORMAT,'log_start_sha256':self.claim['log_start_sha256'],
                'event':event,'previous_head':self.matcher.log.head,'pair':self.active['ordinal'],
                'purpose':thaw(purpose),'identity':identity,'store_claim_sha256':obj.claim_sha256,
                'store':obj.root.name,'json_event':eventname,'json_sha256':sha,'expected':thaw(value)}
            artifact=self._write(f'bridges/progress-{event:012d}.json',bridge)
            expected=self.matcher._expected_event(3,artifact=artifact)
            self.matcher.log.progress(artifact);self.current_frame=expected;self._refresh();self.live()
            return store.EventRef(self.root/eventname,sha)
        result=obj.checkpoint(state,a,b,self.matcher.config,publish_progress=publish)
        self.live();return result
    def complete(self,expected,score,iterations,convergence):
        self.current_frame=expected;self._refresh();self.live();active=self.active;obj=active['store']
        member=active['selected']
        if obj is not None or member is not None:
            self._reserve(control_bytes=2*store.CONTROL,cumulative_bytes=2*store.CONTROL)
            pair={'ordinal':active['ordinal'],'purpose_sha256':cache_key(active['purpose']),
                'numeric_identity':active['identity']['ordered_pair']}
            value={'schema_version':1,'kind':'complete','pair':pair,'event_ordinal':1 if obj is None else obj.generations+1,
                'score':score,'iterations':iterations,'convergence':convergence}
            path=f'events/complete-{expected[0]:012d}.json';sha=self._write(path,value)
            bridge={'schema_version':1,'event':expected[0],'raw':expected[2].hex(),'json_event':path,
                'json_sha256':sha,'expected':value,'purpose':active['purpose'],'identity':active['identity']}
            self._write(f'bridges/complete-{expected[0]:012d}.json',bridge)
            if obj is not None:
                terminal=obj.finish(store.EventRef(self.root/path,sha),expected=value)
                record={'ordinal':active['ordinal'],'claim_sha256':obj.claim_sha256,'terminal_sha256':terminal,
                    'completion_event':expected[0]}
                self._write(f'store-{active["ordinal"]:012d}.json',record);self.stores[active['ordinal']]=record
            if member is not None:
                record=self.selections[member]|{'completion_event':expected[0],
                    'disposition':'first_checkpoint_retained' if obj is not None else 'completed_before_first_scheduled_checkpoint'}
                self._write(f'selected-{member:012d}.json',record)
        self.active=None;self._refresh();self.live()
    def finish_stage(self):
        self.live();require(self.active is None and len(self.selections)==len(self.selection['members']),
            'selected replay members absent or stage incomplete')
        log=self.matcher.log;require(log.state['pending'] is None,'retention pending pair')
        result={'schema_version':1,'format':FORMAT,'claim_sha256':self.expected['claim.json'],
            'inventory_sha256':_digest(_inventory(self.root)),'stores':len(self.stores),'spent':self.spent,
            'events':log.events,'head':log.head,'completed_pairs':log.state['completed_pairs'],
            'progress_events':log.state['progress_events'],'execution_admitted':False}
        reference=_write(self.root/'seal.json',result);self.live();self.closed=True;self._refresh();return reference
