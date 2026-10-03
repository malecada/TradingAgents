"""Pinned prospective release joins. No registration, launch or numerical import."""
import importlib,importlib.abc,importlib.util,json,os,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace
from proof_raw01 import *

class NoNumericalImports(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0] in {'numpy','torch','pandas','pyarrow'}:raise ImportError('numerical imports belong only inside the guarded worker')
        return None

def no_numerics():
    require(not any(n.split('.')[0] in {'numpy','torch','pandas','pyarrow'} for n in sys.modules),'numerical module already imported')
    blocker=NoNumericalImports();sys.meta_path.insert(0,blocker);return blocker

def module(name,path,sha):
    require(digest(path.read_bytes())==sha,'helper source differs')
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value);return value

def check_release(root,release,phase):
    started=time.monotonic();root=Path(root)
    fields={'schema_version','kind','status','phase','root','source','registration','sources','runtime','native_environment','phase_contract','prior_materialization','cpus','remaining'}
    require(set(release)==fields and release['schema_version']==1 and release['kind']=='cold-proof-outer-release-v1' and release['status']=='released' and release['remaining']==[] and release['phase']==phase in IDENTITIES,'proof source draft is not an exact release')
    require(Path.cwd()==root and root.resolve()==root and release['root']==str(root) and (root/'.git').is_dir() and not (root/'.git').is_symlink() and not (root/'.git/objects/info/alternates').exists(),'genuine isolated capsule required')
    require(subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True,timeout=10).strip()==release['source'],'source freeze HEAD differs')
    source_doc=deref(root,release['sources']);require(set(source_doc)=={'schema_version','files'} and source_doc['schema_version']==1 and 0<len(source_doc['files'])<=2048,'source document denominator differs')
    sources=source_doc['files'];required={'proof_tools/proof_supervise01.py','proof_tools/proof_outer01.py','proof_tools/proof_raw01.py','proof_tools/proof_release01.py','proof_tools/runtime_gate01.py','tradingagents/research/onchain_replication/job.py','tradingagents/research/onchain_replication/resources.py','tradingagents/research/onchain_replication/owned_io.py','tradingagents/research/onchain_replication/workflow_storage.py','tradingagents/research/onchain_replication/compact_cold_proof.py','tradingagents/research/onchain_replication/compact_cold_proof_inputs.py','tradingagents/research/onchain_replication/compact_cold_proof_native.py'}
    require(required<=set(sources),'proof source closure missing')
    for name,sha in sources.items():
        raw=body(root,name);require(digest(raw)==sha,'source changed '+name)
        committed=subprocess.check_output(['git','show',release['source']+':'+name],cwd=root,timeout=10)
        require(committed==raw and time.monotonic()-started<=120,'source Git closure/time differs')
    require(Path(__file__).resolve()==root/'proof_tools/proof_release01.py','release verifier outside genuine capsule')
    registration=deref(root,release['registration']);contract=deref(root,release['phase_contract']);identity=IDENTITIES[phase]
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
    require(not any((root/n/identity).exists() or (root/n/identity).is_symlink() for n in ('research_runs',PREFIX,OUTER,ARTIFACT)),'phase identity already reserved/terminal')
    prior=release['prior_materialization']
    if phase=='materialize':require(prior is None and job['payload']['representation_jobs']=={},'materialization cannot claim prior science')
    else:
        require(prior is not None and set(job['payload']['representation_jobs'])=={'cold-proof'},'comparison requires actual materialization')
        require(set(prior)=={'accepted','wait'},'prior materialization closure references differ')
        accepted=deref(root,prior['accepted']);wait=deref(root,prior['wait'])
        require(prior['accepted']['path']==OUTER+IDENTITIES['materialize']+'/accepted.json' and accepted['status']=='accepted' and accepted['phase']=='materialize','materialization outer success absent')
        require(prior['wait']['path']=='proof_supervise/'+IDENTITIES['materialize']+'/exit.json' and wait['status']=='accepted' and wait['controller_exit_code']==0 and wait['controller_pid_absent'] is True and wait['accepted_receipt']==prior['accepted'] and wait['release']==accepted['release'],'actual observed materialization outer exit differs')
        require(all(type(wait[k]) is int and not Path('/proc',str(wait[k])).exists() for k in ('controller_pid','supervisor_pid')) and not (root/'proof_supervise'/IDENTITIES['materialize']/'late-failure.json').exists(),'prior materialization processes/late failure remain')
        require(not any((root/OUTER/IDENTITIES['materialize']/n).exists() for n in ('failed.json','late-failure.json')),'materialization outer failed')
        observed=deref(root,accepted['authentication']);require(observed['proof']['kind']=='materialized-inputs-only' and observed['proof']['scientific_completion'] is False,'materialization was relabeled scientific')
        material=deref(root,observed['proof']['future_inputs'])
        for name,info in material['inputs'].items():
            target='execution_job' if name=='future_execution_job' else name
            require(experiment['inputs'].get(target)==info,'comparison input not actual materialized bytes: '+target)
        require(digest(body(root,material['inputs']['population']['path']))==material['inputs']['population']['sha256'],'materialized population changed')
    runtime=deref(root,release['runtime']);environment=deref(root,release['native_environment'])
    require(sys.executable==runtime['executable'] and sys.prefix==runtime['prefix'],'locked runtime mapping differs')
    sys.path.insert(0,str(root));blocker=no_numerics()
    job_module=importlib.import_module('tradingagents.research.onchain_replication.job')
    require(Path(job_module.__file__).resolve()==root/'tradingagents/research/onchain_replication/job.py','genuine job import origin differs')
    args=SimpleNamespace(root=root,registration=release['registration']['path'],experiment=identity,source=release['source'])
    launch_command=job_module._command(args,'launch');worker_command=job_module._command(args,'worker')
    return {'release':release,'phase':phase,'sources':sources,'runtime':runtime,'environment':environment,'experiment':experiment,'family':family,'job':job,'launch_command':launch_command,'worker_command':worker_command,'blocker':blocker,'source_count':len(sources)}
