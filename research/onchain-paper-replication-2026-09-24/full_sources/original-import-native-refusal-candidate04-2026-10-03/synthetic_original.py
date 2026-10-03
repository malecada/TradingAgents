"""Explicit fabricated metadata; not an empirical dictionary or authority."""
import json,hashlib
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def fixture():
    cfg={'size':32,'sample_count':512,'hop_depth':1,'maximum_neighborhood_nodes':10}
    matching={'alpha':0.5,'max_iterations':100}; gh='a'*64
    graphs=[{'node_ids':[f'n{i}'],'node_features':[[float(i),0,0,0]],'edge_index':[[],[]],
             'edge_features':[],'edge_width':2,'center_id':f'n{i}','parent_hash':gh} for i in range(512)]
    records=[{'graph_hash':gh,'center_id':f'n{i}','center_index':i,'probability':1/(512-i),'node_count':1,'edge_count':0} for i in range(512)]
    rng={'bit_generator':'PCG64','state':{'state':123,'inc':5},'has_uint32':0,'uinteger':0}
    scfg=cfg|{'train_start':'2022-01-03T00:00:00Z','train_end':'2026-01-01T00:00:00Z'}
    sampleid=sha(canonical({'training_graphs':[gh],'config':scfg,'seed':11,'records':records,'rng_state':rng}))
    samples={'graphs':graphs,'records':records,'source_hashes':[gh],'rng_state':rng,'seed':11,'identity':sampleid}
    dictionary={'representatives':graphs[:32],'memberships':[list(range(i,512,32)) for i in range(32)],'sample_hash':sampleid,
      'training_graph_hashes':[gh],'config':cfg,'matching_config_hash':sha(canonical(matching)),'hierarchy':[]}
    science={'graphs':[{'nodes':g['node_ids'],**{k:g[k] for k in ('node_features','edge_index','edge_features','parent_hash','center_id')}} for g in dictionary['representatives']],
      'sample_hash':sampleid,'training_graph_hashes':[gh],'config':cfg,'matching_hash':dictionary['matching_config_hash'],'memberships':dictionary['memberships'],'hierarchy':[]}
    dictionary['identity']=sha(canonical(science))
    values={'dictionary':dictionary,'samples':samples,'dictionary_config':cfg,'matching_config':matching,
      'graph_manifest':{'graph_hash':gh,'metadata':{'start_utc':scfg['train_start'],'available_at':'2022-01-11T00:00:00Z'}},
      'gate':{'experiments':{'old':{'parent':None}}}}
    paths={k:'/original/'+k+'.json' for k in values}
    values['claim']={'experiment_id':'old','source':'b'*40,'design_source':'b'*40,'registration':'gate.json','registration_sha256':sha(canonical(values['gate'])),'experiment':{'parent':None},'prior_exposures':[{'state':'spent'}]}
    values['terminal']={'experiment_id':'old','status':'failed','claim_sha256':sha(canonical(values['claim']))}
    values['dictionary_intent']={'source_commit':'b'*40,'phase':'dictionary','week':'2022-01-03','bindings':{paths['samples']:sha(canonical(samples)),paths['dictionary_config']:sha(canonical(cfg)),paths['matching_config']:sha(canonical(matching))}}
    values['sample_intent']={'source_commit':'b'*40,'phase':'neighborhoods','week':'2022-01-03','bindings':{paths['graph_manifest']:sha(canonical(values['graph_manifest'])),paths['dictionary_config']:sha(canonical(cfg))}}
    values['dictionary_result']={'phase':'dictionary','week':'2022-01-03','status':'complete','details':{'identity':dictionary['identity'],'motifs':32,'resource_only':True}}
    for k in values:paths.setdefault(k,'/original/'+k+'.json')
    blobs={k:canonical(v) for k,v in values.items()}
    policy={'schema_version':1,'kind':'original-dictionary-import-v1','original_claim':'old','original_source':'b'*40,
      'week':'2022-01-03','dictionary_identity':dictionary['identity'],'sample_identity':sampleid,'sample_config':scfg,'seed':11,
      'sample_count':512,'motif_count':32,'required_graphs':[gh],'max_json_bytes':1048576,'max_total_json_bytes':4194304,
      'max_total_nodes':1024,'max_total_edges':1024,'refs':{k:{'input':k,'original_path':paths[k],'sha256':sha(v)} for k,v in blobs.items()}}
    return policy,blobs
