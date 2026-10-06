"""Metadata-only regression; no scientific imports, authorities, arrays or launch."""
import copy, hashlib, importlib.util, json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
FS=HERE.parent
FINAL=FS/'real-data-pilot-final01-2026-10-06'

def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

successor=load(FS/'real-data-pilot-packed-feature-successor02-2026-10-06/successor02.py','successor')
old=successor.load('builder')
# Reuse the existing exact stdlib import adapter and scalar helper.
import types
b=types.ModuleType('candidate');b.__file__=str(HERE/'candidate/build_inputs03.py')
source=Path(b.__file__).read_text()
line='        from tradingagents.research.onchain_replication.archive_control_history import capacity\n'
assert source.count(line)==1
b.capacity=successor.load('history').capacity
exec(compile(source.replace(line,''),b.__file__,'exec'),b.__dict__)
def read(path):
    body=path.read_bytes();assert len(body)<=b.LIMIT;return json.loads(body)

def selected(job):
    assert len(job['payload']['representation_jobs'])==1
    return next(iter(job['payload']['representation_jobs'].values()))

# Only these explicit public JSON metadata bodies are read. Transport and
# numerical/evidence references in the real registered roster remain opaque.
ROLES=('execution_job','producer_plan','compact_policy','archive_policy',
       'pair_policy','original_import','original_import_stage','mcm_policy','mcm_output_policy')

def joins(job,plan,refs,docs):
    s=selected(job);p=plan['producers'][s['producer']]
    assert s['descriptor']==p['descriptor'],'producer descriptor differs'
    d=s['descriptor']
    for field,key,hashkey,backend in (
        ('compact_policy_input','compact_execution','policy_sha256',True),
        ('compact_archive_input','compact_archive_execution','policy_sha256',True),
        ('pair_checkpoint_input','pair_execution','policy_sha256',True),
        ('original_dictionary_input','original_dictionary_import','sha256',False),
        ('original_dictionary_stage_input','original_dictionary_stage','sha256',False)):
        role=s[field];assert p[field]==role,'producer role differs: '+field
        expected={hashkey:refs[role]['sha256']}
        expected['backend' if backend else 'input']=docs[role]['backend'] if backend else role
        assert d[key]==expected,'descriptor differs: '+key
    for field in ('compact_mcm_input','compact_mcm_output_input'):
        role=s[field];assert p[field]==role and role in docs and role in refs,'MCM role differs'
    assert docs[s['compact_policy_input']]['stage_policy']['pair']==docs[s['pair_checkpoint_input']]['limits'],'pair limits differ'
    return True

def run():
    refs=read(FINAL/'INPUT_REFS02.json')
    docs={role:b.metadata(ROOT,refs[role]) for role in ROLES}
    job,plan=docs['execution_job'],docs['producer_plan']
    # Reproduce the exact runtime equality without importing runtime code.
    expected={'backend':docs['compact_policy']['backend'],'policy_sha256':refs['compact_policy']['sha256']}
    assert selected(job)['descriptor']['compact_execution']!=expected
    assert plan['producers'][selected(job)['producer']]['descriptor']['compact_execution']!=expected
    try:joins(job,plan,refs,docs)
    except AssertionError as e:assert str(e)=='descriptor differs: compact_execution'
    else:raise AssertionError('registered old metadata must fail')
    # Full existing builder, actual previously successful metadata spec, no stubs.
    spec=read(FS/'real-data-pilot-seven-graph-packed-input03-2026-10-06/PREPARATION_RESULT07.json')['builder03_spec']
    before=old.build(ROOT,spec);after=b.build(ROOT,spec)
    roles=spec['template_roles'];a=selected(after['inputs'][roles['job']]);z=selected(before['inputs'][roles['job']])
    assert z['descriptor']['compact_execution']!=expected
    assert a['descriptor']['compact_execution']==expected
    ap=after['inputs'][roles['producer_plan']]['producers'][a['producer']]
    assert ap['descriptor']['compact_execution']==expected
    inverse=copy.deepcopy(after)
    for desc in (selected(inverse['inputs'][roles['job']])['descriptor'],inverse['inputs'][roles['producer_plan']]['producers'][a['producer']]['descriptor']):
        desc['compact_execution']=copy.deepcopy(z['descriptor']['compact_execution'])
    assert inverse==before,'candidate changed unrelated builder behavior'
    # Apply only the same two scalar descriptor changes to the real final metadata.
    fixed_job,fixed_plan=copy.deepcopy(job),copy.deepcopy(plan)
    for desc in (selected(fixed_job)['descriptor'],fixed_plan['producers'][selected(job)['producer']]['descriptor']):
        desc['compact_execution']=copy.deepcopy(expected)
    assert joins(fixed_job,fixed_plan,refs,docs)
    negatives=[]
    for key,hk in [('compact_execution','policy_sha256'),('compact_archive_execution','policy_sha256'),('pair_execution','policy_sha256'),('original_dictionary_import','sha256'),('original_dictionary_stage','sha256')]:
        j,p=copy.deepcopy(fixed_job),copy.deepcopy(fixed_plan)
        selected(j)['descriptor'][key][hk]='0'*64;p['producers'][selected(j)['producer']]['descriptor'][key][hk]='0'*64
        try:joins(j,p,refs,docs)
        except AssertionError:negatives.append(key)
        else:raise AssertionError('stale join accepted: '+key)
    for field in ('compact_mcm_input','compact_mcm_output_input'):
        p=copy.deepcopy(fixed_plan);p['producers'][selected(fixed_job)['producer']][field]='missing'
        try:joins(fixed_job,p,refs,docs)
        except AssertionError:negatives.append(field)
        else:raise AssertionError('wrong MCM role accepted')
    p=copy.deepcopy(fixed_plan);p['producers'][selected(fixed_job)['producer']]['descriptor']['compact_execution']['policy_sha256']='0'*64
    try:joins(fixed_job,p,refs,docs)
    except AssertionError:negatives.append('producer_only_stale')
    else:raise AssertionError('producer-only stale accepted')
    # No metadata input mutation, no numerical imports.
    assert all(b.metadata(ROOT,refs[r])==docs[r] for r in ROLES)
    assert not any(k in sys.modules for k in ('numpy','torch','scipy','tradingagents'))
    result={'status':'PASS','old_registered_metadata':'RED: compact_execution differs in both descriptors',
      'old_full_builder':'RED: retains stale compact_execution','candidate_full_builder':'GREEN: both descriptors bind actual selected reference',
      'full_builder_inverse_equal':True,'final_metadata_cross_joins':'GREEN','negative_refusals':negatives,
      'runtime_imports':False,'empirical_start':False,'new_identity_or_allowance':False,
      'qualification':'Metadata-only; does not admit any run or prove numerical or capacity success.'}
    return result,fixed_job,fixed_plan

if __name__=='__main__':
    result,job,plan=run()
    print(json.dumps(result,indent=2))
