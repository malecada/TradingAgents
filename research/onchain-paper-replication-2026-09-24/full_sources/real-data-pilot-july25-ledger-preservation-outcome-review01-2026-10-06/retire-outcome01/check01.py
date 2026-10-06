"""Actual retirement/aggregate metadata outcome; stat-only retained payload joins."""
from pathlib import Path
import datetime,hashlib,json,os,stat
H=Path(__file__).resolve().parent;F=H.parent.parent;R=F.parents[2];D=F/'real-data-pilot-july25-ledger-relocation01-2026-10-06';ev={}
def sig(s):return [s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,stat.S_IMODE(s.st_mode)]
def raw(p,pin=None):
 p=Path(p);s=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<4*1024**2;b=p.read_bytes();assert sig(s)==sig(p.lstat());v=hashlib.sha256(b).hexdigest();assert pin is None or pin==v;ev[str(p.relative_to(R))]=v;return b
def read(p,pin=None):return json.loads(raw(p,pin))
env=read(D/'retire-envelope01.json','c727c6bea2be8194a907713d4326697b103e02e925bc661b2aea0412631b2667');release=read(D/'retire-RELEASE_REVIEW01.json','d04a295c3dd8381202411d60766d6acf9b26f5ae4aa416662593356dac01eb77');assert release['decision']=='accepted' and release['phase']=='retire' and release['envelope_sha256']==ev[str((D/'retire-envelope01.json').relative_to(R))]
for path,pin in env['source_files'].items():raw(R/path,pin)
parts={}
for name in ('copy_receipt','copy_review','copy_native','copy_outer','copy_root'):
 ref=release[name];assert release['evidence'][ref['path']]==ref['sha256'];parts[name]=read(R/ref['path'],ref['sha256'])
copy=parts['copy_receipt'];accepted=parts['copy_review'];native=parts['copy_native'];outercopy=parts['copy_outer'];rootcopy=parts['copy_root']
assert accepted['decision']=='accepted' and accepted['full_destination_readback_verified'] is True and accepted['copy_receipt_sha256']==release['copy_receipt']['sha256']
retire=read(D/'retire-complete01.json','d42caa2f13c0cab1789dd877f685c0c87998b4048fb2a37fc9327107bc214562');mapping=read(D/'relocation-receipt01.json','8fda8ed1b23e0ce2d7c7722d61d9761a2100864fe0aad8686cdc127deae10051');outer=read(D/'retire-outer-exit01.json','56a061b7dcd7c92bd51919d62d9cb29cf8ed22f340140cfe61ec57210d5a1ef3');root=read(D/'RETIRE_ROOT_TERMINAL01.json')
assert all(x['identity']==release['identity'] for x in (retire,mapping,outer,root,copy,accepted))
assert retire['original']==copy['original'] and retire['target']==copy['target']==mapping['target']
assert retire['original_retired'] is True and retire['source_retired'] is True and retire['original_parent_status']=='failed' and retire['no_retry'] is True
assert retire['copy_receipt']==release['copy_receipt'] and retire['copy_review']==release['copy_review']
assert mapping['schema_version']==1 and mapping['kind']=='closed-ledger-cross-volume-relocation' and mapping['predecessor']==copy['predecessor']
assert mapping['original']=={k:copy['original'][k] for k in ('path','bytes','sha256')} and mapping['original_claim_sha256']==copy['original_claim_sha256'] and mapping['original_source']==copy['original_source']
assert mapping['retirement_evidence']=={'path':str((D/'retire-complete01.json').relative_to(R)),'sha256':ev[str((D/'retire-complete01.json').relative_to(R))]}
assert all(mapping[k] is True for k in ('copy_readback_verified','external_byte_recovery_verified','original_retired'))
for key,leaf in [('outer','retire-outer-exit01.json'),('relocation_receipt','relocation-receipt01.json'),('retire_receipt','retire-complete01.json')]:assert root[key]=={'path':str((D/leaf).relative_to(R)),'sha256':ev[str((D/leaf).relative_to(R))]}
assert root['root_session_id']==72198 and root['terminal_chunk']=='442e5f' and root['actual_root_tool_exit_code']==0 and root['phase']=='retire'
assert root['actual_native_child_exit_code'] is None and root['native_cleanup_verified'] is None
assert outer['phase']=='retire' and outer['entry_selected_exit_code']==0 and outer['fatal_type'] is None and all(outer[k] is None for k in ('guard_phase','guard_child_exit_code','cleanup_verified'))
assert not os.path.lexists(R/copy['original']['path']) and root['original_absent'] is True and root['data_target_exists'] is True and root['get_exists'] is True
sel=read(R/env['selection']['path'],env['selection']['sha256']);getrow=sel['recovery_selection']['rows'][0]['recovered'];getpath=R/getrow['path'];s=getpath.lstat();assert getpath.resolve(strict=True)==getpath and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]==getrow['stat_identity'] and stat.S_IMODE(s.st_mode)==getrow['mode']
target=Path(copy['target']['path']);assert target.resolve(strict=True)==target and sig(target.lstat())==copy['target']['stat_identity'] and set(q.name for q in target.parent.iterdir())=={'events.sqlite'}
assert native['cleanup_verified'] is True and native['child_exit_code']==0 and outercopy['entry_selected_exit_code']==0 and rootcopy['actual_root_tool_exit_code']==0
assert not Path(native['cgroup']).exists() and all(not Path('/proc',str(p)).exists() for p in rootcopy['selected_recorded_pids'])
assert rootcopy['unknown_lifetime_process_history'] is None
assert not (D/'retire-failed01.json').exists() and not (D/'copy-failed01.json').exists() and not (D/'retire-guard01').exists()
pre=read(D/'retire-preflight01.json');assert pre==read(D/'retire-launch-attempt01.json') and pre['envelope_sha256']==release['envelope_sha256'] and pre['head']=='884372f857d246960ecd88dae845a1faaf4990b6'
attempt=read(D/'retire-attempt01.json');assert attempt=={'identity':release['identity'],'copy_receipt':release['copy_receipt'],'copy_review':release['copy_review'],'no_retry':True}
G=R/'research_runs/eth-paper-resource-pilot-20260924-02';read(G/'claim.json','05d769f6f50a65c2cf3eeed569077eb84e3871b1e7c23ad3504eed461a0565ca');failed=read(G/'failed.json','3d318717ff7adecb0f07b9db6f3d1bd2e24e0c77705c3e07062cd4b075f8d7f2');assert failed['status']=='failed' and not (G/'complete.json').exists()
result={'decision':'pass','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'identity':release['identity'],'current_get_stat':sig(s),'current_data_stat':sig(target.lstat()),'original_absent':True,'original_retirement_success_accepted':True,'copy_success_accepted':True,'cleanup_verified':True,'cleanup_scope':'Aggregate accepted COPY child/outer/Root cleanup plus actual ordinary RETIRE Root/outer zero and original absence. RETIRE has no native child; its native/guard/cleanup fields remain null. Unknown COPY lifetime history remains null.','evidence':ev,'payload_reads':0}
(H/'CHECK01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='evidence'},sort_keys=True))
