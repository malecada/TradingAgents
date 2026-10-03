"""Deterministic tiny NPY/JSON input bytes. No NumPy, authority or matching runs."""
import hashlib,json,math,struct
from pathlib import Path

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def require(v,m):
    if not v:raise ValueError(m)

def npy(dtype,shape,values):
    require(type(shape) is tuple and shape and all(type(x) is int and 0<x<=32 for x in shape),'finite tiny shape required')
    require(len(values)==math.prod(shape),'NPY values/shape differ')
    if dtype in ('<f8','<i8'):
        require(all(type(x) in (int,float) and not isinstance(x,bool) and math.isfinite(x) for x in values),'finite primitive values required')
        raw=struct.pack('<'+str(len(values))+('d' if dtype=='<f8' else 'q'),*values)
    elif dtype.startswith('<U') and dtype[2:].isdigit():
        width=int(dtype[2:]);require(1<=width<=64 and all(type(x) is str and len(x)<=width for x in values),'bounded Unicode values required')
        raw=b''.join(x.encode('utf-32-le')+b'\0'*(4*(width-len(x))) for x in values)
    else:raise ValueError('explicit safe numeric/Unicode dtype required; no pickle')
    header=repr({'descr':dtype,'fortran_order':False,'shape':shape}).encode('ascii')
    header+=b' '*((-10-len(header)-1)%64)+b'\n'
    require(len(header)<=10000 and len(raw)<=65536,'tiny NPY extent exceeded')
    return b'\x93NUMPY\x01\x00'+struct.pack('<H',len(header))+header+raw

def graphs():
    provenance={'schema_version':1,'kind':'synthetic-original-import-targets','generator':'registered-explicit-arrays-v1','node_denominators':[2,3]}
    files={'fixture_inputs/target-provenance.json':canonical(provenance)};source=sha(files['fixture_inputs/target-provenance.json']);result=[]
    recipes=[([[1.,0.,0.,1.],[0.,1.,1.,0.]],[[0,1],[1,0]],[[1.,0.],[0.,1.]]),([[1.,1.,0.,0.],[0.,1.,0.,1.],[1.,0.,1.,0.]],[[0,1,2],[1,2,0]],[[1.,0.],[0.,1.],[1.,1.]])]
    for i,(nf,ei,ef) in enumerate(recipes,1):
        n=len(nf);ids=[f'synthetic-{i}-{j:02d}' for j in range(n)];prefix=f'fixture_inputs/target-{i:02d}'
        config={'schema_version':1,'data_kind':'synthetic','node_width':4,'edge_width':2,'explicit_recipe':i}
        metadata={'asset':'ETH','start_utc':f'2022-01-{10 if i==1 else 17:02d}T00:00:00Z','end_utc':f'2022-01-{17 if i==1 else 24:02d}T00:00:00Z','available_at':f'2022-01-{17 if i==1 else 24:02d}T00:00:00Z','source_hashes':[source],'graph_config_hash':sha(canonical(config)),'raw_count':len(ef),'admitted_count':len(ef),'exclusion_counts':{}}
        value=metadata|{'node_ids':ids,'node_features':nf,'edge_index':ei,'edge_features':ef,'edge_aggregates':None};identity=sha(canonical(value))
        arrays={'node_ids':npy('<U'+str(max(map(len,ids))),(n,),ids),'node_features':npy('<f8',(n,4),sum(nf,[])),'edge_index':npy('<i8',(2,len(ef)),sum(ei,[])),'edge_features':npy('<f8',(len(ef),2),sum(ef,[]))}
        manifest={'metadata':metadata,'graph_hash':identity,'arrays':{name:{'path':name+'.npy','sha256':sha(raw),'bytes':len(raw)} for name,raw in arrays.items()}}
        for name,raw in arrays.items():files[prefix+'/'+name+'.npy']=raw
        path=prefix+'/manifest.json';files[path]=canonical(manifest)+b'\n';result.append({'graph_hash':identity,'nodes':n,'manifest':path,'sha256':sha(files[path])})
    return sorted(result,key=lambda x:x['graph_hash']),files

BACKEND={'name':'scalar_ranked_typed_graph','version':2,'device':'cpu','affinity':'scalar_float64','normalization':'scipy_float64','hardening':'stable_descending_row_major','objective':'sparse_scalar_float64','output':'float64_score','checkpoint_schema':3}
COMPACT='resident-native-compact-current-owner-v1'

def inputs(*,case,capsule,source_anchor,source_files,original_index,evidence,matching,environment):
    require(case in ('success','second_target_publication_failure'),'finite case required')
    require(type(source_anchor) is str and len(source_anchor)==40 and all(x in '0123456789abcdef' for x in source_anchor),'root committed source anchor required')
    require(Path(capsule).is_absolute(),'exact future absolute capsule required')
    require(len(source_files)==142,'complete composed package closure required')
    targets,files=graphs();inputs={}
    def put(name,value):
        path='fixture_inputs/'+case+'/'+name+'.json';files[path]=canonical(value);inputs[name]={'path':path,'sha256':sha(files[path]),'dataset':'synthetic'};return inputs[name]['sha256']
    roles={}
    for row in original_index['inputs']:
        path=row['origin'];name=('sample_intent' if path.endswith('neighborhoods/intent.json') else 'dictionary_intent' if path.endswith('dictionary/intent.json') else 'dictionary_result' if path.endswith('dictionary/result.json') else 'samples' if path.endswith('samples.json') else 'dictionary' if path.endswith('dictionary/dictionary.json') else 'dictionary_config' if path.endswith('config/dictionary.json') else 'matching_config' if path.endswith('matching-stable.json') else 'graph_manifest' if path.endswith('graph/manifest.json') else 'claim' if path.endswith('claim.json') else 'terminal' if path.endswith('failed.json') else 'gate')
        inp='original_'+name;inputs[inp]={'path':row['capsule_path'],'sha256':row['sha256'],'dataset':'original_dictionary'};roles[name]={'input':inp,'original_path':row['original_path'],'sha256':row['sha256']}
    graph_keys=[x['graph_hash'] for x in targets]
    control={'schema_version':1,'kind':'original-dictionary-import-v1','original_claim':original_index['original_claim'],'original_source':original_index['original_source'],'week':'2022-01-03','dictionary_identity':evidence['dictionary']['semantic_hash'],'sample_identity':evidence['dictionary']['sample_hash'],'sample_config':evidence['samples']['config_from_original_phase'],'seed':11,'sample_count':512,'motif_count':32,'required_graphs':graph_keys,'max_json_bytes':2*1024**2,'max_total_json_bytes':16*1024**2,'max_total_nodes':100000,'max_total_edges':200000,'refs':roles}
    import_hash=put('original_import',control);stage_hash=put('original_import_stage',{'schema_version':1,'max_numeric_bytes':16*1024**2,'max_stage_bytes':262144})
    limits={'max_state_bytes':1048576,'normalization_chunk_entries':65536,'hardening_chunk_entries':65536,'hardening_buffer_bytes':1048576,'max_score_buffer_bytes':1048576,'chunk_edges':65536,'max_checkpoint_bytes':262144,'max_publications':1,'total_checkpoint_bytes':1048576}
    pair={'schema_version':1,'backend':BACKEND,'limits':limits,'numerical_source':{'commit':source_anchor,'files':source_files}};pair_hash=put('pair_policy',pair)
    stage={'schema_version':1,'backend':COMPACT,'pair':limits,'schedule':{'operations_per_call':1000000,'calls_per_checkpoint':10000,'max_checkpoints':1,'max_total_checkpoints':160,'max_total_checkpoint_bytes':60*1024**2},'log':{'chunk_events':64,'max_events':512,'max_pairs':160,'max_logical_bytes':32*1024**2},'score_chunk_cells':64,'max_retained_logical_bytes':128*1024**2}
    envelope={'schema_version':1,'backend':COMPACT,'stage_policy':stage,'max_workflow_retained_logical_bytes':256*1024**2};compact_hash=put('compact_policy',envelope)
    put('mcm_policy',{'schema_version':1,'max_entries':160,'max_workflow_metadata_bytes':6*65536,'numeric':{'schema_version':1,'max_buffer_bytes':1048576,'edge_chunk':65536,'max_output_bytes':1048576,'max_numeric_bytes':2*1048576}})
    put('mcm_output_policy',{'schema_version':1,'backend':COMPACT,'max_artifact_bytes':1048576,'max_workflow_output_bytes':2*(1048576+65536)})
    mapping={}
    for i,t in enumerate(targets):
        name='target_graph_'+str(i+1);inputs[name]={'path':t['manifest'],'sha256':t['sha256'],'dataset':'synthetic'};mapping[t['graph_hash']]=name
        manifest=json.loads(files[t['manifest']])
        for a,info in manifest['arrays'].items():inputs[name+'_'+a]={'path':str(Path(t['manifest']).parent/info['path']),'sha256':info['sha256'],'dataset':'synthetic'}
    inputs['target_provenance']={'path':'fixture_inputs/target-provenance.json','sha256':sha(files['fixture_inputs/target-provenance.json']),'dataset':'synthetic'}
    descriptor={'arm':'proposed','dictionary_origin':'imported-original-v1','original_dictionary_import':{'input':'original_import','sha256':import_hash},'original_dictionary_stage':{'input':'original_import_stage','sha256':stage_hash},'pair_execution':{'backend':BACKEND,'policy_sha256':pair_hash},'compact_execution':{'backend':COMPACT,'policy_sha256':compact_hash},'configs':{'dictionary':evidence['dictionary']['config'],'matching':matching},'required_graphs':graph_keys,'resource_graph_inputs':mapping,'resource_fixture':{'schema_version':1,'case':case,'data_kind':'synthetic-targets-original-dictionary','target_nodes':{x['graph_hash']:x['nodes'] for x in targets},'target_provenance_input':'target_provenance'}}
    selected={'operation':'produce','plan_input':'producer_plan','producer':'original32','pair_checkpoint_input':'pair_policy','descriptor':descriptor,'original_dictionary_input':'original_import','compact_policy_input':'compact_policy','native_backend':COMPACT,'original_dictionary_stage_input':'original_import_stage','compact_mcm_input':'mcm_policy','compact_mcm_output_input':'mcm_output_policy'}
    put('producer_plan',{'schema_version':2,'producers':{'original32':selected|{'binding_output':'resource-binding.json','journal_output':'resource-journal.json'}}})
    put('environment',environment);put('execution_workspace',{'root':capsule,'ledger':str(Path(capsule)/'research_runs'),'artifacts':str(Path(capsule)/'research_artifacts'),'git_common':str(Path(capsule)/'.git')})
    G=1024**3;resource={'memory_max_bytes':3*G,'memory_high_bytes':3*G,'reserve_bytes':3*G,'start_reserve_bytes':6*G,'disk_floor_bytes':10*G,'disk_paths':[capsule],'wall_seconds':1800,'native_unit_limits':{'file_size_bytes':4194304},'storage_budget':{'root':capsule,'limits':{'max_allocated_bytes':G,'max_logical_bytes':G,'max_entries':32768,'max_depth':32,'max_scan_seconds':5}}}
    put('execution_job',{'schema_version':1,'kind':'compact_resource','resources':resource,'environment_input':'environment','payload':{'representation_jobs':{'original32':selected}}})
    return {'inputs':inputs,'targets':targets,'files':files,'job_path':inputs['execution_job']['path'],'workflow_identity':sha(canonical(descriptor)),'status':'unregistered-generated-inputs','source_anchor':source_anchor}


def registration(*,rendered,source_files,runtime_hashes,historical_gate,budget_reference):
    """Return draft gate bytes; coordinator commits/admit separately after review."""
    require(set(rendered)=={'success','second_target_publication_failure'},'both fixed primary cases required')
    family={'mechanism_id':'original-dictionary-import-engineering-v1','attempt_budget':2,'prior_attempts':0,'history_reference':'Separate synthetic authority/IO engineering only. Original eth-paper-resource-pilot-20260924-02 and its spent dictionary/samples remain terminal and are imported without rerun. No paper family/category allowance transfer.'}
    datasets={'synthetic':{'identity':'original-import-explicit-tiny-targets-v1','history_reference':'Generated deterministic synthetic targets; no financial data or inference','exposures':[{'start':'2022-01-10T00:00:00Z','end':'2022-01-24T00:00:00Z','state':'spent'}]},'original_dictionary':{'identity':'original-ethereum-jan03-dictionary-48832eeb','history_reference':'Existing original dictionary component complete inside closed failed historical parent; original ancestry preserved','exposures':[{'start':'2022-01-03T00:00:00Z','end':'2026-01-01T00:00:00Z','state':'spent'}]}}
    require(historical_gate['families']=={'import-engineering':family} and historical_gate['datasets']==datasets,'historical family/datasets changed')
    require(set(budget_reference)=={'extension','review'},'exact cumulative review reference required')
    gate={'schema_version':1,'program_id':'original-dictionary-import-engineering-2026-10-02','families':{'import-engineering':family},'datasets':datasets,'experiments':dict(historical_gate['experiments'])};files={}
    for case,item in rendered.items():
        identity='original-import-native-'+('success' if case=='success' else 'publication-failure')+'-20261003-02'
        denominator=('Both targets must publish and complete all160 scalar-reference comparisons.' if case=='success' else
            'The first target must publish and complete64 scalar-reference comparisons. The second target has96 numerical cells; authenticate its actual retained completed stage separately, while its deliberately failed publication and scalar-reference comparison remain unavailable. Never report160 completed comparisons for this failure case.')
        charter=('Synthetic engineering '+case+'. Import original complete32-motif dictionary and512samples without rerun. Two genuine targets. '+denominator+
            ' Native3GiB/swap0/1800s/file4MiB/whole-tree sampled1GiB/floor10GiB. Expected publication failure remains failed lifecycle. The earlier failed metadata-preflight identity stays spent. Cumulative engineering3 includes that failure and these two fresh fixed02 identities. No financial fit, numerical paper agreement or full-size capacity conclusion. Mutation/legacy refusal acceptance is separate and pending.\n').encode()
        path='fixture_inputs/successor02/'+case+'/charter.md';files[path]=charter
        exp={'family':'import-engineering','parent':'original-import-native-success-20261003-01','charter':{'path':path,'sha256':sha(charter)},'question':'Does the exact genuine imported-original32 typed MCM route preserve both target outputs and terminal failure semantics under the registered native engineering envelope?','stage':'development','reuse':'exploratory','windows':[{'dataset':'synthetic','start':'2022-01-10T00:00:00Z','end':'2022-01-24T00:00:00Z','availability':'existing'},{'dataset':'original_dictionary','start':'2022-01-03T00:00:00Z','end':'2026-01-01T00:00:00Z','availability':'existing'}],'inputs':item['inputs'],'source_files':source_files,'runtime_hashes':runtime_hashes,'selection':None,'cells':['import-target-01','import-target-02'],'outputs':['resource-binding.json','resource-journal.json','cell-ledger.json','resource-summary.json']}
        exp['cumulative_budget_extension']=budget_reference
        require(identity not in gate['experiments'],'fresh engineering identity already registered')
        gate['experiments'][identity]=exp
    return gate,files

# New held-resource metadata planning ONLY. No legacy graphs/registration call.
HELD_ROLES=('runtime','software_environment','native_environment','native_policy','original_import_index','original_evidence','matching','target_catalog','case_contract','registration','budget_extension','budget_review','charter')

def _held_ref(row):
    require(type(row) is dict and set(row)=={'path','sha256','bytes'},'exact held metadata/input reference required')
    p=Path(row['path']);require(type(row['path']) is str and str(p)==row['path'] and not p.is_absolute() and '..' not in p.parts and not any(x in ('keys','apis','.env','hf_token.txt','.git','.venv') or x.startswith('.env.') for x in p.parts),'unsafe held reference')
    require(type(row['sha256']) is str and len(row['sha256'])==64 and all(x in '0123456789abcdef' for x in row['sha256']),'held SHA256 required')
    require(type(row['bytes']) is int and 0<row['bytes']<=4*1024**2,'held per-file reference bound')
    return dict(row)

def held_input_plan(roles,source_plan):
    """Build concrete finite input/native/source joins from already-read metadata.

    Caller-facing output always remains unregistered. Root draft helper performs
    actual source/Git and referenced-body reads anew rather than trusting this
    dictionary as a capability. No arrays are constructed or opened here.
    """
    require(type(roles) is dict and set(roles)<=set(HELD_ROLES),'unknown held metadata role')
    require(type(source_plan) is dict and source_plan.get('source_count')==199 and source_plan.get('package_count')==148 and source_plan.get('execution_admitted') is False,'actual199/148 metadata plan required')
    missing=[n for n in HELD_ROLES if roles.get(n) is None];observed={};inputs={}
    for name,value in roles.items():
        if value is None:continue
        require(type(value) is dict and set(value)=={'reference','document'},'held role body/reference pair required')
        observed[name]=_held_ref(value['reference'])
    require(sum(x['bytes'] for x in observed.values())<=4*1024**2,'held metadata role aggregate bound')
    runtime=roles.get('runtime')
    if runtime is not None:
        r=runtime['document'];require(type(r) is dict and type(r.get('distribution_records')) is list and len(r['distribution_records'])==251,'full251 runtime RECORD metadata required')
        require(all(type(x) is dict and all(k in x for k in ('name','version','record','record_sha256')) for x in r['distribution_records']) and len({x['name'] for x in r['distribution_records']})==251,'runtime RECORD denominator/fields')
        require(r.get('lock_sha256')==source_plan['source_files']['uv.lock'],'runtime lock/source mismatch')
    native=roles.get('native_policy')
    if native is not None:
        n=native['document'];G=1024**3
        require(type(n) is dict and n.get('memory_max_bytes')==n.get('memory_high_bytes')==3*G and n.get('reserve_bytes')==3*G and n.get('start_reserve_bytes')==6*G and n.get('disk_floor_bytes')==10*G and n.get('wall_seconds')==1800 and n.get('native_unit_limits')=={'file_size_bytes':4194304},'held native envelope must retain exact reviewed limits')
        require(n.get('disk_paths')==[source_plan['root']] and n.get('storage_budget',{}).get('root')==source_plan['root'],'native writable root differs')
    original=roles.get('original_import_index')
    if original is not None:
        v=original['document'];require(type(v) is dict and type(v.get('inputs')) is list and len(v['inputs'])==11 and type(v.get('original_source')) is str and len(v['original_source'])==40 and type(v.get('original_claim')) is str,'original11/source/claim provenance required')
        for row in v['inputs']:
            require(type(row) is dict and set(row)=={'name','reference','original_path'},'original input row schema')
            name=row['name'];require(type(name) is str and name.startswith('original_') and name not in inputs and type(row['original_path']) is str,'original role identity')
            inputs[name]=_held_ref(row['reference'])|{'dataset':'original_dictionary','original_path':row['original_path']}
    evidence=roles.get('original_evidence')
    if evidence is not None:
        e=evidence['document'];require(type(e) is dict and e.get('sample_count')==512 and type(e.get('sample_count')) is int and e.get('motif_count')==32 and type(e.get('motif_count')) is int and e.get('resample') is False and e.get('recluster') is False,'original512/32 import-only evidence required')
    catalog=roles.get('target_catalog');targets=[]
    if catalog is not None:
        t=catalog['document'];require(type(t) is dict and set(t)=={'schema_version','kind','targets'} and type(t['schema_version']) is int and t['schema_version']==1 and t['kind']=='registered-imported-held-targets-v1' and type(t['targets']) is list and len(t['targets'])==2,'exact two-target metadata catalog required')
        for row in t['targets']:
            require(type(row) is dict and set(row)=={'graph_hash','nodes','input_name','manifest','components'},'target role schema')
            h=row['graph_hash'];require(type(h) is str and len(h)==64 and all(x in '0123456789abcdef' for x in h) and type(row['nodes']) is int and row['nodes']>0,'target metadata dimensions/hash')
            require(type(row['input_name']) is str and row['input_name'] not in inputs,'target input identity')
            inputs[row['input_name']]=_held_ref(row['manifest'])|{'dataset':'synthetic'}
            require(type(row['components']) is dict and set(row['components'])=={'node_ids','node_features','edge_index','edge_features'},'all four original target components required')
            for name,ref in row['components'].items():inputs[row['input_name']+'_'+name]=_held_ref(ref)|{'dataset':'synthetic'}
            targets.append({'graph_hash':h,'nodes':row['nodes'],'input_name':row['input_name']})
        require([x['graph_hash'] for x in targets]==sorted({x['graph_hash'] for x in targets}) and sorted(x['nodes'] for x in targets)==[2,3],'deterministic complete target order/denominator differs')
    case=roles.get('case_contract');documents={};experiment=None
    if case is not None:
        c=case['document'];require(type(c) is dict and set(c)=={'schema_version','kind','program_id','experiment_id','job_input','plan_input','representation','producer','held_policy_input','readback_outputs','additional_inputs'},'root case contract schema')
        require(type(c['schema_version']) is int and c['schema_version']==1 and c['kind']=='root-selected-imported-held-resource-v1','root selected resource case required')
        experiment=c['experiment_id'];require(type(experiment) is str and experiment and not experiment.startswith(('compact-cold-','original-import-native-')),'closed/cold scientific identity refused')
        require(type(c['readback_outputs']) is dict and (not targets or set(c['readback_outputs'])=={x['graph_hash'] for x in targets}),'complete root selected readback output roles')
        require(len(set(c['readback_outputs'].values()))==len(c['readback_outputs']) and all(type(x) is str and Path(x).name==x and x.endswith('.json') for x in c['readback_outputs'].values()),'unique readback output names')
        require(type(c['additional_inputs']) is dict and len(c['additional_inputs'])<=64,'bounded additional input roles')
        for name,row in c['additional_inputs'].items():
            require(type(name) is str and name not in inputs and type(row) is dict and set(row)=={'reference','dataset'},'distinct additional input role')
            require(row['dataset'] in ('synthetic','original_dictionary'),'declared held dataset');inputs[name]=_held_ref(row['reference'])|{'dataset':row['dataset']}
        if targets:
            policy={'schema_version':1,'kind':'original-import-held-score-readback-v1','targets':{x['graph_hash']:{'output':c['readback_outputs'][x['graph_hash']]} for x in targets},'part_bytes':1048576,'max_read_bytes':max(x['nodes'] for x in targets)*32*8,'max_members':32767}
            documents[c['held_policy_input']]={'raw_utf8':canonical(policy).decode(),'sha256':sha(canonical(policy)),'bytes':len(canonical(policy))}
        reg=roles.get('registration')
        if reg is not None:
            r=reg['document'];require(r.get('program_id')==c['program_id'] and experiment in r.get('experiments',{}),'root current registration missing selected experiment')
            exp=r['experiments'][experiment];require(exp.get('source_files')==source_plan['source_files'],'registered199 source map differs')
            require(set(c['readback_outputs'].values())<=set(exp['outputs']),'held outputs absent from root registration')
            require(exp.get('cumulative_budget_extension') is not None,'reviewed cumulative accounting role required')
    require(len(inputs)<=128 and len({x['path'] for x in inputs.values()})==len(inputs),'complete input roles overlap or exceed finite bound')
    return {'schema_version':1,'kind':'held-resource-input-metadata-plan-v1','status':'unregistered-metadata-only','source':source_plan['source'],'anchor':source_plan['anchor'],'root':source_plan['root'],'source_count':199,'package_count':148,'observed_metadata':observed,'input_rows':dict(sorted(inputs.items())),'target_rows':targets,'rendered_metadata':documents,'experiment_id':experiment,'remaining_roles':missing,'execution_admitted':False,'runtime_installed_verified':False,'arrays_generated':False,'original_sampling_rerun':False}

def generate_held_arrays(*args,**kwargs):
    raise ValueError('held array generation requires a separately implemented genuine guarded input-materialization entry, fresh root registration and finite native release; metadata plans cannot authorize it')
