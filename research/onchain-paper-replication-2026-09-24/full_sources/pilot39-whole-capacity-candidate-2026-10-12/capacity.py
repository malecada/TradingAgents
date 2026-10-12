"""Pure scalar whole39 storage arithmetic. Never scans, imports numerics or admits."""
GIB=1024**3
WHOLE_NODES={'0114d61904938208c75497bdabe82c5dae32b7d2110a4e460d1942f84dc473ba': 1768268, '0e60be7088611cebfd04839fcc7bb4aa4fdd05a28d84e27aeaf9456391997459': 2265481, '2c9ec1d381e8177a8b22e9dfd993302a00cae020c59c5127e8df0ecf9d867531': 1878300, '683ed5f988ebdf4059ce3f0e361f3e31916cff9c75d83ba8edd76ae4f79a781c': 1581441, '7d0a20456b83db5caf7d916be09ea9fec34bf60867fb5ff628a300b4681800cb': 1875043, '825e2c15cf6126c684a90f2e29589cc4fd4914bc4699675ac6783e809817fc75': 2048710, 'efdd6d32f8f2457477e765a25f6ec03c75df8b90d69de21bf64b2cfa2d0f3805': 1581761}
LIMITS={'logical_file_bytes':16*GIB,'allocated_bytes':20*GIB,'entries':1000000,'disk_floor_bytes':10*GIB,'memory_max_bytes':6*GIB,'memory_high_bytes':5*GIB,'swap_max_bytes':0,'cpus':2,'wall_seconds':28800,'startup_reserve_bytes':5*GIB//2}
def require(ok,why):
    if not ok:raise ValueError(why)
def integer(n,label):
    require(type(n) is int and 0<=n<2**63,label+' must be an explicit nonnegative bounded integer');return n
def ceildiv(n,d):return (n+d-1)//d
def allocated(n):return ceildiv(n,4096)*4096
def header_bounds(file_bytes,payload_bytes=None):
    integer(file_bytes,'file bytes')
    if payload_bytes is not None:
        integer(payload_bytes,'payload bytes');h=file_bytes-payload_bytes
        require(10<=h<=10012,'NPY header extent out of accepted loader bounds');return [h,h]
    require(file_bytes>=10,'NPY extent too short');return [10,min(10012,file_bytes)]
def graph_growth(metadata):
    require(metadata['batch_cells']==4096 and metadata['group_batches']==16 and metadata['journal_body_bytes']==4096,'changed batching requires recalculation')
    require(metadata['continuation_manifest_input'] is None and metadata['graph_manifest_inputs']=={},'parent recovery route requires new copy terms')
    require({k:v['nodes'] for k,v in metadata['graphs'].items()}==WHOLE_NODES,'exact seven whole graph cardinalities required')
    result=[]
    for key,v in sorted(metadata['graphs'].items()):
        n=integer(v['nodes'],'nodes');require(n>0 and v['motifs']==32,'whole nodes and dictionary32 required')
        cells=32*n;batches=ceildiv(cells,4096);groups=ceildiv(batches,16)
        require(v['output_bytes']==4*cells,'whole output extent differs')
        require(v['original_parent_bytes']>=v['edge_index_file_bytes'],'retained parent metadata absent')
        header_bounds(v['node_features_file_bytes'],32*n);header_bounds(v['edge_index_file_bytes'])
        low=max(0,ceildiv(v['edge_index_file_bytes']-10012,16));high=(v['edge_index_file_bytes']-10)//16
        tar={1024:0,4096:0}
        for start in range(0,batches,16):
            for cap in tar:
                lengths=[]
                for b in range(start,min(start+16,batches)):
                    lengths.extend((cap,92+53*min(4096,cells-4096*b),cap))
                extent=ceildiv(sum(512+ceildiv(x,512)*512 for x in lengths)+1024,10240)*10240
                require(extent<=v['bundle_chunk_bytes']<=4*1024**2,'group scratch envelope exceeded')
                tar[cap]+=extent
        require(tar[4096]==v['bundle_preserved_bytes'] and 2*tar[4096]==v['bundle_recovered_bytes'],'typed whole bundle extent differs')
        require(v['bundle_operations']==2*groups and v['bundle_chunks']==3*groups,'group count contract differs')
        result.append({'graph':key,'nodes':n,'cells':cells,'batches':batches,'groups':groups,'retained_origins_bytes':9*cells,'retained_summaries_bytes':8192*batches,'spool_and_output_bytes':8*cells,'prefix_bytes':4096*batches,'prefix_entries':batches,'new_group_tar_bytes':tar[4096],'cumulative_transport_addition_not_retained':4*(tar[4096]-tar[1024]),'retained_input_parent_bytes':v['original_parent_bytes'],'edge_payload_byte_interval':[16*low,16*high],'node_feature_header_bytes':header_bounds(v['node_features_file_bytes'],32*n)[0],'raw_output_header_bytes':0})
    require(sum(v['cells'] for v in result)==415968128 and sum(v['batches'] for v in result)==101559 and sum(v['groups'] for v in result)==6352,'whole cardinality changed')
    return result
# Inherited accepted full-route storage terms before continuation delta. No
# downward credit for already retained journals/checkpoints is applied.
BASE_TERMS={
 'scores_origins_summaries_spool_output_work_typed_receipts':(9086624428,9480953856),
 'checkpoint_one_fatal_live_attempt':(273838080,273838080),
 'temporary_group_archive_and_recovery_journal':(16090560,16352640),
 'retained_transport_controls_diagnostics_failure':(236017056,236283231),
 'runtime_temp_cache_residual':(268407622,288063488),
 'owner_stage_publication_sidecars':(1089536,1089536+4095*62),
 'training_lifecycle_residual':(33043195,33314748),
 'current_metadata_headroom':(1048576,1048576)}
def project(metadata,observation,terms,*,conditional=False):
    graphs=graph_growth(metadata)
    require(metadata['storage_writer_sources_unchanged'] is True,'accepted37 storage writer source join missing')
    require(metadata['original_input_manifest_pins_unchanged'] is True,'original seven graph input join missing')
    require(metadata['source_route']=='whole39-from38-remove-entry-stop-only','unsupported whole route')
    require(terms['limits']==LIMITS,'fixed native or writable limits differ')
    needed={'directory_allocated_bytes','directory_entries','other_writer_logical_bytes','other_writer_allocated_bytes','other_writer_entries','additional_headers_edges_logical_bytes','additional_headers_edges_allocated_bytes','additional_headers_edges_entries','other_new_logical_bytes','other_new_allocated_bytes','other_new_entries'}
    require(needed<=set(terms),'missing explicit growth term')
    for k in needed:integer(terms[k],k)
    require(terms['additional_headers_edges_evidence'] and terms['directory_evidence'] and terms['other_writer_evidence'],'missing term provenance')
    require(terms['base_entry_bound']==650016,'inherited base entries changed')
    # This bound includes inherited directories/other writers. Adding the full
    # explicit allowances again is conservative; no guessed partition credit.
    prefix=sum(g['prefix_bytes'] for g in graphs);delta=prefix+98304
    require(delta==416083968,'accepted37 continuation delta changed')
    persistent_subterms={'retained_origins':sum(g['retained_origins_bytes'] for g in graphs),'retained_summaries':sum(g['retained_summaries_bytes'] for g in graphs),'float32_spool_and_output':sum(g['spool_and_output_bytes'] for g in graphs),'work_bodies_headers_and_group_receipts':962598737,'typed_receipt_bodies':203534275,'fixed_closure_tokens':17061912}
    require(sum(persistent_subterms.values())==9086624428,'persistent decomposition differs')
    components={k:{'logical_file_bytes':a,'allocated_bytes':b} for k,(a,b) in BASE_TERMS.items()}
    residuals=observation['storage_observation']['residual_domains']
    for domain,component,logical_cap,allocated_cap in [('runtime_temp_cache','runtime_temp_cache_residual',268435456,288354304),('training_and_lifecycle','training_lifecycle_residual',33554432,33933244)]:
        actual=residuals[domain]
        require(actual['policy']['logical_bytes']==logical_cap and actual['allocated_threshold_bytes']==allocated_cap,'changed residual domain cap')
        logical=integer(actual['logical_file_bytes'],domain+' logical');physical=integer(actual['allocated_bytes'],domain+' allocated')
        require(logical<=logical_cap and physical<=allocated_cap,'existing residual domain exceeds cap')
        components[component]={'logical_file_bytes':logical_cap-logical,'allocated_bytes':allocated_cap-physical}
    components['continuation_markers_and_conservative_live_delta']={'logical_file_bytes':delta,'allocated_bytes':delta}
    components['directory_growth']={'logical_file_bytes':0,'allocated_bytes':terms['directory_allocated_bytes']}
    components['other_writers']={'logical_file_bytes':terms['other_writer_logical_bytes'],'allocated_bytes':terms['other_writer_allocated_bytes']}
    components['additional_headers_edges']={'logical_file_bytes':terms['additional_headers_edges_logical_bytes'],'allocated_bytes':terms['additional_headers_edges_allocated_bytes']}
    components['other_new']={'logical_file_bytes':terms['other_new_logical_bytes'],'allocated_bytes':terms['other_new_allocated_bytes']}
    growth={k:sum(v[k] for v in components.values()) for k in ('logical_file_bytes','allocated_bytes')}
    growth['entries']=650016+101559+terms['directory_entries']+terms['other_writer_entries']+terms['additional_headers_edges_entries']+terms['other_new_entries']
    missing=[]
    if terms.get('review_status')!='root-current-full-growth' or terms.get('observation_sha256')!=observation.get('observation_sha256'):missing.append('current Root directory/other-writer/growth terms bound to final observation')
    if observation.get('filesystem_block_bytes')!=4096:missing.append('actual4096-byte filesystem allocation block join')
    if observation.get('kind')!='final-post38-whole39-writable-union':missing.append('final actual post38 whole39 WritableUnion observation')
    if observation.get('post38_closed_and_recovered') is not True:missing.append('accepted and recovered38 closure')
    if observation.get('source_and_scope_current') is not True:missing.append('current source/input/whole39 scope join')
    for key in ('at','observation_sha256','filesystem_identity'):
        if not observation.get(key):missing.append(key)
    baseline={k:integer(observation['storage_observation'][k],k) for k in ('logical_file_bytes','allocated_bytes','entries')}
    free=integer(observation['disk_free_bytes'],'disk free bytes')
    inodes=observation.get('free_inodes')
    if inodes is None:missing.append('free_inodes')
    else:integer(inodes,'free inodes')
    if not conditional:require(not missing,'missing currentness/observation terms: '+', '.join(missing))
    projection={k:baseline[k]+growth[k] for k in baseline}
    margins={k:LIMITS[k]-projection[k] for k in baseline}
    margins['filesystem_free_after_growth_and_floor']=free-growth['allocated_bytes']-LIMITS['disk_floor_bytes']
    margins['startup_free_after_floor_and_reserve']=free-LIMITS['disk_floor_bytes']-LIMITS['startup_reserve_bytes']
    margins['inodes_after_growth']=None if inodes is None else inodes-growth['entries']
    passed=not missing and all(v is not None and v>=0 for v in margins.values())
    return {'status':'STORAGE_ARITHMETIC_ONLY_NOT_ADMISSION','graphs':graphs,'persistent_subterms_logical':persistent_subterms,'components':components,'growth':growth,'projection':projection,'margins':margins,'storage_caps_and_floor_pass':passed,'missing_terms':missing,'conditional_dated_observation':bool(missing),'memory_fit_proven':False,'memory_requirement':'All original graph parents, GAT full forward/backward/Adam/checkpoint/runtime holds remain unproved under fixed6GiB max/5GiB high; storage arithmetic cannot release training.','physical_reservation':False,'continuation_addition':{'logical_file_bytes':delta,'allocated_bytes':delta,'entries':101559},'cumulative_checkpoint_allowance_not_retained':43058298880,'cumulative_transport_addition_not_retained':sum(g['cumulative_transport_addition_not_retained'] for g in graphs)}
if __name__=='__main__':
    import argparse,json
    from pathlib import Path
    parser=argparse.ArgumentParser();parser.add_argument('metadata');parser.add_argument('observation');parser.add_argument('terms');parser.add_argument('--conditional',action='store_true');args=parser.parse_args()
    load=lambda p:json.loads(Path(p).read_text())
    print(json.dumps(project(load(args.metadata),load(args.observation),load(args.terms),conditional=args.conditional),indent=2))
