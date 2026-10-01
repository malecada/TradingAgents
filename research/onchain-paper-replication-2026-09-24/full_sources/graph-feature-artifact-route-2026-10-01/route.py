"""Strict current-owner native graph checkpoint admission to CPU tensors.

One original saved MCM is also admitted to join actual source values. Its retained
payload is counted separately in the conversion allowance. This is not cold-start,
historical, mapped, full-representation or empirical admission.
"""
import importlib.util
from pathlib import Path
from tradingagents.research.onchain_replication.provenance import file_hash,thaw
from tradingagents.research.onchain_replication.neighborhoods import graph_hash as hash_graph,node_order_hash

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
spec=importlib.util.spec_from_file_location('saved_graph_publication',HERE.parent/'graph-feature-publication-2026-10-01/publication.py')
publication=importlib.util.module_from_spec(spec);spec.loader.exec_module(publication)
saved=publication.saved;reader=publication.reader;boundary=publication.route.boundary
SOURCES=tuple(sorted(set(publication.SOURCES)|{str(Path(__file__).relative_to(ROOT))}))
require=saved.require;equal=saved.equal

def admit(owned,journal,*,dictionary_ticket,graph_hash,mcm_input,mcm_output_input,mcm_read_input,
          feature_input,output_input,read_input,proof_sha256):
    pin=saved.ticket_lease(dictionary_ticket,owned,journal)
    route=owned.workload;bound=route.bound;ad=bound._run.admission;owner=thaw(bound.record)
    def sources():
        for name in SOURCES:
            sha=ad.experiment['source_files'].get(name)
            require(sha is not None and file_hash(ROOT/name)==sha and file_hash(ad.root/name)==sha,'saved graph source differs')
    sources()
    require(type(graph_hash) is str and graph_hash in route.descriptor['required_graphs'] and graph_hash in route._graphs,
        'required saved graph membership differs')
    graph=route._graphs[graph_hash];n=len(graph.node_ids);k=route.settings['size'];order=node_order_hash(graph.node_ids)
    require(hash_graph(graph)==graph_hash and n>0 and k>0 and n*k<=route.control['max_entries'],'saved graph source/capacity differs')
    mcm_bytes=4*n*k;numeric=mcm_bytes+graph.edge_index.nbytes
    directory=Path(owner['journal_directory']);metadata=publication.producer.Metadata(ad.root)
    def registered(name):
        require(type(name) is str and name in ad.inputs,'registered saved graph input required')
        info=ad.inputs[name];return metadata.read(ad.root/info['path'],info['sha256'])
    claim=metadata.read(directory/'claim.json');plan=registered(claim['plan_input']);job=registered('execution_job')
    item=plan.get('producers',{}).get(owner['producer']);selected=job.get('payload',{}).get('representation_jobs',{}).get(owner['representation'])
    require(isinstance(item,dict) and isinstance(selected,dict),'selected saved graph route required')
    for key,name in (('mcm_execution_input',mcm_input),('mcm_output_input',mcm_output_input),('mcm_read_input',mcm_read_input),
            ('feature_tensor_input',feature_input),('graph_output_input',output_input),('graph_read_input',read_input)):
        require(item.get(key)==selected.get(key)==name,'selected saved graph policy differs')
    output=registered(output_input);read=registered(read_input);tensor=registered(feature_input)
    require(isinstance(output,dict) and set(output)=={'schema_version','max_metadata_bytes','max_manifest_bytes','max_artifact_bytes',
        'max_attempt_bytes','max_array_bytes','max_journal_events'} and type(output['schema_version']) is int and output['schema_version']==1
        and all(type(v) is int and v>0 for key,v in output.items() if key!='schema_version')
        and max(output['max_metadata_bytes'],output['max_manifest_bytes'])<=reader.MANIFEST_LIMIT,'saved graph output policy differs')
    require(isinstance(read,dict) and set(read)=={'schema_version','max_array_bytes','max_numeric_bytes','chunk_entries'}
        and type(read['schema_version']) is int and read['schema_version']==1
        and all(type(v) is int and v>0 for key,v in read.items() if key!='schema_version')
        and read['chunk_entries']<=65536,'saved graph read policy differs')
    require(isinstance(tensor,dict) and set(tensor)=={'schema_version','max_numeric_bytes','chunk_entries'}
        and type(tensor['schema_version']) is int and tensor['schema_version']==1
        and all(type(v) is int and v>0 for key,v in tensor.items() if key!='schema_version')
        and tensor['chunk_entries']<=65536,'saved graph tensor policy differs')
    chunk=read['chunk_entries'];conversion=2*numeric+9*chunk;required=mcm_bytes+conversion
    require(numeric<=min(read['max_array_bytes'],output['max_array_bytes']) and required<=read['max_numeric_bytes']
        and 2*numeric+9*tensor['chunk_entries']<=tensor['max_numeric_bytes'],'saved graph read/copy bound exceeded')
    cap=output['max_metadata_bytes'];attempt=publication.attempt_directory(owned,graph_hash);proof_path=attempt/'complete.json'
    require(saved.artifacts.publication.driver.proof.valid_hash(proof_sha256),'explicit graph proof hash required')
    proof=metadata.read(proof_path,proof_sha256,cap)
    fields={'schema_version','status','owner','resumable','start','graph_hash','event_index','storage','feature_provenance',
        'output_input','output_policy_sha256','array_bytes','encoded_artifact_bytes','encoded_event_bytes','event','component'}
    require(isinstance(proof,dict) and set(proof)==fields and type(proof['schema_version']) is int and proof['schema_version']==1
        and proof['status']=='complete' and proof['resumable'] is False and equal(proof['owner'],owner)
        and proof['graph_hash']==graph_hash and proof['storage']=='native_graph_feature_v1'
        and proof['output_input']==output_input and proof['output_policy_sha256']==ad.inputs[output_input]['sha256'],'saved graph proof differs')
    require(type(proof['event_index']) is int and proof['event_index']>=3
        and all(type(proof[x]) is int and proof[x]>0 for x in ('array_bytes','encoded_artifact_bytes','encoded_event_bytes'))
        and proof['array_bytes']==numeric,'saved graph counts differ')
    fp=proof['feature_provenance']
    require(isinstance(fp,dict) and set(fp)=={'schema_version','owner','graph_hash','node_order_sha256','feature_hash','mcm_provenance',
        'tensor_policy','reserved_numeric_bytes','tensor_bytes'} and type(fp['schema_version']) is int and fp['schema_version']==1
        and equal(fp['owner'],owner) and fp['graph_hash']==graph_hash and fp['node_order_sha256']==order
        and fp['tensor_policy']=={'input':feature_input,'sha256':ad.inputs[feature_input]['sha256']}
        and type(fp['reserved_numeric_bytes']) is int and fp['reserved_numeric_bytes']==2*numeric+9*tensor['chunk_entries']
        and type(fp['tensor_bytes']) is int and fp['tensor_bytes']==numeric
        and saved.artifacts.publication.driver.proof.valid_hash(fp['feature_hash']),'saved graph feature provenance differs')
    def inventory():reader.inventory(attempt,{attempt/'start.json',proof_path})
    inventory()
    def reference(ref,path):
        require(isinstance(ref,dict) and set(ref)=={'path','sha256'} and ref['path']==str(path)
            and saved.artifacts.publication.driver.proof.valid_hash(ref['sha256']),'saved graph reference differs')
        return metadata.read(path,ref['sha256'],cap)
    start=reference(proof['start'],attempt/'start.json');index=proof['event_index']
    mcm_path=saved.publication.attempt_directory(owned,graph_hash)/'complete.json'
    mcm_ref=fp.get('mcm_provenance',{}).get('mcm_proof')
    require(isinstance(mcm_ref,dict) and set(mcm_ref)=={'path','sha256'} and mcm_ref['path']==str(mcm_path)
        and saved.artifacts.publication.driver.proof.valid_hash(mcm_ref['sha256']),'saved graph MCM reference differs')
    reserved=4*cap+output['max_artifact_bytes']
    require(set(start)=={'schema_version','status','owner','resumable','graph_hash','event_index','mcm_proof','feature_input',
        'output_input','output_policy_sha256','reserved_encoded_bytes','sources'}
        and type(start['schema_version']) is int and start['schema_version']==1 and start['status']=='reserved'
        and start['resumable'] is False and equal(start['owner'],owner) and start['graph_hash']==graph_hash
        and type(start['event_index']) is int and start['event_index']==index and equal(start['mcm_proof'],mcm_ref)
        and start['feature_input']==feature_input and start['output_input']==output_input
        and start['output_policy_sha256']==ad.inputs[output_input]['sha256']
        and type(start['reserved_encoded_bytes']) is int and start['reserved_encoded_bytes']==reserved<=output['max_attempt_bytes']
        and start['sources']=={name:ad.experiment['source_files'][name] for name in publication.SOURCES},'saved graph start differs')
    expected_owner={key:owner[key] for key in ('experiment','source_commit','producer','workflow_identity')}
    context={'workflow_identity':owner['workflow_identity'],'graph_hash':graph_hash,'dictionary_hash':pin['dictionary'].identity,
        'fold_id':route.descriptor['fold']['id'],'seed':route.descriptor['seed'],'arm':route.descriptor['arm'],
        'storage':'native_graph_feature_v1','feature_provenance':fp,'output_input':output_input,
        'output_policy_sha256':ad.inputs[output_input]['sha256']}
    binding={'owner':expected_owner,'stage':'graph_complete','context':context}
    event=reference(proof['event'],directory/f'event-{index:06d}.json');component=directory/f'checkpoint-{index:06d}/manifest.json'
    require(equal(event,{'stage':'graph_complete','context':context,'path':str(component.relative_to(directory)),
        'sha256':event.get('sha256'),'binding':binding}) and proof['component']=={'path':str(component),'sha256':event['sha256']},
        'saved graph event/component differs')
    def journal_check():
        require(journal.directory==directory and equal(journal.owner,expected_owner) and journal.parent is None and not journal.sealed
            and journal.identity==owner['workflow_identity'] and journal.required==sorted(route.descriptor['required_graphs'])
            and index<len(journal.records)<=output['max_journal_events'] and equal(journal.records[index],event),'saved graph live journal differs')
        hits=[i for i,e in enumerate(journal.records) if e['stage']=='graph_complete' and e['context'].get('graph_hash')==graph_hash]
        require(hits==[index] and not any(e['stage']=='representation_complete' or (e['stage']=='embedding_progress'
            and e['context'].get('graph_hash')==graph_hash) for e in journal.records),'saved graph stage denominator differs')
    journal_check()
    manifest,signatures,headers,files=reader.inspect_component(component,event['sha256'],binding,ad.root,
        output['max_manifest_bytes'],output['max_artifact_bytes'],read['max_array_bytes'])
    def scalar(v):return {'kind':'scalar','value':v}
    tree={'kind':'dict','items':[[scalar('feature'),{'kind':'dict','items':[
        [scalar('mcm'),{'kind':'array','member':'array-000000.npy'}],
        [scalar('edge_index'),{'kind':'array','member':'array-000001.npy'}]]}],[scalar('aligned_vectors'),scalar(None)]]}
    require(equal(manifest['tree'],tree) and set(manifest['arrays'])=={'array-000000.npy','array-000001.npy'},'saved graph native tree differs')
    for name,shape,dtype in (('array-000000.npy',[n,k],'float32'),('array-000001.npy',list(graph.edge_index.shape),'int64')):
        require(manifest['arrays'][name]['shape']==shape and manifest['arrays'][name]['dtype']==dtype and headers[name][1] is False,
            'saved graph native shape/type/order differs')
    require(proof['encoded_artifact_bytes']==sum(sig[2] for sig in signatures.values())
        and proof['encoded_event_bytes']==len(publication.producer.lifecycle._encode(event))
        and proof['encoded_event_bytes']<=min(cap,output['max_manifest_bytes']),'saved graph encoded counts differ')
    def compact():
        metadata.lease();sources();inventory();journal_check();reader.inventory(component.parent,files)
        for path,sig in signatures.items():require(path.resolve()==path and reader.signature(path.lstat())==sig,'saved graph component changed')
        require(route._graphs.get(graph_hash) is graph and hash_graph(graph)==graph_hash and node_order_hash(graph.node_ids)==order,
            'saved graph source changed')
    compact()
    upstream=saved.admit(owned,journal,dictionary_ticket=dictionary_ticket,graph_hash=graph_hash,mcm_input=mcm_input,
        output_input=mcm_output_input,read_input=mcm_read_input,proof_sha256=mcm_ref['sha256'])
    expected=boundary.identity(upstream.mcm,graph.edge_index,chunk)
    require(equal(fp['mcm_provenance'],upstream.record) and fp['feature_hash']==expected,'saved graph actual MCM/value provenance differs')
    mcm_hits=[i for i,e in enumerate(journal.records) if e['stage']=='mcm_progress' and e['context'].get('graph_hash')==graph_hash]
    require(len(mcm_hits)==1 and mcm_hits[0]<index,'saved graph MCM/completion order differs')
    def lease():
        compact();upstream.lease()
        require(boundary.identity(upstream.mcm,graph.edge_index,chunk)==expected,'saved graph upstream value identity changed')
        compact()
    lease()
    payload=reader.read_component(component,event['sha256'],binding,root=ad.root,max_manifest_bytes=output['max_manifest_bytes'],
        max_artifact_bytes=output['max_artifact_bytes'],max_array_bytes=read['max_array_bytes'],lease=lease)
    feature=boundary.materialize(payload['feature']['mcm'],payload['feature']['edge_index'],expected_hash=expected,
        max_numeric_bytes=read['max_numeric_bytes']-mcm_bytes,chunk_entries=chunk,lease=lease)
    del payload
    record={'schema_version':1,'owner':owner,'graph_hash':graph_hash,'feature_hash':expected,
        'graph_proof':{'path':str(proof_path),'sha256':proof_sha256},'event':proof['event'],'component':proof['component'],
        'feature_provenance':fp,'read_policy':{'input':read_input,'sha256':ad.inputs[read_input]['sha256']},
        'reserved_numeric_bytes':required,'retained_mcm_bytes':mcm_bytes}
    result=publication.route.Features(feature,record,lease,chunk);result.lease();return result
