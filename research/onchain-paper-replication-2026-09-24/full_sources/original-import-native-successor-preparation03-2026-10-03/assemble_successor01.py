"""Assemble the fresh finite successor gate/source; never claim or launch."""
import ast,hashlib,importlib.metadata,importlib.util,json,os,platform,stat,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];FULL=HERE.parent;CAP=HERE/'capsule02'
OLD=FULL/'original-import-native-release-2026-10-03'
PARENT='original-import-native-success-20261003-01'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):
    info=path.lstat();assert stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_size<=4*1024**2
    return path.read_bytes()
def save(path,raw,replace=False):
    assert len(raw)<=4*1024**2;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('wb' if replace else 'xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
def encoded(value):return (json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
def git(*args):
    result=subprocess.run(['git',*args],cwd=CAP,capture_output=True,timeout=60)
    assert result.returncode==0 and max(len(result.stdout),len(result.stderr))<=4*1024**2
    return result.stdout
def commit(message,paths):
    git('add','-f','--',*sorted(paths));git('-c','user.name=Research capsule','-c','user.email=research-capsule@localhost','commit','-m',message)
    return git('rev-parse','HEAD').decode().strip()
def main():
    assert Path.cwd()==ROOT and not (HERE/'ASSEMBLY_SUCCESSOR01.json').exists()
    assert git('rev-parse','HEAD').decode().strip()=='529c7a3769fcfea28d3a617270b3025aebbce1f5'
    assert not (CAP/'.git/objects/info/alternates').exists()
    assert not (CAP/'research_runs'/'original-import-native-success-20261003-02').exists()
    assert not (CAP/'research_runs'/'original-import-native-publication-failure-20261003-02').exists()
    original_claim=read(CAP/'research_runs'/PARENT/'claim.json');original_terminal=read(CAP/'research_runs'/PARENT/'failed.json')
    assert sha(original_claim)=='f475dd6c04d7dfc5e9d94bba30b5d3e686d1b71b5f5394dfa1aa0b174797f61e'
    assert sha(original_terminal)=='09206641f5ce569716bbf61246ecc85c20daa3ed40bf7f82427e4772198881c0'
    reviews={
        'metadata':(FULL/'imported-source-metadata-correction02-2026-10-03/REVIEW_METADATA02.md','0816424200fc8ecbbf348f36c56198e95e952bfb1ebd80cf92ed1038e4a43e5c'),
        'cleanup_only':(FULL/'original-import-native-refusal-candidate03-2026-10-03/REVIEW_REFUSAL03.md','e60beb031c7acc868c7dce381131a9c440f58e4ee09bbf10f2736a1712409b41'),
        'budget':(HERE/'REVIEW_BUDGET_EXTENSION01.md','b422f0abdc0a010b8f048f974e95dc634aaa3d1c34309d7f533d316f2653ab95')}
    for path,pin in reviews.values():assert sha(read(path))==pin
    # Root interprets the narrow cleanup disposition, not the withheld suite.
    inv=read(HERE/'source_inventory01.json');assert sha(inv)=='6a8c2f8385b85106e33eb9ea64f9bcc4ffa8eac7716dcab5a07ec15183972569'
    inventory=json.loads(inv);rows=inventory['source_inventory'];assert len(rows)==153
    historical_gate=read(CAP/'fixture-registration.json');save(CAP/'fixture_history01/fixture-registration.json',historical_gate)
    source_files={}
    for row in rows:
        raw=read(ROOT/row['origin']);assert sha(raw)==row['sha256'] and len(raw)==row['bytes']
        target=CAP/row['target']
        if target.exists():
            previous=read(target)
            if previous!=raw:
                assert row['target'] in inventory['replaced_targets'];save(target,raw,replace=True)
        else:save(target,raw)
        assert sha(read(target))==row['sha256'];source_files[row['target']]=row['sha256']
    expected={'successor-allocation01.json':'84c6125302f5ce79cb4a6767443f03ef3bddbb3076a41c63115e80cf4b90457b',
        'cumulative-extension01.json':'3723a4030d581d8dbd9326e004bc6b42d60f4315af23832f0edc04b1e9d8834a',
        'cumulative-extension-review01.json':'6f9a01a049c21e998f00da30c137bbc7709083a1c15aece741de54e6e8aa357d'}
    for name,pin in expected.items():
        raw=read(HERE/name);assert sha(raw)==pin;target='fixture_budget/'+name;save(CAP/target,raw);source_files[target]=pin
    machine=json.loads(read(CAP/'fixture_budget/cumulative-extension-review01.json'));assert machine['decision']=='accepted' and machine['extension_sha256']==expected['cumulative-extension01.json']
    original=json.loads(read(FULL/'original-import-fixture-native-preparation-2026-10-03/original_inputs01.json'))
    for row in original['inputs']:assert sha(read(CAP/row['capsule_path']))==row['sha256']
    for name,pin in original['original_source_files'].items():assert sha(git('show',original['original_source']+':'+name))==pin['claim_sha256']
    anchor=commit('Freeze reviewed successor metadata and cleanup source',set(source_files)|{'fixture_history01/fixture-registration.json'}|{x['capsule_path'] for x in original['inputs']})
    runtime=json.loads(read(FULL/'original-import-fixture-native-preparation-2026-10-03/runtime01.json'))
    assert sys.executable==runtime['executable'] and sys.prefix==runtime['prefix'] and platform.python_version()==runtime['python']
    assert sha(Path(runtime['resolved_executable']).read_bytes())==runtime['executable_sha256']
    for row in runtime['distribution_records']:assert importlib.metadata.version(row['name'])==row['version'] and row['record'] is not None and sha(read(Path(row['record'])))==row['record_sha256']
    environment_reference=json.loads(read(OLD/'EXPECTED_RUNTIME_READBACK01.json'))
    environment=json.loads(read(ROOT/environment_reference['expected_environment_origin']))
    assert sha(read(ROOT/environment_reference['expected_environment_origin']))==environment_reference['expected_environment_sha256']
    tree=ast.parse(read(CAP/'tradingagents/research/onchain_replication/resources.py'))
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_native_owned_env')
    namespace={'Path':Path};exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-native-owned-env','exec'),namespace)
    native_environment=namespace['_native_owned_env'](CAP)
    spec=importlib.util.spec_from_file_location('successor_input_generator',CAP/'fixture_tools/generate_inputs01.py')
    generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)
    evidence=json.loads(read(FULL/'original-dictionary-bridge-investigation-2026-10-02/evidence01.json'))
    matching=json.loads(read(FULL.parent/'config/matching-stable.json'))
    package_sources={name:pin for name,pin in source_files.items() if name.startswith('tradingagents/')};assert len(package_sources)==142
    rendered={case:generator.inputs(case=case,capsule=str(CAP),source_anchor=anchor,source_files=package_sources,original_index=original,evidence=evidence,matching=matching,environment=environment) for case in ['success','second_target_publication_failure']}
    runtime_hashes={p.name:sha(read(p)) for p in (CAP/'tradingagents/research').glob('*.py')}
    refs={'extension':{'path':'fixture_budget/cumulative-extension01.json','sha256':expected['cumulative-extension01.json']},'review':{'path':'fixture_budget/cumulative-extension-review01.json','sha256':expected['cumulative-extension-review01.json']}}
    gate,charters=generator.registration(rendered=rendered,source_files=source_files,runtime_hashes=runtime_hashes,historical_gate=json.loads(historical_gate),budget_reference=refs)
    assert gate['experiments'][PARENT]==json.loads(original_claim)['experiment'] and gate['families']['import-engineering']==json.loads(original_claim)['family']
    files={}
    for item in rendered.values():
        for name,raw in item['files'].items():assert name not in files or files[name]==raw;files[name]=raw
    files.update(charters);files['fixture-registration.json']=encoded(gate)
    for name,raw in files.items():save(CAP/name,raw,replace=(CAP/name).exists())
    final=commit('Freeze cumulative3 fresh original-import successor gate',files)
    cases={}
    for case,item in rendered.items():
        identity='original-import-native-'+('success' if case=='success' else 'publication-failure')+'-20261003-02';experiment=gate['experiments'][identity]
        assert not (CAP/'research_runs'/identity).exists() and not (ROOT/'research_runs'/identity).exists()
        cases[case]={'identity':identity,'experiment':experiment,'targets':item['targets'],'job_resources':json.loads(item['files'][item['job_path']])['resources']}
    assert read(CAP/'research_runs'/PARENT/'claim.json')==original_claim and read(CAP/'research_runs'/PARENT/'failed.json')==original_terminal
    draft={'status':'prospective-NOT-released','remaining':['Independent exact composed-source registration runtime capsule baseline and cumulative-history release review','Actual external committed capsule/source recovery','Root release and fresh startup eligibility'],
        'program_id':gate['program_id'],'family':gate['families']['import-engineering'],'effective_attempt_budget':3,'historical_closed_attempts':1,
        'registration':'fixture-registration.json','registration_sha256':sha(files['fixture-registration.json']),'capsule_root':str(CAP),'capsule_commit':final,
        'source_anchor':anchor,'source_files':source_files,'source_inventory_sha256':sha(inv),'source_reviews':{k:pin for k,(path,pin) in reviews.items()},
        'runtime':runtime,'native_environment':native_environment,'cases':cases,'cumulative_extension_reference':refs,
        'qualification':'Distinct prepared genuine capsule carrying byte-exact failed engineering history and original Git source; no new admission/claim/job/release. Budget3 engineering only, paper36/64 unchanged. Parser03 suite withheld and27refusals remain separate; no scientific representation/fullgraph capacity/financialfit inference.'}
    save(HERE/'release-draft01.json',encoded(draft))
    receipt={'schema_version':1,'status':'fresh_successor_source_input_gate_prepared_not_released','source_anchor':anchor,'capsule_commit':final,
        'source_count':len(source_files),'package_count':142,'registration_sha256':draft['registration_sha256'],'generated_files':len(files),'generated_bytes':sum(map(len,files.values())),
        'historical_claims':1,'new_claims':0,'budget_extension_sha256':expected['cumulative-extension01.json'],'budget_review_sha256':expected['cumulative-extension-review01.json'],
        'release_draft_sha256':sha(read(HERE/'release-draft01.json')),'prepared_utc':datetime.now(timezone.utc).isoformat(),'numerical_imports':False,'historical_replay':False}
    save(HERE/'ASSEMBLY_SUCCESSOR01.json',encoded(receipt));print(json.dumps(receipt,sort_keys=True))
if __name__=='__main__':main()
