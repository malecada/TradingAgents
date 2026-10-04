"""Exclusive current-owner graph completion with native fixed-feature storage.

Saved reuse requires an explicit admitted tensor materializer. Publication alone
does not close the representation or admit model fits, historical or mapped work.
"""
import importlib.util
import io
import os
from pathlib import Path
import numpy as np
from tradingagents.research.onchain_replication.provenance import canonical_bytes,digest,file_hash,thaw,durable_mkdir,sync_directory

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
spec=importlib.util.spec_from_file_location('graph_publication_route',HERE.parent/'graph-feature-route-2026-10-01/route.py')
route=importlib.util.module_from_spec(spec);spec.loader.exec_module(route)
saved=route.saved;reader=saved.reader;producer=saved.producer
spec=importlib.util.spec_from_file_location('graph_encoded_hashes',HERE/'encoded_hashes.py')
encoded_hashes=importlib.util.module_from_spec(spec);spec.loader.exec_module(encoded_hashes)
SOURCES=tuple(sorted(set(route.SOURCES)|{str(Path(p).relative_to(ROOT)) for p in (__file__,encoded_hashes.__file__)}))
require=saved.require;equal=saved.equal

def component_manifest(feature,binding,expected_arrays=None):
    require(type(feature) is dict and set(feature)=={'mcm','edge_index'},'exact native graph feature keys required')
    a=feature['mcm'];e=feature['edge_index']
    require(type(a) is np.ndarray and a.dtype==np.dtype('float32') and a.ndim==2 and all(n>0 for n in a.shape)
        and type(e) is np.ndarray and e.dtype==np.dtype('int64') and e.ndim==2 and e.shape[0]==2,'native graph feature arrays required')
    arrays={};items=[];numeric=0
    def scalar(value):return {'kind':'scalar','value':value}
    for key,array in (('mcm',a),('edge_index',e)):
        header=io.BytesIO();np.lib.format.write_array_header_1_0(header,np.lib.format.header_data_from_array_1_0(array))
        name=f'array-{len(arrays):06d}.npy';size=len(header.getvalue())+array.nbytes;numeric+=array.nbytes
        arrays[name]={'sha256':'0'*64,'bytes':size,'shape':list(array.shape),'dtype':str(array.dtype)}
        items.append([scalar(key),{'kind':'array','member':name}])
    tree={'kind':'dict','items':[[scalar('feature'),{'kind':'dict','items':items}],[scalar('aligned_vectors'),scalar(None)]]}
    manifest={'schema_version':1,'context':binding,'tree':tree,'arrays':arrays}
    if expected_arrays is not None:
        require(set(expected_arrays)==set(arrays) and all(
            {k:v for k,v in expected_arrays[name].items() if k!='sha256'}=={k:v for k,v in info.items() if k!='sha256'}
            for name,info in arrays.items()),'expected graph array descriptors differ')
        manifest['arrays']=expected_arrays
    return manifest

def encoded_size(feature,binding):
    manifest=component_manifest(feature,binding);size=len(canonical_bytes(manifest))
    return size,size+sum(v['bytes'] for v in manifest['arrays'].values()),sum(a.nbytes for a in feature.values())

def attempt_directory(owned,graph_hash):
    require(saved.artifacts.publication.driver.proof.valid_hash(graph_hash),'exact graph hash required')
    bound=owned.workload.bound
    return bound._run.admission.root/'research_artifacts/onchain_graph_feature_workflows'/bound.record['workflow_identity']/bound.record['experiment']/graph_hash

def produce(owned,journal,*,dictionary_ticket,graph_hash,mcm_input,mcm_output_input,read_input,mcm_proof_sha256,feature_input,output_input):
    saved.actual_owner(owned,journal);workload=owned.workload;bound=workload.bound;ad=bound._run.admission
    owner=thaw(bound.record);directory=Path(owner['journal_directory'])
    require(type(graph_hash) is str and graph_hash in workload.descriptor['required_graphs'] and graph_hash in workload._graphs,
        'required graph publication membership differs')
    graph=workload._graphs[graph_hash];numeric=4*len(graph.node_ids)*workload.settings['size']+graph.edge_index.nbytes
    metadata=producer.Metadata(ad.root);attempt=attempt_directory(owned,graph_hash);written={}
    published=False;receipt=None;component_state=None;prefix=thaw(journal.records);index=len(prefix)
    expected_owner={k:owner[k] for k in ('experiment','source_commit','producer','workflow_identity')}
    def sources():
        for name in SOURCES:
            sha=ad.experiment['source_files'].get(name)
            require(sha is not None and file_hash(ROOT/name)==sha and file_hash(ad.root/name)==sha,'graph publication source differs')
    sources()
    def registered(name):
        require(type(name) is str and name in ad.inputs,'registered graph output input required')
        info=ad.inputs[name];return metadata.read(ad.root/info['path'],info['sha256'])
    claim=metadata.read(directory/'claim.json');plan=registered(claim['plan_input']);job=registered('execution_job')
    item=plan.get('producers',{}).get(owner['producer']);selected=job.get('payload',{}).get('representation_jobs',{}).get(owner['representation'])
    require(isinstance(item,dict) and isinstance(selected,dict)
        and item.get('graph_output_input')==selected.get('graph_output_input')==output_input,'selected graph output route differs')
    policy=registered(output_input)
    require(isinstance(policy,dict) and set(policy)=={'schema_version','max_metadata_bytes','max_manifest_bytes',
        'max_artifact_bytes','max_attempt_bytes','max_array_bytes','max_journal_events'}
        and type(policy['schema_version']) is int and policy['schema_version']==1
        and all(type(v) is int and v>0 for k,v in policy.items() if k!='schema_version')
        and max(policy['max_metadata_bytes'],policy['max_manifest_bytes'])<=reader.MANIFEST_LIMIT,'graph output policy differs')
    cap=policy['max_metadata_bytes'];reserved=4*cap+policy['max_artifact_bytes']
    require(reserved<=policy['max_attempt_bytes'] and numeric<=policy['max_array_bytes'],'graph output allowance exceeded')
    require(index<policy['max_journal_events'],'graph event allowance exceeded before preparation')
    require(not attempt.exists(),'graph output attempt already reserved')
    require(not any(e['stage']=='representation_complete' or (e['stage'] in ('embedding_progress','graph_complete')
        and e['context'].get('graph_hash')==graph_hash) for e in prefix),'graph already has downstream progress')
    pin=saved.ticket_lease(dictionary_ticket,owned,journal)
    sample_policy=registered(pin['inputs']['artifact']['input'])
    require(index<sample_policy['max_journal_events'],'upstream journal event allowance exceeded')
    event_path=directory/f'event-{index:06d}.json';component=directory/f'checkpoint-{index:06d}/manifest.json'
    require(not event_path.exists() and not component.parent.exists(),'graph event slot already reserved')
    for i,event in enumerate(prefix):
        require(equal(metadata.read(directory/f'event-{i:06d}.json',cap=sample_policy['max_manifest_bytes']),event),'prior graph journal event differs')
    mcm_path=saved.publication.attempt_directory(owned,graph_hash)/'complete.json'
    require(saved.artifacts.publication.driver.proof.valid_hash(mcm_proof_sha256),'explicit saved MCM proof required')
    mcm_output_policy=registered(mcm_output_input)
    require(isinstance(mcm_output_policy,dict) and type(mcm_output_policy.get('max_metadata_bytes')) is int
        and 0<mcm_output_policy['max_metadata_bytes']<=reader.MANIFEST_LIMIT,'selected MCM metadata cap differs')
    metadata.read(mcm_path,mcm_proof_sha256,mcm_output_policy['max_metadata_bytes'])
    def lease():
        owned.lease();sources();metadata.lease()
        require(journal.directory==directory and equal(journal.owner,expected_owner) and journal.parent is None and not journal.sealed
            and journal.identity==owner['workflow_identity'] and journal.required==sorted(workload.descriptor['required_graphs'])
            and len(journal.records)==index+int(published) and equal(journal.records[:index],prefix),'graph publication journal changed')
        if receipt is not None:receipt.lease()
        if written:
            reader.inventory(attempt,set(written))
            for path,sha in written.items():metadata.read(path,sha,cap)
        owned.lease()
        if component_state is not None:
            signatures,files=component_state;reader.inventory(component.parent,files)
            for path,sig in signatures.items():require(path.resolve()==path and reader.signature(path.lstat())==sig,'published graph component changed')
    lease();require(attempt.resolve()==attempt and attempt.is_relative_to(ad.root),'graph output containment differs')
    durable_mkdir(attempt.parent);lease();attempt.mkdir(exist_ok=False);sync_directory(attempt.parent)
    require(attempt.stat().st_dev==ad.root.stat().st_dev,'graph output device differs')
    def write(name,value):
        raw=canonical_bytes(value);require(len(raw)<=cap,'graph metadata allowance exceeded')
        path=attempt/name
        with path.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        sync_directory(attempt);sha=file_hash(path);written[path]=sha;metadata.read(path,sha,cap)
        return {'path':str(path),'sha256':sha}
    try:
        start=write('start.json',{'schema_version':1,'status':'reserved','owner':owner,'resumable':False,'graph_hash':graph_hash,
            'event_index':index,'mcm_proof':{'path':str(mcm_path),'sha256':mcm_proof_sha256},'feature_input':feature_input,
            'output_input':output_input,'output_policy_sha256':ad.inputs[output_input]['sha256'],
            'reserved_encoded_bytes':reserved,'sources':{name:ad.experiment['source_files'][name] for name in SOURCES}})
        receipt=route.prepare(owned,journal,dictionary_ticket=dictionary_ticket,graph_hash=graph_hash,mcm_input=mcm_input,
            output_input=mcm_output_input,read_input=read_input,proof_sha256=mcm_proof_sha256,feature_input=feature_input)
        lease();provenance=thaw(receipt.record)
        require(provenance['graph_hash']==graph_hash and provenance['tensor_bytes']==numeric
            and equal(provenance['mcm_provenance']['mcm_proof'],{'path':str(mcm_path),'sha256':mcm_proof_sha256}),
            'graph feature provenance differs')
        feature={k:receipt.feature[k].numpy() for k in ('mcm','edge_index')}
        context={'workflow_identity':owner['workflow_identity'],'graph_hash':graph_hash,
            'dictionary_hash':provenance['mcm_provenance']['dictionary_provenance']['dictionary_identity'],
            'fold_id':workload.descriptor['fold']['id'],'seed':workload.descriptor['seed'],'arm':workload.descriptor['arm'],
            'storage':'native_graph_feature_v1','feature_provenance':provenance,
            'output_input':output_input,'output_policy_sha256':ad.inputs[output_input]['sha256']}
        binding={'owner':expected_owner,'stage':'graph_complete','context':context}
        template={'stage':'graph_complete','context':context,'path':str(component.relative_to(directory)),'sha256':'0'*64,'binding':binding}
        event_bytes=len(producer.lifecycle._encode(template));manifest_bytes,encoded,actual_numeric=encoded_size(feature,binding)
        require(actual_numeric==numeric and manifest_bytes<=policy['max_manifest_bytes'] and encoded<=policy['max_artifact_bytes']
            and event_bytes<=min(cap,policy['max_manifest_bytes'],sample_policy['max_manifest_bytes']),
            'graph event/component allowance exceeded before write')
        tensor_policy=registered(feature_input)
        lease()
        expected_manifest=component_manifest(feature,binding,encoded_hashes.descriptors(feature,tensor_policy['chunk_entries']))
        expected_component_hash=digest(canonical_bytes(expected_manifest))
        lease();journal('graph_complete',context,{'feature':feature,'aligned_vectors':None});published=True;lease()
        event_sha=file_hash(event_path);event=metadata.read(event_path,event_sha,cap)
        require(equal(event,template|{'sha256':expected_component_hash}) and equal(event,journal.records[index]),'published graph event/content differs')
        manifest,signatures,_,files=reader.inspect_component(component,event['sha256'],binding,ad.root,
            policy['max_manifest_bytes'],policy['max_artifact_bytes'],policy['max_array_bytes'])
        require(equal(manifest,expected_manifest) and sum(sig[2] for sig in signatures.values())==encoded,'published graph component content/size differs')
        component_state=(signatures,files)
        proof=write('complete.json',{'schema_version':1,'status':'complete','owner':owner,'resumable':False,'start':start,
            'graph_hash':graph_hash,'event_index':index,'storage':'native_graph_feature_v1','feature_provenance':provenance,
            'output_input':output_input,'output_policy_sha256':ad.inputs[output_input]['sha256'],'array_bytes':numeric,
            'encoded_artifact_bytes':encoded,'encoded_event_bytes':event_bytes,
            'event':{'path':str(event_path),'sha256':event_sha},'component':{'path':str(component),'sha256':event['sha256']}})
        lease();return proof
    except BaseException as error:
        try:write('failed.json',{'schema_version':1,'status':'failed','owner':owner,'resumable':False,'graph_hash':graph_hash,
            'reason_type':type(error).__name__,'reason':str(error)[:500]})
        except BaseException:pass
        raise
