def authenticated_materialization(root,accepted_ref,wait_ref):
    """Revalidate retained materialization; never admit/replay its closed run."""
    prior={'accepted':accepted_ref,'wait':wait_ref};identity=IDENTITIES['materialize']
    require(prior['accepted']['path']==OUTER+identity+'/accepted.json' and prior['wait']['path']=='proof_supervise/'+identity+'/exit.json','prior original receipt paths differ')
    accepted=deref(root,prior['accepted']);wait=deref(root,prior['wait'])
    require(accepted['status']==wait['status']=='accepted' and accepted['phase']==wait['phase']=='materialize' and accepted['identity']==wait['identity']==identity,'prior disposition differs')
    require(accepted['source']==wait['source'],'prior source commits conflict')
    require(accepted['release']==wait['release'],'original release references conflict')
    original=deref(root,accepted['release'])
    require(original['source']==accepted['source'],'original materialization source conflicts with retained receipts')
    # This reuses all exact Git/source/registration/input/policy checks but
    # deliberately does not invoke fresh admission or demand absent old claims.
    ctx=_release_context(root,original,'materialize','retained-materialization')
    require(len(ctx['sources'])==195,'historical195 selected source denominator differs')
    runtime_gate=module('cold_prior_runtime_gate',root/'proof_tools/runtime_gate01.py',ctx['sources']['proof_tools/runtime_gate01.py'])
    runtime_gate.check(root,ctx['runtime'])
    require(wait['controller_exit_code']==0 and wait['controller_pid_absent'] is True and wait['accepted_receipt']==prior['accepted'],'actual materialization wait differs')
    require(all(type(wait[k]) is int and wait[k]>1 and not Path('/proc',str(wait[k])).exists() for k in ('controller_pid','supervisor_pid')),'prior controller/supervisor remains')
    for namespace,names in [('proof_supervise/',('late-failure.json',)),(OUTER,('failed.json','late-failure.json'))]:
        require(not any((root/namespace/identity/n).exists() for n in names),'prior late failure remains')
    claim=metadata(root,'proof_supervise/'+identity+'/claim.json');child=metadata(root,'proof_supervise/'+identity+'/child.json');intent=metadata(root,OUTER+identity+'/intent.json')
    require(claim['phase']=='materialize' and claim['identity']==identity and claim['source']==original['source'] and claim['release']==accepted['release'] and claim['owner_pid']==wait['supervisor_pid'] and claim['numerical_claim'] is False,'supervisor claim authority differs')
    require(child['pid']==wait['controller_pid'] and type(child['start_ticks']) is str and child['start_ticks'].isdigit(),'original controller child identity differs')
    command=[sys.executable,'-B',str(root/'proof_tools/proof_outer01.py'),'--release',accepted['release']['path'],'--release-sha256',accepted['release']['sha256'],'--phase','materialize']
    require(claim['command']==command and claim['file_size_limit']==[MAX,MAX],'original controller command differs')
    require(intent['source']==original['source'] and intent['release']==accepted['release'] and intent['phase']=='materialize' and intent['identity']==identity and intent['caller_pid']==child['pid']==wait['controller_pid'],'controller source/release/PID intent differs')
    require(intent['registration']==original['registration'] and intent['sources']==original['sources'] and intent['source_count']==len(ctx['sources']) and intent['launch_command']==ctx['launch_command'] and intent['worker_command']==ctx['worker_command'] and intent['file_limits']==[MAX,MAX] and intent['cpus']==original['cpus'],'controller registered native command differs')
    require(type(claim['owner_start_ticks']) is str and claim['owner_start_ticks'].isdigit() and int(claim['owner_start_ticks'])>0,'supervisor original process identity absent')
    require(wait['disk_free_bytes']>=10*GIB and wait['own_process_death_claimed'] is False,'supervisor final boundary differs')
    storage=wait['storage'];info=root.stat();require(storage['root']==str(root) and storage['root_device']==info.st_dev and storage['root_inode']==info.st_ino,'supervisor watched root differs')
    for key,bound in [('allocated_bytes','max_allocated_bytes'),('logical_file_bytes','max_logical_bytes'),('entries','max_entries')]:require(type(storage[key]) is int and 0<=storage[key]<=ctx['job']['resources']['storage_budget']['limits'][bound],'supervisor final storage differs')
    require(set(wait['controller_logs'])=={'controller.stdout','controller.stderr'},'final controller log denominator differs')
    for name,item in wait['controller_logs'].items():
        require(item['path']=='proof_supervise/'+identity+'/'+name,'final controller log path differs');require(ref(root,item['path'])==item,'final controller log changed')
    # Recompute actual native controls/owner/exit, genuine ResearchRun terminal
    # and original complete population. Summary labels cannot substitute for it.
    observed=authenticate(root,'materialize',ctx)
    require(observed==deref(root,accepted['authentication']),'retained authentication differs from actual original evidence')
    require(accepted['tail']==closure(root,'materialize',ctx['job']['resources']['storage_budget']['limits']),'original native outer closure differs')
    material=deref(root,observed['proof']['future_inputs']);require(set(material['inputs'])==MATERIAL_INPUTS,'materialized denominator reduced')
    return {'context':ctx,'observed':observed,'material':material,'registration':_committed_reference(root,original['source'],original['registration'])}
