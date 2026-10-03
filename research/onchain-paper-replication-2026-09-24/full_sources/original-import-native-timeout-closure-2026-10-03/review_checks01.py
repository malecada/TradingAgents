"""Read-only complete failed-tree, source, denominator and cleanup readback."""
import hashlib,json,os,re,stat,subprocess,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
PREP=HERE.with_name('original-import-native-successor-preparation05-2026-10-03')
CAP=PREP/'capsule03';ID='original-import-native-success-20261003-03'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
result=read(PREP/'EXECUTION_PRIMARY01.json');retained=read(PREP/'RETAINED_PRIMARY01.json');release=read(PREP/'release01.json')
assert sha((PREP/'RETAINED_PRIMARY01.json').read_bytes())==result['retention_sha256']
assert sha((PREP/'release01.json').read_bytes())==result['release_sha256']
rows={r['path']:r for r in retained['members']};assert len(rows)==939
actual={str(p.relative_to(CAP)) for p in [CAP,*CAP.rglob('*')]};assert actual==set(rows)
for name,row in rows.items():
    p=CAP/name;s=p.lstat();assert stat.S_IMODE(s.st_mode)==row['mode'] and s.st_blocks*512==row['allocated_bytes']
    assert p.resolve()==p and s.st_dev==CAP.stat().st_dev
    if row['kind']=='file':
        assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size==row['bytes'] and sha(p.read_bytes())==row['sha256']
    else:assert stat.S_ISDIR(s.st_mode)
archive=PREP/'retained-primary01.tar.gz'
assert archive.stat().st_size==retained['archive_bytes']==2618781
assert sha(archive.read_bytes())==retained['archive_sha256']=='4ef0b859c2529668f4a90965b0555005dc0e8099ea1249717cdcc7390e2544cd'
seen=set()
with tarfile.open(archive,'r:gz') as t:
    for m in t:
        n='.' if m.name=='capsule03' else m.name.removeprefix('capsule03/')
        assert n not in seen and n in rows and m.mode==rows[n]['mode'];seen.add(n)
        if rows[n]['kind']=='directory':assert m.isdir()
        else:
            assert m.isfile() and m.size==rows[n]['bytes']
            with t.extractfile(m) as f:assert sha(f.read())==rows[n]['sha256']
assert seen==set(rows)
assert sum(r['bytes'] for r in rows.values())==retained['logical_bytes']==6585516
assert sum(r['allocated_bytes'] for r in rows.values())==retained['allocated_bytes']==9453568
assert sum(r['kind']=='file' for r in rows.values())==665
assert sum(r['kind']=='directory' for r in rows.values())==274
env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0',GIT_OPTIONAL_LOCKS='0')
def git(*args):return subprocess.check_output(['git','-c','protocol.allow=never',*args],cwd=CAP,env=env)
assert git('rev-parse','HEAD').decode().strip()==result['source_commit']==release['capsule_commit']
assert len(release['source_files'])==159
for name,h in release['source_files'].items():
    b=(CAP/name).read_bytes();assert sha(b)==h and git('show',result['source_commit']+':'+name)==b
gate=(CAP/release['registration']).read_bytes();assert sha(gate)==release['registration_sha256'] and git('show',result['source_commit']+':'+release['registration'])==gate
run=CAP/'research_runs'/ID;claim=read(run/'claim.json');terminal=read(run/'failed.json')
assert sha((run/'claim.json').read_bytes())==result['claim_sha256']==terminal['claim_sha256']
assert sha((run/'failed.json').read_bytes())==result['terminal_sha256'] and not (run/'complete.json').exists()
assert claim['source']==result['source_commit'] and claim['registration_sha256']==release['registration_sha256']
outputs={p.name:sha(p.read_bytes()) for p in (run/'outputs').iterdir()}
assert outputs==terminal['output_sha256'] and set(outputs)=={'resource-binding.json','resource-journal.json'}
for name,inp in claim['experiment']['inputs'].items():
    # Hash only: no NPY or historical sample interpretation.
    p=Path(inp['path']);p=p if p.is_absolute() else CAP/p
    assert sha(p.read_bytes())==inp['sha256'],name
base=CAP/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/ID
observer=read(base/'observer.json');guard=read(base/'guard/final.json');child=read(base/'guard/child_exit.json')
for name,h in observer['evidence_sha256'].items():assert sha((base/name).read_bytes())==h
cells=read(base/'postmortem-cells.json')
assert [x['id'] for x in cells]==claim['experiment']['cells']
assert [x['status'] for x in cells]==['failed','unavailable']
for cell in cells:
    p=CAP/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/ID/(cell['id']+'.json')
    assert read(p)==cell
assert guard['phase']=='failed' and guard['cleanup_verified'] is True and guard['cleanup_unit_properties']['Result']=='timeout'
assert guard['native_unit_properties']=={'LimitFSIZE':'4194304','LimitFSIZESoft':'4194304','RuntimeMaxUSec':'30min'}
assert guard['kernel_controls']=={'memory.high':'3221225472','memory.max':'3221225472','memory.swap.max':'0'}
assert all(v==0 for v in guard['memory_events'].values()) and guard['peak_sampled_memory_current_bytes']==402456576
assert child['exit_code']==125 and child['reason']=='signal' and guard['child_exit_code'] is None
assert guard['elapsed_seconds']==1802.523400692
roots=list((CAP/'research_artifacts/onchain_representations').glob('*/'+ID));assert len(roots)==1
imported=roots[0]/'compact/dictionary-import/import-complete.json'
assert sha(imported.read_bytes())==result['original_dictionary_import_complete_sha256']
irecord=read(imported);assert len(irecord['numeric']['ordered_motifs'])==32 and irecord['historical_work_recomputed'] is False
stages=list((roots[0]/'compact').glob('mcm-*'));assert len(stages)==1 and not (stages[0]/'stage-complete.json').exists()
assert not list((CAP/'research_runs').glob('original-import-native-publication-failure-20261003-03/claim.json'))
journal=(HERE/'unit-journal01.txt').read_text()
pids=set(result['recorded_pids_absent'])|{int(k) for k in guard['cpu_thread_readback']}|{int(x) for x in re.findall(r'Killing process (\d+)',journal)}
assert all(not Path('/proc',str(p)).exists() for p in pids)
assert not Path(guard['cgroup']).exists()
unit=subprocess.run(['systemctl','--user','show',guard['unit'],'--property=ActiveState,SubState,Result,ExecMainStatus,ControlGroup'],capture_output=True,text=True,timeout=10)
assert unit.returncode==0
props=dict(line.split('=',1) for line in unit.stdout.splitlines() if '=' in line)
assert props['ActiveState'] in ('failed','inactive') and props['ControlGroup']==''
print(json.dumps({'result_sha256':sha((PREP/'EXECUTION_PRIMARY01.json').read_bytes()),'retention_sha256':sha((PREP/'RETAINED_PRIMARY01.json').read_bytes()),'archive_sha256':retained['archive_sha256'],'files':665,'directories_including_root':274,'members':939,'logical_bytes':6585516,'allocated_bytes_including_directories':9453568,'source_git_body_joins':159,'registered_input_body_hashes':len(claim['experiment']['inputs']),'actual_postmortem_cells':cells,'missing_worker_outputs':result['missing_registered_outputs'],'native_timeout':True,'peak_sampled_bytes':402456576,'all_recorded_and_journal_thread_pids_now_absent':sorted(pids),'current_unit':props,'numerical_results_not_interpreted':True,'no_extraction_or_replay':True},indent=2))
