"""One-use source/input/gate assembly only; never launches or makes a claim."""
import argparse,ast,hashlib,importlib.metadata,importlib.util,json,os,platform,stat,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
FULL=HERE.parent
CAPSULE=HERE/'capsule01'
INVENTORY=FULL/'original-import-fixture-native-preparation03-2026-10-03/source_inventory03.json'
EXPECTED_INVENTORY='9d701d871f72e5fd8f8213c39c395968147ebb2a5526b7ef4e56fee51eadb831'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def require(condition,message):
    if not condition:raise ValueError(message)
def read(path):
    info=path.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_size<=4*1024**2,'source/input regular bounded body required')
    return path.read_bytes()
def save(path,raw):
    require(len(raw)<=4*1024**2,'one file limit exceeded')
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
def encoded(value):return (json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
def git(*args):
    value=subprocess.run(['git',*args],cwd=CAPSULE,capture_output=True,timeout=60)
    require(value.returncode==0 and max(len(value.stdout),len(value.stderr))<=4*1024**2,'bounded capsule Git command failed')
    return value.stdout
def commit(message,paths):
    git('add','-f','--',*sorted(paths))
    git('-c','user.name=Research capsule','-c','user.email=research-capsule@localhost','commit','-m',message)
    return git('rev-parse','HEAD').decode().strip()

def main(review_hash):
    require(Path.cwd()==ROOT,'active engineering checkout required')
    require(not (HERE/'ASSEMBLY_PRIMARY01.json').exists(),'assembly already has a durable identity')
    require(not (CAPSULE/'fixture-registration.json').exists(),'existing final gate cannot be overwritten')
    require(not (CAPSULE/'fixture_outer').exists(),'reserved outer capsule cannot be changed')
    require(not (CAPSULE/'research_runs').exists(),'claimed capsule cannot be changed')
    review=INVENTORY.parent/'REVIEW_NATIVE_PREPARATION03.md'
    review_raw=read(review);require(sha(review_raw)==review_hash,'review body differs')
    require(sha(read(INVENTORY))==EXPECTED_INVENTORY,'frozen source inventory differs')
    inventory=json.loads(read(INVENTORY));rows=inventory['source_inventory']
    require(len(rows)==153 and inventory['composed_package_count']==142,'complete source closure differs')
    # Root separately interprets the independent disposition before invoking this builder.
    for row in rows:
        raw=read(ROOT/row['origin']);require(sha(raw)==row['sha256'] and len(raw)==row['bytes'],'frozen source body differs')
        target=CAPSULE/row['target'];target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():
            previous=read(target)
            if previous!=raw:
                require(row['target'] in {'tradingagents/research/onchain_replication/resources.py','fixture_tools/outer_controller01.py','fixture_tools/raw_receipts01.py'},'unexpected old-overlay change')
                # No job/claim/reservation exists; all predecessor bodies remain in frozen02.
                with target.open('wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        else:save(target,raw)
        require(sha(read(target))==row['sha256'],'installed source readback differs')
    original_index=json.loads(read(FULL/'original-import-fixture-native-preparation-2026-10-03/original_inputs01.json'))
    for row in original_index['inputs']:
        require(sha(read(CAPSULE/row['capsule_path']))==row['sha256'],'original input differs')
    original_commit=original_index['original_source']
    for name,info in original_index['original_source_files'].items():
        expected=info['claim_sha256'] if isinstance(info,dict) else info
        require(sha(git('show',original_commit+':'+name))==expected,'original imported Git source differs')
    source_files={row['target']:row['sha256'] for row in rows}
    anchor=commit('Freeze reviewed original-import native source',set(source_files)|{row['capsule_path'] for row in original_index['inputs']})
    runtime=json.loads(read(FULL/'original-import-fixture-native-preparation-2026-10-03/runtime01.json'))
    require(sys.executable==runtime['executable'] and sys.prefix==runtime['prefix'] and platform.python_version()==runtime['python'],'shared runtime differs')
    require(sha(Path(runtime['resolved_executable']).read_bytes())==runtime['executable_sha256'],'interpreter body differs')
    for row in runtime['distribution_records']:
        require(importlib.metadata.version(row['name'])==row['version'] and row['record'] is not None and sha(Path(row['record']).read_bytes())==row['record_sha256'],'runtime RECORD differs')
    expected=json.loads(read(HERE/'EXPECTED_RUNTIME_READBACK01.json'))
    environment=json.loads(read(ROOT/expected['expected_environment_origin']))
    require(sha(read(ROOT/expected['expected_environment_origin']))==expected['expected_environment_sha256'],'expected guarded environment differs')
    resource_source=CAPSULE/'tradingagents/research/onchain_replication/resources.py'
    tree=ast.parse(read(resource_source));node=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='_native_owned_env')
    namespace={'Path':Path};exec(compile(ast.Module(body=[node],type_ignores=[]),str(resource_source),'exec'),namespace)
    native_environment=namespace['_native_owned_env'](CAPSULE)
    spec=importlib.util.spec_from_file_location('selected_input_generator',CAPSULE/'fixture_tools/generate_inputs01.py')
    generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)
    evidence=json.loads(read(FULL/'original-dictionary-bridge-investigation-2026-10-02/evidence01.json'))
    matching=json.loads(read(FULL.parent/'config/matching-stable.json'))
    package_sources={name:pin for name,pin in source_files.items() if name.startswith('tradingagents/')}
    runtime_hashes={p.name:sha(read(p)) for p in (CAPSULE/'tradingagents/research').glob('*.py')}
    rendered={case:generator.inputs(case=case,capsule=str(CAPSULE),source_anchor=anchor,source_files=package_sources,original_index=original_index,evidence=evidence,matching=matching,environment=environment) for case in ('success','second_target_publication_failure')}
    files={}
    for item in rendered.values():
        for name,raw in item['files'].items():
            require(name not in files or files[name]==raw,'shared synthetic member differs');files[name]=raw
    gate,charters=generator.registration(rendered=rendered,source_files=source_files,runtime_hashes=runtime_hashes)
    files.update(charters);files['fixture-registration.json']=encoded(gate)
    for name,raw in files.items():save(CAPSULE/name,raw)
    final=commit('Freeze two-claim original-import engineering gate',files)
    cases={}
    for case,item in rendered.items():
        identity='original-import-native-'+('success' if case=='success' else 'publication-failure')+'-20261003-01'
        experiment=gate['experiments'][identity]
        require(not (ROOT/'research_runs'/identity).exists(),'identity already claimed in original checkout')
        cases[case]={'identity':identity,'experiment':experiment,'targets':item['targets'],'job_resources':json.loads(item['files'][item['job_path']])['resources']}
    draft={'status':'prospective-NOT-released','remaining':['Independent exact rendered registration/source/runtime/capsule/baseline review','Root final release and fresh native startup eligibility'],
        'program_id':gate['program_id'],'family':gate['families']['import-engineering'],'registration':'fixture-registration.json','registration_sha256':sha(files['fixture-registration.json']),
        'capsule_root':str(CAPSULE),'capsule_commit':final,'source_anchor':anchor,'source_files':source_files,'source_inventory_sha256':EXPECTED_INVENTORY,
        'source_review_sha256':review_hash,'runtime':runtime,'native_environment':native_environment,'cases':cases,
        'qualification':'Prepared committed design only; no admission/claim/numerical job/release. Scientific representation and all27refusals remain separate.'}
    save(HERE/'release-draft01.json',encoded(draft))
    receipt={'schema_version':1,'status':'source_input_gate_capsule_prepared_not_released','source_anchor':anchor,'capsule_commit':final,
        'source_count':len(source_files),'package_count':len(package_sources),'registration_sha256':draft['registration_sha256'],
        'source_review_sha256':review_hash,'generated_file_count':len(files),'generated_bytes':sum(map(len,files.values())),
        'prepared_utc':datetime.now(timezone.utc).isoformat(),'release_draft_sha256':sha(read(HERE/'release-draft01.json')),
        'original_claim':original_index['original_claim'],'historical_replay':False,'claims':0,'numerical_imports':False}
    save(HERE/'ASSEMBLY_PRIMARY01.json',encoded(receipt));print(json.dumps(receipt,sort_keys=True))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--review-sha256',required=True);args=parser.parse_args();main(args.review_sha256)
