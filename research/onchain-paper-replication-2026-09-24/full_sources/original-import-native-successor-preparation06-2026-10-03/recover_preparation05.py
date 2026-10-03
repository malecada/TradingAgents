"""Recover committed preparation and owned capsule from remote; never replay."""
import hashlib,json,os,shutil,stat,subprocess,sys,tarfile,time
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.cwd();HERE=Path(__file__).resolve().parent
COMMIT=sys.argv[1];assert len(COMMIT)==40 and all(c in '0123456789abcdef' for c in COMMIT)
BRANCH='research/onchain-paper-replication-2026-09-24'
def digest(raw):return hashlib.sha256(raw).hexdigest()
def call(args,cwd=ROOT):
    result=subprocess.run(['git',*args],cwd=cwd,capture_output=True,timeout=60)
    if result.returncode or max(len(result.stdout),len(result.stderr))>4*1024**2:raise RuntimeError('bounded capsule recovery Git command failed')
    return result.stdout

def main():
    started=time.monotonic();assert shutil.disk_usage(ROOT).free>=10*1024**3
    assert call(['ls-remote','origin','refs/heads/'+BRANCH]).decode().split()[0]==COMMIT
    names=call(['ls-tree','-r','--name-only',COMMIT,'--',str(HERE.relative_to(ROOT))]).decode().splitlines();assert names and all(Path(name).parent==HERE.relative_to(ROOT) for name in names)
    index_name=str(HERE.parent.relative_to(ROOT)/'original-import-fixture-native-preparation-2026-10-03/original_inputs01.json')
    names=sorted(set(names)|{index_name});pins={name:digest(call(['show',COMMIT+':'+name])) for name in names}
    out=HERE/'preparation-recovery01';out.mkdir(mode=0o700);repo=out/'repository.git'
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
    metadata=json.loads(selected['CAPSULE_PREPARATION01.json']);draft=json.loads(selected['release-draft01.json'])
    archive=out/'capsule-source-input-gate01.tar.gz'
    with archive.open('xb') as stream:stream.write(selected[archive.name]);stream.flush();os.fsync(stream.fileno())
    assert digest(archive.read_bytes())==metadata['archive_sha256']
    members={('capsule04'+('' if row['path']=='.' else '/'+row['path'])):row for row in metadata['members']}
    restored=out/'recovered-capsule04';seen=set();files=directories=total=0
    with tarfile.open(archive,'r|gz') as source:
        for member in source:
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
    assert call(['rev-parse','HEAD'],restored).decode().strip()==draft['capsule_commit']==metadata['capsule_head']
    for name,pin in draft['source_files'].items():
        raw=(restored/name).read_bytes();assert digest(raw)==pin and call(['show',draft['capsule_commit']+':'+name],restored)==raw
        assert call(['show',draft['source_anchor']+':'+name],restored)==raw
    assert digest((restored/draft['registration']).read_bytes())==draft['registration_sha256']
    original=json.loads(selected['original_inputs01.json'])
    for row in original['inputs']:assert digest((restored/row['capsule_path']).read_bytes())==row['sha256']
    for name,pin in original['original_source_files'].items():assert digest(call(['show',original['original_source']+':'+name],restored))==pin['claim_sha256']
    historic=[('original-import-native-success-20261003-01','f475dd6c04d7dfc5e9d94bba30b5d3e686d1b71b5f5394dfa1aa0b174797f61e','09206641f5ce569716bbf61246ecc85c20daa3ed40bf7f82427e4772198881c0',2),
        ('original-import-native-success-20261003-02','56d653890440a57896a98e87ed641f9dcfd74fca8375b3491e804fd2f5432688','6f088e8cc3252db4ca91ee0b37323793ce53d822e68a2e2ac0c505cea29f1747',3),
        ('original-import-native-success-20261003-03','7e35261724e6bf2d58ca484a2ef39606d7a586313dca5fe7f0c06fe6b8ef88ef','e0fb5527f662461300dfa153bed8a155661c32f0e98e43690b512c5019259351',4)]
    historical=[]
    for identity,claimpin,terminalpin,ceiling in historic:
        prior=restored/'research_runs'/identity
        assert digest((prior/'claim.json').read_bytes())==claimpin
        assert digest((prior/'failed.json').read_bytes())==terminalpin
        claim=json.loads((prior/'claim.json').read_bytes());terminal=json.loads((prior/'failed.json').read_bytes())
        assert terminal['claim_sha256']==claimpin and claim['effective_attempt_budget']==ceiling
        assert not (prior/'complete.json').exists()
        outputs={p.name:digest(p.read_bytes()) for p in (prior/'outputs').iterdir()}
        assert outputs==terminal['output_sha256'] and len(outputs)==(2 if identity.endswith('-03') else 4)
        if identity.endswith('-03'):
            assert set(outputs)=={'resource-binding.json','resource-journal.json'}
            assert all(not (prior/'outputs'/name).exists() for name in ['cell-ledger.json','resource-summary.json'])
            base=restored/'research_artifacts/onchain-paper-replication-2026-09-24'
            cells=[]
            for name,status,pin in [('import-target-01','failed','373e1887802d98aca21e8171d38251a9129a16a5aa6582d8c7e19d7ab628b6ba'),('import-target-02','unavailable','cd6757ffc170cac7f4b9ee01df4df05d4d7365338c2881922ad0c064d26fe6dc')]:
                raw=(base/'sources'/identity/(name+'.json')).read_bytes();assert digest(raw)==pin;cell=json.loads(raw);assert cell['status']==status;cells.append(cell)
            post=(base/'runs'/identity/'postmortem-cells.json').read_bytes();assert digest(post)=='8dc88aae95d2647f35d341503f5d700f2b25f4696733f9a06ed66e570bd14779' and json.loads(post)==cells
        registration=call(['show',claim['source']+':'+claim['registration']],restored)
        assert digest(registration)==claim['registration_sha256']
        registered=json.loads(registration)['experiments'][identity]
        assert registered==claim['experiment']
        for name,pin in claim['experiment']['source_files'].items():assert digest(call(['show',claim['source']+':'+name],restored))==pin
        historical.append({'identity':identity,'claim_sha256':claimpin,'terminal_sha256':terminalpin,'output_sha256':outputs,'source':claim['source'],'source_bodies':len(claim['experiment']['source_files']),'effective_attempt_budget':ceiling})
    for suffix in ('01','02','03','04'):
        assert not (restored/'research_runs'/('original-import-native-publication-failure-20261003-'+suffix)).exists()
    assert not (restored/'research_runs/original-import-native-success-20261003-04').exists()
    assert not (restored/'fixture_outer/original-import-native-success-20261003-04').exists()
    result={'schema_version':1,'status':'fresh_remote_capsule_preparation_recovery_verified','remote_commit':COMMIT,
        'selected_blobs':blobs,'body_count':len(blobs),'capsule_head':draft['capsule_commit'],'source_anchor':draft['source_anchor'],
        'member_count':len(seen),'historical_failed_claims':3,'historical_claims':historical,'new_claims':0,'capsule_files':files,'capsule_directories':directories,'capsule_logical_bytes':total,
        'current_source_bodies':len(draft['source_files']),'original_source_paths':len(original['original_source_files']),
        'original_json_inputs':len(original['inputs']),'archive_sha256':metadata['archive_sha256'],
        'verified_utc':datetime.now(timezone.utc).isoformat(),
        'qualification':'Fresh actual remote partial bare fetch; complete preparation archive names/modes/bytes/hashes recovered into a separate owned tree. Actual recovered Git HEAD, all162 current source bodies and162 anchor joins including142 package and9 old/new budget documents, original26commit:path bodies/11JSON, exact gate, ALL THREE actual failed historical claims with their153/156/159 Git source bodies/registrations/terminals, original4/4/2outputs, missing03workerledger+summary and original FAILED/UNAVAILABLE cells verified. All new04 identities remain unclaimed and unreserved; unused failure01/02/03 remain unlaunched. All older failed/withheld preparations are preserved. Selected remote blobs comprise this exact preparation directory and original input index; outside author-origin blobs are not claimed separately recovered. No shared installed runtime/empirical-store recovery, admission/claim/job, numerical import or replay. Recovered paths do not authorize running the original absolute-workspace gate elsewhere.'}
    with (HERE/'REMOTE_PREPARATION_RECOVERY01.json').open('x') as stream:json.dump(result,stream,indent=2,sort_keys=True);stream.write('\n')
    print(json.dumps({k:result[k] for k in ['status','remote_commit','body_count','capsule_files','capsule_directories','capsule_logical_bytes']}))

if __name__=='__main__':main()
