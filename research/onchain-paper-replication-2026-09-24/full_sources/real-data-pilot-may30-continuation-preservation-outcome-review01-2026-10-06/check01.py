from pathlib import Path
import hashlib,json,os,stat,subprocess,datetime
H=Path(__file__).resolve().parent;R=H.parents[3];B=R/'research/onchain-paper-replication-2026-09-24';D=B/'storage/real-pilot-may30-continuation-preservation-20261006-01'
evidence={}
def raw(p):
    p=Path(p);s=p.lstat();assert p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<4*1024**2
    b=p.read_bytes();t=p.stat();assert (t.st_dev,t.st_ino,t.st_mode,t.st_nlink,t.st_size,t.st_mtime_ns,t.st_ctime_ns)==(s.st_dev,s.st_ino,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns);evidence[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def read(p):return json.loads(raw(p))
def bound(ref):
    p=R/ref['path'];b=raw(p);assert evidence[ref['path']]==ref['sha256'];return json.loads(b)
def sig(p):
    s=p.lstat();assert p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1
    return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns],stat.S_IMODE(s.st_mode)
s=read(D/'selection01.json');assert evidence[str((D/'selection01.json').relative_to(R))]=='e6c39629b96a172f308405fceb2e87c675f2354800fffa7ac79bae07b8d7b5f4'
e=read(D/'envelope01.json');assert evidence[str((D/'envelope01.json').relative_to(R))]=='02c23b7b2adf0c341bce259724d7f00b26f609b85949809dab82a6fc59edbb70'
for path,expected in e['source_files'].items():raw(R/path);assert evidence[path]==expected
bound(e['environment'])
release=read(D/'RELEASE_REVIEW01.json');assert evidence[str((D/'RELEASE_REVIEW01.json').relative_to(R))]=='9e2d5f02370dc74947b5ebed0b35aeba8bda43249187be59d6fdeb52d8614de2'
# Connection is intentionally neither opened nor hashed by review.
for ref in e['evidence']:bound(ref)
original=bound(s['independent_body_hash']);outcome=bound(s['graph_outcome_review']);terminal=bound(s['graph_terminal'])
assert original['decision']=='pass' and outcome['decision']=='accepted' and terminal['status']=='complete'
proofrows={x['path']:x for x in original['files']}
c=read(D/'complete.json');assert evidence[str((D/'complete.json').relative_to(R))]=='ab324caa01ce409703b712851e77867bfd99297963aef2a938051b7ae7893ccc'
assert raw(D/'complete.json')==raw(D/'recovered-complete.json')==raw(D/'completion-candidate.json')
assert c['selection']==s and c['identity']==s['identity'] and c['count']==s['count']==24 and c['bytes_preserved']==s['total_bytes']==432827661
assert all(c[k] is True for k in ('originals_retained','recoveries_retained','no_automatic_retry')) and len(c['files'])==24
assert len(s['directories'])==6 and sum(x['bytes'] for x in s['files'])==432827661
assert not (D/'failed.json').exists()
pids=set();rows=[];get_count=0
def transport(p,size):
    global get_count
    t=read(p);assert t['status']=='complete' and t['returncode']==0 and t['error_type'] is None and t['expected_bytes']==t['received_bytes']==size
    assert type(t['pid']) is int and t['pid']>0;pids.add(t['pid']);get_count+=1
for i,row in enumerate(s['files']):
    n=f'{i:02d}';a=read(D/(n+'-attempted.json'));assert a=={'number':i,'row':row}
    v=read(D/(n+'-verified.json'));k=read(D/(n+'-kept.json'));restore=read(D/(n+'-restore.json'))
    assert v==k==c['files'][i]
    assert all(k[x]==value for x,value in row.items())
    assert k['body_roundtrip_verified'] is True and k['original_retained'] is True and k['recovered_body_retained'] is True
    assert k['remote_object']==s['remote']+'/'+n+'.bin' and k['remote_restore']==s['remote']+'/'+n+'-restore.json'
    assert restore=={key:value for key,value in k.items() if key not in ('original_retained','recovered_body_retained')}
    assert raw(D/(n+'-restore.json'))==raw(D/(n+'-recovered-restore.json'))
    o=R/row['path'];oi,om=sig(o);assert oi==row['stat_identity'] and om==row['mode']
    g=D/(n+'-recovered.bin');gi,gm=sig(g);assert gi[2]==row['bytes']
    transport(D/(n+'-recovered.bin.transport.json'),row['bytes']);transport(D/(n+'-recovered-restore.json.transport.json'),(D/(n+'-restore.json')).stat().st_size)
    payload=row['role']=='independently-hashed-original-payload'
    if payload:
        pr=proofrows[row['path']];assert pr['bytes']==row['bytes'] and pr['sha256']==row['sha256']
    else:
        assert hashlib.sha256(raw(o)).hexdigest()==row['sha256'] and raw(o)==raw(g)
    rows.append({'index':i,'path':row['path'],'sha256':row['sha256'],'bytes':row['bytes'],'original_stat_identity':oi,'original_mode':om,'recovered_path':str(g.relative_to(R)),'recovered_stat_identity':gi,'recovered_mode':gm,'body_hash_basis':'actual pinned helper full streamed SHA after GET; independent metadata/control review; no reviewer payload read' if payload else 'independently compared small original/recovered bytes'})
assert len(proofrows)==5 and sum(r['bytes'] for r in rows if r['path'] in proofrows)==432741928
for row in s['directories']:
    p=R/row['path'];st=p.lstat();assert stat.S_ISDIR(st.st_mode) and p.resolve()==p and stat.S_IMODE(st.st_mode)==row['mode']
# Exact original membership under the three selected completed namespaces.
roots=[R/'research_runs'/outcome['experiment']]+[R/'research_artifacts/onchain-paper-replication-2026-09-24'/kind/outcome['experiment'] for kind in ('runs','sources')]
files=set();dirs=set()
for root in roots:
    for p in [root,*root.rglob('*')]:
        st=p.lstat();assert not p.is_symlink()
        (dirs if stat.S_ISDIR(st.st_mode) else files).add(str(p.relative_to(R)))
assert files=={r['path'] for r in s['files']} and dirs=={r['path'] for r in s['directories']}
transport(D/'recovered-complete.json.transport.json',(D/'recovered-complete.json').stat().st_size)
root=read(D/'ROOT_TERMINAL01.json');native=read(D/'guard01/final.json');outer=read(D/'outer-exit01.json');child=read(D/'guard01/child_exit.json');pre=read(D/'preflight01.json')
assert evidence[str((D/'ROOT_TERMINAL01.json').relative_to(R))]=='87802aec9b7b6009db5753fdce606e4b188665d47848842789d48b1b1f2a09de'
assert root['actual_root_tool_exit_code']==root['original_outer_selected_exit_code']==0 and root['guard_final_sha256']==evidence[str((D/'guard01/final.json').relative_to(R))]
assert root['complete_sha256']==evidence[str((D/'complete.json').relative_to(R))] and root['source_commit']==pre['head']=='b38eb475ca5b11162550d4e7b8d6ff657f03e2a3'
assert native['phase']=='complete' and native['child_exit_code']==child['exit_code']==0 and native['cleanup_verified'] is True and native['cleanup_stop_returncode']==5
assert outer['entry_selected_exit_code']==0 and outer['fatal_type'] is None and outer['cleanup_verified'] is True
assert native['memory_high_bytes']==192*1024**2 and native['memory_max_bytes']==256*1024**2 and native['memory_swap_max_bytes']==0
assert native['memory_events']['high']==1536 and all(native['memory_events'][k]==0 for k in ('max','oom','oom_kill'))
assert not Path(native['cgroup']).exists()
pids.update(root['selected_recorded_pids']);pids.add(native['monitor_pid']);pids.add(child['workload_pid']);pids.update(map(int,native['cpu_thread_readback']))
assert all(not Path('/proc',str(pid)).exists() for pid in pids)
unit=subprocess.run(['systemctl','--user','show',native['unit'],'--property=ActiveState,SubState,MainPID'],capture_output=True,text=True)
assert unit.returncode==0 and 'ActiveState=inactive' in unit.stdout and 'MainPID=0' in unit.stdout
result={'decision':'accepted','identity':s['identity'],'full_scope_byte_recovery':True,'count':24,'bytes':432827661,'directories':s['directories'],'rows':rows,'body_method':'Unchanged authenticated helper performed complete streaming SHA256 after each actual full GET before verified/kept/completion publication; inherited original5 independent body proof; current identity checks and small19 byte comparison. No independent reviewer large-body pass.','get_receipts':get_count,'recorded_pids_absent':sorted(pids),'unit_readback':unit.stdout,'original_cleanup_stop_returncode':5,'original_root_exit_code':0,'whole_lifetime_pid_history_known':False,'effective_accounting':{'prior_scientific_spent':42,'effective_budget':72,'unused':30,'new_scientific_claims_by_preservation':0,'basis_outcome_sha256':s['graph_outcome_review']['sha256']},'qualification':'Actual24-body incremental BYTE recovery only. Original names/modes and6directory descriptors retained; no POSIX reconstruction, runtime body recovery, continuous writer exclusion, current remote availability or financial/capacity authority. Current recovered stats are new observations, not historical post-hash signatures.','payload_reads_by_reviewer':0,'evidence':evidence,'at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(H/'REVIEW01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'decision':result['decision'],'count':24,'bytes':432827661,'gets':get_count,'recorded_pids':len(pids),'review_sha256':hashlib.sha256((H/'REVIEW01.json').read_bytes()).hexdigest()}))
