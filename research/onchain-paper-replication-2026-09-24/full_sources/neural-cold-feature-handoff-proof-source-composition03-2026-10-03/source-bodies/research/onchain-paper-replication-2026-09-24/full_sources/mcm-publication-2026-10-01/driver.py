"""Admitted current dictionary to bounded array MCM workload; not publication."""
import importlib.util
from pathlib import Path
from tradingagents.research.onchain_replication.provenance import file_hash,thaw
from tradingagents.research.onchain_replication.neighborhoods import graph_hash as hash_graph,node_order_hash
from tradingagents.research.onchain_replication.matching_identity import graph_identity
from tradingagents.research.onchain_replication.cache import cache_key

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
spec=importlib.util.spec_from_file_location('mcm_dictionary_artifacts',HERE.parent/'dictionary-artifact-route-2026-10-01/route.py')
artifacts=importlib.util.module_from_spec(spec);spec.loader.exec_module(artifacts)
serial=artifacts.publication.driver.artifacts.consumer.serial
workload=artifacts.publication.driver.workload
spec=importlib.util.spec_from_file_location('bounded_mcm_kernel',HERE.parent/'mcm-array-kernel-2026-10-01/kernel.py')
kernel=importlib.util.module_from_spec(spec);spec.loader.exec_module(kernel)
SOURCES=tuple(sorted(set(artifacts.SOURCES)|{str(Path(p).relative_to(ROOT)) for p in
    (__file__,kernel.__file__,ROOT/'tradingagents/research/onchain_replication/array_neighborhoods.py')}))

def require(value,message):
    if not value:raise ValueError(message)

def compute(owned,journal,*,graph_hash,sampler_input,artifact_input,output_input,dictionary_proof_sha256,mcm_input):
    require(type(owned) is artifacts.producer.artifacts.consumer.ownership.OwnedJournal,'actual admitted MCM owner required')
    route=owned.workload;route.bound.check();owned.lease();ad=route.bound._run.admission
    def sources():
        for name in SOURCES:
            sha=ad.experiment['source_files'].get(name)
            require(sha is not None and file_hash(ROOT/name)==sha and file_hash(ad.root/name)==sha,'MCM driver source differs')
    sources()
    require(type(graph_hash) is str and graph_hash in route.descriptor['required_graphs'] and graph_hash in route._graphs,
        'exact required graph membership needed')
    graph=route._graphs[graph_hash]
    require(hash_graph(graph)==graph_hash,'required MCM graph changed')
    require(0<len(graph.node_ids)*route.settings['size']<=route.control['max_entries'],'MCM output entry allowance exceeded')
    metadata=artifacts.producer.Metadata(ad.root)
    def registered(name):
        require(type(name) is str and name in ad.inputs,'registered MCM input required')
        info=ad.inputs[name];return metadata.read(ad.root/info['path'],info['sha256'])
    claim=metadata.read(Path(route.bound.record['journal_directory'])/'claim.json')
    plan=registered(claim['plan_input']);job=registered('execution_job')
    item=plan.get('producers',{}).get(route.bound.record['producer'])
    selected=job.get('payload',{}).get('representation_jobs',{}).get(route.bound.record['representation'])
    require(isinstance(item,dict) and isinstance(selected,dict)
        and item.get('mcm_execution_input')==selected.get('mcm_execution_input')==mcm_input,'MCM execution route differs')
    policy=kernel.validate_policy(registered(mcm_input),len(graph.node_ids)*route.settings['size'])
    metadata.lease();owned.lease()
    admitted=artifacts.admit(owned,journal,sampler_input=sampler_input,artifact_input=artifact_input,
        output_input=output_input,proof_sha256=dictionary_proof_sha256)
    dictionary=admitted.dictionary;matching=thaw(route.descriptor['configs']['matching'])
    order=node_order_hash(graph.node_ids);motifs=[graph_identity(g) for g in dictionary.representatives]
    scope=cache_key({'schema_version':1,'kind':'mcm','workflow':route.bound.record['workflow_identity'],'backend':serial.pair.BACKEND,
        'graph':graph_hash,'node_order':order,'dictionary':dictionary.identity,'ordered_motifs':motifs,'matching':matching,'dtype':'float32'})
    def lease():
        admitted.lease();sources();metadata.lease();owned.lease();route.lease()
        require(graph_hash in route.descriptor['required_graphs'] and route._graphs.get(graph_hash) is graph
            and hash_graph(graph)==graph_hash,'MCM graph membership or bytes changed')
        admitted.lease()
    lease()
    consumer=serial.Serial(owned.journal,context=thaw(route.bound.context),policy=thaw(route.bound.limits),
        config=matching,workload_sha256=scope,lease=lease,
        operations_per_checkpoint=route.control['operations_per_checkpoint'],max_checkpoints=route.control['max_checkpoints'])
    def score(purpose,left,right):
        lease();require(purpose.get('workload_sha256')==scope and purpose.get('graph_hash')==graph_hash,'MCM purpose scope differs')
        result=consumer(purpose,left,right);lease();return result
    lease()
    result=kernel.mcm(graph,dictionary,matching,workflow=route.bound.record['workflow_identity'],backend=serial.pair.BACKEND,
        max_entries=route.control['max_entries'],score_pair=score,policy=policy,lease=lease)
    matrix=result['mcm']
    require(result['workload_sha256']==scope,'MCM returned workload differs')
    require(matrix.shape==(len(graph.node_ids),len(motifs)) and str(matrix.dtype)=='float32','MCM output shape/type differs')
    lease()
    return result|{'_lease':lease,'mcm_policy':{'input':mcm_input,'sha256':ad.inputs[mcm_input]['sha256']},'graph_hash':graph_hash,'node_order_sha256':order,'ordered_motifs':motifs,
        'workload_sha256':scope,'dictionary_provenance':thaw(admitted.record),'empirical_admission_verified':False}
