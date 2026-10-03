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

def _release_context(root,release,phase,mode):
    require(mode in ('unclaimed','retained-materialization') and (mode=='unclaimed' or phase=='materialize'),'historical context is materialization-only and read-only')
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
    require(Path(__file__).resolve()==root/'proof_tools/proof_release01.py','release verifier outside genuine capsule')
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
    if mode=='unclaimed':require(not any((root/n/identity).exists() or (root/n/identity).is_symlink() for n in ('research_runs',PREFIX,OUTER,ARTIFACT)),'phase identity already reserved/terminal')
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


def check_release(root,release,phase):
    """Only launch-facing gate: an already born identity always refuses."""
    return _release_context(root,release,phase,'unclaimed')


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


def _source_head(root,source,mode):
    require(type(source) is str and len(source)==40 and all(c in '0123456789abcdef' for c in source),'exact Git source required')
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True,timeout=10).strip()
    if head!=source:
        require(mode=='retained-materialization','source freeze HEAD differs')
        parents=subprocess.check_output(['git','rev-list','--parents','-n','1',head],cwd=root,text=True,timeout=10).strip().split()
        require(parents==[head,source],'historical source is not sole exact parent')
    return head


def _committed_reference(root,source,reference):
    value=deref(root,reference);raw=body(root,reference['path'])
    frozen=subprocess.check_output(['git','show',source+':'+reference['path']],cwd=root,timeout=10)
    require(len(frozen)<=MAX and frozen==raw,'original committed document differs')
    return value


def _registration_evolution(original,current,experiment,material):
    first=IDENTITIES['materialize'];second=IDENTITIES['compare']
    require(set(original)==set(current) and {k:v for k,v in original.items() if k!='experiments'}=={k:v for k,v in current.items() if k!='experiments'},'registration family/history/dataset or top-level drift')
    require(set(original['experiments'])=={first} and set(current['experiments'])=={first,second},'exact two-phase registration evolution required')
    old=original['experiments'][first];new=current['experiments'][second]
    require(current['experiments'][first]==old and new==experiment,'original experiment altered or comparison contract differs')
    allowed_changes={'parent','question','cells','outputs','inputs','charter'}
    require({k:v for k,v in new.items() if k not in allowed_changes}=={k:v for k,v in old.items() if k not in allowed_changes},'comparison runtime/window/stage or undeclared experiment drift')
    require(new['parent']==first and new['family']==old['family'] and new['source_files']==old['source_files'] and len(old['source_files'])==195,'comparison lineage/family/195 sources differ')
    require(set(material['inputs'])==MATERIAL_INPUTS,'materialized denominator reduced')
    expected={('execution_job' if name=='future_execution_job' else name):info for name,info in material['inputs'].items()}
    require(set(new['inputs'])==set(expected)|{'environment'} and all(new['inputs'][name]==info for name,info in expected.items()),'comparison inputs differ from actual emitted bytes')
    require(new['inputs']['environment']==old['inputs']['environment'],'original environment input changed')


def _evolution_tree(root,current,original,experiment,material,prior):
    """Exact additive B(parent=A) tree; no self hash or current-commit cycle."""
    parent=original['source'];head=_source_head(root,current['source'],'unclaimed')
    require(head!=parent and _source_head(root,parent,'retained-materialization')==head,'comparison requires the one new exact child commit')
    evolution=_committed_reference(root,head,prior['evolution'])
    fields={'schema_version','kind','parent_source','original_registration','current_registration','accepted','wait','additions'}
    require(set(evolution)==fields and type(evolution['schema_version']) is int and evolution['schema_version']==1 and evolution['kind']=='cold-proof-additive-registration-evolution-v1','typed evolution document differs')
    require(evolution['parent_source']==parent and evolution['original_registration']==original['registration'] and evolution['current_registration']==current['registration'] and evolution['accepted']==prior['accepted'] and evolution['wait']==prior['wait'],'evolution original ancestry differs')
    newreg=_committed_reference(root,head,current['registration']);oldreg=_committed_reference(root,parent,original['registration'])
    _registration_evolution(oldreg,newreg,experiment,material)
    require(current['registration']['path']!=original['registration']['path'],'original registration path cannot be overwritten')
    allowed={}
    def allow(path,sha,role):
        require(path not in allowed,'overlapping evolution file roles');allowed[path]={'path':path,'sha256':sha,'role':role}
    allow(current['registration']['path'],current['registration']['sha256'],'comparison-registration')
    charter=experiment['charter'];allow(charter['path'],charter['sha256'],'comparison-charter')
    for field,role in (('phase_contract','comparison-phase-contract'),('sources','unchanged-source-document')):
        if current[field]['path']!=original[field]['path']:allow(current[field]['path'],current[field]['sha256'],role)
    for info in material['inputs'].values():allow(info['path'],info['sha256'],'emitted-input')
    rows=evolution['additions'];require(type(rows) is list and 2<=len(rows)<=47,'finite addition denominator differs')
    require(all(type(r) is dict and set(r)=={'path','sha256','role'} and allowed.get(r['path'])==r for r in rows),'evolution admits an unregistered file/hash/role')
    paths=[r['path'] for r in rows];require(paths==sorted(set(paths)),'addition membership must be complete sorted unique')
    require({current['registration']['path'],charter['path']}<=set(paths),'new registration and charter must be committed additions')
    own=prior['evolution']['path'];require(own not in allowed and own not in paths,'evolution own document cannot self-hash or overlap')
    # Own document is authenticated by the external release reference and actual
    # B Git blob, not by a recursively embedded own hash or B commit in itself.
    raw=subprocess.check_output(['git','diff-tree','--no-commit-id','--name-status','-r','-z',parent,head],cwd=root,timeout=10)
    require(len(raw)<=65536,'bounded evolution diff exceeded');parts=raw.decode('utf-8').split('\0');require(parts[-1]=='' and (len(parts)-1)%2==0,'Git diff framing differs')
    changes=list(zip(parts[:-1:2],parts[1:-1:2]));require(all(status=='A' for status,path in changes),'evolution modifies/deletes/renames an old body')
    require(len(changes)==len(paths)+1 and {path for status,path in changes}==set(paths)|{own},'actual Git changes exceed declared finite evolution')
    for row in rows:
        raw=body(root,row['path']);require(digest(raw)==row['sha256'],'evolution input/document drift')
        frozen=subprocess.check_output(['git','show',head+':'+row['path']],cwd=root,timeout=10);require(frozen==raw and len(frozen)<=MAX,'added committed bytes differ')
    return {'parent_source':parent,'source':head,'addition_count':len(rows),'evolution':prior['evolution'],'qualification':'Own evolution document is separately release/Git authenticated; original native evidence is independently revalidated.'}


def authenticate_prior(root,current,experiment,job):
    """Actual historical A evidence plus separately committed finite child B."""
    prior=current['prior_materialization']
    require(type(prior) is dict and set(prior)=={'accepted','wait','evolution'} and set(job['payload']['representation_jobs'])=={'cold-proof'},'comparison requires exact prior closure and evolution')
    retained=authenticated_materialization(root,prior['accepted'],prior['wait']);ctx=retained['context'];original=ctx['release']
    require(deref(root,original['sources'])==deref(root,current['sources']) and len(ctx['sources'])==195,'exact195 selected source bodies changed')
    require(original['runtime']==current['runtime'] and original['native_environment']==current['native_environment'] and original['cpus']==current['cpus'],'original runtime/native/CPU contract changed')
    _evolution_tree(root,current,original,experiment,retained['material'],prior)
    return retained['observed']
