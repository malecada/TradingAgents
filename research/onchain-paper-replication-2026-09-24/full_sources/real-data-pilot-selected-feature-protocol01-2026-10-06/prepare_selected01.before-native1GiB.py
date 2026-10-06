"""Fixed metadata-only selection preparation. No admission, payload or credential reads."""
import argparse,copy,hashlib,json,importlib.util
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[3];F=H.parent
CAP=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-canonical-native-20261005-01/source/fixture_inputs/held/success01')
MIB=1024**2;GIB=1024**3;META=8192;DMETA=131072;CELL=65536;PART=4194240;OUTPART=4194304;CHUNK_EVENTS=49152;G=160
IDENTITY='eth-paper-real-data-end-to-end-resource-20261005-01'
ORIGINAL_PINS={'compact_policy': '5540f452f6e12d059afc21d8c2607290ebd91332e5377266c9ac639125ef6465', 'environment': '1ff7418a2b7c77300aea731cea5bba78277d323241ac0ec59f41f43207c66d87', 'execution_job': 'd4f2679d2fd360fcb3bf048faa051a65aa9406191bd67ba66e8fcb30cd177ff8', 'mcm_output_policy': '7e9832eb55c4d7761aab39151492ce8edac61d5475fa52cbfdd68f87b80e1212', 'mcm_policy': 'efdcc827afa56424e0148ce51ba7c5bbb2e7a4332332c4321bbeb458f9d2ef1b', 'original_import': '0844394fac73fe187444a82c484d0ae5bdafc5d1b25c5a09973f8cde9f3905d2', 'original_import_stage': '8f3cd8a5a2f605c0682b727bf45cfd19fb64e0375a4068b76d6b60fe11ec7f3f', 'pair_policy': 'f438af62ea8a6d9a37e7b0b364d460523117cdd6db556538055fc58dde758d30', 'producer_plan': '67a65bee06102aa6e56ed55bf3ce942b50f077fb621f661f5d0504b35d4283c6'}
def need(x,m):
    if not x:raise ValueError(m)
def raw(x):return (json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def read(p):
    need(p.suffix=='.json' and not p.is_symlink() and p.stat().st_size<=4*MIB,'bounded metadata only')
    return json.loads(p.read_bytes())
def ref(p,pin=None):
    need(not p.is_symlink() and p.is_file(),'regular reference absent')
    # Opaque references supply their inherited pin; never read scientific payloads.
    return {'path':str(p.relative_to(ROOT)),'sha256':pin or hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def save(out,name,value):
    p=out/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(raw(value))
    return ref(p)
def checked_reference(r):
    p=ROOT/r['path'];need(p.resolve()==p and p.stat().st_size==r['bytes'],'metadata reference extent/path differs')
    need(hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'],'metadata reference hash differs');return read(p)
def kind_alloc(n):
    c=32*n;b=(c+CELL-1)//CELL;full,last=divmod(c,CELL)
    parts=full*((CELL*80+PART-1)//PART)+(0 if not last else (last*80+PART-1)//PART)
    return {'score-tail-f64':{'chunk_bytes':PART,'max_preserved_bytes':80*c,'max_recovered_bytes':80*c,'max_operations':b,'max_chunks':2*parts},
      'score-batch-f64':{'chunk_bytes':OUTPART,'max_preserved_bytes':8*c,'max_recovered_bytes':8*c,'max_operations':b+1,'max_chunks':2*b},
      'mcm-output-f32':{'chunk_bytes':OUTPART,'max_preserved_bytes':4*c,'max_recovered_bytes':1,'max_operations':1,'max_chunks':(4*c+OUTPART-1)//OUTPART}}
def prepare(out,graph_input,physical=None):
    need(out.is_relative_to(F) and not out.exists(),'fresh owned output required');out.mkdir()
    graphs=read(graph_input)['graphs']
    for item in graphs.values():
        if item is not None:
            m=checked_reference(item['manifest']);n=checked_reference(item['node_count'])
            need(n['graph_manifest_sha256']==item['manifest']['sha256'] and n['node_features_sha256']==m['arrays']['node_features']['sha256'],'count/manifest join differs')
    ready=read(F/'real-data-pilot-population-binding01-2026-10-05/BINDING_READINESS01.json')
    refs={k:ref(Path(v['path']),v['sha256']) for k,v in ready['bound_available_metadata'].items()}
    origins={};templates={};aux={}
    def original(name):
        p=CAP/(name+'.json');need(hashlib.sha256(p.read_bytes()).hexdigest()==ORIGINAL_PINS[name],'original metadata pin differs');v=read(p);origins[name]={'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size};return v
    control=original('original_import')
    for item in control['refs'].values():refs[item['input']]=ref(Path(item['original_path']),item['sha256'])
    control['required_graphs']=[];templates['dictionary']=control
    compact=original('compact_policy');pair=compact['stage_policy']['pair'];K=pair['max_checkpoint_bytes']
    stage=compact['stage_policy'];stage['score_chunk_cells']=CELL;stage['log'].update(chunk_events=CHUNK_EVENTS,max_events=None,max_pairs=None,max_logical_bytes=None)
    # Existing pair method and schedule preserved. Exhausting finite checkpoint capacity is a failure, not truncation.
    stage['restart_retention']={'schema_version':1,'format':'archived-restart-retention-v1','max_stores':G,'max_generations':G,'max_control_bytes':32*MIB,'max_cumulative_bytes':128*MIB,'max_input_bytes':16*MIB,'max_replay_bytes':4*MIB,'max_replays':2,'max_live_bytes':52*MIB+2*K}
    stage['max_retained_logical_bytes']=None;compact['max_workflow_retained_logical_bytes']=None;templates['compact']=compact
    basejob=original('execution_job');selected=next(iter(basejob['payload']['representation_jobs'].values()))
    selected.pop('held_score_consumer_input',None)
    for k in ('resource_fixture','resource_graph_inputs'):selected['descriptor'].pop(k,None)
    selected['descriptor']['required_graphs']=[]
    selected.update(real_pilot_input='pilot',compact_archive_input='archive_policy',compact_archive_transport_input='archive_transport')
    resource={'memory_max_bytes':6*GIB,'memory_high_bytes':5*GIB,'reserve_bytes':3*GIB,'start_reserve_bytes':9*GIB,'wall_seconds':28800,'disk_floor_bytes':10*GIB,'disk_paths':[str(ROOT)],'native_unit_limits':{'file_size_bytes':512*MIB},'storage_budget':{'schema_version':2,'kind':'real-pilot-writable-union','authority_root':str(ROOT),'experiment':IDENTITY,'roots':[str(ROOT/'research_artifacts'),str(ROOT/'research_runs'/IDENTITY)],'shared_files':[str(ROOT/'research_runs/.lock')],'limits':{'max_logical_bytes':16*GIB,'max_allocated_bytes':20*GIB,'max_entries':1000000,'max_depth':64,'max_scan_seconds':5}}}
    basejob['resources']=resource;templates['job']=basejob
    plan=original('producer_plan');producer_key=selected['producer'];item=copy.deepcopy(selected);item.update(binding_output='resource-binding.json',journal_output='resource-journal.json');plan['schema_version']=2;plan['producers']={producer_key:item};templates['producer_plan']=plan
    dates=read(F/'real-data-end-to-end-pilot-preparation01-2026-10-05/INPUT_SELECTION_DRAFT01.json')['selected']['decision_dates']
    templates['pilot']={'schema_version':2,'kind':'real-data-import-training-pilot-v1','asset':'ETH','seed':11,'batch_size':16,'lookback_days':28,'cell_id':'real-eth-one-update','indices':None,'decisions':dates,'graph_inputs':{},'graph_sequences':[],'population_scope':'resource_pilot_subset','population_plan_input':'resource_population_plan','model_input':'model','training_input':'training','model_execution':{'schema_version':2,'backend':'streamed-gat-mulsum-v1','block_edges':65536,'graph_activation_checkpointing':True},'max_checkpoint_bytes':4*MIB,'outputs':{'summary':'pilot-summary.json','ledger':'cell-ledger.json','binding':'resource-binding.json','journal':'resource-journal.json'},'resource_policy':resource,'archive_inputs':{'policy_input':'archive_policy','transport_input':'archive_transport'},'partial_progress':{'schema_version':1,'interval_seconds':60,'max_records':1024},'imported_authority_lease_input':'imported_authority_lease'}
    templates['population']={'schema_version':1,'population_scope':'resource_pilot_subset','financial_fit_complete':False,'fold':'2024','scope_input':'resource_population_scope','calendar_input':'calendar','price_panel_input':'price_panel','graphs':{},'outputs':{'resource_population':'resource-population.json','binding':'resource-population-binding.json'}}
    templates['output']=original('mcm_output_policy');templates['output'].update(schema_version=2,payload_archive_input='typed_payload',max_artifact_bytes=None,max_workflow_output_bytes=None)
    templates['archive']={'schema_version':1,'backend':'compact-archive-events-v1','transport_identity':None,'remote_namespace':'ethpilot-20261006','local_free_floor_bytes':10*GIB,'max_stage_verifications':16,'max_writer_metadata_bytes':None,'max_read_metadata_bytes':None,'max_stage_bytes':None,'max_workflow_metadata_bytes':None,'max_remote_payload_bytes':None,'max_decoded_transfer_bytes':None}
    for name in ('pair_policy','original_import_stage','mcm_policy','environment'):aux[name]=original(name)
    aux['mcm_policy']['max_entries']=None;aux['mcm_policy']['max_workflow_metadata_bytes']=3*META*7
    aux['mcm_policy']['numeric']['max_output_bytes']=None;aux['mcm_policy']['numeric']['max_numeric_bytes']=None
    lease=read(F/'real-data-pilot-imported-authority-lease01-2026-10-06/POLICY_DRAFT01.json')
    lease.update(live_interval_ms=100,fingerprint_interval_ms=1000,full_interval_ms=10000,max_stale_ms=30000,max_calls_between_full=65536);aux['imported_authority_lease']=lease
    counts={w:None if x is None else checked_reference(x['node_count'])['rows'] for w,x in graphs.items()}
    typed={'chunk_cells':CELL,'by_week':{w:None if n is None else kind_alloc(n) for w,n in counts.items()},'max_control_bytes':None}
    transport={'rate_kbit':262144,'max_seconds':28800,'namespace':'ethpilot-20261006','receipt_output':'archive-receipt.json','terminal_output':'archive-terminal.json','max_payload_bytes':None,'max_commands':None,'max_diagnostic_bytes':None,'max_control_bytes':None}
    if all(n is not None for n in counts.values()):
        c=max(counts.values())*32;E=2*c+G;Q=(E+CHUNK_EVENTS-1)//CHUNK_EVENTS;R=16
        stage['log'].update(max_pairs=c,max_events=E,max_logical_bytes=E*168+2*META)
        stage['max_retained_logical_bytes']=stage['log']['max_logical_bytes']+stage['restart_retention']['max_live_bytes']+88*c+(4*((c+CELL-1)//CELL)+4)*META
        compact['max_workflow_retained_logical_bytes']=8*(stage['max_retained_logical_bytes']+2*META)+2*65536
        a=templates['archive'];a.update(max_writer_metadata_bytes=(7*Q+8)*META,max_read_metadata_bytes=(3*Q+8)*META,max_stage_bytes=(3*Q+8)*META+40*G+8*META,max_remote_payload_bytes=8*E*168,max_decoded_transfer_bytes=8*E*168*(3+R))
        ops=8*(1+R);a['max_workflow_metadata_bytes']=(4+3*ops+8)*META+8*(a['max_writer_metadata_bytes']+8*META+R*a['max_stage_bytes'])
        templates['output'].update(max_artifact_bytes=4*c+2*META,max_workflow_output_bytes=7*(4*c+3*META))
        aux['mcm_policy']['max_entries']=c;aux['mcm_policy']['numeric']['max_output_bytes']=4*c;aux['mcm_policy']['numeric']['max_numeric_bytes']=4*c+aux['mcm_policy']['numeric']['max_buffer_bytes']
        allk=[k for week in typed['by_week'].values() for k in week.values()];chunks=sum(k['max_chunks'] for k in allk);top=sum(k['max_operations'] for k in allk)
        typed['max_control_bytes']=(3*top+chunks)*META
        full,last=divmod(E,CHUNK_EVENTS);rounded=full*((CHUNK_EVENTS*168//65536+1)*65536)+(0 if not last else (last*168//65536+1)*65536)
        ncommands=4*chunks+8*Q*(4+R)
        payload=sum(2*k['max_preserved_bytes']+k['max_recovered_bytes']+2*k['max_chunks']*65536 for k in allk)+8*(E*168+(2+R)*rounded)
        transport.update(max_payload_bytes=payload,max_commands=ncommands,max_diagnostic_bytes=payload+DMETA*ncommands,max_control_bytes=max(DMETA*(8+4*ncommands),DMETA*(8+3*ncommands+ops+top)))
    # Genuine descriptor hashes must follow newly encoded metadata, not the tiny template bytes.
    for field,role,value in [('compact_execution','compact_policy',compact),('pair_execution','pair_policy',aux['pair_policy']),('original_dictionary_stage','original_import_stage',aux['original_import_stage'])]:
        if field=='original_dictionary_stage':selected['descriptor'][field]={'input':role,'sha256':hashlib.sha256(raw(value)).hexdigest()}
        else:selected['descriptor'][field]['policy_sha256']=hashlib.sha256(raw(value)).hexdigest()
    selected['descriptor']['compact_archive_execution']={'backend':'compact-archive-events-v1','policy_sha256':hashlib.sha256(raw(templates['archive'])).hexdigest()}
    plan['producers'][producer_key].update(copy.deepcopy(selected))
    roles={'pilot':'pilot','population':'resource_population_plan','job':'execution_job','producer_plan':'producer_plan','dictionary':'original_import','compact':'compact_policy','archive':'archive_policy','output':'mcm_output_policy'}
    for name,v in templates.items():refs[roles[name]]=save(out,'templates/'+roles[name]+'.json',v)
    for name,v in aux.items():refs[name]=save(out,'templates/'+name+'.json',v)
    physical=physical or {'physical_baseline':{'evidence':None,'logical_bytes':None,'allocated_bytes':None,'entries':None},'filesystem':read(H/'FILESYSTEM_POLICY01.json')['selected']|{'evidence_sha256':hashlib.sha256((H/'FILESYSTEM_POLICY01.json').read_bytes()).hexdigest()}}
    protocol={'references':refs,'template_roles':roles,'typed_input_role':'typed_payload','typed_allocations':typed,'transport_limits':transport,**physical,'runtime_reservation':{'logical_bytes':256*MIB,'regular_files':4096,'directories':256,'max_file_bytes':64*MIB},'lifecycle_reservation':{'logical_bytes':32*MIB,'regular_files':68,'directories':16,'max_file_bytes':4*MIB}}
    save(out,'INPUT_DRAFT01.json',{'status':'DRAFT_NOT_RELEASED','graphs':graphs,'protocol':protocol})
    save(out,'TEMPLATE_ORIGINS01.json',origins)
    save(out,'DIMENSIONS01.json',{'known_counts':counts,'known_week_allocations':typed['by_week'],'all_seven_counts':all(n is not None for n in counts.values()),'actual_numeric_or_authority_execution':False,'original_science_unchanged':True})
    return out/'INPUT_DRAFT01.json'
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--graphs',type=Path,required=True);a.add_argument('--physical',type=Path);a.add_argument('--output',type=Path,required=True);v=a.parse_args()
    print(prepare(v.output.resolve(),v.graphs,read(v.physical) if v.physical else None))
