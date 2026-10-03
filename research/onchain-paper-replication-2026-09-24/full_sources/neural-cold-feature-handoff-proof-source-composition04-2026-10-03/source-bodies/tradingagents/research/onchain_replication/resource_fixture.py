"""Finite genuine original-import engineering route; never financial completion."""
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
from .owned_io import _fatal

GIB=1024**3
FILE_MAX=4*1024**2
PROGRAM='original-dictionary-import-engineering-2026-10-02'
MECHANISM='original-dictionary-import-engineering-v1'
CELLS=['import-target-01','import-target-02']
_COMPLETION_SEAL=object()
ORIGINAL='48832eeb9774ef6ca13915364c17d1ac89f5c67165636de5811ebf82ad6ad726'
KEYS={'operation','plan_input','producer','pair_checkpoint_input','descriptor','original_dictionary_input','compact_policy_input','native_backend','original_dictionary_stage_input','compact_mcm_input','compact_mcm_output_input'}

def require(value,message):
    if not value:raise ValueError(message)

def selection(job):
    jobs=job['payload']['representation_jobs']
    require(type(jobs) is dict and len(jobs)==1,'exactly one finite representation required')
    name=next(iter(jobs));s=jobs[name]
    require(type(name) is str and name and type(s) is dict and set(s)==KEYS,'fixture selected fields differ')
    require(s['operation']=='produce' and all(type(s[k]) is str and s[k] for k in KEYS-{'operation','descriptor'}),'explicit selected producer inputs required')
    d=s['descriptor'];require(type(d) is dict and d.get('arm')=='proposed' and d.get('dictionary_origin')=='imported-original-v1','imported proposed descriptor required')
    graphs=d.get('required_graphs');require(type(graphs) is list and len(graphs)==2 and graphs==sorted(set(graphs)) and all(type(h) is str and len(h)==64 and all(c in '0123456789abcdef' for c in h) for h in graphs),'exact two distinct sorted targets required')
    mapping=d.get('resource_graph_inputs');require(type(mapping) is dict and set(mapping)==set(graphs) and len(set(mapping.values()))==2 and all(type(v) is str and v for v in mapping.values()),'complete distinct target mapping required')
    f=d.get('resource_fixture');require(type(f) is dict and set(f)=={'schema_version','case','data_kind','target_nodes','target_provenance_input'} and type(f['schema_version']) is int and f['schema_version']==1,'finite fixture policy fields differ')
    require(f['case'] in ('success','second_target_publication_failure') and f['data_kind']=='synthetic-targets-original-dictionary','explicit synthetic case required')
    require(type(f['target_nodes']) is dict and set(f['target_nodes'])==set(graphs) and all(type(n) is int and 1<=n<=4 for n in f['target_nodes'].values()),'tiny exact node denominator required')
    require(type(f['target_provenance_input']) is str and f['target_provenance_input'],'synthetic provenance input required')
    return name,s,f

def schema(job):
    require(type(job) is dict and set(job)=={'schema_version','kind','resources','environment_input','payload'} and type(job['schema_version']) is int and job['schema_version']==1 and job['kind']=='compact_resource','explicit compact resource schema required')
    require(type(job['payload']) is dict and set(job['payload'])=={'representation_jobs'} and type(job['environment_input']) is str and job['environment_input'],'finite registered payload required')
    selection(job);p=job['resources']
    require(type(p) is dict and 'physical_policy' not in p and 'storage_budget' in p,'whole-workspace sampled storage guard required; neural scope forbidden')
    require(type(p.get('wall_seconds')) is int and 0<p['wall_seconds']<=1800 and type(p.get('memory_max_bytes')) is int and 0<p['memory_max_bytes']<=3*GIB,'finite engineering unit envelope required')
    require(p.get('native_unit_limits')=={'file_size_bytes':FILE_MAX} and type(p['native_unit_limits']['file_size_bytes']) is int,'registered native file cap required')
    budget=p['storage_budget'];limits=budget['limits']
    require(type(budget) is dict and set(budget)=={'root','limits'} and type(limits) is dict and set(limits)=={'max_allocated_bytes','max_logical_bytes','max_entries','max_depth','max_scan_seconds'},'sampled budget schema differs')
    require(all(type(v) is int and v>0 for v in limits.values()) and limits['max_allocated_bytes']<=GIB and limits['max_logical_bytes']<=GIB and limits['max_entries']<=32768 and limits['max_depth']<=32 and limits['max_scan_seconds']<=5,'finite whole-tree inventory ceiling differs')

def _engineering_parent(ad):
    """Retain legacy roots and admit only the exact reviewed finite successor."""
    identities={'original-import-native-success-20261003-02','original-import-native-publication-failure-20261003-02'}
    parent='original-import-native-success-20261003-01'
    if ad.experiment_id not in identities:return ad.experiment.get('parent') is None
    require(ad.experiment.get('parent')==parent and ad.effective_attempt_budget==3,
        'exact reviewed engineering successor parent/ceiling required')
    reference={'extension':{'path':'fixture_budget/cumulative-extension01.json','sha256':'3723a4030d581d8dbd9326e004bc6b42d60f4315af23832f0edc04b1e9d8834a'},
        'review':{'path':'fixture_budget/cumulative-extension-review01.json','sha256':'6f9a01a049c21e998f00da30c137bbc7709083a1c15aece741de54e6e8aa357d'}}
    require(ad.experiment.get('cumulative_budget_extension')==reference,
        'exact reviewed engineering successor extension required')
    for value in reference.values():
        path=ad.root/value['path'];info=path.lstat()
        require(path.resolve()==path and path.is_file() and info.st_nlink==1 and info.st_size<=4*1024**2
            and ad.experiment['source_files'].get(value['path'])==value['sha256']
            and hashlib.sha256(path.read_bytes()).hexdigest()==value['sha256'],
            'engineering successor extension body differs')
    from ..verify import verify_claim
    directory=ad.root/'research_runs'/parent;claim=verify_claim(directory)
    claim_raw=(directory/'claim.json').read_bytes();terminal_raw=(directory/'failed.json').read_bytes()
    require(hashlib.sha256(claim_raw).hexdigest()=='f475dd6c04d7dfc5e9d94bba30b5d3e686d1b71b5f5394dfa1aa0b174797f61e'
        and hashlib.sha256(terminal_raw).hexdigest()=='09206641f5ce569716bbf61246ecc85c20daa3ed40bf7f82427e4772198881c0'
        and claim['program_id']==PROGRAM and claim['family']==ad.family
        and claim['experiment']==ad.spec['experiments'][parent] and not (directory/'complete.json').exists(),
        'genuine closed engineering predecessor differs')
    terminal=json.loads(terminal_raw)
    require(terminal['experiment_id']==parent and terminal['status']=='failed'
        and terminal['claim_sha256']==hashlib.sha256(claim_raw).hexdigest()
        and terminal['reason']=='ValueError: compact metadata bound'
        and set(terminal['output_sha256'])=={'resource-binding.json','resource-journal.json','cell-ledger.json','resource-summary.json'},
        'engineering predecessor failed disposition differs')
    for name,pin in terminal['output_sha256'].items():
        path=directory/'outputs'/name;info=path.lstat()
        require(path.resolve()==path and path.is_file() and info.st_nlink==1 and info.st_size<=4*1024**2
            and hashlib.sha256(path.read_bytes()).hexdigest()==pin,'engineering predecessor failed output differs')
    return True

def admitted(ad,job):
    schema(job)
    require(ad.spec['program_id']==PROGRAM and ad.family['mechanism_id']==MECHANISM,'separate synthetic engineering program/family required')
    require(ad.experiment['cells']==CELLS and _engineering_parent(ad),'fresh exact engineering denominator required')
    require(Path(job['resources']['storage_budget']['root'])==ad.root,'storage watch must include complete isolated checkout, baseline and every output namespace')
    require((ad.root/'.git').is_dir() and (ad.root/'.git').resolve()==ad.root/'.git','independent local Git directory inside watched root required')

def worker_limits():
    # Applies to this worker and descendants, not a claim about systemd manager defaults.
    resource.setrlimit(resource.RLIMIT_FSIZE,(FILE_MAX,FILE_MAX))
    require(resource.getrlimit(resource.RLIMIT_FSIZE)==(FILE_MAX,FILE_MAX),'worker file limit not enforced')
    return {'rlimit_fsize':FILE_MAX,'scope':'worker and inherited descendants; outer launcher/log limits separately required'}

def original_source_blobs(run,control):
    from . import original_dictionary as original
    claim=original.parse(original._read_registered(run,control['refs']['claim']['input']))
    files=claim['experiment']['source_files'];commit=control['original_source']
    require(commit=='c6b568d4b1c177ab94ac37fbad462c2decc721c0' and claim['source']==commit and type(files) is dict and len(files)==26,'original26-source claim required')
    rows=[];total=0;env={**os.environ,'GIT_NO_LAZY_FETCH':'1'}
    for name,sha in sorted(files.items()):
        require(type(name) is str and not Path(name).is_absolute() and '..' not in Path(name).parts and '\n' not in name,'original source path differs')
        ref=commit+':'+name
        size=int(subprocess.check_output(['git','cat-file','-s',ref],cwd=run.admission.root,env=env,timeout=10).strip())
        total+=size;require(0<size<=2*1024**2 and total<=4*1024**2,'original source extent ceiling')
        raw=subprocess.check_output(['git','cat-file','blob',ref],cwd=run.admission.root,env=env,timeout=10)
        require(len(raw)==size and hashlib.sha256(raw).hexdigest()==sha,'original committed source body differs')
        rows.append({'path':name,'sha256':sha,'bytes':size})
    return rows

def preflight(run,job):
    from . import original_dictionary as original,compact_policy,compact_owner
    from .provenance import canonical_bytes
    admitted(run.admission,job);name,s,f=selection(job)
    plan=original.parse(original._read_registered(run,s['plan_input']))
    require(type(plan.get('schema_version')) is int and plan['schema_version']==2 and s['producer'] in plan['producers'],'version2 producer plan required')
    item=plan['producers'][s['producer']]
    require(all(item.get(k)==v for k,v in s.items()),'selected producer plan/job differ')
    outputs={item.get('binding_output'),item.get('journal_output'),'cell-ledger.json','resource-summary.json'}
    require(len(outputs)==4 and None not in outputs and outputs==set(run.admission.experiment['outputs']),'exact resource-only outputs required')
    control=original.parse(original._read_registered(run,s['original_dictionary_input']));original.policy_check(control)
    require(control['motif_count']==32 and control['sample_count']==512 and control['dictionary_identity']==ORIGINAL,'all original32/512 evidence required; no fresh sampling')
    source_rows=original_source_blobs(run,control)
    provenance=original.parse(original._read_registered(run,f['target_provenance_input']))
    require(provenance=={'schema_version':1,'kind':'synthetic-original-import-targets','generator':'registered-explicit-arrays-v1','node_denominators':sorted(f['target_nodes'].values())},'synthetic target provenance differs')
    graphs=[]
    # Every manifest/member capacity is validated before any array loader or journal birth.
    for key in s['descriptor']['required_graphs']:
        inp=s['descriptor']['resource_graph_inputs'][key];info=run.admission.inputs[inp]
        manifest=original.parse(original._read_registered(run,inp));arrays=manifest['arrays']
        require(manifest['graph_hash']==key and manifest['metadata']['source_hashes']==[run.admission.inputs[f['target_provenance_input']]['sha256']],'target source/hash differs')
        require(set(arrays) in ({'node_ids','node_features','edge_index','edge_features'},{'node_ids','node_features','edge_index','edge_features','edge_aggregates'}),'target array membership differs')
        require(all(type(v['bytes']) is int and 0<v['bytes']<=65536 and v['path']==k+'.npy' for k,v in arrays.items()),'tiny target member extent differs')
        graphs.append((key,run.admission.root/info['path'],info['sha256']))
    envelope=original.parse(original._read_registered(run,s['compact_policy_input']))
    import_policy=original.parse(original._read_registered(run,s['original_dictionary_stage_input']))
    from .resource_binding import import_policy as validate_import
    validate_import(import_policy)
    pairs=[32*f['target_nodes'][k] for k,_,_ in graphs]
    require('restart_retention' not in envelope['stage_policy'] and 'archive_transport' not in s['descriptor'],'tiny local route excludes unproved archive/retention')
    reservations=[compact_policy.validate(envelope['stage_policy'],kind='mcm',pairs=n)['logical_reservation_bytes']+compact_owner.STAGE_BYTES for n in pairs]
    require(envelope['max_workflow_retained_logical_bytes']>=compact_owner.OWNER_BYTES+import_policy['max_stage_bytes']+sum(reservations),'both target pair reservations required before owner birth')
    require(envelope['stage_policy']['pair']['max_checkpoint_bytes']+65536<=FILE_MAX,'pair checkpoint excludes inherited per-file headroom')
    return name,s,f,item,graphs,source_rows

class FixturePublicationFailure(ValueError):pass

def publication_boundary(owner,stage):
    if owner.bound.record.get('resource_only') is not True:return
    run=owner.bound._run;job=json.loads(run.read_input(owner.bound.record['job_input']));schema(job)
    _,s,f=selection(job)
    if f['case']=='second_target_publication_failure' and stage.name=='mcm-'+s['descriptor']['required_graphs'][1]:
        raise FixturePublicationFailure('registered second-target publication boundary; retain first output; no retry')


def verify_retained(item,owner):
    from . import compact_mcm,compact_mcm_publication as publication
    from .provenance import thaw
    require(type(item) is compact_mcm.Produced and item._stage.owner is owner,'actual same-owner target required')
    item._integrity();item._numeric();item._evidence()
    record=thaw(item.record);ticket=record['output']
    publication._verify(Path(ticket['directory']),record['output_args']|{'stage_root':item._stage.root},record['output_proof'],lambda:None,ticket['receipt_sha256'])
    return {'graph_hash':record['graph_hash'],'rows':record['rows'],'motifs':record['motifs'],'cells':record['completed_cells'],'matrix_sha256':record['matrix_sha256'],'scope':record['scope'],'producer_receipt_sha256':item.receipt_sha256,'output':ticket}

class _Completion:
    __slots__=('journal','owner','targets','reference','records','binding')
    def __init__(self,journal,owner,targets,reference,records,binding,*,_seal):
        require(_seal is _COMPLETION_SEAL,'private actual completion capture required')
        for k,v in locals().copy().items():
            if k not in ('self','_seal'):object.__setattr__(self,k,v)
    def __setattr__(self,k,v):raise AttributeError('resource completion capture is immutable')

def complete_journal(journal,proof):
    from . import compact_owner,import_metadata
    from .provenance import canonical_bytes,thaw
    require(type(proof) is _Completion and proof.journal is journal and type(proof.owner) is compact_owner.Owner,'actual captured resource completion required')
    owner=proof.owner;bound=owner.bound;run=bound._run
    require(owner.closed and not owner.poisoned and owner.root==journal.directory/'compact' and not journal.sealed,'closed original owner required')
    bound.check();journal._resource_check()
    require(canonical_bytes(thaw(bound.record))==proof.binding,'resource completion Binding changed')
    from . import resource_binding
    resource_binding.assert_selected(bound,'execution_job')
    job=json.loads(run.read_input('execution_job'));schema(job);_,selected,fixture=selection(job)
    require(tuple(owner.required)==tuple(['dictionary-import']+['mcm-'+k for k in selected['descriptor']['required_graphs']]),'exact resource owner stages differ')
    raw=import_metadata.read(owner.root,'complete.json');terminal=json.loads(raw)
    require(hashlib.sha256(raw).hexdigest()==proof.reference and terminal['owner']==owner.identity and terminal['stages']==3 and terminal['pairs']==sum(r['cells'] for r in proof.records),'owner terminal denominator differs')
    records=tuple(verify_retained(x,owner) for x in proof.targets)
    require(records==proof.records and len(records)==2 and all(x['motifs']==32 for x in records),'resource original target artifacts changed')
    validate_records(records,selected['descriptor']['required_graphs'],fixture['target_nodes'])
    value={'schema_version':2,'kind':'original-import-resource-terminal','status':'complete','resource_only':True,'financial_representation_admitted':False,'owner':journal.owner,'compact_owner_sha256':proof.reference,'original_dictionary':ORIGINAL,'targets':list(records),'cells':CELLS}
    # Existing complete.json terminal name revokes Binding; content is not scientific.
    journal._publish(journal.directory/'complete.json',value)
    journal._resource_check();import_metadata.exact(owner.root,'complete.json',raw)
    require(tuple(verify_retained(x,owner) for x in proof.targets)==records,'target changed during resource closure')
    run._active();bound._guard();object.__setattr__(journal,'sealed',True)
    return value


def failure_rows(completed,error):
    first=len(completed)
    require(0<=first<=2,'invalid completed denominator')
    return [{'id':CELLS[index],'status':'failed' if index==first else 'unavailable','reason':type(error).__name__+': '+str(error)[:1024],'resource_only':True} for index in range(first,2)]

def validate_records(records,graphs,counts):
    require(len(records)==2 and [r['graph_hash'] for r in records]==list(graphs),'exact ordered distinct target completion required')
    require(all(type(r['rows']) is int and r['rows']==counts[k] and type(r['motifs']) is int and r['motifs']==32 and type(r['cells']) is int and r['cells']==32*counts[k] for k,r in zip(graphs,records,strict=True)),'exact original32 target denominator required')

def retained_actions(primary,actions,reducer):
    if primary is None:
        reducer(actions);return
    try:raise primary
    except BaseException:
        reducer(actions)
        if isinstance(primary,MemoryError) or not isinstance(primary,Exception):raise


def _preserve_terminal(primary,later):
    """Assembly cannot replace the first actual fatal or fabricate success."""
    if primary is None:return later
    selected=primary
    if not _fatal(primary) and (_fatal(later) or (isinstance(primary,Exception) and not isinstance(later,Exception))):
        selected=later
        if _fatal(later):
            # Optional cause evidence may fail only after an actual fatal has
            # already been selected. Synthetic uncertainty does not run it.
            try:
                if later.__cause__ is None:later.__cause__=primary
                elif later.__cause__ is not primary:later.__cause__=BaseExceptionGroup('prior terminal failure and original cause',[primary,later.__cause__])
            except BaseException:pass
    return selected


def execute(run,payload,*,job_input='execution_job'):
    from . import resource_binding,original_import_preparation,original_import_stage,compact_mcm,compact_owner,import_metadata
    from .imported_mcm_identity import Target
    from .graph_store import load_graph
    from .mcm import mcm_features
    from .provenance import canonical_bytes,thaw,durable_mkdir
    from .workflow_storage import StorageWatch
    import numpy as np
    require(job_input=='execution_job','fixture uses exact guarded worker job input')
    job=json.loads(run.read_input(job_input));require(job['payload']==payload,'registered fixture payload differs')
    name,s,f,item,inputs,source_rows=preflight(run,job)
    watch=StorageWatch(run.admission.root,job['resources']['storage_budget']['limits']);watch.check()
    graphs=[load_graph(path,sha,resident=True) for _,path,sha in inputs]
    require(all(len(g.node_ids)==f['target_nodes'][key] and g.edge_index.shape[1]<=12 and g.node_features.shape[1]==4 and g.edge_features.shape[1]==2 for g,(key,_,_) in zip(graphs,inputs,strict=True)),'actual tiny target dimensions differ')
    ledger=run.admission.root/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/run.admission.experiment_id
    durable_mkdir(ledger.parent);import_metadata.birth(ledger)
    journal=owner=None;targets=[];rows=[];primary=None
    pending=[];terminal=summary=None
    # Construct the finite independent actions before any primary failure exists.
    def missing():
        nonlocal pending
        pending=failure_rows(rows,primary);rows.extend(pending)
    def disposition(index):
        if index<len(pending):
            row=pending[index];import_metadata.write(ledger,row['id']+'.json',canonical_bytes(row))
    def failed_seal():
        if journal is not None and not journal.sealed:
            journal.seal('failed',reason=type(primary).__name__+': '+str(primary)[:1024])
    def retained(index):
        if index<len(targets):verify_retained(targets[index],owner)
    def failed_terminal():
        nonlocal terminal
        terminal={'schema_version':2,'kind':'original-import-resource-terminal','status':'failed','resource_only':True,'financial_representation_admitted':False,'reason':type(primary).__name__+': '+str(primary)[:1024]}
    def assemble_summary():
        nonlocal summary
        summary={'schema_version':1,'resource_only':True,'financial_representation_admitted':False,'case':f['case'],'original_source_blobs':source_rows,'original_dictionary':ORIGINAL,'original_motifs':32,'cells':rows,'file_limit':resource.getrlimit(resource.RLIMIT_FSIZE),'final_outer_inventory_required':True}
    def observation():
        require(summary is not None,'summary assembly failed')
        summary['storage_observation']=watch.check()
    def publish_terminal(name):
        require(terminal is not None,'resource terminal assembly failed')
        run.write_json(name,terminal)
    def publish_summary():
        require(summary is not None,'resource summary assembly failed')
        run.write_json('resource-summary.json',summary)
    failure_actions=(missing,lambda:disposition(0),lambda:disposition(1),failed_seal,lambda:retained(0),lambda:retained(1),failed_terminal)
    output_actions=(assemble_summary,observation,lambda:publish_terminal(item['binding_output']),lambda:publish_terminal(item['journal_output']),lambda:run.write_json('cell-ledger.json',rows),publish_summary)
    try:
        journal,bound=resource_binding.open_first(run,representation=name,plan_input=s['plan_input'],producer=s['producer'],policy_input=s['pair_checkpoint_input'],job_input=job_input)
        prepared=original_import_preparation.prepare(bound,input_name=s['original_dictionary_input'],job_input=job_input)
        owner,stage=original_import_stage.attach(prepared,policy_input=s['compact_policy_input'],stage_policy_input=s['original_dictionary_stage_input'])
        execution=original_import_stage.ImportedExecution(stage)
        require(len(execution._materialized._dictionary.representatives)==32,'all original motifs required')
        # Both actual target policies, source/kernel identities and cumulative outputs before first MCM stage.
        checked=[Target(execution,g,key) for g,(key,_,_) in zip(graphs,inputs,strict=True)]
        for target in checked:compact_mcm._prepare(target,target.key,s['compact_mcm_input'],s['compact_mcm_output_input'])
        for index,(g,(key,_,_)) in enumerate(zip(graphs,inputs,strict=True)):
            watch.check();result=compact_mcm.produce_imported(execution,g,graph_hash=key,input_name=s['compact_mcm_input'],output_input=s['compact_mcm_output_input'])
            result.check();reference=mcm_features(g,execution._materialized._dictionary,thaw(owner.matching),reference=True)
            require(np.isfinite(reference).all() and np.allclose(result.matrix,reference,atol=1e-5,rtol=1e-4),'independent float64 reference MCM differs')
            records=verify_retained(result,owner);targets.append(result)
            row={'id':CELLS[index],'status':'complete','resource_only':True,'target':records,'reference_atol':1e-5,'reference_rtol':1e-4}
            import_metadata.write(ledger,CELLS[index]+'.json',canonical_bytes(row));rows.append(row)
        for target in targets:target.check()
        records=tuple(verify_retained(x,owner) for x in targets)
        with compact_owner._held(owner):reference=owner._finish()
        proof=_Completion(journal,owner,tuple(targets),reference,records,canonical_bytes(thaw(bound.record)),_seal=_COMPLETION_SEAL)
        terminal=journal.resource_complete(proof)
    except BaseException as error:
        primary=error
        for action in failure_actions:
            try:action()
            except BaseException as secondary:primary=_preserve_terminal(primary,secondary)
    # Assembly, formatting and every independently possible publication are
    # protected equally. Completed target rows are never reclassified/retried.
    for action in output_actions:
        try:action()
        except BaseException as secondary:primary=_preserve_terminal(primary,secondary)
    if primary is not None:raise primary
    return rows
