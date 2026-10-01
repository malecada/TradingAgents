"""Explicit guarded reuse of completed native representations; no producer replay.

Historical roots retain their original canonical paths. Every source transition
is registered; only the reviewed job dispatch bridge may replace an old library.
This consumer never reopens an old representation/pair owner or neural fit.
"""
from functools import lru_cache
import importlib.util
import json
from pathlib import Path
from . import job,matching_owner,native_producer
from .environment import inventory
from .feature_pipeline import PreparedFeatures
from .provenance import canonical_bytes,file_hash,freeze,thaw
from ..lifecycle import ResearchRun

ROOT=Path(__file__).resolve().parents[3]
PREFIX='research/onchain-paper-replication-2026-09-24/full_sources/'
SELF=str(Path(__file__).resolve().relative_to(ROOT))
BRIDGE='tradingagents/research/onchain_replication/job_payload.py'
BACKEND='terminal-native-reuse-v1'
READERS=(PREFIX+'cold-native-science-2026-10-01/science.py',PREFIX+'cold-native-publication-2026-10-01/publication.py',PREFIX+'cold-native-history-2026-10-01/terminal.py')
FIELDS={'operation','native_backend','reuse_input','source_transition_input','native_feature_batch_input','population','descriptor','binding_output'}
LIMITS={'max_metadata_bytes','max_total_bytes','max_records','max_dictionary_bytes','max_source_files','max_source_file_bytes','max_source_bytes','max_inventory_entries'}

def require(value,message):
    if not value:raise ValueError(message)
def equal(a,b):return canonical_bytes(a)==canonical_bytes(b)
@lru_cache(maxsize=1)
def api():
    spec=importlib.util.spec_from_file_location('registered_native_reuse_science',ROOT/READERS[0]);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def required_sources():return set(job.required_sources())|native_producer.required_sources()|set(READERS)|{SELF}

def selected(run,representation,route):
    require(isinstance(run,ResearchRun),'actual admitted native reuse run required');run._active()
    if route.get('native_backend')!=BACKEND:return False
    require(set(route)==FIELDS and route['operation']=='reuse','explicit native reuse route differs')
    execution=json.loads(run.read_input('execution_job'))
    require(execution['kind']=='fit' and equal(execution['payload']['representation_jobs'].get(representation),route),'registered native reuse selection differs')
    require(route['binding_output'] in run.admission.experiment['outputs'] and route['descriptor']['arm']=='proposed','registered native reuse output/arm differs')
    for key in ('reuse_input','source_transition_input','native_feature_batch_input'):run.read_input(route[key])
    return True

def _sources(run,old_root,old_claim,transition,limits):
    require(type(transition) is dict and set(transition)=={'schema_version','replacements','additions'}
        and type(transition['schema_version']) is int and transition['schema_version']==1,'source transition schema differs')
    old=old_claim['experiment']['source_files'];current=run.admission.experiment['source_files']
    libraries={n for n in old if n.endswith('.py') and n.startswith(('tradingagents/',PREFIX))}
    required=required_sources()|libraries
    require(required<=set(current) and 2*len(required)+len(libraries)<=limits['max_source_files'],'current reader source closure missing or too large')
    changed={n for n in libraries if old[n]!=current[n]}
    require(changed<= {BRIDGE} and set(transition['replacements'])==changed,'unapproved numerical source transition')
    require(equal(transition['additions'],{n:current[n] for n in required-libraries}),'current reader additions differ')
    for name in changed:
        require(equal(transition['replacements'][name],{'before':old[name],'after':current[name]}),'exact source transition hashes differ')
    reader=api().pub.native.reader;records=[];total=0
    for root,names,hashes in ((old_root,libraries,old),(run.admission.root,required,current),(ROOT,required,current)):
        for name in sorted(names):
            path=root/name
            with reader.opened(path,root) as (stream,sig):
                require(sig[2]<=limits['max_source_file_bytes'] and total+sig[2]<=limits['max_source_bytes'],'source byte allowance exceeded')
                require(reader.digest_stream(stream,sig[2])==hashes[name],'registered library bytes differ: '+name)
            total+=sig[2];records.append((root,path,sig,hashes[name]))
    def lease():
        for root,path,sig,sha in records:
            with reader.opened(path,root,sig) as (stream,_):
                require(reader.digest_stream(stream,sig[2])==sha,'reader source changed')
    lease();return lease

def _historical_lease(root,previous,seal,read,pins,limit):
    """Derive allowed names from admitted declarations, never observed contents."""
    owner=seal['owner'];experiment=owner['experiment'];identity=owner['workflow_identity']
    artifacts=root/'research_artifacts';journal=Path(owner['journal_directory'])
    feature=read(seal['feature_terminal']);publication=read(seal['publication'])
    inventories={root/'research_runs'/experiment/'outputs':set(previous['terminal']['output_sha256']),
        journal:{'owner.json','start.json','claim.json','complete.json'}
            |{f'event-{i:06d}.json' for i in range(len(feature['events']))}
            |{f'checkpoint-{i:06d}' for i in range(len(feature['events']))}}
    for kind in ('onchain_representation_seals','onchain_representation_publications','onchain_dictionary_workflows'):
        inventories[artifacts/kind/identity/experiment]={'start.json','complete.json'}
    for h in publication['closure']['graphs']:
        inventories[artifacts/'onchain_graph_feature_workflows'/identity/experiment/h]={'start.json','complete.json'}
    for path,(_,value) in pins.items():
        if path.is_relative_to(artifacts) and path.name=='manifest.json' and 'arrays' in value:
            inventories[path.parent]={'manifest.json'}|set(value['arrays'])
    require(sum(map(len,inventories.values()))<=limit,'historical inventory allowance exceeded')
    failures={root/'research_runs'/experiment,artifacts/'onchain_pair_workflows'/identity/experiment}|set(inventories)
    def lease():
        for directory,names in inventories.items():
            require(directory.resolve()==directory and directory.is_dir(),'historical directory identity differs')
            api().pub.history._output_inventory(directory,names)
        for directory in failures:
            for name in ('failed.json','attempt-failed.json'):
                marker=directory/name
                require(not marker.exists() and not marker.is_symlink(),'historical lifecycle conflict')
    lease();return lease

def prepare(run,representation,route,examples,scaler):
    require(selected(run,representation,route),'native reuse must be explicitly selected')
    run._check_source();ad=run.admission;science=api();history=science.pub.history;reader=science.pub.native.reader
    reference=json.loads(run.read_input(route['reuse_input']))
    require(type(reference) is dict and set(reference)=={'schema_version','historical_root','history','seal','limits'}
        and type(reference['schema_version']) is int and reference['schema_version']==1,'native reuse reference schema differs')
    limits=reference['limits']
    require(type(limits) is dict and set(limits)==LIMITS and all(type(n) is int and n>0 for n in limits.values()),'native reuse limits differ')
    old_root=Path(reference['historical_root'])
    require(old_root.is_absolute() and old_root.resolve()==old_root and old_root.is_dir(),'original canonical historical root required')
    require(not (old_root==ad.root and reference['history']['experiment']==ad.experiment_id),'current run cannot be its own historical producer')
    execution=json.loads(run.read_input('execution_job'));policy=execution['resources'];base=ad.root/job.PREFIX/'runs'/ad.experiment_id
    require(str(old_root) in policy['disk_paths'],'current guard must cover historical artifact volume')
    signatures={};guard_owner,owner_sha,_=history._read_metadata(ad.root,base/'owner.json',signatures,max_bytes=65536)
    require(guard_owner['experiment']==ad.experiment_id and guard_owner['source_commit']==ad.source,'current guard owner differs')
    def guard():
        run._active();history._read_metadata(ad.root,base/'owner.json',signatures,owner_sha,max_bytes=65536)
        matching_owner._guard(run,policy,guard_owner,base)
    guard()
    require(inventory(ad.root,include_torch=True)==json.loads(run.read_input(execution['environment_input'])),'current runtime inventory differs')
    arguments={k:limits[k] for k in ('max_metadata_bytes','max_total_bytes','max_records')}
    previous=history.inspect(old_root,reference['history'],**arguments)
    source_lease=_sources(run,old_root,previous['claim'],json.loads(run.read_input(route['source_transition_input'])),limits)
    guard()
    checked=science.inspect(old_root,reference['history'],reference['seal'],expected_descriptor=route['descriptor'],
        examples=examples,scaler=scaler,max_dictionary_bytes=limits['max_dictionary_bytes'],**arguments)
    metadata_signatures={};pins={}
    for pin in checked['records']:
        path=Path(pin['path']);value,_,_=history._read_metadata(old_root,path,metadata_signatures,pin['sha256'],max_bytes=pin['bytes'])
        pins[path]=(dict(pin),value)
    def read(ref):
        path=Path(ref['path']);require(path in pins and pins[path][0]['sha256']==ref['sha256'],'unadmitted native metadata reference')
        return pins[path][1]
    seal=read(reference['seal']);publication=read(seal['publication']);binding=thaw(checked['binding'])
    settings=science.pub.native.policy(json.loads(run.read_input(route['native_feature_batch_input'])))
    refs={}
    old_inputs=previous['claim']['experiment']['inputs']
    for h,record in publication['closure']['graphs'].items():
        event=read(record['event']);manifest=read(record['component']);output_info=old_inputs[event['context']['output_input']]
        output=read({'path':str(old_root/output_info['path']),'sha256':output_info['sha256']})
        nodes,motifs=manifest['arrays']['array-000000.npy']['shape']
        refs[h]={'path':record['component']['path'],'sha256':record['component']['sha256'],'context':event['binding'],
            'nodes':nodes,'motifs':motifs,'edge_shape':manifest['arrays']['array-000001.npy']['shape'],'feature_hash':binding['feature_hashes'][h],
            'max_manifest_bytes':output['max_manifest_bytes'],'max_artifact_bytes':output['max_artifact_bytes']}
    historical_lease=_historical_lease(old_root,previous,seal,read,pins,limits['max_inventory_entries'])
    fixed_population=canonical_bytes(science.population_record(examples,scaler));fixed_route=canonical_bytes(route)
    def lease():
        guard();source_lease()
        require(canonical_bytes(route)==fixed_route and canonical_bytes(science.population_record(examples,scaler))==fixed_population,'native consumer scientific inputs changed')
        for name in ('execution_job',route['reuse_input'],route['source_transition_input'],route['native_feature_batch_input']):run.read_input(name)
        for path,(pin,_) in pins.items():history._read_metadata(old_root,path,metadata_signatures,pin['sha256'],max_bytes=pin['bytes'])
        historical_lease()
        guard()
    result=science.pub.native._NativeMap(old_root,refs,settings,lease=lease,read_lease=guard)
    require(result.verified_hashes()==binding['feature_hashes'],'native reused content differs')
    lease()
    return PreparedFeatures(result,binding,None)
