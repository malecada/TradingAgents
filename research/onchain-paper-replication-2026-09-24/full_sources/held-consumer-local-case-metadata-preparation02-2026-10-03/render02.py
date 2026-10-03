"""Render exact unregistered metadata bytes. Never writes the live capsule."""
from pathlib import Path
import copy, hashlib, json, subprocess, sys

REPO = Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
BASE = REPO / 'research/onchain-paper-replication-2026-09-24/full_sources'
ROOT = Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source')
OUT = Path(__file__).resolve().parent
PAYLOAD = OUT / 'capsule_payload'
PROGRAM = 'original-dictionary-import-engineering-2026-10-02'
sys.path.insert(0, str(ROOT))
from fixture_tools import generate_inputs01 as generator

def canonical(value):
    return generator.canonical(value)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def read(path, expected=None):
    path = Path(path)
    assert path.resolve() == path and path.stat().st_nlink == 1 and path.stat().st_size <= 4*1024**2
    raw = path.read_bytes()
    if expected is not None:
        assert len(raw) == expected['bytes'] and sha(raw) == expected['sha256']
    return raw

def main():
    assert Path(generator.__file__).resolve() == ROOT / 'fixture_tools/generate_inputs01.py'
    assert not PAYLOAD.exists()
    PAYLOAD.mkdir()
    source = json.loads(read(BASE / 'held-consumer-actual-source-runtime-role-readback02-2026-10-03/ACTUAL_SOURCE_PLAN02.json'))
    assert source['source_count'] == 199 and source['package_count'] == 148
    donors = json.loads(read(BASE / 'held-consumer-actual-admission-role-binding-investigation01-2026-10-03/ROLE_DONORS01.json'))
    policies = {Path(row['path']).stem: row for row in donors['policy_donors']}
    templates = BASE / 'held-consumer-positive-case-contract-investigation01-2026-10-03'
    extension = BASE / 'held-consumer-cumulative-admission-preparation02-2026-10-03'
    review = BASE / 'held-consumer-cumulative-machine-review01-2026-10-03/cumulative-extension-review04.json'
    bodies = {}

    def put(path, value, raw=False):
        body = value if raw else canonical(value)
        assert isinstance(body, bytes) and len(body) <= 4*1024**2
        if path in bodies:
            assert bodies[path] == body
        else:
            dest = PAYLOAD / path
            assert '..' not in Path(path).parts and not Path(path).is_absolute()
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open('xb') as handle:
                handle.write(body)
            bodies[path] = body
        return {'path': path, 'sha256': sha(body), 'bytes': len(body)}

    common = {}
    for role in ('runtime','software_environment','original_import_index','original_evidence','matching','target_catalog'):
        donor = donors['roles'][role]
        raw = read(donor['path'], donor)
        path = 'fixture_inputs/held/roles01/' + role + '.json'
        common[role] = {'reference': put(path, raw, raw=True), 'document': json.loads(raw)}
    job_template = json.loads(read(templates / 'JOB_TEMPLATE01.json'))
    native = copy.deepcopy(job_template['resources'])
    native['disk_paths'] = [str(ROOT)]
    native['storage_budget']['root'] = str(ROOT)
    env = {'PYTHONPATH':str(ROOT),'TMPDIR':str(ROOT/'fixture_runtime/tmp'),
        'XDG_CACHE_HOME':str(ROOT/'fixture_runtime/cache'),'TORCH_HOME':str(ROOT/'fixture_runtime/torch'),
        'MPLCONFIGDIR':str(ROOT/'fixture_runtime/matplotlib'),'HF_HOME':str(ROOT/'fixture_runtime/hf'),
        'TORCH_EXTENSIONS_DIR':str(ROOT/'fixture_runtime/torch-extensions'),
        'PYTHONDONTWRITEBYTECODE':'1','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1',
        'OPENBLAS_NUM_THREADS':'2','OMP_NUM_THREADS':'2','MKL_NUM_THREADS':'2','NUMEXPR_NUM_THREADS':'2'}
    for name,doc in (('native_policy',native),('native_environment',env)):
        common[name] = {'reference':put('fixture_inputs/held/roles01/'+name+'.json',doc),'document':doc}
    for role,name in (('budget_extension','cumulative-extension04-proposal.json'),
            ('budget_allocation','successor-allocation04-proposal.json')):
        raw = read(extension/name)
        common[role] = {'reference':put(name,raw,raw=True),'document':json.loads(raw)}
    raw = read(review)
    common['budget_review'] = {'reference':put(review.name,raw,raw=True),'document':json.loads(raw)}
    assert common['budget_review']['document']['extension_sha256'] == common['budget_extension']['reference']['sha256']
    claim = json.loads(read(ROOT/'research_runs/original-import-native-success-20261003-04/claim.json'))
    old_raw = subprocess.check_output(['git','-c','protocol.allow=never','cat-file','blob',
        claim['design_source']+':'+claim['registration']],cwd=ROOT,timeout=10)
    assert sha(old_raw) == claim['registration_sha256']
    gate = json.loads(old_raw)
    assert gate['program_id'] == PROGRAM
    closed = {r['experiment'] for r in common['budget_extension']['document']['claims']}
    gate['experiments'] = {k:v for k,v in gate['experiments'].items() if k in closed}
    assert len(gate['experiments']) == 4
    old_exp = copy.deepcopy(gate['experiments']['original-import-native-success-20261003-04'])
    pending = []
    for case,identity in [('success','original-import-held-success-20261003-01'),
            ('second_target_publication_failure','original-import-held-publication-failure-20261003-01')]:
        roles = copy.deepcopy(common)
        prefix = 'fixture_inputs/held/'+case+'01/'
        additional = {}
        def inp(name,doc,raw=False,dataset=None):
            ref=put(prefix+name+'.json',doc,raw=raw)
            additional[name]={'reference':ref,'dataset':dataset or old_exp['inputs'].get(name,{}).get('dataset','synthetic')}
            return ref
        for name in ('original_import','original_import_stage','compact_policy','mcm_policy','mcm_output_policy'):
            row=policies[name];inp(name,read(row['path'],row),raw=True)
        evidence=copy.deepcopy(roles['original_evidence']['document'])
        evidence['control_reference']=dict(additional['original_import']['reference'])
        roles['original_evidence']={'reference':put(prefix+'original-evidence-role.json',evidence),'document':evidence}
        pair=json.loads(read(policies['pair_policy']['path'],policies['pair_policy']))
        pair['numerical_source']={'commit':source['anchor'],'files':source['package_files']}
        pair_ref=inp('pair_policy',pair)
        inp('environment',canonical(roles['software_environment']['document']),raw=True)
        inp('execution_workspace',{'root':str(ROOT),'artifacts':str(ROOT/'research_artifacts'),
            'ledger':str(ROOT/'research_runs'),'git_common':str(ROOT/'.git')})
        provenance={'path':'fixture_inputs/target-provenance.json','sha256':sha(read(ROOT/'fixture_inputs/target-provenance.json')),
            'bytes':len(read(ROOT/'fixture_inputs/target-provenance.json'))}
        additional['target_provenance']={'reference':provenance,'dataset':'synthetic'}
        contract=json.loads(read(templates/'CASE_TEMPLATE01.json'))
        contract.update(program_id=PROGRAM,experiment_id=identity,additional_inputs=additional)
        catalog=roles['target_catalog']['document']['targets']
        held={'schema_version':1,'kind':'original-import-held-score-readback-v1',
            'targets':{row['graph_hash']:{'output':contract['readback_outputs'][row['graph_hash']]} for row in catalog},
            'part_bytes':1048576,'max_read_bytes':768,'max_members':32767}
        inp('held_score_policy',held)
        job=copy.deepcopy(job_template);job['resources']=native
        selected=job['payload']['representation_jobs']['original32']
        selected['descriptor']['pair_execution']['policy_sha256']=pair_ref['sha256']
        selected['descriptor']['resource_fixture']['case']=case
        plan={'schema_version':2,'producers':{'original32':dict(copy.deepcopy(selected),
            binding_output='resource-binding.json',journal_output='resource-journal.json')}}
        inp('producer_plan',plan);inp('execution_job',job)
        contract['additional_inputs']=additional
        roles['case_contract']={'reference':put(prefix+'case-contract.json',contract),'document':contract}
        charter=(f'Synthetic imported-original held MCM engineering case: {case}.\n\n'
            f'Program {PROGRAM}; identity {identity}; parent None; development/exploratory. '
            'The full original dictionary of32motifs and512spent samples is imported without resampling or clustering. '
            'Two authenticated synthetic targets have2 and3nodes and64 and96MCM cells. '
            'Normal success requires160 scalar-reference comparisons, both held f64 readbacks512+768bytes, '
            'both original MCM publications and all six registered outputs. Matching, dictionary and numerical tolerances remain unchanged. '
            'This local resource fixture does not complete the scientific full representation or paper-scope evaluation.\n\n'
            'Cumulative engineering ceiling6 preserves four actual FAILED claims; at most one fresh claim per fixed identity. '
            'No refund, sample reset, transfer, cap ladder, paper budget65, test tuning or closed job replay is allowed. '
            'The dependent publication-failure identity may execute only after COMPLETE normal success, independent outcome review '
            'and actual complete external recovery. Otherwise it remains unavailable. Its expected publication failure stays FAILED; '
            'only the first64 scalar-reference comparisons can be counted complete. Second-target publication and scalar checks stay unavailable; '
            'any actual preceding MCM/held receipts are retained and evaluated separately.\n\n'
            'The exact native envelope is3GiB high=max, zero swap,3GiB host reserve,6GiB startup reserve, two CPU affinity/threads, '
            '1800seconds native/1840seconds outer,4MiB native hard/soft writable-file cap,1GiB whole-tree watch and10GiB disk floor. '
            'Interpreter authentication streams at most64KiB per read with a separate64MiB read ceiling; this changes no writable cap. '
            'Actual source199/package148 plus five admission metadata pins, all33inputs and six outputs must be committed and independently released. '
            'Guard/native readback, whole writable baseline, current resources, one-use parent and complete externally recovered inputs/sources '
            'are prerequisites. These rendered bytes are unregistered; no source/runtime metadata result confers execution authority.\n\n'
            'All13tasks/C01-C18, both assets/history/comparisons, all32Task8 requirements and all1420financial fits remain in scope. '
            'Full55.44GB MCM, real eligible populations, joint gradients, typed tails plus batch/output streaming and capacity remain unproved. '
            'The27mutation variants/16classes are separate. No payment/contact/trading/deployment or deletion is authorized by this case.\n').encode()
        roles['charter']={'reference':put('held-charter-'+case+'01.md',charter,raw=True),'document':charter.decode()}
        declaration=generator.render_held_auxiliary_declaration(roles,source)
        roles['auxiliary_sources']={'reference':put('held-auxiliary-'+case+'01.json',declaration),'document':declaration}
        sources=dict(source['source_files'])
        for name in (*generator.AUXILIARY_ROLES,'auxiliary_sources'):
            ref=roles[name]['reference'];assert ref['path'] not in sources;sources[ref['path']]=ref['sha256']
        inputs={}
        for row in roles['original_import_index']['document']['inputs']:
            inputs[row['name']]={**{k:row['reference'][k] for k in ('path','sha256')},'dataset':'original_dictionary'}
        for row in catalog:
            inputs[row['input_name']]={**{k:row['manifest'][k] for k in ('path','sha256')},'dataset':'synthetic'}
            for name,ref in row['components'].items():
                inputs[row['input_name']+'_'+name]={**{k:ref[k] for k in ('path','sha256')},'dataset':'synthetic'}
        for name,row in additional.items():inputs[name]={**{k:row['reference'][k] for k in ('path','sha256')},'dataset':row['dataset']}
        assert len(inputs)==33 and len(sources)==204
        exp=copy.deepcopy(old_exp)
        exp.update(parent=None,charter={k:roles['charter']['reference'][k] for k in ('path','sha256')},
            question='Does the genuine imported-original held MCM route preserve the fixed two-target numerical and lifecycle contract?',
            inputs=inputs,source_files=dict(sorted(sources.items())),selection=None,
            runtime_hashes={p.name:sha(read(p)) for p in sorted((ROOT/'tradingagents/research').glob('*.py'))},
            outputs=['resource-binding.json','resource-journal.json','cell-ledger.json','resource-summary.json',
                'held-target-01.json','held-target-02.json'],
            cumulative_budget_extension={key:{k:roles[role]['reference'][k] for k in ('path','sha256')}
                for key,role in [('extension','budget_extension'),('review','budget_review')]})
        gate['experiments'][identity]=exp
        pending.append((identity,roles))
    gate_ref=put('held-fixture-registration01.json',gate)
    for identity,roles in pending:
        roles['registration']={'reference':gate_ref,'document':gate}
        planned=generator.held_input_plan(roles,source)
        assert planned['remaining_roles']==[] and len(planned['input_rows'])==33
        assert planned['auxiliary_metadata']['admission_source_count']==204
        name='success' if identity=='original-import-held-success-20261003-01' else 'failure'
        with (OUT/(name+'-roles01.json')).open('x') as handle:
            handle.write(json.dumps({k:v['reference'] for k,v in roles.items()},sort_keys=True,indent=2)+'\n')
        with (OUT/(name+'-input-plan01.json')).open('x') as handle:
            handle.write(json.dumps(planned,sort_keys=True,indent=2)+'\n')
    summary={'schema_version':1,'status':'rendered-unregistered-candidate-bytes-not-release',
        'baseline_source':source['source'],'planned_capsule_root':str(ROOT),'source_count':199,'package_count':148,
        'admission_pins_per_case':204,'roles_per_case':15,'inputs_per_case':33,'outputs_per_case':6,
        'budget_extension_adopted':False,'claim_created':False,'current_design_commit_bound':False,
        'capsule_mutated':False,'native_release':None,'whole_external_recovery':False,
        'qualification':'Actual installed stdlib generator rendered finite metadata only. Payload files remain in this preparation tree, not the capsule. Authentic final source/design/Git/body/native/admission and independent release remain required.',
        'numerical_modules_imported':sorted(n for n in sys.modules if n.split('.')[0] in ('numpy','torch','scipy'))}
    assert summary['numerical_modules_imported']==[]
    with (OUT/'RENDER_SUMMARY01.json').open('x') as handle:handle.write(json.dumps(summary,sort_keys=True,indent=2)+'\n')
    rows=[]
    for path in sorted(OUT.rglob('*')):
        if path.is_file():
            raw=read(path);rows.append({'path':str(path.relative_to(OUT)),'bytes':len(raw),'sha256':sha(raw)})
    with (OUT/'MANIFEST01.json').open('x') as handle:handle.write(json.dumps({'schema_version':1,'files':rows},sort_keys=True,indent=2)+'\n')
    print(json.dumps(summary))

if __name__=='__main__':
    main()
