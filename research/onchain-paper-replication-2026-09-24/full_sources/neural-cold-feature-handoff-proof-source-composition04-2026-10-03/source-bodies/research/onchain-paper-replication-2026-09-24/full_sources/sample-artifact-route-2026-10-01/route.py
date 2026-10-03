"""Read-only current first-owner sample-event admission; not producer release.

Requires an array-backed sample publication. Legacy JSON numeric lists are
refused. Historical reuse, sampler RNG provenance and dictionary/MCM publication
remain separate. The array cap reserves loaded plus immutable-copy payloads;
Python metadata and induced-neighborhood scratch still require the outer guard.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
from tradingagents.research.onchain_replication import feature_journal,serialization
from tradingagents.research.onchain_replication.provenance import canonical_bytes,file_hash,freeze,thaw

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
consumer=load('sample_join_consumer',HERE.parent/'pair-consumer-route-2026-10-01/route.py')
reader=load('sample_join_reader',HERE.parent/'pair-component-reader-2026-10-01/reader.py')
SOURCES=tuple(sorted(set(consumer.SOURCES)|{str(Path(p).relative_to(ROOT)) for p in
    (__file__,reader.__file__,serialization.__file__,feature_journal.__file__)}))

def require(value,message):
    if not value:raise ValueError(message)

def equal(a,b):return canonical_bytes(a)==canonical_bytes(b)

def sources(owned):
    ad=owned.workload.bound._run.admission
    for name in SOURCES:
        expected=ad.experiment['source_files'].get(name)
        require(expected is not None and file_hash(ROOT/name)==expected
            and file_hash(ad.root/name)==expected,'sample join source is not admitted or changed')

class Slot:
    def __init__(self,name,info):self.name=name;self.shape=tuple(info['shape']);self.dtype=info['dtype']

def sample_shape(manifest,route):
    slots={name:Slot(name,info) for name,info in manifest['arrays'].items()}
    value=reader.walk(manifest['tree'],manifest['arrays'],set(),slots)
    require(isinstance(value,dict) and set(value)=={'graphs','records','source_hashes','rng_state','seed','identity'},'sample record schema differs')
    count=route.settings['sample_count']
    require(type(value['seed']) is int and value['seed']==route.descriptor['seed']
        and isinstance(value['graphs'],(list,tuple)) and len(value['graphs'])==count
        and isinstance(value['records'],(list,tuple)) and len(value['records'])==count,'sample metadata dimensions differ')
    used=set()
    for graph in value['graphs']:
        require(isinstance(graph,dict) and set(graph)=={'node_ids','node_features','edge_index','edge_features','edge_width','parent_hash','center_id'},'sample graph schema differs')
        require(isinstance(graph['node_ids'],(list,tuple)) and bool(graph['node_ids'])
            and all(type(x) is str for x in graph['node_ids']),'sample node metadata differs')
        n=len(graph['node_ids']);width=graph['edge_width']
        require(type(width) is int and width>0,'positive sample edge width required')
        for field,dtype in (('node_features','float64'),('edge_index','int64'),('edge_features','float64')):
            slot=graph[field]
            require(type(slot) is Slot and slot.dtype==dtype and len(slot.shape)==2,'native typed sample arrays required')
            used.add(slot.name)
        nodes,edges,features=(graph[x] for x in ('node_features','edge_index','edge_features'))
        require(nodes.shape[0]==n and nodes.shape[1]>0 and edges.shape[0]==2
            and features.shape==(edges.shape[1],width),'sample array shape differs')
    require(used==set(slots),'arrays outside sample numerical fields')
    return value['identity']

class AdmittedSamples:
    def __init__(self,samples,scope,record,lease):
        self.samples=samples;self.scope=scope;self.record=freeze(record);self._lease=lease
    def lease(self):self._lease()

def admit_samples(owned,journal,*,artifact_input,event_index,event_sha256):
    require(type(owned) is consumer.ownership.OwnedJournal
        and type(journal) is feature_journal.FeatureJournal,'actual owner and feature journal required')
    owned.workload.bound.check();owned.lease();sources(owned)
    route=owned.workload;bound=route.bound;ad=bound._run.admission;record=bound.record
    directory=Path(record['journal_directory']);snapshots={}
    def read(path,expected=None,cap=reader.MANIFEST_LIMIT):
        path=Path(path);old=snapshots.get(path)
        with reader.opened(path,ad.root,None if old is None else old[1]) as (stream,sig):
            require(0<sig[2]<=cap,'sample join metadata bound exceeded')
            raw=stream.read(cap+1);sha=hashlib.sha256(raw).hexdigest()
            require(len(raw)==sig[2] and (expected is None or sha==expected)
                and (old is None or sha==old[0]),'sample join metadata changed')
        value=json.loads(raw,object_pairs_hook=reader.unique_object,
            parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite metadata')))
        snapshots[path]=(sha,sig);return value
    def registered(name):
        require(type(name) is str and name in ad.inputs,'registered sample artifact input required')
        info=ad.inputs[name];return read(ad.root/info['path'],info['sha256'])
    claim=read(directory/'claim.json');plan=registered(claim['plan_input']);job=registered('execution_job')
    item=plan.get('producers',{}).get(record['producer'])
    selected=job.get('payload',{}).get('representation_jobs',{}).get(record['representation'])
    require(isinstance(item,dict) and isinstance(selected,dict)
        and item.get('sample_artifact_input')==selected.get('sample_artifact_input')==artifact_input,
        'selected sample artifact policy route differs')
    policy=registered(artifact_input)
    require(isinstance(policy,dict) and set(policy)=={'schema_version','max_manifest_bytes','max_artifact_bytes','max_array_bytes','max_journal_events'}
        and type(policy['schema_version']) is int and policy['schema_version']==1,'sample artifact policy schema differs')
    require(all(type(policy[k]) is int and policy[k]>0 for k in policy if k!='schema_version')
        and policy['max_manifest_bytes']<=reader.MANIFEST_LIMIT and policy['max_array_bytes']>=2,'positive bounded sample artifact policy required')
    require(type(event_index) is int and event_index==0,'explicit first sample event required')
    require(isinstance(event_sha256,str) and reader.re.fullmatch('[0-9a-f]{64}',event_sha256),'exact sample event hash required')
    expected_owner={k:record[k] for k in ('experiment','source_commit','producer','workflow_identity')}
    require(journal.directory==directory and equal(journal.owner,expected_owner),'current feature journal owner/directory differs')
    require(journal.parent is None and bound._ancestry_arguments is None,'historical sample reuse needs separate admission')
    required=sorted(route.descriptor['required_graphs']);policy_sha=ad.inputs[artifact_input]['sha256']
    def events():
        require(journal.directory==directory and not journal.sealed and journal.parent is None and journal.identity==record['workflow_identity']
            and equal(journal.owner,expected_owner) and journal.required==required,'current feature journal changed')
        require(0<len(journal.records)<=policy['max_journal_events'],'feature event budget exceeded')
        expected={directory/n for n in ('owner.json','start.json','claim.json')}
        for i in range(len(journal.records)):
            expected.update((directory/f'event-{i:06d}.json',directory/f'checkpoint-{i:06d}'))
        reader.inventory(directory,expected)
        require(equal(read(directory/'owner.json'),expected_owner),'stored feature owner differs')
        start=read(directory/'start.json')
        require(equal(start.get('owner'),expected_owner) and start.get('parent') is None
            and start.get('workflow_identity') is None and start.get('required_graphs')==required,'stored first-owner start differs')
        require(equal(read(directory/'claim.json').get('owner'),expected_owner),'stored feature claim owner differs')
        sample_events=[];chosen=None
        for i,entry in enumerate(journal.records):
            value=read(directory/f'event-{i:06d}.json',event_sha256 if i==event_index else None,policy['max_manifest_bytes'])
            require(equal(value,entry) and set(value)=={'stage','context','path','sha256','binding'}
                and value['stage'] in feature_journal.STAGES and value['context'].get('workflow_identity')==record['workflow_identity']
                and value['path']==f'checkpoint-{i:06d}/manifest.json','feature event identity differs')
            expected_binding={'owner':expected_owner,'stage':value['stage'],'context':value['context']}
            require(equal(value['binding'],expected_binding),'feature event binding differs')
            if value['stage']=='samples_complete':sample_events.append(i)
            if i==event_index:chosen=value
        require(sample_events==[event_index],'ambiguous or absent published sample event')
        return chosen
    event=events();context=event['context']
    require(set(context)=={'workflow_identity','sample_identity','pair_workload_sha256','artifact_policy_sha256'}
        and context['pair_workload_sha256']==route.descriptor['pair_workload']['sha256']
        and context['artifact_policy_sha256']==policy_sha,'sample publication context differs')
    component=directory/event['path'];cap=policy['max_array_bytes']//2
    manifest,signatures,headers,files=reader.inspect_component(component,event['sha256'],event['binding'],ad.root,
        policy['max_manifest_bytes'],policy['max_artifact_bytes'],cap)
    require(sample_shape(manifest,route)==context['sample_identity'],'published sample identity differs')
    def lease():
        owned.lease();sources(owned)
        for path,(sha,sig) in tuple(snapshots.items()):read(path,sha)
        require(equal(events(),event),'selected sample event changed')
        reader.inventory(component.parent,files)
        for path,sig in signatures.items():
            require(path.resolve()==path and reader.signature(path.lstat())==sig,'sample component changed')
        owned.lease()
    payload=reader.read_component(component,event['sha256'],event['binding'],root=ad.root,
        max_manifest_bytes=policy['max_manifest_bytes'],max_artifact_bytes=policy['max_artifact_bytes'],
        max_array_bytes=cap,lease=lease)
    samples=serialization.samples_from_record(payload)
    scope=route.sample_scope(samples)
    lease()
    receipt={'schema_version':1,'owner':thaw(record),'event':{'path':str(directory/'event-000000.json'),'sha256':event_sha256},
        'component':{'path':str(component),'sha256':event['sha256']},'artifact_input':artifact_input,
        'artifact_policy_sha256':policy_sha,'sample_identity':samples.identity,'workload_sha256':scope}
    return AdmittedSamples(samples,scope,receipt,lease)
