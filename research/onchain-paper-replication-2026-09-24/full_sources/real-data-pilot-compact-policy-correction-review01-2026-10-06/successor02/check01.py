"""Bounded changed-seam successor composition; no runtime/native/scientific imports."""
import ast, copy, hashlib, json, os, stat, types, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
FS=HERE.parent.parent
OLD=FS/'real-data-pilot-final01-2026-10-06'
NEW=FS/'real-data-pilot-final02-2026-10-06'
SU=FS/'real-data-pilot-packed-feature-successor03-2026-10-06'
OLDID='eth-paper-real-data-end-to-end-resource-20261005-01'
NEWID='eth-paper-real-data-end-to-end-resource-20261006-02'
evidence={}
def sha(b):return hashlib.sha256(b).hexdigest()
def raw(v):return (json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def body(path):
    assert path.is_file() and not path.is_symlink() and path.stat().st_size<=4*1024**2
    assert 'real_pilot_runtime' not in path.parts and path.name!='connection.json'
    b=path.read_bytes();evidence[str(path.relative_to(ROOT))]=sha(b);return b
def read(path):return json.loads(body(path))
def auth(ref):
    b=body(ROOT/ref['path']);assert sha(b)==ref['sha256'];return json.loads(b)
def need(ok,message):
    if not ok:raise ValueError(message)
def main():
    oldrelease=read(OLD/'RELEASE_REVIEW01.json');assert oldrelease['decision']=='accepted'
    seams=read(NEW/'SUCCESSOR_SEAMS01.json')
    oldgate=read(OLD/'gate01.json');gate=read(NEW/'gate01.json');x=oldgate['experiments'][OLDID];y=gate['experiments'][NEWID]
    for k in ('datasets','families','program_id','schema_version'):assert oldgate[k]==gate[k]
    assert set(gate['experiments'])=={NEWID} and y['parent'] is None
    changed={'charter','cumulative_budget_extension','inputs','question','source_files'}
    assert {k for k in x if x[k]!=y[k]}==changed
    assert len(y['source_files'])==201 and len(y['inputs'])==59 and len(y['runtime_hashes'])==7
    pairs=seams['source_replacement_pairs'];added=set(y['source_files'])-set(x['source_files'])-set(pairs.values())
    assert set(x['source_files'])-set(y['source_files'])==set(pairs)
    assert len(added)==3
    for p,h in y['source_files'].items():
        assert sha(body(ROOT/p))==h
        if p in x['source_files']:assert x['source_files'][p]==h and oldrelease['evidence'][p]==h
    for old,new in pairs.items():assert oldrelease['evidence'][old]==x['source_files'][old] and y['source_files'][new]==seams['sources'][new]
    numerical={p:h for p,h in y['source_files'].items() if p.startswith('tradingagents/')}
    assert len(numerical)==178 and all(x['source_files'][p]==h for p,h in numerical.items())
    accepted=FS/'real-data-pilot-compact-policy-correction01-2026-10-06/candidate/build_inputs03.py'
    a=body(accepted).decode();b=body(SU/'candidate/build_inputs03.py').decode();assert a.count(OLDID)==1 and b==a.replace(OLDID,NEWID)
    oldsu=FS/'real-data-pilot-packed-feature-successor02-2026-10-06'
    a=body(oldsu/'candidate/controls01.py').decode();b=body(SU/'candidate/controls01.py').decode();assert a.count(OLDID)==1 and b==a.replace(OLDID,NEWID)
    assert body(oldsu/'successor02.py')==body(SU/'successor02.py')
    deps=read(SU/'DEPENDENCIES02.json');olddeps=read(oldsu/'DEPENDENCIES02.json')
    assert {k for k in deps if deps[k]!=olddeps[k]}=={'builder','controls'}
    for r in deps.values():assert sha(body(ROOT/r['path']))==r['sha256']
    assert body(NEW/'root_io.py')==body(OLD/'root_io.py').replace(OLDID.encode(),NEWID.encode())
    preflight=body(NEW/'preflight01.py').decode();oldflight=body(OLD/'preflight01.py').decode()
    expected=oldflight.replace(OLDID,NEWID).replace('real-data-pilot-packed-feature-successor02-2026-10-06','real-data-pilot-packed-feature-successor03-2026-10-06')
    expected=expected.replace('admission.effective_attempt_budget!=72','admission.effective_attempt_budget!=73').replace("'effective_attempt_budget':72","'effective_attempt_budget':73")
    insertion="    for role in ('prior_outcome_review','prior_preservation_complete','prior_recovery_review'):\n        reference(binding.get(role))\n"
    anchor="    # Unknown draft references refuse before admission, subprocesses or scans.\n"
    assert expected.count(anchor)==1 and preflight==expected.replace(anchor,insertion+anchor)
    binding=read(NEW/'BINDING_DRAFT02.json');assert binding['identity']==NEWID
    draft=auth(binding['draft']);saved=auth(binding['preparation']);baseline=auth(binding['baseline']);bound=auth(binding['transport_binding'])
    assert sha(json.dumps(draft['graphs'],sort_keys=True).encode())=='73779a7d29bdf98530b3886282339f76edb4feac28b11470a8c147250fe34247'
    module=types.ModuleType('successor');module.__file__=str(SU/'successor02.py');exec(compile(body(SU/'successor02.py'),module.__file__,'exec'),vars(module))
    assert module.prepare(ROOT,draft)==saved
    # The exact accepted binder inverse is pure, so extract only that function.
    tree=ast.parse(preflight);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='inverse_binding')
    env={'need':need,'copy':copy,'Path':Path,'OPAQUE_ROLE':'archive_transport'}
    exec(compile(ast.Module(body=[fn],type_ignores=[]),'<pure binder inverse>','exec'),env)
    archive=auth(saved['builder03_spec']['references'][saved['builder03_spec']['template_roles']['archive']])
    env['inverse_binding'](saved,archive,bound,binding['transport'],raw,sha)
    assert all(bound['source_request']['prepared'][k]==binding['preparation'][k] for k in ('path','sha256'))
    assert bound['source_request']['prepared'].get('bytes')==len(body(ROOT/binding['preparation']['path']))
    assert bound['private_input']['archive_transport']==binding['transport']
    private=ROOT/binding['transport']['path'];s=private.lstat();p=private.parent.lstat()
    assert private.resolve()==private and s.st_size==binding['transport']['bytes'] and s.st_nlink==1 and s.st_uid==os.getuid() and stat.S_IMODE(s.st_mode)==0o600 and stat.S_IMODE(p.st_mode)==0o700
    evidence[binding['transport']['path']]=binding['transport']['sha256'] # accepted binder public digest; never read private body
    expected_docs={};deltas={}
    for role in bound['inputs']:
        old=auth(x['inputs'][role]);new=auth(y['inputs'][role]);assert new==bound['inputs'][role]
        expected=json.loads(json.dumps(old).replace(OLDID,NEWID))
        if role=='archive_policy':expected['remote_namespace']='ethpilot-20261006-02'
        if role in ('execution_job','producer_plan'):
            d=next(iter(expected['payload']['representation_jobs'].values()))['descriptor'] if role=='execution_job' else expected['producers']['original32']['descriptor']
            d['compact_execution']['policy_sha256']=y['inputs']['compact_policy']['sha256']
            d['compact_archive_execution']['policy_sha256']=y['inputs']['archive_policy']['sha256']
        assert new==expected,role
        expected_docs[role]=new
    for role,ref in y['inputs'].items():
        if role in expected_docs:continue
        if role=='archive_transport':
            assert all(ref[k]==binding['transport'][k] for k in ('path','sha256'));continue
        assert ref==x['inputs'][role] and oldrelease['evidence'][ref['path']]==ref['sha256']
        evidence[ref['path']]=ref['sha256'] # immutable accepted public input identity; no numerical reread
    selected=expected_docs['execution_job']['payload']['representation_jobs']['original32'];producer=expected_docs['producer_plan']['producers']['original32'];assert selected['descriptor']==producer['descriptor']
    for field,key,hkey,backend in [('compact_policy_input','compact_execution','policy_sha256',True),('compact_archive_input','compact_archive_execution','policy_sha256',True),('pair_checkpoint_input','pair_execution','policy_sha256',True),('original_dictionary_input','original_dictionary_import','sha256',False),('original_dictionary_stage_input','original_dictionary_stage','sha256',False)]:
        role=selected[field];assert role==producer[field]
        doc=auth(y['inputs'][role]);expected={hkey:y['inputs'][role]['sha256'],('backend' if backend else 'input'):(doc['backend'] if backend else role)}
        assert selected['descriptor'][key]==expected
    for field in ('compact_mcm_input','compact_mcm_output_input'):assert selected[field]==producer[field] and selected[field] in y['inputs']
    # Baseline is inherited public evidence; live storage remains preflight responsibility.
    assert draft['protocol']['physical_baseline']['evidence']==binding['baseline']
    obs=baseline['result']['observation'];decl=draft['protocol']['physical_baseline']
    assert all(decl[k]==obs[o] for k,o in [('logical_bytes','logical_file_bytes'),('allocated_bytes','allocated_bytes'),('entries','entries')])
    job=expected_docs['execution_job'];assert saved['inventory']['storage_budget_unchanged']==job['resources']['storage_budget']
    extension=auth(y['cumulative_budget_extension']['extension']);review=auth(y['cumulative_budget_extension']['review'])
    assert review['decision']=='accepted' and review['extension_sha256']==y['cumulative_budget_extension']['extension']['sha256'] and extension['cumulative_ceiling']==73 and extension['initial_experiment']==NEWID
    assert not (ROOT/'research_runs'/NEWID).exists()
    assert not any(k in sys.modules for k in ('numpy','torch','tradingagents','scipy'))
    result={'status':'PASS_SOURCE_AND_BINDING_COMPOSITION_ONLY','identity':NEWID,'gate_source_pins':201,'gate_input_roles':59,'unchanged_numerical_package_pins':178,'private_body_opened':False,'full_preparation_equal':True,'whole_generated_document_inverse':True,'preflight_exact_delta':True,'all_descriptor_joins':True,'evidence':evidence,'not_tested':'Actual committed HEAD admission, fresh physical/process/namespace/native eligibility, actual Owner/Binding, numerical results and full capacity; final prior recovery refs still require bound acceptance.'}
    (HERE/'CHECK01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    six={binding[k]['path']:binding[k]['sha256'] for k in ('gate','draft','preparation','baseline','transport','transport_binding')}
    output={'schema_version':1,'decision':'accepted','identity':NEWID,'reviewer':'independent pilot_correction_review','scope':'Exact six public/opaque reference binding composition only; independent preparation equality, source and generated-document inverses, descriptor joins and unchanged resources. Final recovery binding and full source/entry release remain required.','evidence':six,'private_input_qualification':'Public binder digest joined; private mode/size/owner/path/link stat checked. Body not opened. Entry must opaquely authenticate current bytes.','checks':{'source_pins':201,'input_roles':59,'unchanged_numerical_package_pins':178,'full_preparation_equal':True,'whole_generated_document_inverse':True}}
    (HERE/'BINDING_REVIEW01.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='evidence'},indent=2))
if __name__=='__main__':main()
