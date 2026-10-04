"""Current-owner dictionary proof/artifact admission, without matching or clustering."""
import importlib.util
import math
from pathlib import Path
import numpy as np
from tradingagents.research.onchain_replication.provenance import canonical_bytes,file_hash,freeze,thaw
from tradingagents.research.onchain_replication.matching_identity import graph_identity

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
spec=importlib.util.spec_from_file_location('dictionary_admission_publication',HERE.parent/'dictionary-publication-2026-10-01/publication.py')
publication=importlib.util.module_from_spec(spec);spec.loader.exec_module(publication)
reader=publication.reader;producer=publication.producer
SOURCES=tuple(sorted(set(publication.SOURCES)|{str(Path(__file__).relative_to(ROOT))}))

def require(value,message):
    if not value:raise ValueError(message)
def equal(a,b):return canonical_bytes(a)==canonical_bytes(b)

class Admitted:
    def __init__(self,dictionary,record,lease):self.dictionary=dictionary;self.record=freeze(record);self._lease=lease
    def lease(self):self._lease()


def membership(dictionary,samples,settings,matching,backend):
    """Validate fixed partition/owner structure, not recompute medoid objectives."""
    n=len(samples.graphs);k=settings['size']
    require(n==settings['sample_count'] and 0<k<=n,'dictionary population dimensions differ')
    require(equal(dictionary.config,settings|{'pair_execution':backend})
        and dictionary.matching_config_hash==producer.core.cache_key({'config':matching,'backend':backend})
        and dictionary.sample_hash==samples.identity
        and equal(dictionary.training_graph_hashes,samples.source_hashes),'dictionary settings/training binding differs')
    typed=[graph_identity(g) for g in samples.graphs]
    require(len(set(typed))==n,'ambiguous sample graph identities')
    lookup={h:i for i,h in enumerate(typed)};representatives=[]
    for graph in dictionary.representatives:
        h=graph_identity(graph);require(h in lookup,'dictionary representative outside sampled population')
        representatives.append(lookup[h])
    threshold=settings['partition_threshold'];chunk=settings['partition_size']
    require(type(threshold) is int and threshold>=k and type(chunk) is int and chunk>k,'dictionary partition bounds differ')
    def groups(selected,values,indices,owners,wanted):
        require(isinstance(selected,(list,tuple)) and len(selected)==wanted
            and all(type(x) is int for x in selected) and list(selected)==sorted(set(selected))
            and set(selected)<=set(indices),'ordered representative indices differ')
        require(isinstance(values,(list,tuple)) and len(values)==wanted,'dictionary group count differs')
        flattened=[]
        for center,group in zip(selected,values,strict=True):
            require(isinstance(group,(list,tuple)) and bool(group) and all(type(x) is int for x in group)
                and list(group)==sorted(set(group)),'dictionary group indices differ')
            members=set(group)
            require(set(owners[center])<=members,'representative not owned by its group')
            for index in indices:
                own=set(owners[index]);require(not own&members or own<=members,'hierarchy splits a prior group')
            flattened.extend(group)
        require(sorted(flattened)==sorted(j for i in indices for j in owners[i]),'dictionary groups omit or duplicate samples')
    indices=list(range(n));owners={i:[i] for i in indices};rng=np.random.Generator(np.random.PCG64(samples.seed))
    hierarchy=thaw(dictionary.hierarchy);position=0;matrices=set()
    while len(indices)>threshold:
        shuffled=list(rng.permutation(sorted(indices)));selected=[];next_owners={}
        for start in range(0,len(shuffled),chunk):
            part=sorted(map(int,shuffled[start:start+chunk]));matrices.add(tuple(part))
            require(position<len(hierarchy),'dictionary hierarchy incomplete')
            item=hierarchy[position];position+=1
            require(isinstance(item,dict) and set(item)=={'samples','representatives','original_memberships'}
                and equal(item['samples'],part),'dictionary partition order differs')
            centers=item['representatives'];expanded=item['original_memberships']
            groups(centers,expanded,part,owners,min(k,len(part)))
            selected.extend(centers);next_owners.update(zip(centers,expanded,strict=True))
        require(len(selected)<len(indices),'dictionary hierarchy does not reduce')
        indices=sorted(selected);owners=next_owners
    require(position==len(hierarchy),'dictionary hierarchy has an unused suffix')
    groups(representatives,dictionary.memberships,indices,owners,k);matrices.add(tuple(indices))
    return 8*sum(len(key)**2 for key in matrices)


def shape(manifest,settings):
    artifacts=producer.artifacts
    slots={name:artifacts.Slot(name,info) for name,info in manifest['arrays'].items()}
    value=reader.walk(manifest['tree'],manifest['arrays'],set(),slots)
    require(isinstance(value,dict) and set(value)=={'memberships','sample_hash','training_graph_hashes','config',
        'matching_config_hash','identity','hierarchy','representatives'},'dictionary artifact schema differs')
    graphs=value['representatives']
    require(isinstance(graphs,(list,tuple)) and len(graphs)==settings['size'],'dictionary representative count differs')
    used=set()
    for graph in graphs:
        require(isinstance(graph,dict) and set(graph)=={'node_ids','node_features','edge_index','edge_features','edge_width','parent_hash','center_id'},'dictionary graph schema differs')
        require(isinstance(graph['node_ids'],(list,tuple)) and bool(graph['node_ids'])
            and all(type(x) is str and x for x in graph['node_ids']),'dictionary node metadata differs')
        for field,dtype in (('node_features','float64'),('edge_index','int64'),('edge_features','float64')):
            slot=graph[field];require(type(slot) is artifacts.Slot and slot.dtype==dtype and len(slot.shape)==2,'native dictionary arrays required');used.add(slot.name)
        nodes,edges,features=(graph[x] for x in ('node_features','edge_index','edge_features'));width=graph['edge_width']
        require(type(width) is int and width>0 and nodes.shape[0]==len(graph['node_ids']) and nodes.shape[1]>0
            and edges.shape[0]==2 and features.shape==(edges.shape[1],width),'dictionary array dimensions differ')
    require(used==set(slots),'dictionary has unrelated arrays')
    return value


def admit(owned,journal,*,sampler_input,artifact_input,output_input,proof_sha256):
    require(type(owned) is producer.artifacts.consumer.ownership.OwnedJournal
        and type(journal) is producer.artifacts.feature_journal.FeatureJournal,'actual dictionary owner/journal required')
    route=owned.workload;bound=route.bound;bound.check();owned.lease()
    require(bound._ancestry_arguments is None,'historical dictionary reuse requires separate admission')
    ad=bound._run.admission;owner=thaw(bound.record);directory=Path(owner['journal_directory'])
    attempt=publication.attempt_directory(owned);metadata=producer.Metadata(ad.root)
    def sources():
        for name in SOURCES:
            sha=ad.experiment['source_files'].get(name)
            require(sha is not None and file_hash(ROOT/name)==sha and file_hash(ad.root/name)==sha,'dictionary admission source differs')
    sources()
    def registered(name):
        require(type(name) is str and name in ad.inputs,'registered dictionary admission input required')
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
    cap=policy['max_metadata_bytes'];require(publication.driver.proof.valid_hash(proof_sha256),'explicit dictionary proof hash required')
    proof_path=attempt/'complete.json';proof=metadata.read(proof_path,proof_sha256,cap)
    fields={'schema_version','status','owner','resumable','start','output_input','output_policy_sha256','dictionary_identity',
        'sample_provenance','workload_sha256','event','component','encoded_artifact_bytes','encoded_event_bytes',
        'dictionary_array_bytes','sample_array_bytes','matrix_array_bytes'}
    require(isinstance(proof,dict) and set(proof)==fields and type(proof['schema_version']) is int
        and proof['schema_version']==1 and proof['status']=='complete' and proof['resumable'] is False
        and equal(proof['owner'],owner) and proof['output_input']==output_input
        and proof['output_policy_sha256']==ad.inputs[output_input]['sha256'],'dictionary proof owner/policy/schema differs')
    require(all(type(proof[k]) is int and proof[k]>0 for k in ('encoded_artifact_bytes','encoded_event_bytes',
        'dictionary_array_bytes','sample_array_bytes','matrix_array_bytes')),'dictionary byte claims differ')
    def inventory():reader.inventory(attempt,{attempt/'start.json',proof_path})
    inventory()
    def reference(ref,path):
        require(isinstance(ref,dict) and set(ref)=={'path','sha256'} and ref['path']==str(path)
            and publication.driver.proof.valid_hash(ref['sha256']),'dictionary reference differs')
        return metadata.read(path,ref['sha256'],cap)
    start=reference(proof['start'],attempt/'start.json')
    require(set(start)=={'schema_version','status','owner','resumable','output_input','output_policy_sha256','sampler_proof','sources','reserved_encoded_bytes'}
        and type(start['schema_version']) is int and start['schema_version']==1 and start['status']=='reserved'
        and start['resumable'] is False and equal(start['owner'],owner)
        and start['output_input']==output_input and start['output_policy_sha256']==proof['output_policy_sha256']
        and start['sources']=={name:ad.experiment['source_files'][name] for name in publication.SOURCES}
        and type(start['reserved_encoded_bytes']) is int
        and start['reserved_encoded_bytes']==4*cap+policy['max_artifact_bytes']<=policy['max_attempt_bytes'],'dictionary start/reservation differs')
    require(isinstance(proof['sample_provenance'],dict) and set(proof['sample_provenance'])=={'sample_artifact','sampler_proof'}
        and equal(start['sampler_proof'],proof['sample_provenance']['sampler_proof']),'dictionary sampler proof differs')
    sampler_ref=start['sampler_proof']
    require(set(sampler_ref)=={'path','sha256'} and sampler_ref['path']==str(producer.attempt_directory(owned)/'complete.json')
        and publication.driver.proof.valid_hash(sampler_ref['sha256']),'dictionary sampler reference differs')
    event=reference(proof['event'],directory/'event-000001.json')
    expected_owner={k:owner[k] for k in ('experiment','source_commit','producer','workflow_identity')}
    context={'workflow_identity':owner['workflow_identity'],'dictionary_identity':proof['dictionary_identity'],
        'sample_provenance':proof['sample_provenance'],'dictionary_workload_sha256':proof['workload_sha256'],
        'pair_workload_sha256':route.descriptor['pair_workload']['sha256'],'output_input':output_input,'output_policy_sha256':proof['output_policy_sha256']}
    binding={'owner':expected_owner,'stage':'dictionary_complete','context':context}
    require(equal(event,{'stage':'dictionary_complete','context':context,'path':'checkpoint-000001/manifest.json','sha256':event.get('sha256'),'binding':binding})
        and proof['component']=={'path':str(directory/'checkpoint-000001/manifest.json'),'sha256':event['sha256']},'dictionary event/component binding differs')
    sample_policy=registered(artifact_input)
    require(type(sample_policy.get('max_array_bytes')) is int and sample_policy['max_array_bytes']>0
        and type(sample_policy.get('max_journal_events')) is int and sample_policy['max_journal_events']>=2,'sample read/event bounds differ')
    def journal_check():
        require(journal.directory==directory and equal(journal.owner,expected_owner) and not journal.sealed
            and journal.parent is None and journal.identity==owner['workflow_identity']
            and journal.required==sorted(route.descriptor['required_graphs'])
            and 2<=len(journal.records)<=sample_policy['max_journal_events']
            and equal(journal.records[1],event),'live dictionary journal changed')
        require([i for i,e in enumerate(journal.records) if e['stage']=='dictionary_complete']==[1]
            and not any(e['stage']=='dictionary_progress' for e in journal.records[2:]),'dictionary publication denominator differs')
    journal_check();settings=thaw(route.settings);component=Path(proof['component']['path'])
    remaining=policy['max_sample_matrix_array_bytes']-sample_policy['max_array_bytes']
    require(remaining>=2,'dictionary load/copy residency allowance absent')
    array_cap=remaining//2
    manifest,signatures,headers,files=reader.inspect_component(component,event['sha256'],binding,ad.root,
        policy['max_manifest_bytes'],policy['max_artifact_bytes'],array_cap)
    value=shape(manifest,settings)
    require(value['identity']==proof['dictionary_identity'],'dictionary manifest identity differs')
    numeric=sum(math.prod(info['shape'])*np.dtype(info['dtype']).itemsize for info in manifest['arrays'].values())
    encoded=signatures[component][2]+sum(info['bytes'] for info in manifest['arrays'].values())
    require(numeric==proof['dictionary_array_bytes'] and encoded==proof['encoded_artifact_bytes']
        and proof['encoded_event_bytes']==len(producer.lifecycle._encode(event))
        and proof['encoded_event_bytes']<=min(cap,policy['max_manifest_bytes'],sample_policy['max_manifest_bytes'])
        and sample_policy['max_array_bytes']+8*route.control['max_entries']<=policy['max_sample_matrix_array_bytes'],
        'dictionary output/production allowance differs')
    def compact():
        metadata.lease();inventory();journal_check();reader.inventory(component.parent,files)
        for path,sig in signatures.items():require(path.resolve()==path and reader.signature(path.lstat())==sig,'dictionary component changed')
    compact()
    samples=publication.driver.proof.admit(owned,journal,sampler_input=sampler_input,artifact_input=artifact_input,proof_sha256=sampler_ref['sha256'])
    require(equal(samples.record,proof['sample_provenance']) and samples.scope==proof['workload_sha256'],'dictionary sample provenance differs')
    sample_bytes=sum(producer.neighborhood_policy.sample_array_bytes(g) for g in samples.samples.graphs)
    require(sample_bytes==proof['sample_array_bytes'] and sample_bytes+2*numeric<=policy['max_sample_matrix_array_bytes'],'dictionary live payload allowance differs')
    def lease():
        owned.lease();sources();compact();samples.lease();owned.lease();compact()
    lease()
    payload=reader.read_component(component,event['sha256'],binding,root=ad.root,max_manifest_bytes=policy['max_manifest_bytes'],
        max_artifact_bytes=policy['max_artifact_bytes'],max_array_bytes=array_cap,lease=lease)
    dictionary=publication.serialization.dictionary_from_record(payload);del payload
    matrix_bytes=membership(dictionary,samples.samples,settings,thaw(route.descriptor['configs']['matching']),publication.driver.artifacts.consumer.serial.pair.BACKEND)
    require(matrix_bytes==proof['matrix_array_bytes'] and matrix_bytes<=8*route.control['max_entries']
        and sample_bytes+matrix_bytes<=policy['max_sample_matrix_array_bytes'],'dictionary matrix accounting differs')
    lease()
    record={'schema_version':1,'owner':owner,'dictionary_proof':{'path':str(proof_path),'sha256':proof_sha256},
        'event':proof['event'],'component':proof['component'],'dictionary_identity':dictionary.identity,
        'workload_sha256':samples.scope,'sample_provenance':proof['sample_provenance'],
        'output_input':output_input,'output_policy_sha256':proof['output_policy_sha256']}
    return Admitted(dictionary,record,lease)
