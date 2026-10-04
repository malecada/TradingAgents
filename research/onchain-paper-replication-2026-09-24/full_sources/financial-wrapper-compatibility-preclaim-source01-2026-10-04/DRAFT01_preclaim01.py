"""Read-only metadata prerequisite for the one reviewed operational source edge.

Call with the original genuine Admission returned by job._admitted, then call
Run.start only in the separately reviewed Parent. This module never spends a
claim, decodes a checkpoint, imports a numerical package or publishes evidence.
All reads are sampled/currentness checks, not continuous writer exclusion.
"""
import hashlib
import importlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import time

FILE = 4 * 1024**2
TOTAL = 8 * 1024**2
SECONDS = 120
PREFIX = 'tradingagents/research/onchain_replication/'
HELPER = PREFIX + 'operational_source_compatibility.py'
HELPER_SHA = 'd0d770b45def89e8e00e81fa1bbb35416034eaace5ecab0f15193fd43b7a32d8'
POLICY_SHA = 'ae8fbdc9d13e75fc453b70b5ee633c89fb4577e9b68a35b4147cf1bbd58c6887'
ROLE = 'operational_source_compatibility'
REVIEW_ROLE = ROLE + '_review'
RECOVERY_ROLE = ROLE + '_recovery'
BASE = {'environment','execution_job','model','runtime_mapping','source_closure','synthetic_recipe','training','wrapper_plan',ROLE,REVIEW_ROLE,RECOVERY_ROLE}
EXTERNAL = {'review_proof','review_machine','review_manifest','review_report','recovery_proof','recovery_machine','recovery_manifest','recovery_report','final_parent_contract','final_parent_review'}
FIXED = {'complete100': {'experiment':'financial-wrapper-classification-eager-complete100-compatibility-20261004-01','cell_id':'financial-wrapper-classification-eager-reference-compatibility-20261004-01'}, 'continue100': {'experiment':'financial-wrapper-classification-eager-continue100-compatibility-20261004-01','cell_id':'financial-wrapper-classification-eager-continued-20261003-01'}, 'predict': {'experiment':'financial-wrapper-classification-eager-predict-compatibility-20261004-01','cell_id':'financial-wrapper-classification-eager-continued-20261003-01'}}

class Unavailable(ValueError): pass
class CleanupFailure(RuntimeError): pass

def require(ok, why):
    if not ok: raise Unavailable(why)

def sha(raw): return hashlib.sha256(raw).hexdigest()
def canonical(value): return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def encoded(value): return (json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def digest(value): return type(value) is str and len(value)==64 and all(c in '0123456789abcdef' for c in value)
def relative(value):
    require(type(value) is str and value and str(PurePosixPath(value))==value and not Path(value).is_absolute() and '..' not in PurePosixPath(value).parts and value!='.', 'canonical relative path required')
    require(not any(p in {'keys','apis','.env','hf_token.txt'} or p.startswith('.env.') for p in PurePosixPath(value).parts),'secret evidence path forbidden')
    return value

def _close(fd, primary):
    try: os.close(fd)
    except BaseException as error:
        fatal=lambda e: not isinstance(e,Exception) or isinstance(e,MemoryError)
        if primary is not None and fatal(primary):
            try:
                state=BaseException.__dict__['__dict__'].__get__(primary)
                prior=dict.get(state,'storage_cleanup_errors',())
                if type(prior) is not tuple: prior=(prior,)
                dict.__setitem__(state,'storage_cleanup_errors',prior+(error,))
            except BaseException as diagnostic: raise primary from diagnostic
            raise primary
        if fatal(error): raise error from primary
        failure=CleanupFailure('preclaim descriptor close uncertain')
        failure.storage_cleanup_errors=(error,)
        raise failure from primary

class Reader:
    """Bounded regular-file reads; cached paths rehashed before successful return."""
    def __init__(self):
        self.deadline=time.monotonic()+SECONDS
        self.total=0
        self.cache={}
    def tick(self): require(time.monotonic()<self.deadline,'preclaim metadata deadline')
    def read(self,path):
        path=Path(path)
        self.tick()
        require(path.is_absolute() and len(path.parts)<=64 and path.resolve(strict=True)==path,'canonical evidence origin')
        relative(path.relative_to('/').as_posix())
        if path in self.cache: return self.cache[path]
        raw=self._physical(path)
        self.cache[path]=raw
        return raw
    def _physical(self,path):
        self.tick();fds=[];primary=None
        try:
            fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_CLOEXEC);fds.append(fd)
            for part in path.parts[1:-1]:
                fd=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=fd);fds.append(fd)
            parent=fd
            fd=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=parent);fds.append(fd)
            first=os.fstat(fd)
            require(stat.S_ISREG(first.st_mode) and 0<=first.st_size<=FILE,'bounded regular metadata only')
            require(self.total+first.st_size<=TOTAL,'preclaim total byte bound')
            raw=bytearray()
            while True:
                self.tick()
                block=os.read(fd,min(65536,FILE+1-len(raw)))
                if not block: break
                self.total+=len(block)
                require(self.total<=TOTAL,'preclaim total actual byte bound')
                raw.extend(block)
                require(len(raw)<=FILE,'preclaim individual byte bound')
            signature=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
            require(signature(first)==signature(os.fstat(fd))==signature(os.stat(path.name,dir_fd=parent,follow_symlinks=False))==signature(path.lstat()) and path.resolve(strict=True)==path and len(raw)==first.st_size,'preclaim evidence changed during read')
            return bytes(raw)
        except BaseException as error: primary=error;raise
        finally:
            selected=primary
            for fd in reversed(fds):
                try: _close(fd,selected)
                except BaseException as error: selected=error
            if selected is not primary: raise selected
    def finish(self):
        for path,raw in self.cache.items():
            require(self._physical(path)==raw,'preclaim evidence changed after validation')
        self.tick()
    def reference(self,ref):
        require(type(ref) is dict and set(ref)=={'path','sha256'} and digest(ref['sha256']),'exact external body reference required')
        raw=self.read(Path(ref['path']))
        require(sha(raw)==ref['sha256'],'external reference hash differs')
        return raw

class Inputs:
    def __init__(self,root,registered,reader):
        require(type(registered) is dict and registered,'registered input denominator unavailable')
        self.root=root;self.registered=registered;self.reader=reader;self.bodies={};self.used=set()
        for role,info in registered.items():
            require(type(role) is str and role and type(info) is dict and set(info)=={'path','sha256','dataset'} and info['dataset']=='synthetic' and digest(info['sha256']),'every registered input must have a concrete synthetic pin')
            raw=reader.read(root/relative(info['path']))
            require(sha(raw)==info['sha256'],'registered input bytes differ: '+role)
            self.bodies[role]=raw
    def raw(self,role):
        require(type(role) is str and role in self.bodies,'missing registered prerequisite')
        self.used.add(role);return self.bodies[role]
    def json(self,role): return json.loads(self.raw(role))
    def path(self,role):
        self.raw(role);return self.root/self.registered[role]['path']
    def exact(self,role,path):
        require(self.path(role)==path,'registered evidence absolute path differs')
        return self.json(role)

def _roles(registered,phase):
    require(BASE<=set(registered),'all11 base and policy/proof inputs required before claim')
    if phase=='complete100': require(set(registered)==BASE,'reference phase has exactly11 registered inputs')

def _sealed(manifest,manifest_ref,ref,reader):
    require(type(manifest) is dict and type(manifest.get('members')) is list,'actual typed evidence manifest required')
    parent=Path(manifest_ref['path']).parent;path=Path(ref['path'])
    require(path.is_relative_to(parent),'sealed evidence is outside its manifest scope')
    name=path.relative_to(parent).as_posix()
    matches=[r for r in manifest['members'] if r.get('path')==name]
    require(len(matches)==1,'one exact sealed evidence member required')
    row=matches[0];raw=reader.reference(ref);st=path.lstat()
    require(row.get('kind')=='file' and row.get('sha256')==ref['sha256'] and row.get('bytes')==len(raw) and row.get('mode')==stat.S_IMODE(st.st_mode),'sealed evidence member body/type/extent/mode differs')

def _proof_bundle(kind,refs,inputs,policy,reader):
    role=REVIEW_ROLE if kind=='review' else RECOVERY_ROLE
    proofraw=reader.reference(refs[kind+'_proof'])
    require(proofraw==inputs.raw(role),'registered proof differs from separately referenced genuine evidence')
    proof=json.loads(proofraw)
    expected={'schema_version':1,'kind':role,'policy_sha256':POLICY_SHA,'historical_map_sha256':sha(canonical(policy['historical']['installed'])),'target_map_sha256':sha(canonical(policy['target']['installed'])),'checker_sha256':HELPER_SHA,'decision':'accepted'}
    require(proof==expected,'strict seven-field proof required')
    machine=json.loads(reader.reference(refs[kind+'_machine']));report=reader.reference(refs[kind+'_report']);manifest=json.loads(reader.reference(refs[kind+'_manifest']))
    for suffix in ('proof','machine','report'):_sealed(manifest,refs[kind+'_manifest'],refs[kind+'_'+suffix],reader)
    require(machine.get('schema_version')==1 and machine.get('policy_sha256')==POLICY_SHA and machine.get('checker_sha256')==HELPER_SHA and machine.get('historical_map_sha256')==expected['historical_map_sha256'] and machine.get('target_map_sha256')==expected['target_map_sha256'] and machine.get(kind+'_proof_sha256')==sha(proofraw) and machine.get('report_sha256')==sha(report),'independent evidence source/policy/proof/report joins differ')
    if kind=='review':
        require(machine.get('decision')=='ACCEPTED_EXACT_CONCRETE_POLICY_ONLY' and machine.get('consumers')==FIXED and machine.get('closure_sha256')==sha(inputs.raw(policy['target']['closure_input'])) and type(machine.get('reviewer')) is str and machine['reviewer'],'genuine concrete policy review unavailable')
    else:
        require(machine.get('decision')=='ACCEPTED_ACTUAL_OPERATIONAL_POLICY_RECOVERY','actual policy recovery not independently accepted')
        receipts=machine.get('recovery_receipts')
        require(type(receipts) is list and receipts,'actual recovery receipt denominator unavailable')
        require(len({json.dumps(r,sort_keys=True) for r in receipts})==len(receipts),'duplicate actual recovery receipts')
        for receipt in receipts:
            reader.reference(receipt);_sealed(manifest,refs[kind+'_manifest'],receipt,reader)
    return machine

def _parent_release(ad,plan,inputs,refs,reader):
    require(type(refs) is dict and set(refs)==EXTERNAL,'exact Root-authenticated external reference set required')
    q=json.loads(reader.reference(refs['final_parent_contract']));review=json.loads(reader.reference(refs['final_parent_review']))
    fields={'schema_version','status','capsule_root','parent_root','identity','source','design_source','registration','registration_sha256','source_files','input_hashes','runtime_mapping','caller_sha256','helper_hashes','proofs','final_review','expected_phase'}
    require(type(q) is dict and set(q)==fields and q['schema_version']==1 and q['status']=='RELEASED_ONE_USE_FINANCIAL_PARENT','actual released Parent contract required')
    require(q['capsule_root']==str(ad.root) and q['identity']==ad.experiment_id and q['source']==q['design_source']==ad.source and q['registration']==ad.registration and q['registration_sha256']==ad.registration_sha256 and q['source_files']==ad.experiment['source_files'] and q['expected_phase']==plan['phase'],'Parent/admission exact source/identity/registration join differs')
    require(q['input_hashes']=={r:v['sha256'] for r,v in ad.inputs.items()} and q['runtime_mapping']==inputs.json(plan['runtime_input']),'Parent full input/runtime map differs')
    require(q['final_review']==refs['final_parent_review'],'actual final Parent review reference differs')
    require(type(q['proofs']) is dict and set(q['proofs'])=={'cumulative','full_recovery','independent_source_input_runtime'},'Parent complete original proof denominator required')
    proofpins={k:sha(reader.reference(v)) for k,v in q['proofs'].items()}
    expected={'schema_version':1,'decision':'accepted-exact-one-use-financial-parent','contract_sha256':sha(encoded({k:v for k,v in q.items() if k!='final_review'})),'proof_sha256':proofpins,'identity':q['identity'],'source':q['source'],'caller_sha256':q['caller_sha256']}
    require(review==expected,'exact independently reviewed final Parent contract required')
    parent=Path(q['parent_root']);require(parent.is_absolute() and parent.resolve(strict=True)==parent and not parent.is_relative_to(ad.root) and not ad.root.is_relative_to(parent),'canonical external Parent scope required')
    require(sha(reader.read(parent/'parent01.py'))==q['caller_sha256'],'actual caller bytes differ')
    require(type(q['helper_hashes']) is dict and q['helper_hashes'].get(Path(__file__).name)==sha(reader.read(Path(__file__).resolve())) and Path(__file__).resolve()==parent/Path(__file__).name,'this actual external preclaim helper must be pinned by final Parent')
    for name,pin in q['helper_hashes'].items():
        require(Path(name).name==name and digest(pin) and sha(reader.read(parent/name))==pin,'actual Parent helper closure differs')
    # The caller supplies the exact trusted refs; bind their full literal map in
    # the separately source-pinned Parent metadata proof, not a Boolean flag.
    metadata=json.loads(reader.reference(q['proofs']['independent_source_input_runtime']))
    require(metadata.get('compatibility_preclaim_external_refs')=={k:v for k,v in refs.items() if k not in ('final_parent_contract','final_parent_review')},'Root metadata proof must authenticate exact external review/recovery references')
    return q

def _provenance(inputs,plan,source,installed,fixture):
    return {'source_hashes':sorted(set(installed.values())),'config_hash':sha(canonical({'model':inputs.json(plan['model_input']),'training':inputs.json(plan['training_input']),'task':plan['task'],'recipe':fixture.RECIPE})),'input_hash':sha(inputs.raw(plan['recipe_input'])),'dictionary_hash':sha(b'synthetic opaque MCM; no empirical dictionary fitted or recovered'),'fold_id':'synthetic-16x28-distinct','cell_id':plan['cell_id'],'source_commit':source}

def _claim(inputs,descriptor,root,identity,status,verify,reader):
    directory=root/'research_runs'/identity
    claim=inputs.exact(descriptor['claim_input'],directory/'claim.json')
    terminal=inputs.exact(descriptor['terminal_input'],directory/(status+'.json'))
    require(not os.path.lexists(directory/('failed.json' if status=='complete' else 'complete.json')),'opposite historical terminal present')
    require(claim['experiment_id']==identity and terminal['experiment_id']==identity and terminal['status']==status and terminal['claim_sha256']==sha(inputs.raw(descriptor['claim_input'])),'actual claim/terminal identity/hash join differs')
    reader.tick();genuine=verify.verify_claim(directory);reader.tick()
    require(genuine==claim,'original committed claim verification differs')
    return claim

def _checkpoint(inputs,role,provenance,fit,reader):
    path=inputs.path(role);require(path.is_relative_to(fit/'checkpoints'),'checkpoint is outside exact fit ancestry')
    manifest=inputs.json(role);require(manifest.get('provenance')==provenance and type(manifest.get('members')) is dict and set(manifest['members'])=={'state.pt'},'checkpoint exact provenance/member denominator differs')
    for name,item in manifest['members'].items():
        require(type(item) is dict and set(item)=={'size','sha256'} and type(item['size']) is int and 0<item['size']<=FILE and digest(item['sha256']),'opaque checkpoint member fields')
        member=path.parent/name;rel=member.relative_to(inputs.root).as_posix();roles=[r for r,v in inputs.registered.items() if v['path']==rel and v['sha256']==item['sha256']]
        require(roles,'every opaque checkpoint body must be registered before claim')
        for r in roles: require(len(inputs.raw(r))==item['size'],'opaque checkpoint member extent differs')
    return path,manifest

def _complete(inputs,descriptor,policy,phase,provenance,root,helper,verify,reader):
    consumer=policy['consumers'][phase];identity=consumer['experiment'];claim=_claim(inputs,descriptor,root,identity,'complete',verify,reader)
    require(claim['inputs'].get(ROLE,{}).get('sha256')==POLICY_SHA and claim['inputs'].get(policy['target']['closure_input'],{}).get('sha256')==sha(inputs.raw(policy['target']['closure_input'])),'completed dependency policy/closure differs')
    require(claim['experiment']['cells']==[consumer['cell_id']] and all(claim['experiment']['source_files'].get(p)==h for p,h in policy['target']['installed'].items()),'completed dependency fixed cell/195 source map differs')
    old=descriptor['provenance'];exclude={'source_commit','cell_id'} if phase=='complete100' else {'source_commit'}
    require({k:v for k,v in old.items() if k not in exclude}=={k:v for k,v in provenance.items() if k not in exclude} and old['source_commit']==claim['source'] and old['cell_id']==consumer['cell_id'],'completed dependency strict scientific/source provenance differs')
    fit=root/'research_artifacts/onchain_fit_cells'/sha(consumer['cell_id'].encode())/identity
    path,manifest=_checkpoint(inputs,descriptor['checkpoint_input'],old,fit,reader)
    completion=inputs.exact(descriptor['completion_input'],fit/'complete.json')
    require(not os.path.lexists(fit/'failed.json') and set(completion)=={'checkpoint','sha256','epochs'} and type(completion['epochs']) is int and completion['epochs']==100 and completion['checkpoint']==str(path) and completion['sha256']==sha(inputs.raw(descriptor['checkpoint_input'])),'actual COMPLETE100 fit/checkpoint join unavailable')
    if phase=='continue100':helper.validate_prediction_parent(policy,POLICY_SHA,sha(inputs.raw(policy['target']['closure_input'])),identity,claim['inputs'],claim['experiment']['source_files'],claim['experiment']['cells'])
    return claim

def _historical(inputs,prior,policy,plan,provenance,root,helper,fixture,verify,reader):
    hist=policy['historical'];identity=hist['identity'];claim=_claim(inputs,prior,root,identity,'failed',verify,reader)
    for descriptor,key in (('claim_input','claim_input'),('terminal_input','failed_input'),('checkpoint_input','checkpoint_input'),('parent_job_input','job_input'),('parent_plan_input','plan_input')):
        require(prior[descriptor]==hist[key],'exact historical alias linkage differs')
    require(prior['completion_input'] is None and prior['parent']==identity and prior['provenance']==hist['provenance'],'original interruption descriptor differs')
    require(sha(inputs.raw(hist['claim_input']))==hist['claim_sha256'] and sha(inputs.raw(hist['failed_input']))==hist['failed_sha256'] and sha(inputs.raw(hist['checkpoint_input']))==hist['checkpoint_sha256'],'original historical body pin differs')
    old=hist['provenance'];helper.validate_relation(hist['installed'],policy['target']['installed'],old,provenance)
    require(claim['source']==claim['design_source']==hist['source'] and claim['program_id']==helper.PROGRAM and claim['experiment']['family']==helper.FAMILY and claim['experiment']['charter']['sha256']==hist['protocol_sha256'] and all(claim['experiment']['source_files'].get(p)==h for p,h in hist['installed'].items()),'original source/program/protocol/map differs')
    oldjob=inputs.json(hist['job_input']);fixture.schema(oldjob);oldplan=inputs.json(hist['plan_input']);fixture.validate_plan(oldplan)
    require(sha(inputs.raw(hist['job_input']))==claim['inputs']['execution_job']['sha256'] and sha(inputs.raw(hist['plan_input']))==claim['inputs'][oldjob['payload']['plan_input']]['sha256'],'old claim-selected job/plan differs')
    require(oldplan['experiment']==identity and oldplan['phase']=='interrupt1' and all(oldplan[k]==plan[k] for k in ('cell_id','task','execution')) and claim['experiment']['cells']==[plan['cell_id']],'original interrupt method/cell differs')
    for key,pin in (('model_input',fixture.MODEL),('training_input',fixture.TRAINING),('recipe_input',old['input_hash'])):require(claim['inputs'][oldplan[key]]['sha256']==pin,'original scientific configuration differs')
    oldclosure=inputs.json(hist['closure_input']);require(oldclosure['installed']==hist['installed'] and sha(inputs.raw(hist['closure_input']))==claim['inputs'][oldplan['closure_input']]['sha256'],'old exact path-complete closure differs')
    fit=root/'research_artifacts/onchain_fit_cells'/sha(plan['cell_id'].encode())/identity
    path,manifest=_checkpoint(inputs,hist['checkpoint_input'],old,fit,reader)
    require(manifest['members']=={'state.pt':{'size':493424,'sha256':helper.HISTORICAL_STATE_SHA256}} and not os.path.lexists(fit/'complete.json'),'original opaque state/member/failed fit differs')
    require(inputs.exact(prior['fit_claim_input'],fit/'claim.json')=={'experiment_id':identity,'provenance':old,'parent_checkpoint':None},'original fit claim differs')
    require(inputs.exact(prior['failed_fit_input'],fit/'failed.json')=={'type':'PlannedInterruption','reason':'prospective engineering failed-parent fixture after one real update; no fit completion','last_checkpoint':str(path)},'original planned interruption differs')
    diagnostic=root/'research_artifacts/financial_wrapper_engineering'/oldplan['namespace']/'interrupted-checkpoint.json'
    require(inputs.exact(prior['diagnostic_input'],diagnostic)=={'checkpoint':str(path),'sha256':hist['checkpoint_sha256'],'provenance':old,'epochs_completed':1,'requires_genuine_failed_parent':True},'original interruption diagnostic differs')
    require(inputs.exact(prior['schedule_input'],fit/'schedule.json')=={'training':inputs.json(plan['training_input']),'seed':11,'task':plan['task'],'n_examples':16},'original schedule differs')
    require(sorted(p.name for p in fit.parent.iterdir())==[identity],'original continued cell gained another attempt')

def validate_preclaim(admission,job,plan,release_refs):
    """Validate existing genuine Admission; return evidence only, never authority.

    Original Parent source/Git/runtime/native/full-recovery checks remain required.
    No fake Admission, alternative binding, role omission or missing outcome may
    bypass these checks. This must be called immediately before Run.start.
    """
    admission_module=importlib.import_module('tradingagents.research.admission')
    require(type(admission) is admission_module.Admission,'original genuine Admission required')
    ad=admission;root=ad.root;reader=Reader()
    require(type(root) is Path or isinstance(root,Path),'canonical admitted root required')
    require(root.is_absolute() and root.resolve(strict=True)==root and ad.ready is True and ad.source==ad.design_source and ad.bindings is None and ad.bindings_sha256 is None,'genuine ready same-source unbound Admission required')
    inputs=Inputs(root,ad.inputs,reader)
    require(reader.read(root/relative(ad.registration)) and sha(reader.read(root/relative(ad.registration)))==ad.registration_sha256,'current admission registration differs')
    registration=json.loads(reader.read(root/ad.registration));require(registration==ad.spec and registration['experiments'][ad.experiment_id]==ad.experiment and registration['families'][ad.experiment['family']]==ad.family and ad.inputs==ad.experiment['inputs'],'admitted complete registration fields differ')
    helper=importlib.import_module('tradingagents.research.onchain_replication.operational_source_compatibility')
    fixture=importlib.import_module('tradingagents.research.onchain_replication.financial_wrapper_fixture')
    verify=importlib.import_module('tradingagents.research.verify')
    policy=inputs.json(ROLE);require(sha(inputs.raw(ROLE))==POLICY_SHA,'exact concrete reviewed policy required')
    _roles(ad.inputs,plan.get('phase'));require(policy['consumers']==FIXED,'fixed three consumer policy required')
    require(sha(reader.read(root/HELPER))==HELPER_SHA,'exact accepted installed compatibility helper required')
    helper.validate_contract(policy,HELPER_SHA)
    for module,rel in ((admission_module,'tradingagents/research/admission.py'),(helper,HELPER),(fixture,PREFIX+'financial_wrapper_fixture.py'),(verify,'tradingagents/research/verify.py')):
        require(Path(module.__file__).resolve()==root/rel,'original imported module origin differs')
    for rel,pin in policy['target']['installed'].items():
        require(ad.experiment['source_files'].get(rel)==pin and sha(reader.read(root/relative(rel)))==pin,'actual full195 registered target source differs')
    for role in (ROLE,REVIEW_ROLE,RECOVERY_ROLE):require(ad.experiment['source_files'].get(ad.inputs[role]['path'])==ad.inputs[role]['sha256'],'policy/proofs must be committed source-pinned inputs')
    require(job==inputs.json('execution_job') and plan==inputs.json(job['payload']['plan_input']),'exact registered current job/plan bytes required')
    fixture.schema(job);fixture.validate_plan(plan)
    require(job['payload']['plan_input']=='wrapper_plan' and job['environment_input']=='environment' and all(plan[k]==v for k,v in {'model_input':'model','training_input':'training','recipe_input':'synthetic_recipe','runtime_input':'runtime_mapping','closure_input':'source_closure'}.items()),'fixed base role mapping differs')
    require(plan['phase'] in FIXED and FIXED[plan['phase']]=={'experiment':ad.experiment_id,'cell_id':plan['cell_id']} and plan['experiment']==plan['namespace']==ad.experiment_id and plan['task']=='classification' and plan['execution']=='eager','exact fixed consumer/method required')
    expected_parent={'complete100':None,'continue100':policy['historical']['identity'],'predict':FIXED['continue100']['experiment']}[plan['phase']]
    require(ad.experiment['parent']==expected_parent and ad.experiment['cells']==[plan['cell_id']] and set(ad.experiment['outputs'])==fixture.OUTPUTS and ad.spec['program_id']==helper.PROGRAM and ad.experiment['family']==helper.FAMILY,'fixed source-edge consumer topology/cell/program differs')
    require(job['resources']['disk_paths']==[str(root)] and job['resources']['storage_budget']['root']==str(root),'original whole-root resource policy differs')
    require(sha(inputs.raw('model'))==fixture.MODEL and sha(inputs.raw('training'))==fixture.TRAINING and inputs.json('synthetic_recipe')==fixture.RECIPE,'original scientific input bytes/seed/recipe differs')
    inputs.raw('environment');runtime=inputs.json('runtime_mapping')
    require(runtime['python']=='3.13.13' and runtime['executable']==sys.executable and runtime['prefix']==sys.prefix,'original Parent-verified runtime identity differs')
    closure=inputs.json('source_closure')
    require(set(closure)=={'schema_version','installed','scientific_model','scientific_training','candidate02'} and closure['schema_version']==1 and closure['installed']==policy['target']['installed'] and closure['scientific_model']==fixture.MODEL and closure['scientific_training']==fixture.TRAINING and closure['candidate02']==fixture.CANDIDATE,'exact full source/scientific closure differs')
    _parent_release(ad,plan,inputs,release_refs,reader)
    _proof_bundle('review',release_refs,inputs,policy,reader)
    _proof_bundle('recovery',release_refs,inputs,policy,reader)
    for path in (root/'research_runs'/ad.experiment_id,root/'research_artifacts/financial_wrapper_engineering'/plan['namespace'],root/'research_artifacts/onchain_fit_cells'/sha(plan['cell_id'].encode())/ad.experiment_id):require(not os.path.lexists(path),'prospective consumer namespace already exists')
    provenance=_provenance(inputs,plan,ad.source,policy['target']['installed'],fixture)
    if plan['phase']=='complete100':
        require(not os.path.lexists(root/'research_artifacts/onchain_fit_cells'/sha(plan['cell_id'].encode())),'reference fit cell already used')
    else:
        prior=inputs.json(plan['prior_input']);fields={'parent','claim_input','terminal_input','checkpoint_input','completion_input','provenance'}
        if plan['phase']=='continue100':fields|={'parent_job_input','parent_plan_input','fit_claim_input','failed_fit_input','diagnostic_input','schedule_input'}
        require(type(prior) is dict and set(prior)==fields and prior['parent']==expected_parent,'exact authentic prior descriptor required')
        if plan['phase']=='continue100':
            _historical(inputs,prior,policy,plan,provenance,root,helper,fixture,verify,reader)
            reference=inputs.json(plan['reference_input'])
            require(type(reference) is dict and set(reference)=={'checkpoint_input','provenance','completion_input','claim_input','terminal_input'},'actual complete reference descriptor required')
            _complete(inputs,reference,policy,'complete100',provenance,root,helper,verify,reader)
        else:_complete(inputs,prior,policy,'continue100',provenance,root,helper,verify,reader)
    require(inputs.used==set(ad.inputs),'unconsumed registered role denominator differs')
    reader.finish()
    return {'schema_version':1,'status':'PRECLAIM_METADATA_VALIDATED_NO_CLAIM','source':ad.source,'experiment':ad.experiment_id,'phase':plan['phase'],'policy_sha256':POLICY_SHA,'input_hashes':{r:sha(v) for r,v in inputs.bodies.items()},'metadata_bytes_read':reader.total,'checkpoint_decoded':False,'qualification':'sampled metadata only; no Run/Admission creation, numerical/native release, full recovery or writer exclusion'}
