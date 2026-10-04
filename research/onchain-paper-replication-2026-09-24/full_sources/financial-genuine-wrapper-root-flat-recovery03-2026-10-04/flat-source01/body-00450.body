"""First-owner dictionary publication; historical/reuse admission is separate."""
import importlib.util
import os
from pathlib import Path
from tradingagents.research.onchain_replication.provenance import canonical_bytes,file_hash,thaw,durable_mkdir,sync_directory
from tradingagents.research.onchain_replication import serialization

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
spec=importlib.util.spec_from_file_location('dictionary_publication_driver',HERE/'driver.py')
driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
producer=driver.proof.producer;reader=producer.artifacts.reader
SOURCES=tuple(sorted(set(driver.SOURCES)|{str(Path(p).relative_to(ROOT)) for p in (__file__,serialization.__file__)}))

def require(value,message):
    if not value:raise ValueError(message)
def equal(a,b):return canonical_bytes(a)==canonical_bytes(b)

def attempt_directory(owned):
    bound=owned.workload.bound
    return bound._run.admission.root/'research_artifacts/onchain_dictionary_workflows'/bound.record['workflow_identity']/bound.record['experiment']

def numeric_record(dictionary):
    result={name:thaw(getattr(dictionary,name)) for name in ('memberships','sample_hash','training_graph_hashes','config','matching_config_hash','identity','hierarchy')}
    result['representatives']=[{'node_ids':g.node_ids,'node_features':g.node_features,'edge_index':g.edge_index,
        'edge_features':g.edge_features,'edge_width':g.edge_features.shape[1],'parent_hash':g.parent_hash,'center_id':g.center_id}
        for g in dictionary.representatives]
    return result

def produce(owned,journal,*,sampler_input,artifact_input,proof_sha256,output_input):
    require(type(owned) is driver.artifacts.consumer.ownership.OwnedJournal
        and type(journal) is driver.artifacts.feature_journal.FeatureJournal,'actual dictionary owner/journal required')
    route=owned.workload;bound=route.bound;bound.check();owned.lease()
    require(bound._ancestry_arguments is None,'historical dictionary production needs separate admission')
    ad=bound._run.admission;owner=thaw(bound.record);directory=Path(owner['journal_directory'])
    attempt=attempt_directory(owned);metadata=producer.Metadata(ad.root);written={};published=False;admitted=None;component_state=None
    expected_owner={k:owner[k] for k in ('experiment','source_commit','producer','workflow_identity')}
    def sources():
        for name in SOURCES:
            sha=ad.experiment['source_files'].get(name)
            require(sha is not None and file_hash(ROOT/name)==sha and file_hash(ad.root/name)==sha,'dictionary publication source differs')
    sources()
    def registered(name):
        require(type(name) is str and name in ad.inputs,'registered dictionary output input required')
        info=ad.inputs[name];return metadata.read(ad.root/info['path'],info['sha256'])
    claim=metadata.read(directory/'claim.json');plan=registered(claim['plan_input']);job=registered('execution_job')
    item=plan.get('producers',{}).get(owner['producer']);selected=job.get('payload',{}).get('representation_jobs',{}).get(owner['representation'])
    require(isinstance(item,dict) and isinstance(selected,dict)
        and item.get('dictionary_output_input')==selected.get('dictionary_output_input')==output_input,'dictionary output route differs')
    policy=registered(output_input)
    require(isinstance(policy,dict) and set(policy)=={'schema_version','max_metadata_bytes','max_manifest_bytes',
        'max_artifact_bytes','max_attempt_bytes','max_sample_matrix_array_bytes'}
        and type(policy['schema_version']) is int and policy['schema_version']==1
        and all(type(policy[k]) is int and policy[k]>0 for k in policy if k!='schema_version')
        and max(policy['max_metadata_bytes'],policy['max_manifest_bytes'])<=reader.MANIFEST_LIMIT,'dictionary output policy differs')
    cap=policy['max_metadata_bytes'];reserved=4*cap+policy['max_artifact_bytes']
    require(reserved<=policy['max_attempt_bytes'],'dictionary attempt reservation exceeded')
    sample_policy=registered(artifact_input)
    require(type(sample_policy.get('max_array_bytes')) is int and sample_policy['max_array_bytes']>0,'sample array allowance required')
    require(type(sample_policy.get('max_journal_events')) is int and sample_policy['max_journal_events']>=2,
        'registered journal allowance must include dictionary event')
    # Covers sample-reader numeric copies and all retained dictionary matrices.
    # Parents, pair workspace, NumPy/SciPy scratch and Python metadata are separate.
    require(sample_policy['max_array_bytes']+8*route.control['max_entries']<=policy['max_sample_matrix_array_bytes'],
        'sample/matrix numeric allowance exceeded before fit')
    require(driver.proof.valid_hash(proof_sha256),'explicit sampler proof hash required')
    sampler_path=producer.attempt_directory(owned)/'complete.json'
    sampler_policy=registered(sampler_input)
    metadata.read(sampler_path,proof_sha256,sampler_policy['max_metadata_bytes'])
    def lease():
        owned.lease();sources();metadata.lease()
        require(journal.directory==directory and equal(journal.owner,expected_owner)
            and journal.parent is None and not journal.sealed and journal.identity==owner['workflow_identity']
            and journal.required==sorted(route.descriptor['required_graphs'])
            and len(journal.records)==(2 if published else 1),'dictionary feature journal changed')
        if admitted is not None:admitted.lease()
        if written:
            reader.inventory(attempt,set(written))
            for path,sha in written.items():metadata.read(path,sha,cap)
        owned.lease()
        if component_state is not None:
            component,signatures,files=component_state
            reader.inventory(component.parent,files)
            for path,sig in signatures.items():
                require(path.resolve()==path and reader.signature(path.lstat())==sig,'published dictionary component changed')
    lease()
    require(attempt.resolve()==attempt and attempt.is_relative_to(ad.root),'dictionary attempt containment differs')
    if attempt.parent.exists():require(not any(attempt.parent.iterdir()),'dictionary workflow already reserved')
    durable_mkdir(attempt.parent);lease();attempt.mkdir(exist_ok=False);sync_directory(attempt.parent)
    require(attempt.stat().st_dev==ad.root.stat().st_dev,'dictionary attempt device differs')
    def write(name,value):
        raw=canonical_bytes(value);require(len(raw)<=cap,'dictionary metadata publication allowance exceeded')
        path=attempt/name
        with path.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        sync_directory(attempt);sha=file_hash(path);written[path]=sha;metadata.read(path,sha,cap)
        return {'path':str(path),'sha256':sha}
    try:
        start=write('start.json',{'schema_version':1,'status':'reserved','owner':owner,'resumable':False,
            'output_input':output_input,'output_policy_sha256':ad.inputs[output_input]['sha256'],
            'sampler_proof':{'path':str(sampler_path),'sha256':proof_sha256},
            'sources':{name:ad.experiment['source_files'][name] for name in SOURCES},'reserved_encoded_bytes':reserved})
        result=driver.fit(owned,journal,sampler_input=sampler_input,artifact_input=artifact_input,proof_sha256=proof_sha256)
        admitted=result.pop('_admitted_samples');lease()
        dictionary=result['dictionary'];payload=numeric_record(dictionary)
        sample_bytes=sum(producer.neighborhood_policy.sample_array_bytes(g) for g in admitted.samples.graphs)
        matrix_bytes=sum(block['matrix'].nbytes for block in result['matrices'])
        require(sample_bytes+matrix_bytes<=policy['max_sample_matrix_array_bytes'],'actual sample/matrix allowance exceeded')
        require(equal(result['sample_provenance'],admitted.record) and result['workload_sha256']==admitted.scope
            and dictionary.sample_hash==admitted.samples.identity
            and tuple(dictionary.training_graph_hashes)==tuple(admitted.samples.source_hashes),'dictionary sample/workload binding differs')
        context={'workflow_identity':owner['workflow_identity'],'dictionary_identity':dictionary.identity,
            'sample_provenance':result['sample_provenance'],'dictionary_workload_sha256':admitted.scope,
            'pair_workload_sha256':route.descriptor['pair_workload']['sha256'],
            'output_input':output_input,'output_policy_sha256':ad.inputs[output_input]['sha256']}
        binding={'owner':expected_owner,'stage':'dictionary_complete','context':context}
        event_template={'stage':'dictionary_complete','context':context,'path':'checkpoint-000001/manifest.json','sha256':'0'*64,'binding':binding}
        event_bytes=len(producer.lifecycle._encode(event_template))
        manifest_bytes,encoded,numeric=producer.encoded_size(payload,binding)
        require(event_bytes<=min(cap,policy['max_manifest_bytes'],sample_policy['max_manifest_bytes'])
            and manifest_bytes<=policy['max_manifest_bytes'] and encoded<=policy['max_artifact_bytes']
            and numeric<=policy['max_sample_matrix_array_bytes'],
            'dictionary event/component allowance exceeded before write')
        lease();journal('dictionary_complete',context,payload);published=True;lease()
        event_path=directory/'event-000001.json';event_sha=file_hash(event_path)
        event=metadata.read(event_path,event_sha,cap);component=directory/event['path']
        require(equal(event,event_template|{'sha256':event['sha256']})
            and equal(event,journal.records[1]),'dictionary published event differs')
        _,signatures,_,files=reader.inspect_component(component,event['sha256'],binding,ad.root,
            policy['max_manifest_bytes'],policy['max_artifact_bytes'],policy['max_sample_matrix_array_bytes'])
        component_state=(component,signatures,files)
        proof=write('complete.json',{'schema_version':1,'status':'complete','owner':owner,'resumable':False,
            'start':start,'output_input':output_input,'output_policy_sha256':ad.inputs[output_input]['sha256'],
            'dictionary_identity':dictionary.identity,'sample_provenance':result['sample_provenance'],
            'workload_sha256':admitted.scope,'event':{'path':str(event_path),'sha256':event_sha},
            'component':{'path':str(component),'sha256':event['sha256']},
            'encoded_artifact_bytes':encoded,'encoded_event_bytes':event_bytes,'dictionary_array_bytes':numeric,
            'sample_array_bytes':sample_bytes,'matrix_array_bytes':matrix_bytes})
        lease();return proof
    except BaseException as error:
        try:write('failed.json',{'schema_version':1,'status':'failed','owner':owner,'resumable':False,
            'reason_type':type(error).__name__,'reason':str(error)[:500]})
        except BaseException:pass
        raise
