"""Copy freshly recovered failed history into a distinct unlaunched capsule."""
import hashlib,importlib.util,json,os,shutil,stat,subprocess,tarfile,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;FULL=HERE.parent;CAP=HERE/'capsule02'
REL=FULL/'original-import-native-release-2026-10-03'
IDENTITY='original-import-native-success-20261003-01'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
    assert shutil.disk_usage(HERE).free>=10*1024**3 and not CAP.exists()
    recovery=REL/'REMOTE_FAILED_PRIMARY_RECOVERY01.json';review=REL/'REVIEW_FAILED_PRIMARY_RECOVERY01.md'
    assert sha(recovery.read_bytes())=='ece5bfc599a351d1caf077d73296fac880c2a513548064f8ef81354be4205830'
    assert sha(review.read_bytes())=='b837d027d8449c7b8d05802932004678c485fdf6808677f505d8270e724b43b2'
    receipt=json.loads(recovery.read_bytes());assert receipt['status']=='fresh_remote_failed_primary_recovery_verified'
    archive=REL/'failure-recovery01/retained-primary01.tar.gz';inventory=json.loads((REL/'RETAINED_PRIMARY01.json').read_bytes())
    assert sha(archive.read_bytes())==receipt['archive_sha256']==inventory['archive_sha256']
    rows={('capsule01'+('' if row['path']=='.' else '/'+row['path'])):row for row in inventory['members']}
    seen=set();started=time.monotonic()
    with tarfile.open(archive,'r|gz') as source:
        for member in source:
            assert time.monotonic()-started<60 and member.name in rows and member.name not in seen
            seen.add(member.name);row=rows[member.name];relative=Path(row['path'])
            assert not relative.is_absolute() and '..' not in relative.parts and not member.issym() and not member.islnk() and member.mode==row['mode']
            path=CAP/relative
            if row['kind']=='directory':assert member.isdir();path.mkdir();os.chmod(path,row['mode'])
            else:
                assert member.isfile() and member.size==row['bytes']<=4*1024**2
                with source.extractfile(member) as stream:raw=stream.read(member.size+1)
                assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
                with path.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
                os.chmod(path,row['mode'])
    assert seen==set(rows) and not (CAP/'.git/objects/info/alternates').exists()
    actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=CAP,text=True,timeout=10).strip()
    assert actual==receipt['capsule_head']=='529c7a3769fcfea28d3a617270b3025aebbce1f5'
    # Verify actual old claim against its genuine historical committed gate,
    # source and terminal. This loads only the real stdlib verification module.
    spec=importlib.util.spec_from_file_location('successor_historical_verify',CAP/'tradingagents/research/verify.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    claim=module.verify_claim(CAP/'research_runs'/IDENTITY)
    assert claim['family']==json.loads((HERE/'cumulative-extension01.json').read_bytes())['base_family']
    terminal=json.loads((CAP/'research_runs'/IDENTITY/'failed.json').read_bytes())
    assert terminal['claim_sha256']==receipt['claim_sha256'] and terminal['status']=='failed'
    assert sorted(p.name for p in (CAP/'research_runs').iterdir() if not p.name.startswith('.'))==[IDENTITY]
    assert not (CAP/'research_runs'/'original-import-native-success-20261003-02').exists()
    assert not (CAP/'research_runs'/'original-import-native-publication-failure-20261003-02').exists()
    sourcepin={row['path']:row['sha256'] for row in inventory['members'] if row['kind']=='file'}
    for name,pin in sourcepin.items():assert sha((CAP/name).read_bytes())==pin
    allocated=sum(path.lstat().st_blocks*512 for path in [CAP,*CAP.rglob('*')]);assert allocated<=128*1024**2
    result={'schema_version':1,'status':'distinct_owned_historical_capsule_staged_not_released','capsule_root':str(CAP.resolve()),
        'historical_head':actual,'fresh_remote_recovery_sha256':sha(recovery.read_bytes()),'independent_recovery_review_sha256':sha(review.read_bytes()),
        'retained_members':len(seen),'retained_files':inventory['files'],'retained_directories':inventory['directories'],'retained_logical_bytes':inventory['logical_bytes'],
        'new_baseline_allocated_bytes':allocated,'unchanged_historical_claim_sha256':sha((CAP/'research_runs'/IDENTITY/'claim.json').read_bytes()),
        'unchanged_historical_terminal_sha256':sha((CAP/'research_runs'/IDENTITY/'failed.json').read_bytes()),
        'historical_claims':1,'new_claims':0,'numerical_imports':False,
        'qualification':'A distinct owned archive copy preserves one genuine closed failed engineering claim and all original source/Git/raw evidence. Original and remotely recovered trees remain unchanged. Old absolute raw paths are provenance only; they are not authority in the new root. No source correction, new gate/admission/release/claim/job, replay or installed runtime copy yet.'}
    with (HERE/'STAGED_SUCCESSOR01.json').open('x') as stream:json.dump(result,stream,indent=2,sort_keys=True);stream.write('\n')
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
