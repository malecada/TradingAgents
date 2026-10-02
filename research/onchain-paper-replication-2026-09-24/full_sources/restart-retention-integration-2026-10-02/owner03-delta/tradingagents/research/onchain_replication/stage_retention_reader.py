"""Strict callback-free retention content and actual archived-frame joins.

The caller supplies original stage/selector/seal authority. This module does not
promote a freshly self-hashed directory into an admitted stage.
"""
import json
import sys
from pathlib import Path
import numpy as np
from . import stage_retention as retention, restart_retention as store
from . import compact_pair_log as events, matching_pair as pair
from .contracts import AttributedGraph
from .matching_identity import graph_identity
from .provenance import thaw

io=events.io
require=io._require


def _same(a,b):return store._raw(thaw(a))==store._raw(thaw(b))


def check(root,*,policy,selection,expected_sha256,start_sha256):
    root=Path(root);retention.validate(policy);retention._selection(thaw(selection))
    raw=store._read(root/'seal.json',store.CONTROL);require(io._hash(raw)==expected_sha256,'original stage retention seal differs')
    seal=json.loads(raw);claim=retention._read(root/'claim.json')
    require(seal['format']==claim['format']==retention.FORMAT and seal['claim_sha256']==io._hash(store._raw(claim))
        and claim['root']==str(root) and claim['inode']==store._pin(root)
        and claim['log_start_sha256']==start_sha256 and _same(claim['policy'],policy)
        and _same(claim['selection'],selection),'retention original policy/selector/namespace differs')
    require(seal['inventory_sha256']==retention._digest(retention._inventory(root)),
        'retention exact inventory commitment differs')
    allowed={'claim.json','seal.json','stores','bridges','events','inputs'};store_names=set();count=0
    for path in sorted(root.glob('store-*.json')):
        record=retention._read(path);ordinal=record['ordinal'];name=f'pair-{ordinal:012d}'
        require(path.name==f'store-{ordinal:012d}.json','retention store index differs')
        terminal=store.verify(root/'stores'/name,expected_claim=record['claim_sha256'],expected_terminal=record['terminal_sha256'])
        actual=retention._read(root/'stores'/name/'claim.json')
        require(actual['pair']['ordinal']==ordinal and actual['bindings']['owner']==claim['owner']
            and actual['bindings']['stage']==claim['stage'] and actual['bindings']['policy']==retention.cache_key(policy),
            'retention original store binding differs')
        complete=retention._read(root/'bridges'/f'complete-{record["completion_event"]:012d}.json')
        require(_same(terminal['completion']['event'],complete['expected'])
            and terminal['completion']['sha256']==complete['json_sha256'],'store completion frame bridge differs')
        count+=terminal['generations'];allowed.add(path.name);store_names.add(name)
    require(store._names(root/'stores',policy['max_stores']+1)==store_names and len(store_names)==seal['stores'],
        'exact lazy retention stores differ')
    selected=set();inputs=set();input_upper=0;replays=0
    for index,member in enumerate(selection['members']):
        name=f'selected-{index:012d}.json';record=retention._read(root/name);allowed.add(name)
        require(record['member']==list(member) and record['ordinal'] not in selected,
            'fixed selected replay member differs');selected.add(record['ordinal'])
        bridge=retention._read(root/'bridges'/f'complete-{record["completion_event"]:012d}.json')
        purpose=bridge['purpose'];expected_member=(purpose['sample_indices'] if selection['kind']=='dictionary'
            else [purpose['center_index'],purpose['motif_index']])
        require(expected_member==list(member) and record['purpose_sha256']==retention.cache_key(purpose),
            'selected actual purpose differs')
        path=root/'stores'/f'pair-{record["ordinal"]:012d}'
        if path.name in store_names:
            replays+=1
            require(record['disposition']=='first_checkpoint_retained' and retention._read(path/'claim.json')['replay_first'],
                'selected FIRST disposition differs')
        else:require(record['disposition']=='completed_before_first_scheduled_checkpoint','selected zero checkpoint disposition differs')
        name=f'input-{index:012d}.json';meta=retention._read(root/'inputs'/name);inputs.add(name)
        identities=[];input_upper+=store.CONTROL
        for graph in meta['graphs']:
            arrays={}
            try:
                for key,item in graph['files'].items():
                    require(Path(item['path']).name==item['path'] and item['bytes']<=policy['max_input_bytes'],
                        'bounded replay input extent')
                    body=root/'inputs'/item['path'];store.snapshots._file(body,item['bytes'],item['sha256']);inputs.add(item['path'])
                    arrays[key]=np.load(body,allow_pickle=False,mmap_mode='r',max_header_size=1024)
                    input_upper+=arrays[key].nbytes+256
                actual=AttributedGraph(tuple(graph['node_ids']),arrays['node_features'],arrays['edge_index'],
                    arrays['edge_features'],graph['parent_hash'],graph['center_id'])
                require(graph_identity(actual)==graph['typed_identity'],'replay input numeric identity differs')
                identities.append(graph['typed_identity'])
            finally:
                store._cleanup(tuple(v._mmap.close for v in arrays.values() if getattr(v,'_mmap',None) is not None),sys.exception())
        require(identities==purpose['typed_graphs'],'selected replay ordered input identities differ')
    reservations=seal['reservations'];require(type(reservations) is int and 0<=reservations<=3*policy['max_generations']+8,'retention reservation count')
    running={'stores':0,'generations':0,'control_bytes':8*store.CONTROL,'cumulative_bytes':8*store.CONTROL,'replay_bytes':0,'input_bytes':0,'replays':0};head=None
    for i in range(reservations):
        name=f'reserve-{i:012d}.json';allowed.add(name);record=retention._read(root/name)
        require(record['ordinal']==i and record['predecessor']==head and record['reason'] in {'inputs','generation','store','completion'},'retention reservation chain')
        for key,value in record['delta'].items():
            require(key in running and type(value) is int and value>=0,'retention positive reservation delta');running[key]+=value
        require(running==record['spent'] and all(v<=policy['max_'+k] for k,v in running.items()),'retention monotone reservation cap')
        head=io._hash(store._raw(record))
    require(head==seal['reservation_head'] and running==seal['spent'],'retention final original spending')
    require(store._names(root/'inputs',len(inputs)+1)==inputs and store._names(root,len(allowed)+1)==allowed,
        'retention exact root/input inventory differs')
    progress=0;completions=0
    bridge_names=set();event_names=set()
    for path in sorted((root/'bridges').iterdir()):
        require(path.name.startswith(('progress-','complete-')) and path.name.endswith('.json'),'foreign bridge member')
        bridge=retention._read(path);event_names.add(Path(bridge['json_event']).name);bridge_names.add(path.name)
        require(bridge['json_event']=='events/'+Path(bridge['json_event']).name,'event view namespace differs')
        require(io._hash(store._read(root/bridge['json_event'],store.CONTROL))==bridge['json_sha256']
            and _same(retention._read(root/bridge['json_event']),bridge['expected']),'exact event JSON view differs')
        if path.name.startswith('complete-'):completions+=1
        if path.name.startswith('progress-'):
            progress+=1;obj=root/'stores'/bridge['store'];i=bridge['expected']['generation']
            proof=retention._read(obj/f'progress-{i:020d}.json')
            require(proof['claim_sha256']==bridge['store_claim_sha256'] and proof['state_sha256']==bridge['expected']['state_sha256']
                and _same(proof['event'],{'sha256':bridge['json_sha256'],'event':bridge['expected']}),
                'retention snapshot actual progress bridge differs')
    require(store._names(root/'events',len(event_names)+1)==event_names and progress==count==seal['progress_events'],
        'retention exact progress population differs')
    C=store.CONTROL;G=store.GENERATION_CONTROL;size=claim['pair_policy']['max_checkpoint_bytes'];n=len(selected);s=len(store_names)
    control=8*C+count*(G+4*C)+s*7*C+n*3*C+completions*3*C
    expected={'stores':s,'generations':count,'control_bytes':control,'cumulative_bytes':control+count*size+replays*size+input_upper,
        'replay_bytes':replays*size,'input_bytes':input_upper,'replays':replays}
    require(seal['spent']==expected,'independent stage reservation arithmetic differs')
    for key,value in seal['spent'].items():require(type(value) is int and 0<=value<=policy['max_'+key],'retention aggregate budget differs')
    require(seal['spent']['generations']==count and seal['spent']['stores']==len(store_names),
        'retention aggregate exact counts differ')
    return seal


class Visitor:
    """Each exact decoded frame in the one reserved archived replay visits once."""
    def __init__(self,root,*,policy,selection,expected_sha256,start_sha256):
        self.root=Path(root);self.arguments=dict(policy=policy,selection=selection,
            expected_sha256=expected_sha256,start_sha256=start_sha256)
        self.seal=check(root,**self.arguments);self.head=start_sha256;self.count=0;self.progress=0
    def visit(self,frame):
        require(frame[0]==self.count,'retention actual frame ordinal differs')
        packed=events.FRAME.pack(*frame);head=io._hash(bytes.fromhex(self.head)+packed)
        event,kind,ordinal,score,iterations,purpose,identity,artifact=frame
        if kind==3:
            path=self.root/'bridges'/f'progress-{event:012d}.json';bridge=retention._read(path)
            require(io._hash(store._read(path,store.CONTROL))==artifact.hex()
                and bridge['event']==event and bridge['previous_head']==self.head
                and bridge['pair']==ordinal and bridge['log_start_sha256']==self.arguments['start_sha256']
                and retention.cache_key(bridge['purpose'])==purpose.hex()
                and pair.digest(bridge['identity'])==identity.hex()
                and bridge['expected']['pair']['numeric_identity']==bridge['identity']['ordered_pair']
                and bridge['expected']['pair']['ordinal']==ordinal,'actual progress frame bridge differs')
            self.progress+=1
        elif kind in (1,2):
            path=self.root/'bridges'/f'complete-{event:012d}.json'
            if path.exists():
                bridge=retention._read(path);value=bridge['expected']
                require(bridge['raw']==(packed+bytes.fromhex(head)).hex()
                    and value['pair']['ordinal']==ordinal and value['pair']['purpose_sha256']==purpose.hex()
                    and retention.cache_key(bridge['purpose'])==purpose.hex()
                    and pair.digest(bridge['identity'])==identity.hex()
                    and value['score']==score and value['iterations']==iterations
                    and value['convergence']==('temperature_complete' if kind==1 else 'iteration_cap'),
                    'actual completion frame bridge differs')
        self.head=head;self.count+=1
    def finish(self):
        require(self.count==self.seal['events'] and self.head==self.seal['head']
            and self.progress==self.seal['progress_events'],'retention actual full frame population differs')
        require(check(self.root,**self.arguments)==self.seal,'retention changed after actual archived read')
        return self.seal
