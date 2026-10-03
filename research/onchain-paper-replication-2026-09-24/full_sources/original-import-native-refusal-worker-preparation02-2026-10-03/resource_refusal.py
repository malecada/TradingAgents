"""Registered negative fixture. Uses genuine run/Binding/Owner; never a fit.

Numerical imports occur only when the real worker calls execute inside its
original native unit. Each case has a fresh claim and at most one fresh Owner.
"""
import copy,json
from . import resource_refusal_cases as cases

class RefusalObserved(ValueError):pass

def require(value,message):
    if not value:raise ValueError(message)

def observe(action,fragment):
    """A wrong exception, no exception or fatal is not an observed refusal."""
    try:action()
    except ValueError as error:
        require(type(error) is ValueError and fragment in str(error),'wrong refusal boundary')
        return {'exception':'ValueError','expected_message_fragment':fragment,'observed':True}
    raise AssertionError('registered mutation was accepted')

def active_case(owner):
    if owner.bound.record.get('resource_only') is not True:return None
    raw=owner.bound._run.read_input(owner.bound.record['job_input']);job=json.loads(raw)
    value=next(iter(job['payload']['representation_jobs'].values()))['descriptor']['resource_fixture']['case']
    return value[8:] if value.startswith('refusal-') else None

def score_callback(owner,stream):
    """One fixed bad purpose at the first actual imported-kernel callback."""
    if active_case(owner)!='wrong-purpose':return stream
    called=False
    def selected(purpose,a,b):
        nonlocal called
        require(not called,'refusal numerical callback reused');called=True
        wrong=dict(purpose);wrong['workload_sha256']='0'*64
        # Real stream checks the real kernel purpose against its genuine Target.
        return stream(wrong,a,b)
    return selected

def compute_callback(owner,matcher):
    if active_case(owner)!='wrong-ack':return matcher
    called=False
    def selected(purpose,a,b):
        nonlocal called
        require(not called,'refusal matcher callback reused');called=True
        result=matcher(purpose,a,b)
        wrong=dict(result);wrong['purpose_sha256']='0'*64
        return wrong
    return selected

def returned(owner,result):
    if active_case(owner)=='wrong-matrix':
        result=dict(result);result['mcm']=result['mcm'][:,:-1]
    if active_case(owner)=='wrong-count':
        result=dict(result);result['completed_cells']+=1
    return result

def forbidden_compute(*args,**kwargs):
    raise AssertionError('legacy refusal reached forbidden computation')


def genuine_oracle(target):
    """Real guarded Target only. Durable observation precedes every Owner mutation."""
    import hashlib,importlib,sys
    from pathlib import Path
    from . import import_metadata
    from .imported_mcm_identity import Target
    from .provenance import thaw
    from .cache import cache_key
    require(type(target) is Target,'genuine original-import Target required')
    target.check();run=target.owner.bound._run;run._active();root=run.admission.root
    sources=run.admission.experiment['source_files'];tools=root/'fixture_tools'
    names=('raw_receipts01','original_semantics','refusal_pair_identity','resource_policy05','guarded_formula_oracle05')
    for name in names:
        path=tools/(name+'.py');require(path.resolve()==path and path.stat().st_size<=131072 and sources.get('fixture_tools/'+name+'.py')==hashlib.sha256(path.read_bytes()).hexdigest(),'oracle helper source not admitted')
    if str(tools) not in sys.path:sys.path.insert(0,str(tools))
    modules={name:importlib.import_module(name) for name in names}
    for name,module in modules.items():
        path=Path(module.__file__).resolve();require(path==tools/(name+'.py') and hashlib.sha256(path.read_bytes()).hexdigest()==sources['fixture_tools/'+name+'.py'],'oracle helper import origin differs')
    record=target.execution.check();manifest=json.loads(target._manifest)
    expected=modules['refusal_pair_identity'].expected_pairs(root,run.admission.inputs[target._input]['path'],manifest,run.admission.inputs,numeric=record['original'],dictionary_config=target.dictionary.config,matching=thaw(target.owner.matching),context=thaw(target.owner.bound.context),backend=record['current']['backend'],workload=target.scope['workflow'],source_files=sources)
    proof=modules['guarded_formula_oracle05'].verify(target,expected)
    target.check();run._active()
    value={'schema_version':1,'kind':'guarded-original-target-identity-observation','identity':run.admission.experiment_id,'source':run.admission.source,'claim_sha256':run._claim_sha256,'binding_sha256':cache_key(thaw(target.owner.bound.record)),'owner':target.owner.identity,'proof':proof,'expected_pair_identity_sha256':cache_key(expected),'tool_sources':{name:sources['fixture_tools/'+name+'.py'] for name in names}}
    require(proof['pair_count']==64 and proof['pair_identity_sha256']==value['expected_pair_identity_sha256'],'genuine64pair observation differs')
    raw=(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode();require(len(raw)<=8192,'oracle metadata ceiling')
    digest=import_metadata.write(run.directory,'refusal-oracle.json',raw)
    import_metadata.exact(run.directory,'refusal-oracle.json',raw);target.check();run._active()
    return {'path':str((run.directory/'refusal-oracle.json').relative_to(root)),'sha256':digest,'bytes':len(raw)}

def execute(run,payload,*,job_input='execution_job'):
    from . import resource_fixture as fixture,resource_binding,original_import_preparation,original_import_stage
    from . import compact_mcm,compact_owner,matching_owner,original_dictionary,compact_closure
    from . import mcm_score_stream
    from .matching_pair import BACKEND
    from .graph_store import load_graph
    from .imported_mcm_identity import Target
    from .provenance import thaw,freeze
    require(job_input=='execution_job','refusal genuine worker job input differs')
    job=json.loads(run.read_input(job_input));case=cases.selected(job)
    require(job['payload']==payload and run.admission.experiment_id==cases.identity(case),'registered refusal identity/payload differs')
    require(case not in cases.PRECLAIM,'preclaim refusal must never reach worker claim')
    name,s,f=fixture.selection(job);item=json.loads(run.read_input(s['plan_input']))['producers'][s['producer']]
    fragment=cases.FRAGMENTS[case]
    journal=owner=None;observed=None;primary=None;graph=None;execution=None;target=None;oracle=None
    try:
        if case=='reservation':
            observed=observe(lambda:fixture.preflight(run,job),fragment)
        elif case in ('policy-bool','policy-unknown'):
            fixture.preflight(run,job)
            wrong=json.loads(run.read_input(s['original_dictionary_stage_input']))
            if case=='policy-bool':wrong['max_numeric_bytes']=True
            else:wrong['unknown_policy']=1
            observed=observe(lambda:resource_binding.import_policy(wrong),fragment)
        elif case=='target-mapping':
            fixture.preflight(run,job);wrong=copy.deepcopy(job)
            mapping=next(iter(wrong['payload']['representation_jobs'].values()))['descriptor']['resource_graph_inputs'];mapping.pop(sorted(mapping)[-1])
            observed=observe(lambda:fixture.selection(wrong),fragment)
        else:
            name,s,f,item,inputs,source_rows=fixture.preflight(run,job)
            journal,bound=resource_binding.open_first(run,representation=name,plan_input=s['plan_input'],producer=s['producer'],policy_input=s['pair_checkpoint_input'],job_input=job_input)
            if case=='job-input':
                observed=observe(lambda:resource_binding.assert_selected(bound,'alternate_execution_job'),fragment)
            elif case=='job-hash':
                changed=thaw(bound.record);changed['job_sha256']=run.admission.inputs['alternate_execution_job']['sha256'];bound.record=freeze(changed)
                observed=observe(lambda:resource_binding.assert_selected(bound,job_input),fragment)
            else:
                prepared=original_import_preparation.prepare(bound,input_name=s['original_dictionary_input'],job_input=job_input)
                owner,stage=original_import_stage.attach(prepared,policy_input=s['compact_policy_input'],stage_policy_input=s['original_dictionary_stage_input'])
                execution=original_import_stage.ImportedExecution(stage)
                key,path,sha=inputs[0];graph=load_graph(path,sha,resident=True);target=Target(execution,graph,key)
                oracle=genuine_oracle(target)
                if case=='matching-swap':
                    d=execution._materialized._dictionary;object.__setattr__(d,'matching_config_hash',execution.check()['current']['execution_matching']);observed=observe(execution.check,fragment)
                elif case=='motif-identity':
                    object.__setattr__(execution._materialized._dictionary,'identity','0'*64);observed=observe(execution.check,fragment)
                elif case=='motif-order':
                    d=execution._materialized._dictionary;object.__setattr__(d,'representatives',tuple(reversed(d.representatives)));observed=observe(execution.check,fragment)
                elif case=='node-order':
                    object.__setattr__(graph,'node_ids',tuple(reversed(graph.node_ids)));observed=observe(target.check,fragment)
                elif case in ('target-array','post-lease-mutation'):
                    if case=='post-lease-mutation':target.lease()
                    object.__setattr__(graph,'node_features',graph.node_features.copy());observed=observe(target.check,fragment)
                elif case=='capability-copy':
                    copied=copy.copy(execution);copied._stage=copy.copy(stage);observed=observe(copied.check,fragment)
                elif case=='receipt-copy':
                    copied=copy.copy(stage);observed=observe(lambda:original_import_stage.ImportedExecution(copied),fragment)
                elif case=='owner-death':
                    journal.seal('failed',reason='registered negative owner terminal boundary');observed=observe(lambda:compact_owner.verify_current(owner),fragment)
                elif case=='lease-terminal':
                    journal.seal('failed',reason='registered negative lease-terminal boundary');observed=observe(target.lease,fragment)
                elif case in ('wrong-purpose','wrong-ack','wrong-matrix','wrong-count'):
                    # Selected fixed source hooks alter one bad purpose or one
                    # returned count. Numerical engines and their real leases
                    # are not replaced. No current target is ever published.
                    observed=observe(lambda:compact_mcm.produce_imported(execution,graph,graph_hash=key,input_name=s['compact_mcm_input'],output_input=s['compact_mcm_output_input']),fragment)
                elif case=='legacy-backend':
                    observed=observe(lambda:mcm_score_stream.MCMScoreStream(owner.root/'legacy-refusal',graph=graph,dictionary=execution._materialized._dictionary,matching_config=thaw(owner.matching),workflow=bound.record['workflow_identity'],backend=BACKEND,owner=owner.identity,chunk_cells=64,compute=forbidden_compute,lease=target.lease),fragment)
                elif case=='journal-scientific':observed=observe(lambda:journal('representation_complete',{},None),fragment)
                elif case=='financial-closure':observed=observe(lambda:compact_closure._membership(execution,None,[]),fragment)
                else:raise AssertionError('unhandled registered refusal')
        require(observed is not None,'refusal evidence absent')
    except BaseException as error:primary=error
    # Original terminal is selected before diagnostic allocation. Every
    # independently possible seal/output remains attempted without retry.
    terminal=rows=None
    def poison():
        if owner is not None:owner.poisoned=True
    def seal():
        if journal is not None and not journal.sealed:journal.seal('failed',reason='registered negative fixture; no retry')
    def assemble():
        nonlocal terminal,rows
        terminal={'schema_version':1,'kind':'original-import-refusal','status':'observed' if primary is None else 'failed','case':case,'identity':run.admission.experiment_id,'boundary':observed,'resource_only':True,'financial_representation_admitted':False,'oracle_observation':oracle}
        rows=[{'id':'import-target-01','status':'unavailable','reason':'registered refusal before publication'},{'id':'import-target-02','status':'unavailable','reason':'registered refusal before publication'}]
    def publish(name):
        require(terminal is not None,'refusal terminal assembly absent');run.write_json(name,terminal)
    def cells():
        require(rows is not None,'refusal cell assembly absent');run.write_json('cell-ledger.json',rows)
    for action in (poison,seal,assemble,lambda:publish(item['binding_output']),lambda:publish(item['journal_output']),lambda:publish('resource-summary.json'),cells):
        try:action()
        except BaseException as later:primary=fixture._preserve_terminal(primary,later)
    if primary is not None:raise primary
    raise RefusalObserved('registered original-import refusal observed: '+case)
