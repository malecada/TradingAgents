"""Future guarded input materialization; no production or admission by this file."""
from dataclasses import asdict
from datetime import datetime,timedelta,timezone
import json
from pathlib import Path

RECIPE={'schema_version':1,'kind':'fresh-synthetic-cold-population-v1','asset':'ETH','seed':11,'nodes':4,
 'graph_start':'2024-01-01','graph_weeks':19,'price_start':'2023-12-04','price_end':'2024-05-13',
 'missing_price':'2024-02-18','train_start':'2024-01-01T00:00:00Z','train_end':'2024-05-01T00:00:00Z',
 'test_start':'2024-05-01T00:00:00Z','test_end':'2024-05-13T00:00:00Z',
 'sample_count':32,'dictionary_size':32,'lookback_days':28,'batch_size':16,
 'price_formula':'100 + i/10 + (i%7)/20','node_formula':'1 + week/100 + node/10 + feature/1000',
 'edges':[[0,1],[1,2],[2,3],[3,0]],'edge_formula':'1 + week/100 + edge/10 + feature/1000'}


def materialize(run,p,directory):
    # Called only by selected() after genuine guard/claim/source checks.
    from .compact_cold_proof import require,_read,_write,_batches,KIND,IDENTITIES,CELL,ARTIFACT
    require(_read(run,p['inputs']['recipe'])==RECIPE,'frozen synthetic recipe changed')
    import numpy as np
    from .contracts import GraphSnapshot,PricePanel
    from .dataset import build_examples,fit_scaler
    from .calendar import build_folds
    from .neighborhoods import graph_hash
    from .graph_store import save_graph
    from .job_payload import population_record
    from .registered_features import representation_descriptor
    from .provenance import canonical_bytes,digest,file_hash,sync_directory
    from . import compact_policy,matching_pair,compact_native_producer,compact_cold_features
    from .compact_cold_proof import PROGRAM
    cfg=_read(run,p['inputs']['configs']);model=_read(run,p['inputs']['model']);training=_read(run,p['inputs']['training'])
    require(set(cfg)=={'graph','dictionary','matching','baselines'},'science config collection differs')
    require(cfg['dictionary']['sample_count']==32 and cfg['dictionary']['size']==32 and model['mcm_input']==32 and model['lookback_days']==28 and training['batch_size']==16,'synthetic full architecture dimensions differ')
    inputs={};cap=p['max_file_bytes']
    def put(name,value):
        path=directory/(name+'.json');_write(path,value,cap)
        inputs[name]={'path':str(path.relative_to(run.admission.root)),'sha256':file_hash(path),'dataset':'synthetic-cold'}
        return inputs[name]['sha256']
    graph_config_hash=digest(canonical_bytes(cfg['graph']));graphs=[];refs={}
    start=datetime.fromisoformat(RECIPE['graph_start']).replace(tzinfo=timezone.utc)
    stamp=lambda t:t.isoformat().replace('+00:00','Z')
    for week in range(RECIPE['graph_weeks']):
        a=start+timedelta(weeks=week);b=a+timedelta(days=7)
        source=digest(canonical_bytes({'recipe':RECIPE,'week':week}))
        nodes=np.asarray([[1+week/100+n/10+f/1000 for f in range(4)] for n in range(4)],dtype=np.float64)
        edges=np.asarray(RECIPE['edges'],dtype=np.int64).T
        attrs=np.asarray([[1+week/100+e/10+f/1000 for f in range(2)] for e in range(4)],dtype=np.float64)
        g=GraphSnapshot('ETH',stamp(a),stamp(b),stamp(b+timedelta(days=1)),(source,),graph_config_hash,tuple('synthetic-node-'+str(n) for n in range(4)),nodes,edges,attrs,4,4,{})
        h=graph_hash(g);manifest=save_graph(directory/'graphs'/('week-'+str(week).zfill(2)),g)
        name='graph-'+str(week).zfill(2);inputs[name]={'path':str(manifest.relative_to(run.admission.root)),'sha256':file_hash(manifest),'dataset':'synthetic-cold'};refs[h]={'input':name};graphs.append(g)
    begin=datetime.fromisoformat(RECIPE['price_start']);end=datetime.fromisoformat(RECIPE['price_end']);dates=[];values=[]
    for i in range((end-begin).days):
        day=(begin+timedelta(days=i)).date().isoformat()
        if day==RECIPE['missing_price']:continue
        dates.append(day);values.append(100+i/10+(i%7)/20)
    prices=PricePanel('ETH-USD',tuple(dates),tuple(values),(),digest(canonical_bytes(RECIPE)),stamp(end.replace(tzinfo=timezone.utc)))
    coverage={'kind':'fresh-synthetic-only','recipe_sha256':digest(canonical_bytes(RECIPE)),'graphs':sorted(refs),'prices_source':prices.source_hash}
    row={'id':'synthetic-cold',**{k:RECIPE[k] for k in ('train_start','train_end','test_start','test_end')},'validation_start':None,'validation_end':None}
    calendar={'schema_version':1,'lookback_days':28,'folds':[row]};fold=build_folds(calendar,coverage)[0]
    examples=build_examples(graphs,prices,fold,calendar);scaler=fit_scaler(examples,prices,fold);batches=_batches(examples)
    put('population',population_record(examples,scaler));put('model',model);put('training',training);put('calendar',calendar);put('coverage',coverage)
    control={'schema_version':1,'example_manifest_sha256':digest(canonical_bytes({**vars(examples),'train':[asdict(x) for x in examples.train],'test':[asdict(x) for x in examples.test]}))}
    pair={'max_state_bytes':100000,'normalization_chunk_entries':64,'hardening_chunk_entries':2,'hardening_buffer_bytes':4096,'max_score_buffer_bytes':4096,'chunk_edges':2,'max_checkpoint_bytes':400000,'max_publications':10,'total_checkpoint_bytes':5000000}
    stage={'schema_version':1,'backend':compact_policy.BACKEND,'pair':pair,
      'schedule':{'operations_per_call':10000,'calls_per_checkpoint':64,'max_checkpoints':4,'max_total_checkpoints':10,'max_total_checkpoint_bytes':6000000},
      'log':{'chunk_events':64,'max_events':3000,'max_pairs':1024,'max_logical_bytes':1048576},'score_chunk_cells':64,'max_retained_logical_bytes':10000000}
    compact_policy.validate(stage,kind='dictionary',pairs=992);compact_policy.validate(stage,kind='mcm',pairs=128)
    anchor=_read(run,p['inputs']['anchor'])
    require(set(anchor)=={'commit','files'} and type(anchor['commit']) is str and len(anchor['commit'])==40 and anchor['files'],'genuine numerical source anchor required')
    policies={
      'pair_checkpoint':{'schema_version':1,'backend':matching_pair.BACKEND,'limits':pair,'numerical_source':anchor},
      'compact_policy':{'schema_version':1,'backend':compact_policy.BACKEND,'stage_policy':stage,'max_workflow_retained_logical_bytes':200000000},
      'compact_training':control,
      'compact_sampler':{'schema_version':1,'kernel':'resident-leased-v1','max_metadata_bytes':65536,'max_attempt_bytes':35*65536,'limits':{'schema_version':1,'max_centers':1000,'max_direct_weight_bytes':16000,'neighborhood':{'schema_version':1,'mode':'array','max_buffer_bytes':65536,'edge_chunk':8,'max_sample_array_bytes':65536}}},
      'compact_samples':{'schema_version':1,'max_manifest_bytes':65536,'max_artifact_bytes':1000000,'max_resident_array_bytes':1000000,'max_attempt_bytes':1024576},
      'compact_dictionary':{'schema_version':1,'max_matrix_bytes':65536,'max_identity_array_bytes':65536,'max_manifest_bytes':65536,'max_artifact_bytes':1000000,'max_loaded_array_bytes':65536,'max_attempt_bytes':1024576},
      'compact_mcm':{'schema_version':1,'max_entries':128,'max_workflow_metadata_bytes':1048576,'numeric':{'schema_version':1,'max_buffer_bytes':65536,'edge_chunk':2,'max_output_bytes':4000,'max_numeric_bytes':69536}},
      'compact_mcm_output':{'schema_version':1,'backend':compact_policy.BACKEND,'max_artifact_bytes':12192,'max_workflow_output_bytes':1048576},
      'compact_feature':{'schema_version':1,'chunk_entries':64,'max_numeric_bytes':65536},
      'compact_graph_output':{'schema_version':1,'max_manifest_bytes':32768,'max_artifact_bytes':65536,'max_resident_array_bytes':65536,'max_workflow_output_bytes':2000000},
      'compact_denominator':{'schema_version':1,'calendar_input':'calendar','coverage_input':'coverage','max_calendar_days':180},
      'compact_closure':{'schema_version':1,'max_graphs':19,'max_record_bytes':1048576,'max_numeric_payload_bytes':1048576},
      'compact_publication':{'schema_version':1,'max_metadata_bytes':1048576,'max_attempt_bytes':4194304},
      'compact_terminal':{'schema_version':1,'max_metadata_bytes':1048576,'max_attempt_bytes':8388608},
      'compact_native_features':{'schema_version':1,'max_live_tensor_bytes':576*max(len({h for i in indices for h in examples.train[i].graph_hashes}) for _,indices in batches),'max_numeric_bytes':4194304,'chunk_entries':64}}
    for name,value in policies.items():put(name,value)
    descriptor=representation_descriptor(graphs,examples,fold,'proposed',11,cfg)
    descriptor.update(pair_execution={'backend':matching_pair.BACKEND,'policy_sha256':inputs['pair_checkpoint']['sha256']},compact_execution={'backend':compact_policy.BACKEND,'policy_sha256':inputs['compact_policy']['sha256']},compact_training={'input':'compact_training','sha256':inputs['compact_training']['sha256']})
    identity=digest(canonical_bytes(descriptor));future=_read(run,p['inputs']['future_resources'])
    cold={'schema_version':1,'kind':compact_cold_features.KIND,'evidence_roots':sorted('research_artifacts/'+n+'/'+identity for n in compact_native_producer.NAMESPACES),'watch':future['storage_budget'],'handoff_output':'cold-handoff.json','max_metadata_bytes':2097152,'max_files':20000,'max_directories':2000,'max_total_bytes':268435456,'max_file_bytes':4194304,'max_depth':20,'chunk_bytes':65536}
    put('compact_cold_handoff',cold)
    selection={'schema_version':1,'kind':KIND,'phase':'compare','experiment':IDENTITIES['compare'],'output':'proof-compare.json','inputs':{'population':'population','model':'model','training':'training'},'source_files':p['source_files'],'watch':future['storage_budget'],'max_file_bytes':4194304,'max_total_bytes':268435456}
    put('cold_proof',selection)
    job={'operation':'produce','plan_input':'plan','producer':'synthetic-producer','native_backend':compact_policy.BACKEND,'descriptor':descriptor,'binding_output':'binding.json','journal_output':'journal.json','graphs':refs,'compact_dictionary_count_policy':'capacity-with-exact-completion-v1','max_graph_payload_bytes':1048576,'compact_cold_handoff_input':'compact_cold_handoff','cold_proof_input':'cold_proof'}
    job.update({name:name.removesuffix('_input') for name in compact_native_producer.ROUTES})
    job.update({name:None for name in compact_native_producer.UNSUPPORTED})
    put('plan',{'schema_version':2,'producers':{'synthetic-producer':job}})
    payload={'cold_proof_input':'cold_proof','representation_jobs':{'cold-proof':job}}
    put('future_execution_job',{'schema_version':1,'kind':'fit','environment_input':'environment','resources':future,'payload':payload})
    # Environment is captured/frozen by root immediately before registration;
    # materialization is never a registration or a successful future admission.
    result={'status':'materialized','program_id':PROGRAM,'future_identity':IDENTITIES['compare'],'future_cell':CELL['compare'],'future_outputs':['binding.json','journal.json','cold-handoff.json','proof-compare.json'],
      'inputs':inputs,'execution_input_rename':{'future_execution_job':'execution_job'},'environment_input_pending':True,'registration_pending':True,
      'train_rows':len(examples.train),'test_rows':len(examples.test),'excluded_rows':len(examples.exclusions),'graph_population':len(graphs),'required_graphs':len(descriptor['required_graphs']),
      'batches':[{'kind':kind,'indices':indices,'decisions':[examples.train[i].decision_at for i in indices]} for kind,indices in batches],
      'fresh_sample_count':32,'dictionary_size':32,'dictionary_max_pairs':992,'mcm_pairs_per_required_graph':128,'historical_jobs_reopened':False}
    _write(directory/'future-inputs.json',result,cap);sync_directory(directory)
    return result
