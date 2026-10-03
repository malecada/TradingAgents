"""Independent already-fetched recovery inspection. No fetch, extract or execution."""
import hashlib,json,os,stat,subprocess,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
P5=HERE.with_name('original-import-native-successor-preparation05-2026-10-03')
OUT=P5/'outcome-recovery01';REPO=OUT/'repository.git';CAP=OUT/'recovered-terminal-capsule03'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
r=read(P5/'REMOTE_PRIMARY_RECOVERY01.json');commit=r['remote_commit']
env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0',GIT_OPTIONAL_LOCKS='0')
def git(root,*args):return subprocess.check_output(['git','-c','protocol.allow=never',*args],cwd=root,env=env)
assert git(REPO,'rev-parse','FETCH_HEAD').decode().strip()==commit=='325dda4a532a7d406aa0e3a2a50b6ace170a4890'
assert not (REPO/'objects/info/alternates').exists() and not (CAP/'.git/objects/info/alternates').exists()
assert len(r['selected_blobs'])==r['body_count']==67
selected={}
for row in r['selected_blobs']:
    b=git(REPO,'show',commit+':'+row['path'])
    assert len(b)==row['bytes'] and sha(b)==row['sha256'] and b==(ROOT/row['path']).read_bytes()
    selected[Path(row['path']).name]=b
ret=json.loads(selected['RETAINED_PRIMARY01.json']);ex=json.loads(selected['EXECUTION_PRIMARY01.json']);rel=json.loads(selected['release01.json']);cor=json.loads(selected['CELL_DISPOSITION_CORRECTION01.json'])
assert sha(selected['RETAINED_PRIMARY01.json'])==ex['retention_sha256']==cor['retention_sha256']
assert sha(selected['EXECUTION_PRIMARY01.json'])==cor['execution_sha256']
archive=OUT/'retained-primary01.tar.gz'
assert archive.read_bytes()==selected['retained-primary01.tar.gz']
assert sha(archive.read_bytes())==ret['archive_sha256']==r['archive_sha256']
rows={x['path']:x for x in ret['members']};seen=set()
assert {str(p.relative_to(CAP)) for p in [CAP,*CAP.rglob('*')]}==set(rows)
with tarfile.open(archive,'r:gz') as t:
    for m in t:
        n='.' if m.name=='capsule03' else m.name.removeprefix('capsule03/')
        assert n not in seen and n in rows;seen.add(n);row=rows[n];p=CAP/n;st=p.lstat()
        assert m.mode==stat.S_IMODE(st.st_mode)==row['mode'] and p.resolve()==p
        if row['kind']=='directory':assert m.isdir() and stat.S_ISDIR(st.st_mode)
        else:
            assert m.isfile() and stat.S_ISREG(st.st_mode) and st.st_nlink==1 and m.size==st.st_size==row['bytes']
            with t.extractfile(m) as f:body=f.read()
            assert sha(body)==row['sha256'] and p.read_bytes()==body
assert len(seen)==939 and sum(x['kind']=='file' for x in rows.values())==665 and sum(x['kind']=='directory' for x in rows.values())==274
assert sum(x['bytes'] for x in rows.values())==6585516 and sum(x['allocated_bytes'] for x in rows.values())==9453568
assert git(CAP,'rev-parse','HEAD').decode().strip()==rel['capsule_commit']==r['capsule_head']
for name,h in rel['source_files'].items():
    b=(CAP/name).read_bytes();assert sha(b)==h
    assert git(CAP,'show',rel['capsule_commit']+':'+name)==b==git(CAP,'show',rel['source_anchor']+':'+name)
assert len(rel['source_files'])==159
gate=(CAP/rel['registration']).read_bytes();assert sha(gate)==rel['registration_sha256']
assert git(CAP,'show',rel['capsule_commit']+':'+rel['registration'])==gate
orig=json.loads(selected['original_inputs01.json']);assert len(orig['inputs'])==11 and len(orig['original_source_files'])==26
for row in orig['inputs']:assert sha((CAP/row['capsule_path']).read_bytes())==row['sha256']
for name,row in orig['original_source_files'].items():assert sha(git(CAP,'show',orig['original_source']+':'+name))==row['claim_sha256']
hist=[]
for i in range(1,4):
    identity=f'original-import-native-success-20261003-0{i}';run=CAP/'research_runs'/identity
    c=read(run/'claim.json');t=read(run/'failed.json');assert not (run/'complete.json').exists()
    assert c['effective_attempt_budget']==i+1 and t['status']=='failed' and t['claim_sha256']==sha((run/'claim.json').read_bytes())
    outputs={f.name:sha(f.read_bytes()) for f in (run/'outputs').iterdir()};assert outputs==t['output_sha256'] and len(outputs)==(4 if i<3 else 2)
    g=git(CAP,'show',c['source']+':'+c['registration']);assert sha(g)==c['registration_sha256'] and json.loads(g)['experiments'][identity]==c['experiment']
    for name,h in c['experiment']['source_files'].items():assert sha(git(CAP,'show',c['source']+':'+name))==h
    hist.append({'identity':identity,'claim_sha256':sha((run/'claim.json').read_bytes()),'terminal_sha256':sha((run/'failed.json').read_bytes()),'source_bodies':len(c['experiment']['source_files']),'outputs':sorted(outputs)})
identity='original-import-native-success-20261003-03';run=CAP/'research_runs'/identity
assert hist[-1]['claim_sha256']==r['claim_sha256']==ex['claim_sha256'] and hist[-1]['terminal_sha256']==ex['terminal_sha256']
assert not any((run/'outputs'/n).exists() for n in ('cell-ledger.json','resource-summary.json'))
assert sha(selected['CELL_DISPOSITION_CORRECTION01.json'])==r['correction_sha256']=='edb8a1d9aa9eac5f96231c5580dfba17b89b72f4cdeafd323b39e634ffbe570f'
cells=[]
for ref in cor['source_cells']:
    b=(CAP/ref['path']).read_bytes();assert len(b)==ref['bytes'] and sha(b)==ref['sha256'];cells.append(json.loads(b))
assert cells==cor['original_durable_cells']==r['cell_dispositions'] and [c['status'] for c in cells]==['failed','unavailable']
post=(CAP/cor['postmortem']['path']).read_bytes();assert sha(post)==cor['postmortem']['sha256'] and json.loads(post)==cells
base=CAP/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/identity
obs=read(base/'observer.json')
for name,h in obs['evidence_sha256'].items():assert sha((base/name).read_bytes())==h
guard=read(base/'guard/final.json');child=read(base/'guard/child_exit.json')
assert guard['phase']=='failed' and guard['cleanup_unit_properties']['Result']=='timeout' and child['exit_code']==125
assert guard['native_unit_properties']=={'LimitFSIZE':'4194304','LimitFSIZESoft':'4194304','RuntimeMaxUSec':'30min'}
assert all(v==0 for v in guard['memory_events'].values()) and guard['child_exit_code'] is None
outer=CAP/'fixture_outer'/identity
assert read(outer/'cleanup.json')==ex['original_outer_cleanup'] and read(outer/'cleanup.json')['unresolved_pid_absence'] is True
assert read(outer/'terminal.json')['proof'] is None
roots=list((CAP/'research_artifacts/onchain_representations').glob('*/'+identity));assert len(roots)==1
assert sha((roots[0]/'compact/dictionary-import/import-complete.json').read_bytes())==ex['original_dictionary_import_complete_sha256']
stages=list((roots[0]/'compact').glob('mcm-*'));assert len(stages)==1 and not (stages[0]/'stage-complete.json').exists()
print(json.dumps({'recovery_receipt_sha256':sha((P5/'REMOTE_PRIMARY_RECOVERY01.json').read_bytes()),'actual_already_fetched_commit':commit,'selected_remote_blobs':67,'archive_members':939,'files':665,'directories':274,'logical_bytes':6585516,'retained_original_allocated_bytes':9453568,'current_and_anchor_source_joins':159,'original_git_paths':26,'original_json_inputs':11,'failed_histories':hist,'corrected_cells':cells,'unresolved_original_outer_cleanup_preserved':True,'native_timeout_preserved':True,'current_live_process_absence_not_inferred_from_restore':True,'network_fetch_extraction_imports_or_replay':False},indent=2))
