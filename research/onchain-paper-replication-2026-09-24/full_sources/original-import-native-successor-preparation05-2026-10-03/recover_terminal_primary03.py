"""Freshly recover the actual failed capsule from the remote without replay."""
import hashlib,json,os,shutil,subprocess,sys,tarfile,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path.cwd();HERE=Path(__file__).resolve().parent
COMMIT=sys.argv[1];assert len(COMMIT)==40 and all(c in '0123456789abcdef' for c in COMMIT)
BRANCH='research/onchain-paper-replication-2026-09-24'
IDENTITY='original-import-native-success-20261003-03'
def digest(raw):return hashlib.sha256(raw).hexdigest()
def call(args,cwd=ROOT):
    result=subprocess.run(['git',*args],cwd=cwd,capture_output=True,timeout=60)
    if result.returncode or max(len(result.stdout),len(result.stderr))>4*1024**2:raise RuntimeError('bounded failed capsule recovery Git command failed')
    return result.stdout
def read(path):return json.loads(path.read_bytes())
def main():
    started=time.monotonic();assert shutil.disk_usage(ROOT).free>=10*1024**3
    assert call(['ls-remote','origin','refs/heads/'+BRANCH]).decode().split()[0]==COMMIT
    names=call(['ls-tree','-r','--name-only',COMMIT,'--',str(HERE.relative_to(ROOT))]).decode().splitlines();assert names and all(Path(n).parent==HERE.relative_to(ROOT) for n in names)
    index_name=str(HERE.parent.relative_to(ROOT)/'original-import-fixture-native-preparation-2026-10-03/original_inputs01.json')
    names=sorted(set(names)|{index_name,*[str(HERE.relative_to(ROOT)/n) for n in ['release01.json','release-draft01.json']]})
    pins={name:digest(call(['show',COMMIT+':'+name])) for name in names}
    out=HERE/'outcome-recovery01';out.mkdir(mode=0o700);repo=out/'repository.git'
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
    members={('capsule03'+('' if row['path']=='.' else '/'+row['path'])):row for row in metadata['members']}
    restored=out/'recovered-terminal-capsule03';seen=set();files=directories=total=0
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
        assert call(['show',release['source_anchor']+':'+name],restored)==raw
    assert digest((restored/release['registration']).read_bytes())==release['registration_sha256']
    original=json.loads(selected['original_inputs01.json'])
    for row in original['inputs']:assert digest((restored/row['capsule_path']).read_bytes())==row['sha256']
    for name,pin in original['original_source_files'].items():assert digest(call(['show',original['original_source']+':'+name],restored))==pin['claim_sha256']
    run=restored/'research_runs'/IDENTITY;claim=read(run/'claim.json');status=execution['lifecycle_status'];assert status in ('complete','failed');terminal=read(run/(status+'.json'))
    assert digest((run/'claim.json').read_bytes())==execution['claim_sha256']==terminal['claim_sha256']
    assert claim['source']==release['capsule_commit'] and claim['registration_sha256']==release['registration_sha256']
    assert terminal.get('reason')==execution['parent_failure_reason']
    assert terminal['status']==status and not (run/('failed.json' if status=='complete' else 'complete.json')).exists()
    assert digest((run/(status+'.json')).read_bytes())==execution['terminal_sha256']
    assert claim['effective_attempt_budget']==4
    historical=[]
    for identity,cp,tp,ceiling in [('original-import-native-success-20261003-01','f475dd6c04d7dfc5e9d94bba30b5d3e686d1b71b5f5394dfa1aa0b174797f61e','09206641f5ce569716bbf61246ecc85c20daa3ed40bf7f82427e4772198881c0',2),('original-import-native-success-20261003-02','56d653890440a57896a98e87ed641f9dcfd74fca8375b3491e804fd2f5432688','6f088e8cc3252db4ca91ee0b37323793ce53d822e68a2e2ac0c505cea29f1747',3)]:
        oldrun=restored/'research_runs'/identity;oldclaim=read(oldrun/'claim.json');oldterminal=read(oldrun/'failed.json')
        assert digest((oldrun/'claim.json').read_bytes())==cp and digest((oldrun/'failed.json').read_bytes())==tp
        assert oldterminal['claim_sha256']==cp and oldclaim['effective_attempt_budget']==ceiling and not (oldrun/'complete.json').exists()
        oldoutputs={f.name:digest(f.read_bytes()) for f in (oldrun/'outputs').iterdir()}
        assert len(oldoutputs)==4 and oldoutputs==oldterminal['output_sha256']
        originalregistration=call(['show',oldclaim['source']+':'+oldclaim['registration']],restored)
        assert digest(originalregistration)==oldclaim['registration_sha256'] and json.loads(originalregistration)['experiments'][identity]==oldclaim['experiment']
        for name,pin in oldclaim['experiment']['source_files'].items():assert digest(call(['show',oldclaim['source']+':'+name],restored))==pin
        historical.append({'identity':identity,'claim_sha256':cp,'terminal_sha256':tp,'source':oldclaim['source'],'source_bodies':len(oldclaim['experiment']['source_files']),'outputs':oldoutputs})
    outputs={f.name:digest(f.read_bytes()) for f in (run/'outputs').iterdir()};assert outputs==terminal['output_sha256'] and len(outputs)==4
    assert read(run/'outputs/cell-ledger.json')==execution['cells']
    roots=list((restored/'research_artifacts/onchain_representations').glob('*/'+IDENTITY));assert len(roots)==1
    journal=roots[0];assert (journal/(status+'.json')).exists() and not (journal/('failed.json' if status=='complete' else 'complete.json')).exists()
    imported=journal/'compact/dictionary-import/import-complete.json'
    assert (digest(imported.read_bytes()) if imported.exists() else None)==execution['original_dictionary_import_complete_sha256']
    stages=list(journal.glob('compact/mcm-*'));completed=[f for f in stages if (f/'stage-complete.json').exists()]
    assert len(stages)==execution['retained_mcm_stage_directories'] and len(completed)==execution['complete_mcm_stage_markers']
    outer=restored/'fixture_outer'/IDENTITY
    assert read(outer/'terminal.json')['status']==execution['outer_terminal_status']
    assert read(outer/'cleanup.json')==execution['original_outer_cleanup']
    assert execution['repeat_allowed'] is False and execution['source_freeze_ended'] is True
    result={'schema_version':1,'status':'fresh_remote_terminal_primary_recovery_verified','remote_commit':COMMIT,
        'selected_blobs':blobs,'body_count':len(blobs),'capsule_head':release['capsule_commit'],'source_anchor':release['source_anchor'],
        'capsule_files':files,'capsule_directories':directories,'capsule_logical_bytes':total,'member_count':len(seen),
        'current_source_bodies':len(release['source_files']),'original_source_paths':len(original['original_source_files']),
        'original_json_inputs':len(original['inputs']),'archive_sha256':metadata['archive_sha256'],'claim_sha256':execution['claim_sha256'],
        'actual_disposition':status,'completed_mcm_targets':len(completed),'historical_failed_claims':historical,'output_hashes':outputs,
        'verified_utc':datetime.now(timezone.utc).isoformat(),
        'qualification':'Fresh actual remote partial bare fetch and complete terminal owned archive into a separate tree. Exact names/modes/bytes/hashes, recovered Git HEAD, all159 current+anchor bodies, original26commit:path11JSON, exact gate, both permanently failed original01/02 claims and historical153/156source/registrations/fouroutputs, current03claim/terminal/fouroutputs/cells/import and actual MCM stage dispositions, original outer terminal/cleanup verified. Actual complete/failed/unavailable outcome is retained without relabeling. Restored files do not establish live PID absence or recreate authority. Shared installed runtime/empirical stores and other unqueried source-origin Git objects are excluded. No numerical import, admission, job or replay; no scientific representation_complete/full-sized capacity/financial fit/paper agreement is inferred.'}
    with (HERE/'REMOTE_PRIMARY_RECOVERY01.json').open('x') as stream:json.dump(result,stream,indent=2,sort_keys=True);stream.write('\n')
    print(json.dumps({k:result[k] for k in ['status','remote_commit','body_count','member_count','capsule_files','capsule_directories','capsule_logical_bytes','actual_disposition']}))
if __name__=='__main__':main()
