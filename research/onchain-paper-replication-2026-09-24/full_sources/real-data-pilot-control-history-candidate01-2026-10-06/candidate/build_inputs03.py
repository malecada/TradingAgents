"""Metadata-only DRAFT preparation. Never creates authority or reads numeric bodies."""
import argparse,copy,hashlib,json,os,stat,struct
from datetime import datetime,timedelta,timezone
from pathlib import Path
LIMIT=4*1024**2
TRANSPORT_META=131072
ARCHIVE_MAX_BYTES=8*1024**2  # archive_chunks.MAX_BYTES == score_batches.MAX_CHUNK_BYTES
BACKEND='resident-native-compact-current-owner-v1'
ASSUMPTION=('Historical proof authenticates prior full byte and semantic recovery against '
 'the original roster. It does not establish current remote byte availability; '
 'every future restore/use must freshly retrieve and authenticate its bytes.')
PINS={'scope':'57a97518d2b12e0c787b49f91d9bf509888f9c63fb8f644d1ace90b5bd05e2a8','calendar':'21bb348b9c779238b212d0e4074cf806f6a54d0ce3b7713d97bc3ad65d57ef22','prices':'f7a4d89ff66d37ec00d8d4d834a1a771ac55f36bc9b210cfbecb6768ecc3bbbe'}
GRAPH_CONFIG='01ed0f0dc76b2685598dd7687466dd81880e5d332c0c6827da8f90f8f17a4a9d'
KINDS={'score-tail-f64':80,'score-batch-f64':8,'mcm-output-f32':4}
def stamp(d):return d.isoformat().replace('+00:00','Z')
DECISIONS=[stamp(datetime(2022,6,7,tzinfo=timezone.utc)+timedelta(days=i)) for i in range(16)]
WEEKS=[stamp(datetime(2022,5,2,tzinfo=timezone.utc)+timedelta(days=7*i)) for i in range(7)]
def need(ok,message):
    if not ok:raise ValueError(message)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def raw(v):return (json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def h(v):need(type(v) is str and len(v)==64 and all(c in '0123456789abcdef' for c in v),'SHA256 required')
def positive(v):need(type(v) is int and 0<v<2**63,'finite positive integer required')
def date(v):
    d=datetime.fromisoformat(v.replace('Z','+00:00'));need(d.utcoffset()==timedelta(0) and stamp(d)==v,'canonical UTC metadata required');return d

def ref_path(root,ref):
    need(type(ref) is dict and set(ref)=={'path','sha256','bytes'},'exact file reference required');h(ref['sha256']);positive(ref['bytes'])
    name=Path(ref['path']);need(not name.is_absolute() and '..' not in name.parts,'reference must remain inside declared root')
    need(not any(x in {'keys','apis','.env','hf_token.txt'} or x.startswith('.env.') or 'private_key' in x for x in name.parts),'secret reference refused')
    path=root/name;need(path.resolve()==path and path.is_relative_to(root),'redirected reference refused')
    try:info=path.lstat()
    except FileNotFoundError:raise ValueError('missing prerequisite: '+str(path)) from None
    need(stat.S_ISREG(info.st_mode) and info.st_size==ref['bytes'],'reference type/extent differs: '+str(path))
    return path

def metadata(root,ref):
    need(ref['sha256'] not in {PINS['prices'],'46b18f3df967405374b1f6ee8a3d11ee1b7a5b176ac9fb4342caf6bf8648f2cc'},'numeric price body must remain opaque')
    path=ref_path(root,ref);need(ref['bytes']<=LIMIT,'metadata exceeds fixed limit')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        before=os.fstat(fd);body=bytearray()
        while len(body)<=LIMIT:
            part=os.read(fd,min(65536,LIMIT+1-len(body)))
            if not part:break
            body.extend(part)
        after=os.fstat(fd);current=path.lstat()
        def pin(s):return s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns
        need(pin(before)==pin(after)==pin(current) and len(body)==ref['bytes'] and sha(body)==ref['sha256'],'metadata hash/identity changed: '+str(path))
        return json.loads(body)
    finally:os.close(fd)

def graphs(root,records):
    need(type(records) is dict and set(records)==set(WEEKS),'exact seven fixed weekly graph references required')
    result={};seen=set()
    for week in WEEKS:
        item=records[week];need(set(item)=={'role','manifest','node_count'},'graph reference fields differ')
        need(type(item['role']) is str and item['role'] and item['role'] not in seen,'distinct graph roles required');seen.add(item['role'])
        g=metadata(root,item['manifest']);need(set(g)=={'metadata','graph_hash','arrays'},'original graph manifest shape differs');h(g['graph_hash'])
        m=g['metadata'];start=date(week)
        need(m['asset']=='ETH' and m['start_utc']==week and date(m['end_utc'])==start+timedelta(days=7) and date(m['available_at'])>=start+timedelta(days=8) and m['graph_config_hash']==GRAPH_CONFIG,'original graph calendar/config differs')
        need(type(m['source_hashes']) is list and m['source_hashes'] and len(set(m['source_hashes']))==len(m['source_hashes']),'original graph source membership differs')
        for key in m['source_hashes']:h(key)
        arrays=g['arrays'];need(set(arrays)=={'node_ids','node_features','edge_index','edge_features','edge_aggregates'},'five original graph array descriptors required')
        for name,a in arrays.items():
            need(set(a)=={'path','sha256','bytes'} and a['path']==name+'.npy','array descriptor differs');h(a['sha256']);positive(a['bytes'])
        n=metadata(root,item['node_count'])
        need(set(n)=={'schema_version','kind','graph_manifest_sha256','node_features_sha256','rows','method','evidence'} and n['schema_version']==1 and n['kind']=='graph-node-count-metadata-v1' and n['graph_manifest_sha256']==item['manifest']['sha256'] and n['node_features_sha256']==arrays['node_features']['sha256'] and n['method']=='retained-header-only','pinned original node-count metadata required')
        positive(n['rows']);ref_path(root,n['evidence']) # evidence reference only; never read arrays or count-source body
        result[week]={'hash':g['graph_hash'],'role':item['role'],'rows':n['rows'],'available_at':m['available_at'],'manifest':item['manifest'],'node_count':item['node_count']}
    need(len({v['hash'] for v in result.values()})==7,'seven distinct genuine graph identities required')
    return result

def sequences(g):
    result=[]
    for decision in DECISIONS:
        row=[]
        for i in range(28,0,-1):
            # Original dataset uses each input close date plus one day as graph step.
            step=date(decision)-timedelta(days=i-1);lagged=step-timedelta(days=1)
            end=(lagged-timedelta(days=lagged.weekday())).replace(hour=0,minute=0,second=0,microsecond=0)
            week=stamp(end-timedelta(days=7));item=g[week]
            need(date(item['available_at'])<=step,'late graph for original input step: '+week);row.append(item['hash'])
        result.append(row)
    return result

def typed_budget(g,selection):
    need(set(selection)=={'chunk_cells','by_week','max_control_bytes'},'explicit typed allocations required')
    cells=selection['chunk_cells'];positive(cells);need(cells<=65536,'original batch limit exceeded');positive(selection['max_control_bytes'])
    need(set(selection['by_week'])==set(WEEKS),'all weekly typed allocations required')
    policy={'schema_version':1,'format':'typed-payload-budget-v1','assumption':ASSUMPTION,'graphs':{},'local_free_floor_bytes':10*1024**3,'max_control_bytes':selection['max_control_bytes']}
    total={'logical_bytes':0,'rounded_bytes':0,'commands':0,'chunks':0};minima={}
    for week,item in g.items():
        count=item['rows']*32;batches=(count+cells-1)//cells;budgets=copy.deepcopy(selection['by_week'][week]);need(set(budgets)==set(KINDS),'all three typed kinds required')
        low={}
        for kind,width in KINDS.items():
            b=budgets[kind];need(set(b)=={'max_operations','max_preserved_bytes','max_recovered_bytes','max_chunks','chunk_bytes'},'typed allowance fields differ')
            for v in b.values():positive(v)
            part=b['chunk_bytes'];need(part<=LIMIT and part%width==0,'aligned <=4MiB transport chunk required')
            if kind=='score-tail-f64':
                full,last=divmod(count,cells);chunks=full*((cells*80+part-1)//part)+(0 if not last else (last*80+part-1)//part);ops=batches;reads=count*80;chunks*=2
            elif kind=='score-batch-f64':
                need(part>=cells*8,'original f64 batch must fit selected part');chunks=2*batches;ops=batches+1;reads=count*8
            else:chunks=(count*4+part-1)//part;ops=1;reads=0
            need(b['max_preserved_bytes']>=count*width and b['max_recovered_bytes']>=reads and b['max_chunks']>=chunks and b['max_operations']>=ops,'typed allocation below one original production/conversion traversal: '+week+'/'+kind)
            low[kind]={'preserved_bytes':count*width,'recovered_bytes':reads,'chunks':chunks,'operations':ops}
            p,r,n=b['max_preserved_bytes'],b['max_recovered_bytes'],b['max_chunks'];total['logical_bytes']+=2*p+r;total['rounded_bytes']+=2*p+r+2*n*65536;total['commands']+=4*n;total['chunks']+=n
        policy['graphs'][item['hash']]={'rows':item['rows'],'chunk_cells':cells,'kinds':budgets};minima[week]=low
    return policy,total,minima

def selected_buffers(g,selection,pair_chunk):
    # Reuse the sealed scalar calculator, never import the scientific package.
    path=Path(__file__).resolve().parent.parent.parent/'real-data-pilot-resource-buffer-allocation01-2026-10-06'/'allocation01.py'
    need(not path.is_symlink() and path.stat().st_size<=LIMIT,'bounded calculator source required')
    source=path.read_bytes()
    need(sha(source)=='3912e68c232553f1fab5e39a92c0741c2c0ddab49316321c1189781d19611dfd','pinned allocation calculator changed')
    functions={};exec(compile(source,str(path),'exec'),functions)
    result={}
    for week,item in g.items():
        kinds=selection['by_week'][week]
        value=functions['graph'](item['rows'],selection['chunk_cells'],kinds['score-tail-f64']['chunk_bytes'],kinds['mcm-output-f32']['chunk_bytes'],pair_chunk)
        functions['check_typed_allowances'](value,kinds);result[week]=value
    return result

def build(root,spec):
    need(set(spec)=={'graphs','references','template_roles','typed_input_role','typed_allocations','physical_store','transport_limits'},'exact builder metadata specification required')
    root=Path(root).resolve();g=graphs(root,spec['graphs']) # missing genuine graph fails before template/numeric access
    refs=copy.deepcopy(spec['references'])
    for role,ref in refs.items():need(type(role) is str and role,'named reference required');ref_path(root,ref)
    need(len(set(spec['template_roles'].values()))==8,'distinct metadata template roles required')
    control=metadata(root,refs[spec['template_roles']['dictionary']])
    opaque_hashes={v['sha256'] for k,v in control['refs'].items() if k in ('dictionary','samples')}
    need(not opaque_hashes & {refs[role]['sha256'] for role in spec['template_roles'].values()},'original numerical evidence cannot be a metadata template')
    templates={key:metadata(root,refs[role]) for key,role in spec['template_roles'].items()}
    need(set(templates)=={'pilot','population','job','producer_plan','dictionary','compact','archive','output'},'exact metadata templates required')
    p,pop,job,plan,control,compact,archive,output=[templates[k] for k in ('pilot','population','job','producer_plan','dictionary','compact','archive','output')]
    need(len(job['payload']['representation_jobs'])==1,'one original representation required');rep,selected=next(iter(job['payload']['representation_jobs'].items()))
    need(selected['descriptor']['dictionary_origin']=='imported-original-v1' and selected['descriptor']['arm']=='proposed','preserved original proposed descriptor required')
    need(control['sample_count']==512 and control['motif_count']==32 and control['kind']=='original-dictionary-import-v1','original512/32 control required')
    need(set(control['refs'])=={'dictionary','samples','dictionary_config','matching_config','graph_manifest','claim','terminal','gate','dictionary_intent','sample_intent','dictionary_result'},'original import roster differs')
    for evidence in control['refs'].values():
        need(evidence['input'] in refs and refs[evidence['input']]['sha256']==evidence['sha256'],'original opaque import role/hash differs')
    for key,role in [('scope',pop['scope_input']),('calendar',pop['calendar_input']),('prices',pop['price_panel_input'])]:need(refs[role]['sha256']==PINS[key],'frozen '+key+' reference differs')
    mapping={v['hash']:v['role'] for v in g.values()};required=sorted(mapping)
    p.update(schema_version=2,population_scope='resource_pilot_subset',indices=None,decisions=DECISIONS,graph_inputs=mapping,graph_sequences=sequences(g),resource_policy=copy.deepcopy(job['resources']))
    need(p['model_input'] in refs and p['training_input'] in refs,'frozen model/training roles required')
    need(p['asset']=='ETH' and p['seed']==11 and p['batch_size']==16 and p['lookback_days']==28,'fixed pilot settings differ')
    need(p['archive_inputs']=={'policy_input':selected['compact_archive_input'],'transport_input':selected['compact_archive_transport_input']},'caller/archive input join differs')
    pop.update(graphs={week:v['role'] for week,v in g.items()});need(pop['fold']=='2024' and pop['population_scope']=='resource_pilot_subset' and pop['financial_fit_complete'] is False,'resource population declaration differs')
    control['required_graphs']=required
    typed,total,minima=typed_budget(g,spec['typed_allocations']);typed_role=spec['typed_input_role'];need(type(typed_role) is str and typed_role,'explicit typed input role required')
    need(compact['stage_policy']['score_chunk_cells']==spec['typed_allocations']['chunk_cells'],'original compact/typed batch selection differs')
    output.update(schema_version=2,payload_archive_input=typed_role);need(output['backend']==BACKEND,'original output backend differs')
    max_matrix=max(v['rows']*32*4 for v in g.values());need(output['max_artifact_bytes']>=max_matrix+2*8192 and output['max_workflow_output_bytes']>=7*(output['max_artifact_bytes']+8192),'full original output reservation insufficient')
    resource=job['resources'];need(resource['native_unit_limits']['file_size_bytes']>=max(max_matrix,LIMIT),'finite native cap must cover original matrix and chunks')
    budget=resource['storage_budget'];limits=budget['limits'];experiment='eth-paper-real-data-end-to-end-resource-20261005-01'
    need(budget['authority_root']==str(root) and budget['schema_version']==2 and budget['kind']=='real-pilot-writable-union' and budget['experiment']==experiment and budget['roots']==[str(root/'research_artifacts'),str(root/'research_runs'/experiment)] and budget['shared_files']==[str(root/'research_runs/.lock')],'exact common writable union required')
    need(resource['disk_floor_bytes']==typed['local_free_floor_bytes']==archive['local_free_floor_bytes'],'one physical-store floor required')
    store=spec['physical_store'];need(set(store)=={'baseline_evidence','baseline_allocated_bytes','baseline_logical_bytes','reserved_growth_bytes','reserved_control_bytes','retained_diagnostic_bytes','caller_scratch_bytes','allocation_overhead_bytes','typed_attempt_metadata_bytes','remaining_control_inventory','additional_scratch_bytes'},'explicit retained local store components required');ref_path(root,store['baseline_evidence'])
    for key in set(store)-{'baseline_evidence','remaining_control_inventory','additional_scratch_bytes'}:positive(store[key])
    inventory=store['remaining_control_inventory']
    need(type(inventory) is dict and set(inventory)=={'stream_tail_batch_headers_bytes','producer_output_controls_bytes','other_selected_controls_bytes'},'complete remaining control declarations required')
    for value in inventory.values():positive(value)
    extra=store['additional_scratch_bytes'];need(type(extra) is int and 0<=extra<2**63,'explicit finite additional scratch declaration required')
    need(store['reserved_growth_bytes']>=sum(v['rows']*128 for v in g.values()),'all retained original f32 outputs require common store reservation')
    transport=copy.deepcopy(spec['transport_limits']);need('connection' not in transport,'builder must not consume connection credentials')
    need(set(transport)-{'control_history'}=={'rate_kbit','max_seconds','max_payload_bytes','max_commands','max_diagnostic_bytes','max_control_bytes','namespace','receipt_output','terminal_output'},'exact transport limit template required')
    for key in ('rate_kbit','max_seconds','max_payload_bytes','max_commands','max_diagnostic_bytes','max_control_bytes'):positive(transport[key])
    # Existing archive_dispatch capacity formula for eight original stages.
    log=compact['stage_policy']['log'];events,chunk,reads=log['max_events'],log['chunk_events'],archive['max_stage_verifications'];width=struct.calcsize('<QB7xQdQ32s32s32s')+32
    for n in (events,chunk,reads):positive(n)
    full,last=divmod(events,chunk);rounded=full*((chunk*width//65536+1)*65536)+(0 if not last else (last*width//65536+1)*65536);payload=events*width;parts=(events+chunk-1)//chunk
    pair={'logical_bytes':8*payload*(3+reads),'rounded_bytes':8*(payload+(2+reads)*rounded),'commands':8*parts*(4+reads),'chunks':8*parts}
    need(pair['logical_bytes']<=archive['max_decoded_transfer_bytes'] and 8*payload<=archive['max_remote_payload_bytes'],'original pair archive allowances insufficient')
    combined={k:total[k]+pair[k] for k in total}
    for value in combined.values():positive(value)
    need(combined['rounded_bytes']<=transport['max_payload_bytes'] and combined['commands']<=transport['max_commands'],'shared pair/typed transport allowance insufficient')
    history_bounds=None
    if 'control_history' in transport:
        from tradingagents.research.onchain_replication.archive_control_history import capacity
        history_bounds=capacity(transport['control_history'],transport['max_commands'])
        need(transport['max_diagnostic_bytes']>=history_bounds['diagnostic_bytes'] and transport['max_control_bytes']>=history_bounds['control_bytes'],'selected bounded controls underfunded')
    else:
        need(transport['max_diagnostic_bytes']>=transport['max_payload_bytes']+131072*transport['max_commands'] and transport['max_control_bytes']>=131072*(8+4*transport['max_commands']),'shared transport diagnostic/control allowance insufficient')
    # Cumulative rounded network/diagnostic caps above remain unchanged. They
    # are not simultaneous retained local payloads: successful get staging is
    # moved to the caller, while each call retains one bounded transport JSON.
    # Context serialization and first-failure poisoning allow at most one
    # in-flight/failed get diagnostic body; caller destinations remain separate.
    buffers=selected_buffers(g,spec['typed_allocations'],chunk*width)
    local_bounds={'retained_diagnostic_bytes':history_bounds['diagnostic_bytes'] if history_bounds is not None else TRANSPORT_META*transport['max_commands']+ARCHIVE_MAX_BYTES,
        'reserved_control_bytes':typed['max_control_bytes']+archive['max_workflow_metadata_bytes']+transport['max_control_bytes'],
        'caller_scratch_bytes':max(3*ARCHIVE_MAX_BYTES,max(v['selected_payload_overlap_upper_bytes'] for v in buffers.values()))+extra,
        'typed_attempt_metadata_bytes':max(sum(v['typed_attempt_metadata_allowance_bytes'] for v in buffers.values()),4*8192*sum(b['max_chunks'] for kinds in spec['typed_allocations']['by_week'].values() for b in kinds.values()))}
    for key,minimum in local_bounds.items():
        positive(minimum);need(store[key]>=minimum,'retained local component underfunded: '+key)
    # Selected overlap excludes retained matrices and controls, charged separately.
    # Remaining controls/extra scratch are explicit prospective declarations:
    # their completeness and actual filesystem overhead require Root admission.
    logical_growth=sum(store[k] for k in ('reserved_growth_bytes','reserved_control_bytes','retained_diagnostic_bytes','caller_scratch_bytes','typed_attempt_metadata_bytes'))+sum(inventory.values())
    allocated_growth=logical_growth+store['allocation_overhead_bytes']
    positive(logical_growth);positive(allocated_growth)
    need(store['baseline_allocated_bytes']+allocated_growth<=limits['max_allocated_bytes'] and store['baseline_logical_bytes']+logical_growth<=limits['max_logical_bytes'],'common store allocation exceeded')
    transport.update(schema_version=2,format='archive-dispatch-v1',typed_payload_input=typed_role,connection=None)
    # Connection remains a conspicuous invalid template until Root supplies private configuration.
    selected['descriptor'].update(required_graphs=required,resource_graph_inputs=mapping,original_dictionary_import={'input':selected['original_dictionary_input'],'sha256':sha(raw(control))})
    item=plan['producers'][selected['producer']];item.update(copy.deepcopy(selected));item['binding_output']=p['outputs']['binding'];item['journal_output']=p['outputs']['journal']
    docs={spec['template_roles'][key]:value for key,value in [('pilot',p),('population',pop),('job',job),('producer_plan',plan),('dictionary',control),('output',output)]};docs[typed_role]=typed;docs[selected['compact_archive_transport_input']]=transport
    need(selected['real_pilot_input']==spec['template_roles']['pilot'] and selected['plan_input']==spec['template_roles']['producer_plan'] and selected['original_dictionary_input']==spec['template_roles']['dictionary'] and selected['compact_mcm_output_input']==spec['template_roles']['output'] and p['population_plan_input']==spec['template_roles']['population'],'exact generated role joins differ')
    need(len(docs)==8 and not set(mapping.values()) & set(docs),'generated input role collision')
    role_fields={'real_pilot_input','plan_input','pair_checkpoint_input','original_dictionary_input','compact_policy_input','original_dictionary_stage_input','compact_mcm_input','compact_mcm_output_input','compact_archive_input','compact_archive_transport_input'}
    consumed={selected[k] for k in role_fields}|{job['environment_input'],p['population_plan_input'],p['model_input'],p['training_input'],pop['scope_input'],pop['calendar_input'],pop['price_panel_input'],typed_role}|set(mapping.values())
    if 'imported_authority_lease_input' in p:consumed.add(p['imported_authority_lease_input'])
    need(consumed<=set(refs)|set(docs)|set(mapping.values()),'missing referenced input role: '+str(sorted(consumed-(set(refs)|set(docs)|set(mapping.values())))))
    need(selected['compact_policy_input']==spec['template_roles']['compact'] and selected['compact_archive_input']==spec['template_roles']['archive'],'original compact/archive template roles differ')
    opaque={role:ref for role,ref in refs.items() if role not in docs}
    opaque.update({v['role']:v['manifest'] for v in g.values()})
    return {'status':'DRAFT_NOT_REGISTERED_NOT_ADMITTED','inputs':docs,'opaque_references':opaque,'source_template_references':{role:refs[role] for role in spec['template_roles'].values()},'graphs':g,'physical_store_declaration':store,'capacity_lower_bounds':{'typed':total,'pair_archive':pair,'shared':combined,'per_graph':minima,'largest_matrix_file_bytes':max_matrix,'retained_local_lower_bounds':local_bounds,'selected_buffer_calculations':buffers,'mandatory_typed_attempt_directory_count':sum(v['typed_attempt_directory_count'] for v in buffers.values()),'admitted_typed_attempt_count_bound':sum(b['max_chunks'] for kinds in spec['typed_allocations']['by_week'].values() for b in kinds.values()),'remaining_control_declared_bytes':sum(inventory.values()),'declared_logical_growth_bytes':logical_growth,'declared_allocated_growth_bytes':allocated_growth},'remaining':['Root verifies complete retained-control/scratch inventory, block/directory/inode overhead and current baseline; declared lower bounds are not capacity proof','Root private connection and transport_identity match','genuine complete graph admission and node-count proof review','current source/runtime/Owner/Binding, resource/storage/network admission','worker derives price eligibility, consecutive indices and resource-only scaler; no numeric data read here'],'no_authority_or_capacity_claim':True}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',required=True);ap.add_argument('--spec',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
    source=Path(a.spec);need(source.stat().st_size<=LIMIT,'spec metadata bound');result=build(Path(a.root),json.loads(source.read_bytes()));out=Path(a.output);need(not out.exists(),'fresh draft namespace required')
    for role in result['inputs']:need(Path(role).name==role and role not in ('.','..'),'safe input role filename required')
    out.mkdir()
    for role,value in result['inputs'].items():
        with (out/(role+'.json')).open('xb') as f:f.write(raw(value))
    (out/'DRAFT_INDEX.json').write_bytes(raw(result))
if __name__=='__main__':main()
