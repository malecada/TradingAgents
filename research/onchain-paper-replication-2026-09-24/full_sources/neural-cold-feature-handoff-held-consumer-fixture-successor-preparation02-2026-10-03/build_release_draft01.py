"""Exclusive compact release drafts from root-selected genuine documents.

Never changes a registration, marks a release accepted, or launches a process.
All referenced documents must already exist in the supplied isolated capsule.
"""
import argparse,json,os
from pathlib import Path
from proof_raw01 import *

def draft(root,destination,phase,source,registration_path,runtime_path,environment_path,cpus,prior=None):
    root=Path(root).resolve();directory=root/destination
    require(phase in IDENTITIES and directory.resolve()==directory and directory.is_relative_to(root) and not directory.exists(),'fresh release-draft destination required')
    registration=document(root,registration_path);experiment=registration['experiments'][IDENTITIES[phase]];family=registration['families'][experiment['family']]
    require(registration['program_id']==PROGRAM and experiment['cells']==[CELLS[phase]],'genuine phase registration differs')
    # The proof_tools closure must be merged into the phase1 policy and frozen
    # BEFORE materialization. Never rewrite materialized phase2 policy inputs.
    selected=document(root,experiment['inputs']['execution_job']['path']);policy=document(root,experiment['inputs'][selected['payload']['cold_proof_input']]['path'])
    sources=experiment['source_files'];require(policy['source_files']==sources and 'proof_tools/proof_supervise01.py' in sources,'source integration must precede phase1 freeze')
    directory.mkdir(exist_ok=False)
    def put(name,value,limit):
        raw=canonical(value)+b'\n';require(len(raw)<=limit,'draft document bound exceeded')
        with (directory/name).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        return ref(root,str((directory/name).relative_to(root)),kind='metadata' if limit==META else 'document')
    source_ref=put('source-document.json',{'schema_version':1,'files':sources},MAX)
    contract_ref=put('phase-contract.json',{'schema_version':1,'identity':IDENTITIES[phase],'experiment':experiment,'family':family,'expected_outputs':experiment['outputs']},MAX)
    release={'schema_version':1,'kind':'cold-proof-outer-release-v1','status':'draft','phase':phase,'root':str(root),'source':source,'registration':ref(root,registration_path),'sources':source_ref,'runtime':ref(root,runtime_path),'native_environment':ref(root,environment_path),'phase_contract':contract_ref,'prior_materialization':prior,'cpus':cpus,'remaining':['root exact source/Git/runtime/input/registration and baseline review','independent exact prospective release; create a new immutable released envelope']}
    result=put('release-draft.json',release,META)
    fd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--destination',required=True);p.add_argument('--phase',choices=list(IDENTITIES),required=True);p.add_argument('--source',required=True);p.add_argument('--registration',required=True);p.add_argument('--runtime',required=True);p.add_argument('--native-environment',required=True);p.add_argument('--cpus',type=int,nargs=2,required=True);p.add_argument('--prior-json');a=p.parse_args()
    prior=None if a.prior_json is None else metadata(Path(a.root),a.prior_json)
    draft(a.root,a.destination,a.phase,a.source,a.registration,a.runtime,a.native_environment,a.cpus,prior)


def held_metadata_draft(root,source,anchor,rows,role_references):
    """Actual source/Git and metadata readback for a distinct imported route.

    No OUT3 historical rules, fixed cold identities or old44 role set are reused.
    No registration is authored and no released envelope can be returned.
    """
    from fixture_tools import capsule_builder01 as builder
    from fixture_tools import generate_inputs01 as generator
    root=Path(root)
    for module,name in ((builder,'fixture_tools/capsule_builder01.py'),(generator,'fixture_tools/generate_inputs01.py')):
        require(Path(module.__file__).resolve()==root/name,'held metadata helper origin differs')
    require(Path(__file__).resolve()==root/'proof_tools/build_release_draft01.py','held draft helper origin differs')
    source_plan=builder.held_source_plan(root,source,anchor,rows)
    require(type(role_references) is dict and set(role_references)<=set(generator.HELD_ROLES),'unknown held release role')
    roles={}
    for name in generator.HELD_ROLES:
        reference=role_references.get(name)
        if reference is None:roles[name]=None;continue
        raw=builder.held_document(root,reference)
        # Charter is exact text; all remaining roles are metadata JSON only.
        document=raw.decode('utf-8') if name=='charter' else json.loads(raw)
        roles[name]={'reference':reference,'document':document}
    plan=generator.held_input_plan(roles,source_plan)
    route_readback=None
    if roles.get('case_contract') is not None:
        case=roles['case_contract']['document'];table=plan['input_rows']
        def input_metadata(name):
            require(type(name) is str and name in table,'required root selected input role missing')
            row=table[name];return json.loads(builder.held_document(root,{k:row[k] for k in ('path','sha256','bytes')}))
        require(roles.get('original_import_index') is not None and roles.get('target_catalog') is not None and len(plan['target_rows'])==2,'complete original11 plus target10 metadata required')
        original_names={x['name'] for x in roles['original_import_index']['document']['inputs']}
        target_names={name for t in roles['target_catalog']['document']['targets'] for name in [t['input_name']]+[t['input_name']+'_'+k for k in t['components']]}
        require(len(original_names)==11 and len(target_names)==10 and original_names.isdisjoint(target_names),'complete disjoint original/target role populations required')
        require(all(table[n]['dataset']=='original_dictionary' for n in original_names) and all(table[n]['dataset']=='synthetic' for n in target_names),'original/target dataset binding differs')
        require('target_provenance' in case['additional_inputs'] and table['target_provenance']['dataset']=='synthetic','distinct registered target provenance required')
        provenance=input_metadata('target_provenance')
        require(provenance=={'schema_version':1,'kind':'synthetic-original-import-targets','generator':'registered-explicit-arrays-v1','node_denominators':[2,3]},'original tiny-target provenance differs')
        require(roles.get('registration') is not None,'actual selected registration metadata required for route readback')
        registered=roles['registration']['document']['experiments'][case['experiment_id']]
        exact_inputs={name:{key:row[key] for key in ('path','sha256','dataset')} for name,row in table.items()}
        require(registered.get('inputs')==exact_inputs,'registered complete input-role map differs')
        require(len(table)==21+len(case['additional_inputs']),'complete registered input cardinality differs')
        name=case['held_policy_input']
        require(name in case['additional_inputs'] and table[name]['dataset']=='synthetic' and name in plan['rendered_metadata'],'selected held policy must be a distinct registered synthetic input')
        policy_ref={k:table[name][k] for k in ('path','sha256','bytes')}
        policy_raw=builder.held_document(root,policy_ref)
        rendered=plan['rendered_metadata'][name]
        require(len(policy_raw)<=8192 and policy_raw==rendered['raw_utf8'].encode('utf-8') and policy_ref['sha256']==rendered['sha256'] and policy_ref['bytes']==rendered['bytes'],'actual selected held policy bytes/header differ from canonical rendered policy')
        job=input_metadata(case['job_input']);producer_plan=input_metadata(case['plan_input'])
        require(type(job) is dict and set(job)=={'schema_version','kind','resources','environment_input','payload'} and job['schema_version']==1 and job['kind']=='compact_resource','actual registered resource job required')
        require(type(job['payload']) is dict and set(job['payload'])=={'representation_jobs'} and case['representation'] in job['payload']['representation_jobs'],'actual representation role missing')
        selected=job['payload']['representation_jobs'][case['representation']]
        require(producer_plan['schema_version']==2 and case['producer'] in producer_plan['producers'],'actual producer role missing')
        item=producer_plan['producers'][case['producer']]
        require(selected['plan_input']==case['plan_input'] and selected['producer']==case['producer'] and selected['descriptor']==item['descriptor'],'actual producer/plan/descriptor join differs')
        require(selected.get('held_score_consumer_input')==item.get('held_score_consumer_input')==case['held_policy_input'],'actual held selection equality required')
        require(selected.get('operation')=='produce' and {k:v for k,v in item.items() if k not in ('binding_output','journal_output')}==selected,'full job/plan producer selection differs')
        require(not any(type(k) is str and k.startswith('held_score_') and k!='held_score_consumer_input' for obj in (selected,item) for k in obj),'unknown held selector')
        headers=[item.get('binding_output'),item.get('journal_output')]
        require(all(type(x) is str and x and Path(x).name==x and x.endswith('.json') for x in headers) and len(set(headers))==2,'original producer header outputs required')
        readbacks=set(case['readback_outputs'].values())
        reserved={v for obj in (selected,item) for k,v in obj.items() if type(k) is str and k.endswith('_output') and type(v) is str}
        outputs=registered.get('outputs')
        require(type(outputs) is list and len(set(outputs))==len(outputs) and set(headers)|readbacks<=set(outputs) and not readbacks.intersection(reserved),'registered header/readback output closure conflicts')
        require(selected['descriptor']['dictionary_origin']=='imported-original-v1' and selected['descriptor']['required_graphs']==[x['graph_hash'] for x in plan['target_rows']],'actual imported target population differs')
        pair=input_metadata(selected['pair_checkpoint_input'])
        require(pair['numerical_source']=={'commit':anchor,'files':source_plan['package_files']},'actual148 numerical anchor policy differs')
        control=input_metadata(selected['original_dictionary_input'])
        require(control['sample_count']==512 and control['motif_count']==32 and control['kind']=='original-dictionary-import-v1','actual original512/32 control differs')
        require(roles.get('original_import_index') is not None and control['original_source']==roles['original_import_index']['document']['original_source'] and control['original_claim']==roles['original_import_index']['document']['original_claim'],'original committed import provenance differs')
        require(roles.get('native_policy') is not None and job['resources']==roles['native_policy']['document'],'actual native policy differs')
        require(roles.get('software_environment') is not None and job['environment_input'] in table and table[job['environment_input']]['sha256']==roles['software_environment']['reference']['sha256'],'actual software input differs')
        route_readback={'kind':'authenticated-metadata-only-imported-route','job_input':case['job_input'],'plan_input':case['plan_input'],'representation':case['representation'],'producer':case['producer'],'anchor':anchor,'target_count':len(plan['target_rows']),'numeric_arrays_read':False,'execution_admitted':False}
    runtime=None
    if roles.get('runtime') is not None:runtime=builder.held_runtime_metadata(root,roles['runtime']['document'])
    return {'schema_version':1,'kind':'held-resource-release-metadata-draft-v1','status':'draft-not-released','source_document':source_plan,'input_plan':plan,'route_readback':route_readback,'runtime_readback':runtime,'registration_authority':None,'budget_authority':None,'native_release':None,'guarded_input_materialization':None,'remaining':plan['remaining_roles']+['root independent source/runtime/input/registered-role review','fresh finite cumulative accounting and unused identity admission','genuine guarded numerical input-materialization entry','imported Target/native/current-guard/one-use launcher proof','whole writable-tree eligibility and actual external recovery'],'execution_admitted':False}
