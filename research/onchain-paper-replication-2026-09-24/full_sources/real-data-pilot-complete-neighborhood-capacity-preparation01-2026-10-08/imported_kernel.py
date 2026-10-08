"""Exact resident MCM with bounded numeric index/output and mandatory leases.

Limits exclude input graphs/dictionary, callback pair workspace, Python metadata,
graph validation internals and process RSS. This is not empirical admission.
"""
import importlib.util
from pathlib import Path
import numpy as np
from tradingagents.research.onchain_replication.array_neighborhoods import ArrayNeighborhoodIndex
from tradingagents.research.onchain_replication.dictionary import dictionary_hash
from tradingagents.research.onchain_replication.neighborhoods import graph_hash,node_order_hash
from tradingagents.research.onchain_replication.matching_identity import graph_identity
from tradingagents.research.onchain_replication.cache import cache_key

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('array_mcm_scalar_workload',HERE.parent/'pair-workload-2026-09-30/workload.py')
workload=importlib.util.module_from_spec(spec);spec.loader.exec_module(workload)
require=workload.require

def validate_policy(policy,entries):
    fields={'schema_version','max_buffer_bytes','edge_chunk','max_output_bytes','max_numeric_bytes'}
    require(isinstance(policy,dict) and set(policy) in (fields,fields|{'extraction_limit'})
        and type(policy['schema_version']) is int and policy['schema_version']==1
        and all(type(policy[k]) is int and policy[k]>0 for k in fields-{'schema_version'}),'MCM numeric policy differs')
    if 'extraction_limit' in policy:
        require(type(policy['extraction_limit']) is int and 0<policy['extraction_limit']<2**63,'explicit finite extraction limit required')
    require(type(entries) is int and entries>0,'positive MCM entry count required')
    output_bytes=4*entries
    require(output_bytes<=policy['max_output_bytes'],'MCM output byte allowance exceeded')
    require(output_bytes+policy['max_buffer_bytes']<=policy['max_numeric_bytes'],'MCM combined numeric allowance exceeded')
    return dict(policy)

def mcm(graph,dictionary,matching_config,*,workflow,backend,max_entries,score_pair,policy,lease,imported):
    workload.common(workflow,backend,max_entries,score_pair)
    require(callable(lease),'mandatory MCM lease required')
    lease()
    from tradingagents.research.onchain_replication.imported_mcm_identity import Target
    require(type(imported) is Target,'actual imported target capability required')
    imported.check()
    require(graph is imported.graph and dictionary is imported.dictionary and workflow==imported.owner.bound.record['workflow_identity'],'imported kernel object/workflow differs')
    require(cache_key(matching_config)==cache_key(dict(imported.owner.matching)),'imported kernel matching config differs')
    expected=imported.derive_scope()
    require(expected==imported.scope,'imported kernel workload differs')
    n=len(graph.node_ids);motifs=dictionary.representatives;k=len(motifs)
    require(n>0 and k>0 and n*k<=max_entries,'MCM matrix capacity exceeded')
    policy=validate_policy(policy,n*k)
    extraction_config=dictionary.config
    if 'extraction_limit' in policy:
        require(policy['extraction_limit']>=dictionary.config['maximum_neighborhood_nodes'],'extraction ceiling cannot reduce original capacity')
        extraction_config=dict(dictionary.config)
        extraction_config['maximum_neighborhood_nodes']=policy['extraction_limit']
    typed=[graph_identity(m) for m in motifs];parent=graph_hash(graph)
    scope=expected['workflow']
    lease();rows=0;cells=0
    with ArrayNeighborhoodIndex(graph,max_buffer_bytes=policy['max_buffer_bytes'],edge_chunk=policy['edge_chunk']) as index:
        lease()
        result=np.empty((n,k),dtype=np.float32)
        for center in range(n):
            lease()
            local=index.neighborhood(center,extraction_config)
            try:
                lease();local_id=graph_identity(local)
                for motif,m in enumerate(motifs):
                    purpose={'schema_version':1,'kind':'mcm','workload_sha256':scope,'graph_hash':parent,
                        'center_index':center,'center_id':graph.node_ids[center],'motif_index':motif,
                        'typed_graphs':[local_id,typed[motif]]}
                    lease();value=workload.score(score_pair,purpose,local,m);lease()
                    result[center,motif]=value;cells+=1
                rows+=1
            finally:
                # Do not keep the previous immutable local arrays alive while
                # the next neighborhood uses its single-output scratch budget.
                del local
    require(rows==n and cells==n*k,'incomplete MCM output')
    lease();imported.final()
    return {'mcm':result,'completed_rows':rows,'completed_cells':cells,
        'output_bytes':result.nbytes,'workload_sha256':scope}
