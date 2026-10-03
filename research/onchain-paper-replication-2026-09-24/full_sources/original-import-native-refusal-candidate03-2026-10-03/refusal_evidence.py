"""Bounded original journal/Owner and failed producer joins; no numerical loads."""
import hashlib,json,os,stat
from pathlib import Path
from refusal_cases import PRECLAIM,NO_OWNER,NO_JOURNAL,identity
from raw_receipts01 import body,metadata,require,digest
NUMERIC=('wrong-purpose','wrong-ack','wrong-matrix','wrong-count')
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def key(value):return digest(canonical(value))
def present(path):return path.exists() or path.is_symlink()
def directories(path,*,allow_files=False):
    if not present(path):return []
    info=path.lstat();require(stat.S_ISDIR(info.st_mode) and path.resolve()==path,'evidence namespace redirected')
    iterator=os.scandir(path);primary=None;result=[];seen=0
    try:
        for entry in iterator:
            seen+=1;require(seen<=32768,'evidence directory count exceeds bound')
            if allow_files and entry.is_file(follow_symlinks=False):continue
            require(entry.is_dir(follow_symlinks=False),'evidence directory membership differs')
            member=path/entry.name;require(member.resolve()==member,'evidence directory redirected');result.append(member)
        return result
    except BaseException as error:primary=error;raise
    finally:
        try:iterator.close()
        except BaseException as error:
            if primary is not None and (isinstance(primary,MemoryError) or not isinstance(primary,Exception)):pass
            else:raise

def attempt_directories(root,namespace,name):
    result=[]
    for workflow in directories(root/namespace):
        require(len(workflow.name)==64 and all(c in '0123456789abcdef' for c in workflow.name),'workflow evidence namespace differs')
        selected=workflow/name
        if present(selected):
            require(selected.resolve()==selected and selected.is_dir(),'attempt evidence directory redirected');result.append(selected)
    return result

def authenticate(root,variant,claim_raw):
    root=Path(root);name=identity(variant);claim=json.loads(claim_raw)
    require(variant not in PRECLAIM and claim['experiment_id']==name,'postclaim original evidence identity differs')
    inputs=claim['inputs'];require(inputs==claim['experiment']['inputs'],'claim input membership differs')
    def load(inp):
        row=inputs[inp];raw=body(root,row['path']);require(digest(raw)==row['sha256'],'registered evidence input changed');return json.loads(raw)
    job=load('execution_job');jobs=job['payload']['representation_jobs'];require(len(jobs)==1 and job['kind']=='compact_resource','genuine compact refusal job differs')
    representation,selected=next(iter(jobs.items()));descriptor=selected['descriptor'];workflow=key(descriptor)
    require(descriptor['resource_fixture']['case']=='refusal-'+variant,'claim selected refusal differs')
    plan=load(selected['plan_input'])['producers'][selected['producer']]
    require(all(plan[k]==v for k,v in selected.items()),'original plan/job differs')
    required=descriptor['required_graphs'];require(len(required)==2 and required==sorted(set(required)),'original target denominator differs')
    journal_roots=attempt_directories(root,'research_artifacts/onchain_representations',name)
    expected_journal=0 if variant in NO_JOURNAL else 1
    require(len(journal_roots)==expected_journal,'actual journal count differs')
    all_producers=attempt_directories(root,'research_artifacts/onchain_compact_mcm',name)
    all_outputs=attempt_directories(root,'research_artifacts/onchain_compact_outputs',name)
    require(not all_outputs,'refusal created target publication namespace')
    observed={'journal_count':expected_journal,'owner_count':0,'producer_count':0,'journal_hashes':{},'owner_sha256':None,'import_sha256':None,'producer_hashes':{}}
    if not journal_roots:
        require(not all_producers,'pre-Owner refusal created MCM producer');return observed
    journal=journal_roots[0];require(journal.parent.name==workflow,'original workflow journal differs')
    prefix=str(journal.relative_to(root));owner={'experiment':name,'source_commit':claim['source'],'producer':selected['producer'],'workflow_identity':workflow}
    def saved(relative):
        raw=body(root,prefix+'/'+relative);observed['journal_hashes'][relative]=digest(raw);return json.loads(raw)
    require(not present(journal/'complete.json'),'refusal journal unexpectedly completed')
    require(canonical(saved('owner.json'))==canonical(owner),'original journal owner differs')
    start=saved('start.json');require(start=={'schema_version':1,'owner':owner,'required_graphs':required,'parent':None,'workflow_identity':None},'original journal start differs')
    journal_claim=saved('claim.json');expected_claim={'owner':owner,'descriptor':descriptor,'plan_input':selected['plan_input'],'binding_output':plan['binding_output'],'registration_sha256':claim['registration_sha256'],'pair_checkpoint_input':selected['pair_checkpoint_input'],'pair_checkpoint_policy_sha256':inputs[selected['pair_checkpoint_input']]['sha256'],'continuation_input':None,'death_input':None,'job_input':'execution_job','job_sha256':inputs['execution_job']['sha256'],'resource_only':True}
    require(canonical(journal_claim)==canonical(expected_claim),'original journal claim differs')
    failed=saved('failed.json');reason={'owner-death':'registered negative owner terminal boundary','lease-terminal':'registered negative lease-terminal boundary'}.get(variant,'registered negative fixture; no retry')
    require(failed=={'schema_version':1,'status':'failed','reason':reason,'owner':owner,'workflow_identity':None,'events':[],'parent':None,'required_graphs':required},'genuine failed journal terminal differs')
    compact=journal/'compact';expected_owner=0 if variant in NO_OWNER else 1
    require(present(compact)==bool(expected_owner),'actual compact Owner count differs')
    if not expected_owner:
        require(not all_producers,'pre-Owner refusal created MCM producer');return observed
    require(compact.is_dir() and compact.resolve()==compact and not present(compact/'complete.json'),'compact Owner redirected or unexpectedly complete')
    pair=load(selected['pair_checkpoint_input']);envelope=load(selected['compact_policy_input']);environment=load(job['environment_input'])
    binding={'experiment':name,'source_commit':claim['source'],'claim_sha256':digest(claim_raw),'registration_sha256':claim['registration_sha256'],'representation':representation,'producer':selected['producer'],'workflow_identity':workflow,'policy_sha256':inputs[selected['pair_checkpoint_input']]['sha256'],'journal_directory':str(journal),'numerical_source':pair['numerical_source'],'job_input':'execution_job','job_sha256':inputs['execution_job']['sha256'],'resource_only':True}
    stage_contract={'kind':'dictionary-import','required_stages':['dictionary-import']+['mcm-'+k for k in required],'current_binding':key(binding),'control_input':selected['original_dictionary_input'],'control_sha256':inputs[selected['original_dictionary_input']]['sha256'],'job_input':'execution_job','job_sha256':inputs['execution_job']['sha256'],'descriptor_sha256':workflow}
    compact_owner=saved('compact/owner.json');expected={'schema_version':1,'backend':envelope['backend'],'binding':binding,'context':{'namespace':workflow,'source_commit':pair['numerical_source']['commit'],'runtime_hash':key(environment)},'policy_input':selected['compact_policy_input'],'policy_sha256':inputs[selected['compact_policy_input']]['sha256'],'required_stages':stage_contract['required_stages'],'maximum_retained_logical_bytes':envelope['max_workflow_retained_logical_bytes'],'original_import':stage_contract}
    require(canonical(compact_owner)==canonical(expected),'actual original compact Owner birth differs')
    owner_identity=key(compact_owner);observed.update(owner_count=1,owner_sha256=observed['journal_hashes']['compact/owner.json'])
    intent=saved('compact/dictionary-import/intent.json');receipt=saved('compact/dictionary-import/import-complete.json')
    require(intent['owner']==owner_identity and intent['stage']==intent['kind']=='dictionary-import' and intent['binding_sha256']==key(binding) and intent['prebirth_contract']==stage_contract,'original import stage intent differs')
    stage_policy=load(selected['original_dictionary_stage_input']);require(intent['policy']==stage_policy and intent['reserved_logical_bytes']==stage_policy['max_stage_bytes'],'import stage reservation differs')
    require(type(receipt['schema_version']) is int and receipt['schema_version']==1 and receipt['kind']=='dictionary-import-complete' and receipt['owner']==owner_identity and receipt['intent_sha256']==observed['journal_hashes']['compact/dictionary-import/intent.json'] and receipt['execution']==intent['execution'] and type(receipt['current_matching_pairs']) is int and receipt['current_matching_pairs']==0 and receipt['historical_work_recomputed'] is False,'genuine completed import stage differs')
    from original_semantics import expected_numeric
    original=load(selected['original_dictionary_input']);blobs={}
    require(original['motif_count']==32,'exact original32 required')
    for role,reference in original['refs'].items():
        row=inputs[reference['input']];raw=body(root,row['path'],original['max_json_bytes'])
        require(digest(raw)==row['sha256']==reference['sha256'],'original registered evidence changed');blobs[role]=raw
    numeric=receipt['numeric'];expected_numeric_record=expected_numeric(original,blobs)
    require(canonical(numeric)==canonical(expected_numeric_record) and numeric['original_matching']==key(descriptor['configs']['matching']),'original32 import numeric metadata differs')
    execution=receipt['execution'];require(execution['original_dictionary']==numeric['original_dictionary'] and execution['original_matching']==numeric['original_matching'] and execution['current_binding']==key(binding) and execution['current_source']==claim['source'] and execution['runtime_hash']==key(environment) and execution['stage_contract']==stage_contract and execution['backend']==pair['backend'] and execution['execution_matching']==key({'config':descriptor['configs']['matching'],'backend':pair['backend']}),'import execution/original identity join differs')
    expected_execution={'original_dictionary':numeric['original_dictionary'],'original_matching':numeric['original_matching'],'execution_matching':key({'config':descriptor['configs']['matching'],'backend':pair['backend']}),'backend':pair['backend'],'current_binding':key(binding),'current_source':claim['source'],'runtime_hash':key(environment),'source_modules':{n:claim['experiment']['source_files'][n] for n in ('tradingagents/research/onchain_replication/original_import_preparation.py','tradingagents/research/onchain_replication/original_dictionary.py')},'stage_contract':stage_contract,'mcm_execution_admitted':False}
    require(canonical(execution)==canonical(expected_execution),'exact imported execution source contract differs')
    observed['import_sha256']=observed['journal_hashes']['compact/dictionary-import/import-complete.json']
    numeric_case=variant in NUMERIC
    expected_children=['dictionary-import']+(['mcm-'+required[0]] if numeric_case else [])
    require(sorted(p.name for p in directories(compact,allow_files=True))==sorted(expected_children),'unexpected compact stage population')
    require(len(all_producers)==int(numeric_case),'actual MCM attempt group count differs')
    if numeric_case:
        parent=all_producers[0];require(parent.parent.name==workflow,'MCM producer workflow differs')
        attempts=directories(parent);require([p.name for p in attempts]==['mcm-'+required[0]],'unexpected target producer population')
        producer=attempts[0];stage=compact/producer.name
        require(not present(producer/'complete.json') and not present(stage/'stage-complete.json'),'refusal unexpectedly completed MCM producer/stage')
        rp=str(producer.relative_to(root));start_raw=body(root,rp+'/start.json');failed_raw=body(root,rp+'/failed.json');producer_start=json.loads(start_raw)
        require(producer_start['owner']==owner_identity and producer_start['graph_hash']==required[0] and producer_start['rows']==2 and producer_start['motifs']==32 and producer_start['cells']==64,'original failed producer denominator differs')
        require(json.loads(failed_raw)=={'schema_version':1,'status':'failed','owner':owner_identity},'original failed producer marker differs')
        from refusal_stage import authenticate_stage,target_node_order
        manifest_input=descriptor['resource_graph_inputs'][required[0]];manifest=load(manifest_input)
        require(manifest['graph_hash']==required[0],'registered first target manifest differs')
        node_order=target_node_order(root,inputs[manifest_input]['path'],manifest,inputs)
        observed['numerical_stage']=authenticate_stage(root,stage,variant,owner_identity,producer_start,envelope['stage_policy'],descriptor['configs']['matching'],expected['context'],claim['experiment']['source_files'],numeric,execution,observed['import_sha256'],node_order)
        observed['producer_count']=1;observed['producer_hashes']={'start.json':digest(start_raw),'failed.json':digest(failed_raw)}
    return observed
