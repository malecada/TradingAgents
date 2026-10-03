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
    put('mcm_policy',{'schema_version':1,'max_entries':160,'max_workflow_metadata_bytes':6*65536,'numeric':{'schema_version':1,'max_buffer_bytes':1048576,'edge_chunk':4096,'max_output_bytes':1048576,'max_numeric_bytes':2*1048576}})
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
        identity='original-import-native-'+('success' if case=='success' else 'publication-failure')+'-20261003-03'
        denominator=('Both targets must publish and complete all160 scalar-reference comparisons.' if case=='success' else
            'The first target must publish and complete64 scalar-reference comparisons. The second target has96 numerical cells; authenticate its actual retained completed stage separately, while its deliberately failed publication and scalar-reference comparison remain unavailable. Never report160 completed comparisons for this failure case.')
        charter=('Synthetic engineering '+case+'. Import original complete32-motif dictionary and512samples without rerun. Two genuine targets. '+denominator+
            ' MCMArrayNeighborhoodIndex uses edge_chunk4096/max_buffer1048576B: the exact registered2/3-node constructor allowances are655600/655692B. This declared preclaim resource correction changes chunk capacity, not matching/model mathematics. Native3GiB/swap0/1800s/file4MiB/whole-tree sampled1GiB/floor10GiB. Expected publication failure remains failed lifecycle. Both earlier FAILEDmetadata01 and FAILEDmissing-hook02 identities stay spent. Cumulative engineering4 retains both actual FAILED01metadata and FAILED02missing-module attempts and only these two fresh fixed03 identities. Exact cleanup-only composition preserves original numerical bodies and complete selected imports; old attempts remain spent. No financial fit, numerical paper agreement or full-size capacity conclusion. Mutation/legacy refusal acceptance is separate and pending.\n').encode()
        path='fixture_inputs/successor03/'+case+'/charter.md';files[path]=charter
        exp={'family':'import-engineering','parent':'original-import-native-success-20261003-02','charter':{'path':path,'sha256':sha(charter)},'question':'Does the exact genuine imported-original32 typed MCM route preserve both target outputs and terminal failure semantics under the registered native engineering envelope?','stage':'development','reuse':'exploratory','windows':[{'dataset':'synthetic','start':'2022-01-10T00:00:00Z','end':'2022-01-24T00:00:00Z','availability':'existing'},{'dataset':'original_dictionary','start':'2022-01-03T00:00:00Z','end':'2026-01-01T00:00:00Z','availability':'existing'}],'inputs':item['inputs'],'source_files':source_files,'runtime_hashes':runtime_hashes,'selection':None,'cells':['import-target-01','import-target-02'],'outputs':['resource-binding.json','resource-journal.json','cell-ledger.json','resource-summary.json']}
        exp['cumulative_budget_extension']=budget_reference
        require(identity not in gate['experiments'],'fresh engineering identity already registered')
        gate['experiments'][identity]=exp
    return gate,files

