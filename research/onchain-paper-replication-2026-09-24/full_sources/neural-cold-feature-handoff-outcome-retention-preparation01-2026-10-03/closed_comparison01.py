"""Explicit read-only CLOSED comparison verifier; never a preclaim gate.
All original context joins retained; actual born successful lifecycle required.
"""
import importlib,json,os,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace

def closed_comparison_context(root,release,api):
    phase='compare';mode='closed-comparison'
    require=api.require;digest=api.digest;body=api.body;deref=api.deref;document=api.document
    _source_head=api._source_head;_committed_reference=api._committed_reference
    authenticate_prior=api.authenticate_prior;no_numerics=api.no_numerics
    IDENTITIES=api.IDENTITIES;PROGRAM=api.PROGRAM;CELLS=api.CELLS
    PREFIX=api.PREFIX;OUTER=api.OUTER;ARTIFACT=api.ARTIFACT;GIB=api.GIB;MAX=api.MAX
    started=time.monotonic();root=Path(root)
    fields={'schema_version','kind','status','phase','root','source','registration','sources','runtime','native_environment','phase_contract','prior_materialization','cpus','remaining'}
    require(set(release)==fields and release['schema_version']==1 and release['kind']=='cold-proof-outer-release-v1' and release['status']=='released' and release['remaining']==[] and release['phase']==phase in IDENTITIES,'proof source draft is not an exact release')
    require(Path.cwd()==root and root.resolve()==root and release['root']==str(root) and (root/'.git').is_dir() and not (root/'.git').is_symlink() and not (root/'.git/objects/info/alternates').exists(),'genuine isolated capsule required')
    _source_head(root,release['source'],mode)
    source_doc=deref(root,release['sources']);require(set(source_doc)=={'schema_version','files'} and source_doc['schema_version']==1 and 0<len(source_doc['files'])<=2048,'source document denominator differs')
    sources=source_doc['files'];required={'proof_tools/proof_supervise01.py','proof_tools/proof_outer01.py','proof_tools/proof_raw01.py','proof_tools/proof_release01.py','proof_tools/runtime_gate01.py','tradingagents/research/onchain_replication/job.py','tradingagents/research/onchain_replication/resources.py','tradingagents/research/onchain_replication/owned_io.py','tradingagents/research/onchain_replication/workflow_storage.py','tradingagents/research/onchain_replication/compact_cold_proof.py','tradingagents/research/onchain_replication/compact_cold_proof_inputs.py','tradingagents/research/onchain_replication/compact_cold_proof_native.py'}
    require(required<=set(sources),'proof source closure missing')
    for name,sha in sources.items():
        raw=body(root,name);require(digest(raw)==sha,'source changed '+name)
        committed=subprocess.check_output(['git','show',release['source']+':'+name],cwd=root,timeout=10)
        require(committed==raw and time.monotonic()-started<=120,'source Git closure/time differs')
    require(Path(api.__file__).resolve()==root/'proof_tools/proof_release01.py','release verifier outside genuine capsule')
    registration=_committed_reference(root,release['source'],release['registration']);contract=deref(root,release['phase_contract']);identity=IDENTITIES[phase]
    require(set(contract)=={'schema_version','identity','experiment','family','expected_outputs'} and contract['schema_version']==1 and contract['identity']==identity,'phase contract differs')
    experiment=contract['experiment'];family=contract['family'];require(registration['program_id']==PROGRAM and registration['experiments'][identity]==experiment and registration['families'][experiment['family']]==family,'original registration/phase contract differs')
    require(family['attempt_budget']==2 and family['prior_attempts']==0 and experiment['cells']==[CELLS[phase]],'separate finite engineering budget/cell differs')
    outputs=['proof-materialize.json'] if phase=='materialize' else ['binding.json','journal.json','cold-handoff.json','proof-compare.json']
    require(sorted(experiment['outputs'])==sorted(contract['expected_outputs'])==sorted(outputs),'exact phase output denominator differs')
    require(experiment['source_files']==sources,'registration source closure differs')
    for name,info in experiment['inputs'].items():require(digest(body(root,info['path']))==info['sha256'],'input changed '+name)
    job=document(root,experiment['inputs']['execution_job']['path']);p=job['resources']
    require(job['kind']=='fit' and set(job['payload'])=={'cold_proof_input','representation_jobs'},'genuine proof fit dispatch differs')
    policy=document(root,experiment['inputs'][job['payload']['cold_proof_input']]['path'])
    require(policy['source_files']==sources and policy['experiment']==identity and policy['phase']==phase and policy['kind']=='genuine-compact-cold-engineering-proof-v1','selected proof authority differs')
    require(p['memory_max_bytes']==p['memory_high_bytes']==3*GIB and p['reserve_bytes']==3*GIB and p['start_reserve_bytes']==6*GIB and p['wall_seconds']==1800 and p['disk_floor_bytes']==10*GIB and p['disk_paths']==[str(root)] and p['native_unit_limits']=={'file_size_bytes':MAX} and 'physical_policy' not in p,'exact native policy differs')
    require(p['storage_budget']=={'root':str(root),'limits':{'max_allocated_bytes':GIB,'max_logical_bytes':GIB,'max_entries':32768,'max_depth':32,'max_scan_seconds':5}},'whole writable capsule watch differs')
    require(type(release['cpus']) is list and release['cpus']==sorted(release['cpus']) and len(release['cpus'])==len(set(release['cpus']))==2 and all(type(x) is int for x in release['cpus']),'CPU affinity denominator differs')
    require((root/'research_runs'/identity/'claim.json').is_file() and (root/'research_runs'/identity/'complete.json').is_file() and not (root/'research_runs'/identity/'failed.json').exists(),'actual closed successful comparison claim/terminal required')
    evolution=deref(root,release['prior_materialization']['evolution'])
    require(len(evolution['additions'])==3 and {r['role'] for r in evolution['additions']}=={'comparison-registration','comparison-charter','comparison-phase-contract'},'exact three additions plus evolution document required')
    prior=release['prior_materialization']
    if phase=='materialize':require(prior is None and job['payload']['representation_jobs']=={},'materialization cannot claim prior science')
    else:authenticate_prior(root,release,experiment,job)
    runtime=deref(root,release['runtime']);environment=deref(root,release['native_environment'])
    require(sys.executable==runtime['executable'] and sys.prefix==runtime['prefix'],'locked runtime mapping differs')
    sys.path.insert(0,str(root));blocker=no_numerics()
    job_module=importlib.import_module('tradingagents.research.onchain_replication.job')
    require(Path(job_module.__file__).resolve()==root/'tradingagents/research/onchain_replication/job.py','genuine job import origin differs')
    args=SimpleNamespace(root=root,registration=release['registration']['path'],experiment=identity,source=release['source'])
    launch_command=job_module._command(args,'launch');worker_command=job_module._command(args,'worker')
    return {'release':release,'phase':phase,'sources':sources,'runtime':runtime,'environment':environment,'experiment':experiment,'family':family,'job':job,'launch_command':launch_command,'worker_command':worker_command,'blocker':blocker,'source_count':len(sources)}


def authenticate_closed_comparison(root, release, accepted_ref, wait_ref, api):
    """Strict readonly comparison analogue; actual original authority required."""
    require=api.require;deref=api.deref;metadata=api.metadata;ref=api.ref
    module=api.module;authenticate=api.authenticate;closure=api.closure
    IDENTITIES=api.IDENTITIES;OUTER=api.OUTER;MAX=api.MAX;GIB=api.GIB
    prior={'accepted':accepted_ref,'wait':wait_ref};identity=IDENTITIES['compare']
    require(prior['accepted']['path']==OUTER+identity+'/accepted.json' and prior['wait']['path']=='proof_supervise/'+identity+'/exit.json','prior original receipt paths differ')
    accepted=deref(root,prior['accepted']);wait=deref(root,prior['wait'])
    require(accepted['status']==wait['status']=='accepted' and accepted['phase']==wait['phase']=='compare' and accepted['identity']==wait['identity']==identity,'prior disposition differs')
    require(accepted['source']==wait['source'],'prior source commits conflict')
    require(accepted['release']==wait['release'],'original release references conflict')
    original=deref(root,accepted['release'])
    require(original['source']==accepted['source'],'original materialization source conflicts with retained receipts')
    # This reuses all exact Git/source/registration/input/policy checks but
    # deliberately does not invoke fresh admission or demand absent old claims.
    require(original==release,'original comparison release differs')
    ctx=closed_comparison_context(root,original,api)
    require(len(ctx['experiment']['inputs'])==44,'comparison44 inputs required')
    require(len(ctx['sources'])==195,'historical195 selected source denominator differs')
    runtime_gate=module('cold_prior_runtime_gate',root/'proof_tools/runtime_gate01.py',ctx['sources']['proof_tools/runtime_gate01.py'])
    runtime_gate.check(root,ctx['runtime'])
    require(wait['controller_exit_code']==0 and wait['controller_pid_absent'] is True and wait['accepted_receipt']==prior['accepted'],'actual materialization wait differs')
    require(all(type(wait[k]) is int and wait[k]>1 and not Path('/proc',str(wait[k])).exists() for k in ('controller_pid','supervisor_pid')),'prior controller/supervisor remains')
    for namespace,names in [('proof_supervise/',('late-failure.json',)),(OUTER,('failed.json','late-failure.json'))]:
        require(not any((root/namespace/identity/n).exists() for n in names),'prior late failure remains')
    claim=metadata(root,'proof_supervise/'+identity+'/claim.json');child=metadata(root,'proof_supervise/'+identity+'/child.json');intent=metadata(root,OUTER+identity+'/intent.json')
    require(claim['phase']=='compare' and claim['identity']==identity and claim['source']==original['source'] and claim['release']==accepted['release'] and claim['owner_pid']==wait['supervisor_pid'] and claim['numerical_claim'] is False,'supervisor claim authority differs')
    require(child['pid']==wait['controller_pid'] and type(child['start_ticks']) is str and child['start_ticks'].isdigit(),'original controller child identity differs')
    command=[sys.executable,'-B',str(root/'proof_tools/proof_outer01.py'),'--release',accepted['release']['path'],'--release-sha256',accepted['release']['sha256'],'--phase','compare']
    require(claim['command']==command and claim['file_size_limit']==[MAX,MAX],'original controller command differs')
    require(intent['source']==original['source'] and intent['release']==accepted['release'] and intent['phase']=='compare' and intent['identity']==identity and intent['caller_pid']==child['pid']==wait['controller_pid'],'controller source/release/PID intent differs')
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
    observed=authenticate(root,'compare',ctx)
    require(observed==deref(root,accepted['authentication']),'retained authentication differs from actual original evidence')
    require(accepted['tail']==closure(root,'compare',ctx['job']['resources']['storage_budget']['limits']),'original native outer closure differs')
    return {'context':ctx,'observed':observed}
