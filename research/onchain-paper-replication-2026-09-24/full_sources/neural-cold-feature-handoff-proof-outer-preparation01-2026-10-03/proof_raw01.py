"""Strict proof-specific retained-byte authentication. Never loads arrays/pickle."""
import hashlib,io,json,os,re,stat,zipfile,time
from pathlib import Path
META=8192
DEADLINE=None
MAX=4*1024**2
GIB=1024**3
PROGRAM='compact-cold-engineering-20261003'
IDENTITIES={'materialize':'compact-cold-inputs-20261003-01','compare':'compact-cold-comparison-20261003-01'}
CELLS={'materialize':'cold-input-materialization','compare':'cold-genuine-comparison'}
PREFIX='research_artifacts/onchain-paper-replication-2026-09-24/runs/'
ARTIFACT='research_artifacts/compact-cold-engineering-20261003/'
OUTER='proof_outer/'

def require(value,message):
    if not value:raise ValueError(message)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def fatal(error):return error is not None and (not isinstance(error,Exception) or isinstance(error,(MemoryError,RecursionError)))
def preserve(first,later):return first if fatal(first) else later if fatal(later) or first is None else first

def body(root,relative,limit=MAX):
    require(DEADLINE is None or time.monotonic()<=DEADLINE,'raw verification deadline exceeded')
    root=Path(root);relative=Path(relative);p=root/relative
    require(not any(x in {'keys','apis','.env','hf_token.txt','id_rsa','id_ed25519'} for x in relative.parts),'secret location is outside evidence scope')
    require(not relative.is_absolute() and '..' not in relative.parts and p.resolve()==p and p.is_relative_to(root),'raw path redirected')
    before=p.lstat();require(stat.S_ISREG(before.st_mode) and before.st_nlink==1 and before.st_dev==root.stat().st_dev and before.st_size<=limit<=MAX,'raw regular extent differs')
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW);primary=None;result=None
    try:
        opened=os.fstat(fd);require((opened.st_dev,opened.st_ino)==(before.st_dev,before.st_ino),'raw inode differs')
        chunks=[];left=before.st_size
        while left:
            require(DEADLINE is None or time.monotonic()<=DEADLINE,'raw body deadline exceeded')
            part=os.read(fd,min(left,65536));require(part,'raw truncated');chunks.append(part);left-=len(part)
        require(not os.read(fd,1),'raw extended');after=p.lstat();again=os.fstat(fd)
        sig=lambda x:(x.st_dev,x.st_ino,x.st_size,x.st_mtime_ns,x.st_ctime_ns,x.st_nlink)
        require(sig(before)==sig(after)==sig(again),'raw changed during read');result=b''.join(chunks)
    except BaseException as error:primary=error
    try:os.close(fd)
    except BaseException as error:primary=preserve(primary,error)
    if primary is not None:raise primary
    return result

def parse(raw):
    def pairs(values):
        d={}
        for k,v in values:require(k not in d,'duplicate JSON key');d[k]=v
        return d
    def bad(value):raise ValueError('nonfinite JSON constant')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)
def metadata(root,path):return parse(body(root,path,META))
def native_metadata(root,path):return parse(body(root,path,65536))
def document(root,path):return parse(body(root,path,MAX))
def ref(root,path,*,kind='document'):
    raw=body(root,path,META if kind=='metadata' else MAX)
    return {'path':str(path),'sha256':digest(raw),'bytes':len(raw),'kind':kind}
def deref(root,item):
    require(type(item) is dict and set(item)=={'path','sha256','bytes','kind'} and item['kind'] in ('metadata','document'),'reference schema differs')
    raw=body(root,item['path'],META if item['kind']=='metadata' else MAX)
    require(type(item['bytes']) is int and len(raw)==item['bytes'] and digest(raw)==item['sha256'],'reference bytes differ')
    return parse(raw)
def absolute_ref(root,item):
    require(set(item)=={'path','sha256'},'absolute scientific reference differs')
    path=Path(item['path']);require(path.is_absolute() and path.is_relative_to(root),'scientific reference outside capsule')
    raw=body(root,str(path.relative_to(root)));require(digest(raw)==item['sha256'],'scientific saved bytes differ');return parse(raw)

def positive_native_observations(root,guard,child,limits):
    """Authenticate genuine existing snapshot fields, without numeric loading."""
    require('snapshot_error' in child and child['snapshot_error'] is None and child.get('reason')=='workload exited','child terminal snapshot failed/missing')
    snapshot=child.get('terminal_memory_snapshot')
    require(type(snapshot) is dict and guard.get('terminal_memory_snapshot')==snapshot,'original child terminal memory join differs')
    events=snapshot.get('memory_events');current=snapshot.get('memory_current_bytes')
    require(type(events) is dict and all(type(v) is int and v>=0 for v in events.values())
        and events.get('oom')==events.get('oom_kill')==0,'terminal memory events differ')
    require(type(current) is int and 0<=current<=limits['memory_max_bytes']
        and guard.get('memory_events')==events and guard.get('memory_current_bytes')==current,'terminal memory current differs')
    peak=guard.get('peak_sampled_memory_current_bytes')
    require(type(peak) is int and current<=peak<=limits['memory_max_bytes'],'positive sampled memory peak missing/differs')
    initial=guard.get('initial_memory_events')
    require(type(initial) is dict and initial and all(type(v) is int and v==0 for v in initial.values()),'initial memory event evidence differs')
    elapsed=guard.get('elapsed_seconds')
    require(type(elapsed) in (int,float) and 0<=elapsed<=limits['wall_seconds']+60,'native elapsed evidence missing/differs')
    host=guard.get('host_mem_available_bytes')
    require(type(host) is int and host>=limits['reserve_bytes'],'observed host reserve missing/breached')
    disk=guard.get('disk_free_bytes')
    require(type(disk) is dict and set(disk)=={str(root)} and type(disk[str(root)]) is int
        and disk[str(root)]>=limits['disk_floor_bytes'],'native disk-floor evidence missing/breached')
    budget=limits['storage_budget'];observation=guard.get('storage_observation')
    require(guard.get('storage_budget')==budget and type(observation) is dict,'positive storage observation missing')
    info=root.stat();require(observation.get('root')==str(root) and observation.get('root_device')==info.st_dev
        and observation.get('root_inode')==info.st_ino,'native storage original root differs')
    bounds=budget['limits']
    for key,cap in (('allocated_bytes','max_allocated_bytes'),('logical_file_bytes','max_logical_bytes'),('entries','max_entries')):
        last=observation.get(key);high=guard.get('storage_peak_'+key)
        require(type(last) is int and type(high) is int and 0<=last<=high<=bounds[cap],'positive storage/peak missing/differs: '+key)
    files=observation.get('regular_files');dirs=observation.get('directories');scan=observation.get('elapsed_seconds')
    require(type(files) is int and files>0 and type(dirs) is int and dirs>0
        and observation['entries']==files+dirs-1 and type(scan) in (int,float)
        and 0<=scan<=bounds['max_scan_seconds'],'storage scan denominator/time differs')
    return {'sampled_memory_current_bytes':current,'sampled_memory_peak_bytes':peak,
        'native_elapsed_seconds':elapsed,'native_disk_free_bytes':disk[str(root)],
        'storage_observation':observation,'qualification':'Sampled guard observations precede outer tail; no kernel aggregate filesystem quota or full-size capacity inference.'}

def native(root,phase,ctx):
    identity=IDENTITIES[phase];base=PREFIX+identity;limits=ctx['job']['resources'];source=ctx['release']['source']
    launch=metadata(root,base+'/launch.json');owner=metadata(root,base+'/owner.json')
    guard=native_metadata(root,base+'/guard/final.json');ready=native_metadata(root,base+'/guard/cpu_ready.json');child=native_metadata(root,base+'/guard/child_exit.json')
    require(set(launch)=={'experiment','source_commit','supervisor_pid','nonce'} and launch['experiment']==identity and launch['source_commit']==source,'genuine launch identity differs')
    supervisor=metadata(root,OUTER+identity+'/supervisor.json');require(supervisor['pid']==launch['supervisor_pid'],'outer supervisor join differs')
    require(set(owner)==set(launch)|{'monitor_pid','monitor_start_ticks'} and all(owner[k]==v for k,v in launch.items()),'genuine monitor owner differs')
    require(guard['owner_identity']==owner and type(guard['monitor_pid']) is int and guard['monitor_pid']==owner['monitor_pid'] and guard['command']==ctx['worker_command'] and guard['cwd']==str(root),'genuine native command/owner differs')
    require(not (root/base/'guard/native-finalization-failed.json').exists(),'native finalization failed')
    require(all(guard[k]==v for k,v in limits.items()) and guard['memory_swap_max_bytes']==0,'registered actual native policy differs')
    require(guard['kernel_controls']=={'memory.max':str(3*GIB),'memory.high':str(3*GIB),'memory.swap.max':'0'},'actual kernel controls differ')
    require(metadata(root,base+'/guard/release.json')=={'kernel_controls_verified':True},'native release missing')
    require(ready['cpus']==guard['cpus']==ctx['release']['cpus'] and len(guard['cpus'])==len(set(guard['cpus']))==2 and all(type(x) is int for x in guard['cpus']),'native CPU identity differs')
    props=guard['native_unit_properties'];require(props['LimitFSIZE']==props['LimitFSIZESoft']=='4194304' and props['RuntimeMaxUSec'] in ('30min','1800s','1800000000us'),'actual native file/time controls differ')
    require(ready['file_size_limit']==[MAX,MAX] and ready['native_unit_limits']=={'file_size_bytes':MAX},'actual child native limits missing')
    require(ready['native_environment']==guard['native_environment']==ctx['environment'],'owned native environment differs')
    for role,pid in [('worker',child['workload_pid']),('monitor',owner['monitor_pid'])]:
        value=native_metadata(root,base+'/'+role+'-file-limit.json')
        require(value['role']==role and value['experiment']==identity and value['source_commit']==source and value['pid']==pid and value['file_size_limit']==[MAX,MAX] and value['before_claim'] is True and value['native_environment']==ctx['environment'],'genuine before-claim receipt differs')
        if role=='worker':require(value['native_unit']==guard['unit'] and value['native_cgroup']==guard['cgroup'],'genuine worker unit differs')
    require((root/base/'worker-file-limit.json').stat().st_mtime_ns<=(root/'research_runs'/identity/'claim.json').stat().st_mtime_ns,'worker control receipt is late')
    require(guard['cleanup_verified'] is True and guard['cleanup_unit_properties']['ActiveState'] in ('inactive','failed') and guard['cleanup_unit_properties']['SubState'] in ('dead','failed'),'native cleanup readback differs')
    for key in ('storage_breach','storage_last_error','cleanup_error','elapsed_time_kill','child_log_limit_reached'):require(not guard.get(key),'native boundary breach '+key)
    require(guard['phase']=='complete' and guard['child_exit_code']==child['exit_code']==0 and guard['limit_reason'] is None,'native workload did not strictly succeed')
    observations=positive_native_observations(root,guard,child,limits)
    pids={supervisor['pid'],launch['supervisor_pid'],owner['monitor_pid'],ready['pid'],child['workload_pid']}
    require(all(type(p) is int and p>1 and not Path('/proc',str(p)).exists() for p in pids),'original PID absence unproved')
    group=Path(guard['cgroup']);require(re.fullmatch(r'onchain-replication-[0-9a-f]{32}\.service',guard['unit']) and group.is_relative_to('/sys/fs/cgroup') and group.name==guard['unit'] and not group.exists(),'original cgroup absence unproved')
    require((root/base/'guard/child.log').stat().st_size<MAX,'child log may be truncated')
    return {'recorded_pids':sorted(pids),'original_cgroup':str(group),'native_final':ref(root,base+'/guard/final.json'),'observations':observations}


def lifecycle(root,phase,ctx):
    identity=IDENTITIES[phase];prefix='research_runs/'+identity;raw=body(root,prefix+'/claim.json');claim=parse(raw)
    require(claim['program_id']==PROGRAM and claim['experiment_id']==identity and claim['source']==ctx['release']['source'] and claim['registration']==ctx['release']['registration']['path'] and claim['registration_sha256']==ctx['release']['registration']['sha256'],'genuine ResearchRun claim differs')
    require(claim['family']==ctx['family'] and claim['experiment']==ctx['experiment'] and claim['inputs']==ctx['experiment']['inputs'],'genuine claim authority differs')
    require(not (root/prefix/'failed.json').exists(),'lifecycle failed')
    terminal=document(root,prefix+'/complete.json')
    require(terminal['status']=='complete' and terminal['experiment_id']==identity and terminal['source']==ctx['release']['source'] and terminal['claim_sha256']==digest(raw) and terminal['registration_sha256']==claim['registration_sha256'],'genuine lifecycle completion differs')
    expected=[{'id':CELLS[phase],'status':'complete','scientific_id':CELLS[phase]}]
    require(terminal['cells']==expected and terminal['cell_count']==1 and terminal['unavailable_count']==0,'actual finite cell did not strictly succeed')
    names=ctx['experiment']['outputs'];directory=root/prefix/'outputs';require(set(names)=={f.name for f in directory.iterdir()},'output membership differs')
    hashes={n:digest(body(root,prefix+'/outputs/'+n)) for n in names};require(terminal['output_sha256']==hashes,'lifecycle output hashes differ')
    return claim,terminal,{'claim':ref(root,prefix+'/claim.json'),'terminal':ref(root,prefix+'/complete.json'),'outputs':hashes}


def materialization(root,ctx,summary):
    identity=IDENTITIES['materialize'];prefix=ARTIFACT+identity
    require(summary['status']=='materialized' and summary['program_id']==PROGRAM and summary['future_identity']==IDENTITIES['compare'] and summary['future_cell']==CELLS['compare'],'materialization identity/status differs')
    require(summary['registration_pending'] is True and summary['environment_input_pending'] is True and summary['historical_jobs_reopened'] is False,'materialization incorrectly claims admission')
    require((summary['train_rows'],summary['test_rows'],summary['excluded_rows'],summary['graph_population'],summary['required_graphs'])==(56,12,65,19,18),'actual materialized denominator differs')
    require(summary['fresh_sample_count']==summary['dictionary_size']==32 and summary['dictionary_max_pairs']==992 and summary['mcm_pairs_per_required_graph']==128,'fresh synthetic sample accounting differs')
    require(document(root,prefix+'/future-inputs.json')==summary and document(root,prefix+'/complete.json')==summary,'materializer original saved completion differs')
    refs=summary['inputs'];require(len([n for n in refs if n.startswith('graph-')])==19,'graph manifest denominator differs')
    population=None;graphs={};members=0
    for name,item in refs.items():
        raw=body(root,item['path']);require(digest(raw)==item['sha256'],'materialized input hash differs: '+name)
        value=parse(raw)
        if name=='population':population=value
        if name.startswith('graph-'):
            require(set(value['arrays'])=={'node_features','edge_index','edge_features','node_ids'},'actual graph members differ')
            graphs[value['graph_hash']]=value
            for key,entry in value['arrays'].items():
                require(entry['path']==key+'.npy','graph component path differs')
                component=Path(item['path']).parent/entry['path'];data=body(root,component)
                require(len(data)==entry['bytes'] and digest(data)==entry['sha256'],'actual graph component bytes differ');members+=1
    require(len(graphs)==19 and members==76 and population is not None,'materialized population missing')
    rows=population['examples'];require(len(rows['train'])==56 and len(rows['test'])==12 and len(rows['exclusions'])==65,'population actual row denominator differs')
    require(digest(canonical(rows['train']))==rows['train_hash'] and digest(canonical([r['decision_at'] for r in rows['test']]))==rows['test_mask_hash'],'population membership hash differs')
    required=sorted({h for row in rows['train']+rows['test'] for h in row['graph_hashes']});require(len(required)==18 and set(required)<=set(graphs),'materialized required graph union differs')
    for record in summary['batches']:
        indices=record['indices'];require(indices==list(range(indices[0],indices[-1]+1)) and record['decisions']==[rows['train'][i]['decision_at'] for i in indices],'consecutive eligible batch differs')
    require([len(r['indices']) for r in summary['batches']]==[16,16,8],'actual batch dimensions differ')
    future=document(root,refs['future_execution_job']['path']);require(future['payload']['cold_proof_input']=='cold_proof' and set(future['payload']['representation_jobs'])=={'cold-proof'},'future scientific dispatch differs')
    descriptor=future['payload']['representation_jobs']['cold-proof']['descriptor'];require(descriptor['required_graphs']==required and descriptor['graph_population']==sorted(graphs) and descriptor['train_hash']==rows['train_hash'],'future descriptor differs')
    # No representation completion should exist for an input-only phase.
    for namespace in ('onchain_representations','onchain_compact_handoffs'):
        require(not any((root/'research_artifacts'/namespace).glob('*/'+identity)),'materialization unexpectedly produced scientific authority')
    return {'kind':'materialized-inputs-only','future_inputs':ref(root,prefix+'/future-inputs.json'),'population':ref(root,refs['population']['path']),'graph_manifests':19,'graph_components':76,'required_graphs':18,'scientific_completion':False}


def proof_archives(root,prefix):
    results={}
    for task in ('direction','regression'):
        a=body(root,prefix+'/resident-'+task+'.pt');b=body(root,prefix+'/detached-'+task+'.pt')
        # Compare stored tensor bytes and the exact pickle description, without
        # unpickling, numeric imports, interpreting tensor arrays, or execution.
        def members(raw):
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                info=z.infolist();require(len(info)<=10000 and len({x.filename for x in info})==len(info),'proof archive members invalid')
                require(sum(x.file_size for x in info)<=MAX and all(x.compress_type==zipfile.ZIP_STORED and x.file_size<=MAX for x in info),'proof archive expansion/type differs')
                require(all(re.fullmatch(r'archive/(data/[0-9]+|data\.pkl|byteorder|version|\.format_version|\.storage_alignment|\.data/serialization_id)',x.filename) for x in info),'unknown torch archive member')
                return {x.filename:z.read(x) for x in info if x.filename!='archive/.data/serialization_id'}
        left,right=members(a),members(b);require('archive/data.pkl' in left and any(k.startswith('archive/data/') for k in left),'actual tensor proof absent')
        require(left==right,'saved resident/detached tensor description or raw storage differs')
        results[task]={'resident_sha256':digest(a),'detached_sha256':digest(b),'matched_members':len(left),'raw_storage_equality':True,'unpickled':False}
    return results


def component(root,prefix,expected):
    raw=body(root,prefix+'/manifest.json',65536);require(digest(raw)==expected,'scientific component manifest changed')
    value=parse(raw);require(value['schema_version']==1 and type(value['arrays']) is dict and 0<len(value['arrays'])<=1024,'scientific component extent differs')
    require({p.name for p in (root/prefix).iterdir()}=={'manifest.json',*value['arrays']},'scientific component membership differs')
    for name,item in value['arrays'].items():
        require(re.fullmatch(r'array-[0-9]{6}\.npy',name) is not None,'scientific component name differs')
        data=body(root,prefix+'/'+name);require(len(data)==item['bytes'] and digest(data)==item['sha256'],'scientific component payload differs')
    return value


def comparison(root,ctx,summary):
    identity=IDENTITIES['compare'];prefix=ARTIFACT+identity;outputs='research_runs/'+identity+'/outputs/'
    require(summary['status']=='complete' and summary['memory_saving_proved'] is False and summary['fullgraph_capacity_proved'] is False,'proof scientific qualification differs')
    require(document(root,prefix+'/complete.json')==summary and not (root/prefix/'failed.json').exists(),'proof worker saved completion differs')
    counts=summary['bitwise_tensor_comparisons'];require(set(counts)=={'direction','regression'} and all(type(v) is int and v>0 for v in counts.values()),'actual numerical comparison counters absent')
    release=summary['release'];names={'terminal','published','closure','training','dictionary','owner'}
    names|={f'graph-{i}'+suffix for i in range(19) for suffix in ('','-node_features','-edge_index','-edge_features')}
    names|={f'{kind}-{i}' for i in range(18) for kind in ('mcm','matrix')}
    require(release['observed']==sorted(names) and release['remaining']==[] and release['deliberate_alias_survivors']==sorted('graph-0'+s for s in ('','-node_features','-edge_index','-edge_features')),'actual lifetime ancestry denominator differs')
    job=ctx['job']['payload']['representation_jobs']['cold-proof'];d=job['descriptor'];workflow=digest(canonical(d))
    binding=document(root,outputs+job['binding_output']);journal=document(root,outputs+job['journal_output']);cold=document(root,outputs+'cold-handoff.json')
    require(binding['schema_version']==3 and binding['feature_hashes']==summary['feature_hashes'] and sorted(binding['feature_hashes'])==d['required_graphs'],'full schema3 feature binding differs')
    require(cold['kind']=='same-run-complete-compact-file-authority-v1' and cold['status']=='complete' and cold['experiment']==identity and cold['source']==ctx['release']['source'] and cold['registration_sha256']==ctx['release']['registration']['sha256'] and cold['workflow_identity']==workflow,'genuine cold authority identity differs')
    require(cold['original_object_verification_retired'] is True and cold['external_alias_release_verified'] is False and cold['memory_saving_verified'] is False and cold['empirical_admission_verified'] is False,'cold authority qualification differs')
    cold_saved=document(root,'research_artifacts/onchain_compact_handoffs/'+workflow+'/'+identity+'/complete.json');require(cold_saved==cold,'saved cold receipt differs')
    t=cold['terminal'];require(t['format']=='compact-representation-v1' and t['schema_version']==2 and t['status']=='complete' and t['resident_originals_retained'] is True and t['empirical_admission_verified'] is False and t['representation']==journal,'genuine original scientific terminal differs')
    require(document(root,'research_artifacts/onchain_compact_terminals/'+workflow+'/'+identity+'/complete.json')==t,'actual original terminal bytes differ')
    marker_path=journal['path'];marker=document(root,marker_path);require(digest(body(root,marker_path))==journal['sha256'] and marker['publication']==t['publication'] and marker['compact_owner']==t['owner_terminal'],'original terminal/publication/owner joins differ')
    publication=absolute_ref(root,t['publication']);owner_done=absolute_ref(root,t['owner_terminal'])
    closure=publication['closure'];require(publication['status']=='complete' and closure['binding']==binding and set(closure['graph_receipts'])==set(d['required_graphs']),'genuine Published/Closure population differs')
    require(cold['binding_sha256']==digest(body(root,outputs+job['binding_output'])) and marker['binding_sha256']==digest(canonical(binding)) and marker['closure_sha256']==publication['closure_sha256']==digest(canonical(closure)),'scientific binding/closure byte joins differ')
    denominator=closure['denominator']['denominator']
    require(denominator['train_rows']==56 and denominator['test_rows']==12 and denominator['lookback_days']==28 and denominator['calendar_days']==133 and sum(denominator['excluded_by_reason'].values())==65 and denominator['required_graphs']==d['required_graphs'] and denominator['graph_population']==d['graph_population'],'genuine complete scientific denominator differs')
    dictionary_prefix='research_artifacts/onchain_compact_dictionary/'+workflow+'/'+identity
    dictionary_raw=body(root,dictionary_prefix+'/complete.json',META);dictionary=parse(dictionary_raw)
    require(digest(dictionary_raw)==closure['dictionary_receipt_sha256'] and dictionary['dictionary_identity']==binding['dictionary_hash'] and dictionary['sample_provenance_admitted'] is True and dictionary['numeric_artifact_published'] is True,'genuine sampled dictionary receipt differs')
    component(root,dictionary_prefix+'/artifact',dictionary['artifact_sha256'])
    for h,sha in closure['graph_receipts'].items():
        graph_prefix='research_artifacts/onchain_compact_graphs/'+workflow+'/'+identity+'/'+h
        receipt_raw=body(root,graph_prefix+'/complete.json',META);graph=parse(receipt_raw)
        require(digest(receipt_raw)==sha and graph['graph_hash']==h and graph['feature_hash']==binding['feature_hashes'][h] and graph['numeric_payload_bytes']==576,'genuine required graph feature receipt differs')
        component(root,graph_prefix+'/artifact',graph['artifact_sha256'])
    original=journal['owner'];require(original['experiment']==identity and original['source_commit']==ctx['release']['source'] and original['workflow_identity']==workflow and original['claim_sha256']==digest(body(root,'research_runs/'+identity+'/claim.json')),'genuine Binding/ResearchRun join differs')
    require(marker['owner']==original and original['representation']=='cold-proof' and owner_done['representation_admitted'] is False,'original owner scientific disposition differs')
    # Genuine cold receipt pins complete immutable original content. Recheck every
    # body and directory membership; never synthesize a terminal callback.
    require(len(cold['file_pins'])<=20000 and len(cold['directory_pins'])<=2000,'cold inventory denominator exceeds admitted bound')
    for rel,sig,sha in cold['file_pins']:
        raw=body(root,rel);now=(root/rel).lstat();actual=(now.st_dev,now.st_ino,now.st_mode,now.st_nlink,now.st_size,now.st_mtime_ns,now.st_ctime_ns)
        require(tuple(sig)==actual and len(raw)==sig[4] and digest(raw)==sha,'original scientific saved content changed')
    for rel,signature,children in cold['directory_pins']:
        path=root/rel;info=path.lstat();require(tuple(signature)==(info.st_dev,info.st_ino,info.st_mode) and path.resolve()==path and path.is_dir() and sorted(p.name for p in path.iterdir())==list(children),'original scientific directory membership changed')
    stages=cold['stages'];require(len(stages)==19 and {Path(s['root']).name for s in stages}=={'dictionary',*('mcm-'+h for h in d['required_graphs'])},'actual stage denominator differs')
    for stage in stages:
        require('archive' not in stage['contract'],'local proof cannot certify archive transport')
        path=Path(stage['root']);require(path.is_relative_to(root),'stage path outside capsule')
        terminal=body(root,str(path.relative_to(root))+'/stage-complete.json',META);require(digest(terminal)==stage['sha256'],'actual stage terminal hash differs')
    checkpoints=[]
    for branch in ('resident','detached'):
        for task in ('direction','regression'):
            paths=list((root/prefix/branch/task/'checkpoint').glob('*/manifest.json'));require(len(paths)==1,'checkpoint artifact denominator differs')
            rel=str(paths[0].relative_to(root));manifest=document(root,rel)
            # The maintained cache is independently pinned below; raw oracle
            # trees already include the exact load/continuation observations.
            checkpoints.append(ref(root,rel))
            state=paths[0].parent/'state.pt';require(state.is_file() and state.stat().st_size<=MAX,'checkpoint state missing/oversized')
            raw=body(root,str(state.relative_to(root)));require(set(manifest['members'])=={'state.pt'} and manifest['members']['state.pt']=={'sha256':digest(raw),'size':len(raw)},'checkpoint member hash differs')
            selected=document(root,ctx['experiment']['inputs'][ctx['job']['payload']['cold_proof_input']]['path']);route=selected['inputs']
            model=document(root,ctx['experiment']['inputs'][route['model']]['path']);training=document(root,ctx['experiment']['inputs'][route['training']]['path']);population=document(root,ctx['experiment']['inputs'][route['population']]['path'])
            config_sha=digest(canonical({'model':model,'training':training,'execution':{'schema_version':1,'backend':'streamed-gat-mulsum-v1','block_edges':65536},'task':task}))
            provenance=manifest['provenance'];require(provenance['config_hash']==config_sha and provenance['source_hashes']==population['examples']['source_hashes'],'checkpoint configuration/source population differs')
            require(provenance['source_commit']==ctx['release']['source'] and provenance['dictionary_hash']==binding['dictionary_hash'] and provenance['input_hash']==d['train_hash'] and provenance['cell_id']==CELLS['compare'] and provenance['fold_id']=='synthetic-cold','actual checkpoint provenance differs')
            require(manifest['key']==paths[0].parent.name==digest(canonical({'provenance':provenance,'epoch':0,'batch':1})),'checkpoint cursor identity differs')
    return {'kind':'genuine-scientific-cold-comparison','binding':ref(root,outputs+job['binding_output']),'cold_authority':ref(root,outputs+'cold-handoff.json'),'original_terminal':ref(root,'research_artifacts/onchain_compact_terminals/'+workflow+'/'+identity+'/complete.json'),'stages':19,'tracked_ancestries':len(names),'tensor_archive_equality':proof_archives(root,prefix),'checkpoint_manifests':checkpoints,'worker_reported_comparison_counts':counts,'memory_saving_proved':False}


def authenticate(root,phase,ctx):
    root=Path(root);require(phase in IDENTITIES,'unknown phase')
    native_result=native(root,phase,ctx);claim,terminal,life=lifecycle(root,phase,ctx)
    path='research_runs/'+IDENTITIES[phase]+'/outputs/proof-'+phase+'.json';summary=document(root,path)
    proof=materialization(root,ctx,summary) if phase=='materialize' else comparison(root,ctx,summary)
    return {'schema_version':1,'phase':phase,'identity':IDENTITIES[phase],'status':'authenticated','lifecycle':life,'native':native_result,'proof':proof,'numerical_imports':False}


def closure(root,phase,limits):
    prefix=OUTER+IDENTITIES[phase]
    require(not any((root/prefix/n).exists() for n in ('failed.json','late-failure.json')),'outer failure remains')
    value=metadata(root,prefix+'/post-tail.json');require(value['disk_floor_bytes']==10*GIB and value['disk_free_bytes']>=10*GIB and value['excludes_own_file'] is True,'post-tail floor/boundary differs')
    info=root.stat();observed=value['storage'];require(observed['root']==str(root) and observed['root_device']==info.st_dev and observed['root_inode']==info.st_ino,'post-tail root differs')
    for key,bound in [('allocated_bytes','max_allocated_bytes'),('logical_file_bytes','max_logical_bytes'),('entries','max_entries')]:require(type(observed[key]) is int and 0<=observed[key]<=limits[bound],'post-tail storage bound differs')
    return ref(root,prefix+'/post-tail.json',kind='metadata')
