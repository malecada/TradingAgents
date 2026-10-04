"""Registered first-attempt resident sampler publication, not empirical release.

Every existing attempt is refused, including partial/failed/complete attempts.
Logical encoded-byte reservations are not physical quotas or process RAM bounds.
Completion proof admission by future consumers and exact resume remain separate.
"""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import numpy as np
from tradingagents.research import lifecycle
from tradingagents.research.onchain_replication import component_store,neighborhoods,neighborhood_policy,array_neighborhoods
from tradingagents.research.onchain_replication.provenance import canonical_bytes,file_hash,thaw,durable_mkdir,sync_directory

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
artifacts=load('producer_sample_artifacts',HERE.parent/'sample-artifact-route-2026-10-01/route.py')
core=load('producer_leased_sampler',HERE.parent/'sampler-leased-core-2026-10-01/core.py')
SOURCES=tuple(sorted(set(artifacts.SOURCES)|{str(Path(p).relative_to(ROOT)) for p in
    (__file__,core.__file__,lifecycle.__file__,component_store.__file__,neighborhoods.__file__,neighborhood_policy.__file__,array_neighborhoods.__file__)}))

def require(value,message):
    if not value:raise ValueError(message)

def attempt_directory(owned):
    record=owned.workload.bound.record
    return owned.workload.bound._run.admission.root/'research_artifacts/onchain_sampler_workflows'/record['workflow_identity']/record['experiment']

def numeric_record(samples):
    return {'graphs':[{'node_ids':g.node_ids,'node_features':g.node_features,'edge_index':g.edge_index,
        'edge_features':g.edge_features,'edge_width':g.edge_features.shape[1],
        'parent_hash':g.parent_hash,'center_id':g.center_id} for g in samples.graphs],
        'records':thaw(samples.records),'source_hashes':samples.source_hashes,
        'rng_state':thaw(samples.rng_state),'seed':samples.seed,'identity':samples.identity}

def encoded_size(payload,binding):
    """Mirror numeric-only component encoding; hash placeholders have exact width."""
    arrays={};numeric=0
    def encode(value):
        nonlocal numeric
        if isinstance(value,np.ndarray):
            require(value.dtype in (np.dtype('float64'),np.dtype('int64')),'native sample numeric types required')
            header=io.BytesIO();np.lib.format.write_array_header_1_0(header,np.lib.format.header_data_from_array_1_0(value))
            name=f'array-{len(arrays):06d}.npy';numeric+=value.nbytes
            arrays[name]={'sha256':'0'*64,'bytes':len(header.getvalue())+value.nbytes,'shape':list(value.shape),'dtype':str(value.dtype)}
            return {'kind':'array','member':name}
        if isinstance(value,np.generic):value=value.item()
        if isinstance(value,dict):return {'kind':'dict','items':[[encode(k),encode(v)] for k,v in value.items()]}
        if isinstance(value,(list,tuple)):return {'kind':'tuple' if isinstance(value,tuple) else 'list','items':[encode(x) for x in value]}
        require(value is None or type(value) in (bool,str,int,float),'unsupported sample metadata')
        canonical_bytes(value);return {'kind':'scalar','value':value}
    tree=encode(payload)
    manifest=len(canonical_bytes({'schema_version':1,'context':binding,'tree':tree,'arrays':arrays}))
    return manifest,manifest+sum(a['bytes'] for a in arrays.values()),numeric

class Metadata:
    """Bounded immutable metadata snapshots retaining each admitted read ceiling."""
    def __init__(self,root):self.root=Path(root);self.snapshots={}
    def read(self,path,expected=None,cap=65536):
        require(type(cap) is int and 0<cap<=artifacts.reader.MANIFEST_LIMIT,'metadata read ceiling differs')
        path=Path(path);old=self.snapshots.get(path)
        require(old is None or old[2]==cap,'metadata read ceiling changed')
        with artifacts.reader.opened(path,self.root,None if old is None else old[1]) as (stream,sig):
            require(0<sig[2]<=cap,'sampler metadata cap exceeded')
            raw=stream.read(cap+1);sha=hashlib.sha256(raw).hexdigest()
            require(len(raw)==sig[2] and (expected is None or sha==expected)
                and (old is None or sha==old[0]),'sampler metadata changed')
        value=json.loads(raw,object_pairs_hook=artifacts.reader.unique_object,
            parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite metadata')))
        self.snapshots[path]=(sha,sig,cap);return value
    def lease(self):
        for path,(sha,sig,cap) in tuple(self.snapshots.items()):self.read(path,sha,cap)

def produce(owned,journal,*,sampler_input,artifact_input):
    require(type(owned) is artifacts.consumer.ownership.OwnedJournal
        and type(journal) is artifacts.feature_journal.FeatureJournal,'actual owner and feature journal required')
    route=owned.workload;bound=route.bound;ad=bound._run.admission;record=bound.record
    bound.check();owned.lease()
    directory=Path(record['journal_directory']);attempt=attempt_directory(owned)
    expected_owner={k:record[k] for k in ('experiment','source_commit','producer','workflow_identity')}
    metadata=Metadata(ad.root);read=metadata.read;written={};draws=[];published=False;admitted=None
    def registered(name):
        require(type(name) is str and name in ad.inputs,'registered sampler input required')
        info=ad.inputs[name];return read(ad.root/info['path'],info['sha256'])
    def sources():
        for name in SOURCES:
            expected=ad.experiment['source_files'].get(name)
            require(expected is not None and file_hash(ROOT/name)==expected
                and file_hash(ad.root/name)==expected,'sampler source not admitted or changed')
    sources()
    claim=read(directory/'claim.json');plan=registered(claim['plan_input']);job=registered('execution_job')
    item=plan.get('producers',{}).get(record['producer']);selected=job.get('payload',{}).get('representation_jobs',{}).get(record['representation'])
    require(isinstance(item,dict) and isinstance(selected,dict)
        and item.get('sampler_input')==selected.get('sampler_input')==sampler_input
        and item.get('sample_artifact_input')==selected.get('sample_artifact_input')==artifact_input,'selected sampler policy route differs')
    policy=registered(sampler_input);artifact=registered(artifact_input)
    require(set(policy)=={'schema_version','kernel','max_metadata_bytes','max_attempt_bytes','limits'}
        and type(policy['schema_version']) is int and policy['schema_version']==1
        and policy['kernel']=='resident-leased-v1','sampler policy schema differs')
    require(all(type(policy[k]) is int and policy[k]>0 for k in ('max_metadata_bytes','max_attempt_bytes'))
        and policy['max_metadata_bytes']<=artifacts.reader.MANIFEST_LIMIT,'sampler metadata/reservation caps differ')
    limits=policy['limits']
    require(isinstance(limits,dict) and set(limits)=={'schema_version','max_centers','max_direct_weight_bytes','neighborhood'}
        and type(limits['schema_version']) is int and limits['schema_version']==1
        and all(type(limits[k]) is int and limits[k]>0 for k in ('max_centers','max_direct_weight_bytes')),'sampler limits differ')
    require(neighborhood_policy.validate_neighborhood_policy(limits['neighborhood']) is not None,'bounded neighborhoods required')
    require(set(artifact)=={'schema_version','max_manifest_bytes','max_artifact_bytes','max_array_bytes','max_journal_events'}
        and type(artifact['schema_version']) is int and artifact['schema_version']==1
        and all(type(artifact[k]) is int and artifact[k]>0 for k in artifact if k!='schema_version')
        and artifact['max_manifest_bytes']<=artifacts.reader.MANIFEST_LIMIT and artifact['max_array_bytes']>=2,'artifact read policy differs')
    settings=thaw(route.settings);seed=route.descriptor['seed'];count=settings['sample_count']
    reserved=(count+4)*policy['max_metadata_bytes']+artifact['max_artifact_bytes']
    require(reserved<=policy['max_attempt_bytes'],'sampler encoded-byte reservation exceeded')
    require(bound._ancestry_arguments is None,'historical sampler continuation needs separate admission')
    require(artifacts.equal(read(directory/'owner.json'),expected_owner),'stored sampler feature owner differs')
    start=read(directory/'start.json')
    require(start.get('parent') is None and start.get('workflow_identity') is None
        and artifacts.equal(start.get('owner'),expected_owner)
        and start.get('required_graphs')==sorted(route.descriptor['required_graphs']),'stored first-owner start differs')
    def lease():
        owned.lease();sources()
        require(journal.directory==directory and not journal.sealed and journal.parent is None
            and artifacts.equal(journal.owner,expected_owner)
            and journal.required==sorted(route.descriptor['required_graphs']),'live sampler journal changed')
        if not published:
            require(not journal.records and journal.identity is None,'sampler needs empty first journal')
            artifacts.reader.inventory(directory,{directory/n for n in ('owner.json','start.json','claim.json')})
        elif admitted is not None:admitted.lease()
        metadata.lease()
        if written:
            require(attempt.resolve()==attempt and attempt.is_dir(),'sampler attempt directory changed')
            artifacts.reader.inventory(attempt,set(written))
            for path,sha in written.items():read(path,sha,policy['max_metadata_bytes'])
        owned.lease()
    lease()
    for h,g in route._graphs.items():require(neighborhoods.graph_hash(g)==h,'sampler parent graph changed')
    require(attempt.resolve()==attempt and attempt.is_relative_to(ad.root),'sampler attempt containment differs')
    if attempt.parent.exists():
        require(not any(attempt.parent.iterdir()),'sampler workflow already reserved')
    durable_mkdir(attempt.parent);lease();attempt.mkdir(exist_ok=False);sync_directory(attempt.parent)
    require(attempt.stat().st_dev==ad.root.stat().st_dev,'sampler attempt device differs')
    def write(name,value):
        raw=canonical_bytes(value)
        require(len(raw)<=policy['max_metadata_bytes'],'sampler metadata publication cap exceeded')
        path=attempt/name
        with path.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        sync_directory(attempt);sha=file_hash(path);written[path]=sha
        read(path,sha,policy['max_metadata_bytes']);return {'path':str(path),'sha256':sha}
    try:
        initial_rng=thaw(np.random.PCG64(seed).state)
        start_ref=write('start.json',{'schema_version':1,'status':'reserved','owner':thaw(record),
            'sampler_input':sampler_input,'sampler_policy_sha256':ad.inputs[sampler_input]['sha256'],
            'artifact_input':artifact_input,'artifact_policy_sha256':ad.inputs[artifact_input]['sha256'],
            'sources':{n:ad.experiment['source_files'][n] for n in SOURCES},
            'configuration_sha256':core.cache_key(settings),'seed':seed,'rng_initial':initial_rng,
            'reserved_encoded_bytes':reserved,'resumable':False})
        last_rng=initial_rng;previous=None
        def checkpoint(event):
            nonlocal last_rng,previous
            lease();value=thaw(event);sha=value.pop('sha256')
            require(value['index']==len(draws) and value['previous_sha256']==previous
                and core.cache_key(value)==sha and artifacts.equal(value['rng_before'],last_rng)
                and value['configuration_sha256']==core.cache_key(settings) and value['seed']==seed,'sampler draw evidence differs')
            draws.append(write(f'draw-{len(draws):06d}.json',thaw(event)))
            previous=sha;last_rng=value['rng_after'];lease()
        samples=core.sample(tuple(route._graphs.values()),settings,seed,policy=limits,lease=lease,checkpoint=checkpoint)
        require(len(draws)==count and artifacts.equal(samples.rng_state,last_rng),'sampler final RNG/draw count differs')
        route.sample_scope(samples);lease()
        payload=numeric_record(samples)
        context={'workflow_identity':record['workflow_identity'],'sample_identity':samples.identity,
            'pair_workload_sha256':route.descriptor['pair_workload']['sha256'],
            'artifact_policy_sha256':ad.inputs[artifact_input]['sha256']}
        binding={'owner':expected_owner,'stage':'samples_complete','context':context}
        event_bytes=len(lifecycle._encode({'stage':'samples_complete','context':context,
            'path':'checkpoint-000000/manifest.json','sha256':'0'*64,'binding':binding}))
        require(event_bytes<=min(policy['max_metadata_bytes'],artifact['max_manifest_bytes']),
            'sample event publication cap exceeded before write')
        manifest_bytes,artifact_bytes,numeric_bytes=encoded_size(payload,binding)
        require(manifest_bytes<=artifact['max_manifest_bytes'] and artifact_bytes<=artifact['max_artifact_bytes']
            and 2*numeric_bytes<=artifact['max_array_bytes'],'sample publication byte cap exceeded before write')
        lease();journal('samples_complete',context,payload);published=True
        training_hashes=samples.source_hashes
        del samples,payload # Release original numeric payload before the strict reader's two-copy load.
        event_path=directory/'event-000000.json';event_sha=file_hash(event_path)
        admitted=artifacts.admit_samples(owned,journal,artifact_input=artifact_input,event_index=0,event_sha256=event_sha)
        lease()
        proof=write('complete.json',{'schema_version':1,'status':'complete','owner':thaw(record),'start':start_ref,
            'draws':draws,'last_draw_sha256':previous,'rng_initial':initial_rng,'rng_final':last_rng,
            'sample_identity':context['sample_identity'],'training_graphs':training_hashes,
            'sampler_input':sampler_input,'sampler_policy_sha256':ad.inputs[sampler_input]['sha256'],
            'artifact_input':artifact_input,'artifact_policy_sha256':ad.inputs[artifact_input]['sha256'],
            'event':{'path':str(event_path),'sha256':event_sha},'component':thaw(admitted.record['component']),
            'encoded_artifact_bytes':artifact_bytes,'encoded_event_bytes':event_bytes,'resident_sample_bytes':numeric_bytes,'resumable':False})
        lease() # A failure here retains complete+failed; proof admission must reject that conflict.
        return {'admitted':admitted,'proof':proof}
    except BaseException as error:
        # Preserve partial files even if failure publication itself cannot finish.
        try:write('failed.json',{'schema_version':1,'status':'failed','owner':thaw(record),
            'completed_draws':len(draws),'reason_type':type(error).__name__,'reason':str(error)[:500],'resumable':False})
        except BaseException:pass
        raise
