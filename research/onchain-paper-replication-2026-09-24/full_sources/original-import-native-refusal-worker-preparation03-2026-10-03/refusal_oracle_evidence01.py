"""Original-record joins for durable guarded64pair identity observations."""
import json
from pathlib import Path
from raw_receipts01 import body,require,digest,metadata
from refusal_cases import identity,NO_OWNER
from refusal_evidence import key
from refusal_stage import target_node_order
from refusal_pair_identity import expected_pairs
from resource_policy05 import NUMERIC,CONSTRUCTOR_SHA256
TOOLS=('raw_receipts01','original_semantics','refusal_pair_identity','resource_policy05','guarded_formula_oracle05')
def authenticate_oracle(root,case,claim_raw):
    root=Path(root);claim=json.loads(claim_raw);name=identity(case);prefix='research_runs/'+name
    summary=metadata(root,prefix+'/outputs/resource-summary.json');path=prefix+'/refusal-oracle.json'
    if case in NO_OWNER:
        require(summary['oracle_observation'] is None and not (root/path).exists(),'pre-Owner case created oracle evidence');return None
    raw=body(root,path,8192);record=json.loads(raw)
    require(summary['oracle_observation']=={'path':path,'sha256':digest(raw),'bytes':len(raw)},'durable oracle reference differs')
    require(set(record)=={'schema_version','kind','identity','source','claim_sha256','binding_sha256','owner','proof','expected_pair_identity_sha256','tool_sources'} and record['schema_version']==1 and record['kind']=='guarded-original-target-identity-observation','oracle record schema differs')
    require(record['identity']==name==claim['experiment_id'] and record['source']==claim['source'] and record['claim_sha256']==digest(claim_raw),'oracle original claim differs')
    inputs=claim['inputs'];sources=claim['experiment']['source_files']
    def load(k):
        row=inputs[k];data=body(root,row['path']);require(digest(data)==row['sha256'],'oracle registered input differs');return json.loads(data)
    require(record['tool_sources']=={n:sources['fixture_tools/'+n+'.py'] for n in TOOLS},'oracle helper source denominator differs')
    for n,sha in record['tool_sources'].items():require(digest(body(root,'fixture_tools/'+n+'.py'))==sha,'oracle selected helper body changed')
    job=load('execution_job');s=next(iter(job['payload']['representation_jobs'].values()));descriptor=s['descriptor'];workflow=key(descriptor)
    journal='research_artifacts/onchain_representations/'+workflow+'/'+name
    compact=metadata(root,journal+'/compact/owner.json');receipt_raw=body(root,journal+'/compact/dictionary-import/import-complete.json');receipt=json.loads(receipt_raw)
    numeric=receipt['numeric'];execution=receipt['execution'];first=descriptor['required_graphs'][0];inp=descriptor['resource_graph_inputs'][first];manifest=load(inp);node_order=target_node_order(root,inputs[inp]['path'],manifest,inputs)
    imported_identity=key({'import_receipt':digest(receipt_raw),'current':execution})
    workload=key({'schema_version':2,'kind':'mcm-imported-original','workflow':workflow,'backend':execution['backend'],'graph':first,'node_order':node_order,'dictionary':numeric['original_dictionary'],'ordered_motifs':numeric['ordered_motifs'],'matching':descriptor['configs']['matching'],'original_matching':numeric['original_matching'],'execution_matching':execution['execution_matching'],'import_execution_identity':imported_identity,'dtype':'float32'})
    pairs=expected_pairs(root,inputs[inp]['path'],manifest,inputs,numeric=numeric,dictionary_config=descriptor['configs']['dictionary'],matching=descriptor['configs']['matching'],context=compact['context'],backend=execution['backend'],workload=workload,source_files=sources)
    expected={'schema_version':1,'kind':'genuine-array-identity-oracle','graph_hash':first,'import_receipt_sha256':digest(receipt_raw),'workload_sha256':workload,'pair_count':64,'pair_identity_sha256':key(pairs),'source_sha256':sources['fixture_tools/guarded_formula_oracle05.py'],'matching_computations':0,'numeric_policy':NUMERIC,'constructor_allowance_bytes':655600,'constructor_source_sha256':CONSTRUCTOR_SHA256}
    require(record['proof']==expected and record['expected_pair_identity_sha256']==key(pairs),'genuine oracle result/registered workload differs')
    require(record['owner']==receipt['owner'] and record['binding_sha256']==key(compact['binding']),'oracle original Owner/Binding differs')
    return {'path':path,'sha256':digest(raw),'pair_count':64,'matching_computations':0,'status':'authenticated-guarded-observation'}
