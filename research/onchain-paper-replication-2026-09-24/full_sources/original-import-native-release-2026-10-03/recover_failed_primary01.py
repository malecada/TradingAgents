"""Freshly recover the actual failed capsule from the remote without replay."""
import hashlib,json,os,shutil,subprocess,tarfile,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.cwd();HERE=Path(__file__).resolve().parent
COMMIT='0325504b48fe0270734e20e1d0b67a1ffe738738'
BRANCH='research/onchain-paper-replication-2026-09-24'
IDENTITY='original-import-native-success-20261003-01'
def digest(raw):return hashlib.sha256(raw).hexdigest()
def call(args,cwd=ROOT):
    result=subprocess.run(['git',*args],cwd=cwd,capture_output=True,timeout=60)
    if result.returncode or max(len(result.stdout),len(result.stderr))>4*1024**2:raise RuntimeError('bounded failed capsule recovery Git command failed')
    return result.stdout
def read(path):return json.loads(path.read_bytes())
def main():
    started=time.monotonic();assert shutil.disk_usage(ROOT).free>=10*1024**3
    assert call(['ls-remote','origin','refs/heads/'+BRANCH]).decode().split()[0]==COMMIT
    names=call(['diff-tree','--no-commit-id','--name-only','-r',COMMIT]).decode().splitlines()
    index_name=str(HERE.parent.relative_to(ROOT)/'original-import-fixture-native-preparation-2026-10-03/original_inputs01.json')
    names=sorted(set(names)|{index_name,*[str(HERE.relative_to(ROOT)/n) for n in ['release01.json','release-draft01.json']]})
    pins={name:digest(call(['show',COMMIT+':'+name])) for name in names}
    out=HERE/'failure-recovery01';out.mkdir(mode=0o700);repo=out/'repository.git'
    call(['init','--bare',str(repo)]);call(['remote','add','origin',call(['remote','get-url','origin']).decode().strip()],repo)
    call(['config','remote.origin.promisor','true'],repo);call(['config','remote.origin.partialclonefilter','blob:none'],repo)
    call(['fetch','--depth=1','--filter=blob:none','origin',COMMIT],repo)
    assert call(['rev-parse','FETCH_HEAD'],repo).decode().strip()==COMMIT
    blobs=[];selected={}
    for name,pin in pins.items():
        assert time.monotonic()-started<600
        raw=call(['show',COMMIT+':'+name],repo);assert digest(raw)==pin
        blobs.append({'path':name,'bytes':len(raw),'sha256':pin})
        if name.startswith(str(HERE.relative_to(ROOT))) or name==index_name:selected[Path(name).name]=raw
    metadata=json.loads(selected['RETAINED_PRIMARY01.json']);release=json.loads(selected['release01.json']);execution=json.loads(selected['EXECUTION_PRIMARY01.json'])
    archive=out/'retained-primary01.tar.gz'
    with archive.open('xb') as stream:stream.write(selected[archive.name]);stream.flush();os.fsync(stream.fileno())
    assert digest(archive.read_bytes())==metadata['archive_sha256']==execution.get('archive_sha256',metadata['archive_sha256'])
    assert digest(selected['RETAINED_PRIMARY01.json'])==execution['retention_sha256']
    members={('capsule01'+('' if row['path']=='.' else '/'+row['path'])):row for row in metadata['members']}
    restored=out/'recovered-failed-capsule01';seen=set();files=directories=total=0
    with tarfile.open(archive,'r|gz') as source:
        for member in source:
            assert time.monotonic()-started<600
            assert member.name in members and member.name not in seen;seen.add(member.name);row=members[member.name]
            assert member.mode==row['mode'] and not member.issym() and not member.islnk()
            relative=Path(row['path']);assert not relative.is_absolute() and '..' not in relative.parts
            path=restored/relative
            if row['kind']=='directory':
                assert member.isdir();path.mkdir();os.chmod(path,row['mode']);directories+=1
            else:
                assert member.isfile() and member.size==row['bytes']<=4*1024**2
                source_file=source.extractfile(member);assert source_file is not None
                with source_file:raw=source_file.read(member.size+1)
                assert len(raw)==member.size and digest(raw)==row['sha256']
                with path.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
                os.chmod(path,row['mode']);files+=1;total+=len(raw)
    assert seen==set(members) and (files,directories,total)==(metadata['files'],metadata['directories'],metadata['logical_bytes'])
    assert call(['rev-parse','HEAD'],restored).decode().strip()==release['capsule_commit']==execution['source_commit']
    for name,pin in release['source_files'].items():
        raw=(restored/name).read_bytes();assert digest(raw)==pin and call(['show',release['capsule_commit']+':'+name],restored)==raw
        if name.startswith('tradingagents/'):assert call(['show',release['source_anchor']+':'+name],restored)==raw
    assert digest((restored/release['registration']).read_bytes())==release['registration_sha256']
    original=json.loads(selected['original_inputs01.json'])
    for row in original['inputs']:assert digest((restored/row['capsule_path']).read_bytes())==row['sha256']
    for name,pin in original['original_source_files'].items():assert digest(call(['show',original['original_source']+':'+name],restored))==pin['claim_sha256']
    run=restored/'research_runs'/IDENTITY;claim=read(run/'claim.json');terminal=read(run/'failed.json')
    assert digest((run/'claim.json').read_bytes())==execution['claim_sha256']==terminal['claim_sha256']
    assert claim['source']==release['capsule_commit'] and claim['registration_sha256']==release['registration_sha256']
    assert terminal['reason']==execution['parent_failure_reason']=='ValueError: compact metadata bound' and not (run/'complete.json').exists()
    outputs={p.name:digest(p.read_bytes()) for p in (run/'outputs').iterdir()};assert outputs==terminal['output_sha256'] and len(outputs)==4
    assert read(run/'outputs/cell-ledger.json')==execution['cells'] and [r['status'] for r in execution['cells']]==['failed','unavailable']
    roots=list((restored/'research_artifacts/onchain_representations').glob('*/'+IDENTITY));assert len(roots)==1
    journal=roots[0];assert (journal/'failed.json').exists() and not (journal/'complete.json').exists()
    assert digest((journal/'compact/dictionary-import/import-complete.json').read_bytes())==execution['original_dictionary_import_complete_sha256']
    assert not list(journal.glob('compact/mcm-*')) and not (restored/'research_artifacts/onchain_compact_outputs').exists()
    outer=restored/'fixture_outer'/IDENTITY
    assert read(outer/'terminal.json')['proof'] is None and read(outer/'cleanup.json')['unresolved_pid_absence'] is True
    assert execution['repeat_allowed'] is False and execution['completed_mcm_targets']==execution['scalar_reference_comparisons']==0
    result={'schema_version':1,'status':'fresh_remote_failed_primary_recovery_verified','remote_commit':COMMIT,
        'selected_blobs':blobs,'body_count':len(blobs),'capsule_head':release['capsule_commit'],'source_anchor':release['source_anchor'],
        'capsule_files':files,'capsule_directories':directories,'capsule_logical_bytes':total,'member_count':len(seen),
        'current_source_bodies':len(release['source_files']),'original_source_paths':len(original['original_source_files']),
        'original_json_inputs':len(original['inputs']),'archive_sha256':metadata['archive_sha256'],'claim_sha256':execution['claim_sha256'],
        'actual_disposition':'failed','completed_mcm_targets':0,'scalar_reference_comparisons':0,'output_hashes':outputs,
        'verified_utc':datetime.now(timezone.utc).isoformat(),
        'qualification':'Fresh actual remote partial bare fetch and complete failed owned archive recovered into a separate tree. All names/modes/bytes/hashes, recovered Git HEAD,153 source bodies/142 anchor joins,26 original commit:path bodies/11JSON, gate, actual failed claim/4outputs/cells/import completion and unchanged unresolved outer cleanup verified. No installed shared runtime/empirical-store recovery, PID absence inference from restored files, numerical import, admission, replay or new release.'}
    with (HERE/'REMOTE_FAILED_PRIMARY_RECOVERY01.json').open('x') as stream:json.dump(result,stream,indent=2,sort_keys=True);stream.write('\n')
    print(json.dumps({k:result[k] for k in ['status','remote_commit','body_count','member_count','capsule_files','capsule_directories','capsule_logical_bytes','actual_disposition']}))
if __name__=='__main__':main()
