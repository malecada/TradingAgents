from pathlib import Path
import ast, datetime, hashlib, json, os, stat, subprocess, types
R=Path.cwd(); F=R/'research/onchain-paper-replication-2026-09-24/full_sources'; H=Path(__file__).resolve().parent; P=H.parent
D=F/'real-data-pilot-sixth-graph-get-duplicates-retirement01-2026-10-06'; L=F/'real-data-pilot-sixth-graph-ledger-retirement01-2026-10-06'; A=F/'real-data-pilot-sixth-graph-retirement-preparation01-2026-10-06'
evidence={}; cache={}
def sig(s):return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
def raw(p,pin=None):
 p=Path(p); p=p if p.is_absolute() else R/p
 rel=str(p.relative_to(R)); assert not any(x in rel.lower() for x in ('local-connection','local_connection','connection.json','/keys/','/apis/','.env'))
 assert p.resolve(strict=True)==p
 if rel not in cache:
  s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2
  b=p.read_bytes();assert sig(s)==sig(p.lstat());cache[rel]=b
 b=cache[rel];h=hashlib.sha256(b).hexdigest();assert pin is None or h==pin,(rel,h,pin);evidence[rel]=h;return b
def obj(p,pin=None):return json.loads(raw(p,pin))
def put(name,v):
 with (H/name).open('x') as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
c=obj(D/'SELECTION01.json','a3290ec188b35530c04e043cb3309400be22442f0bcf3ca1f1aaf39c06d78db2')
draft=obj(D/'BOUND_RELEASE_DRAFT01.json','25f944b84ec98a27327c04ddb9b982a809f74f649b19c7594948951c5260dbde')
assert draft['decision'] is None and draft['retire_only_five_verified_array_get_duplicates'] is None
for refs in (c['evidence'],draft['evidence']):
 for path,pin in refs.items():raw(path,pin)
src=raw(D/'retire01.py','202efc83b7a53857ce735f87a28d6338998a5acc63bf496b963984f6b8008e9c')
inv=obj(A/'INVERSE01.json')['gets01.py']; old=raw(inv['baseline'],inv['baseline_sha256']); adapted=old.decode()
for change in inv['literal_changes']:
 assert adapted.count(change['old'])==change['count'];adapted=adapted.replace(change['old'],change['new'])
assert adapted.encode()==src and ast.dump(ast.parse(adapted))==ast.dump(ast.parse(src))
assert raw(A/'gets01.py')==src
m=types.ModuleType('review_metadata_only');m.__file__=str(D/'retire01.py');exec(compile(src,m.__file__,'exec'),vars(m))
# Only read-only metadata and stat predicates; execute() is never called.
m.selected(R,c);m.recovery(R,c);m.inactive()
prior=obj(P/'REVIEW01.json','1e76c7a937cc3de2bd04491001ca408f5a09d2209fc3d5ff949bcaa2e93f55ee')
rows=[]
for row in c['rows']:
 oldrow=next(x for x in prior['rows'] if x['index']==row['index'])
 for k,prevprefix in [('original','original'),('recovered','recovered')]:
  v=row[k];assert v['path']==oldrow['path' if k=='original' else 'recovered_path']
  assert v['sha256']==oldrow['sha256'] and v['bytes']==oldrow['bytes']
  assert v['stat_identity']==oldrow[prevprefix+'_stat_identity'] and v['mode']==oldrow[prevprefix+'_mode']
  s=(R/v['path']).lstat();assert sig(s)==v['stat_identity'] and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==v['mode']
 rows.append(row)
assert sum(r['recovered']['bytes'] for r in rows)==429403880
complete=obj(L/'complete01.json','b9aff6f854fba9f6913a8dae28f1bed743cbf246a16980e77b7a403ea6a6e3ea')
root=obj(L/'ROOT_TERMINAL01.json','d7f12da153914409ea508a4e1d08be51bfd0f5a93e0b533105e745d903437e66')
assert root['actual_root_exit_code']==0 and root['actual_root_tool_exit_chunk']=='447a9d' and root['actual_root_tool_session']==15215
assert complete['removed']==c['removed_ledger_paths'] and complete['payload_bytes_retired']==6198239232
for path in c['removed_ledger_paths']:assert not os.path.lexists(R/path)
backup=R/m.BACKUP
assert obj(R/(c['removed_ledger_paths'][0]+'.remote.json'))==obj(backup/'11-kept.json')==complete['remote_restore']
assert complete['arrays_retained'] is True and complete['all_other_originals_and_recoveries_retained'] is True
release=raw(L/'RELEASE_REVIEW01.json','cb499d22028096ca2b2fe6e29ffebfe453a91b7aa6bac2feb1e0f7f491836f04')
for name in ['RELEASE_REVIEW01.json','retire01.py']:
 committed=subprocess.check_output(['git','show','a55823c68668cef70fd7a9909a3ff46420d3d668:'+str((L/name).relative_to(R))]);assert committed==raw(L/name)
final=obj(backup/'guard01/final.json');outer=obj(backup/'outer-exit01.json')
assert final['phase']=='complete' and final['child_exit_code']==0 and final['cleanup_verified'] is True
assert not Path(final['cgroup']).exists() and not Path('/proc',str(final['monitor_pid'])).exists()
assert outer['entry_selected_exit_code']==0
for name in ['attempt01.json','complete01.json','failed01.json','RELEASE_REVIEW01.json']:assert not os.path.lexists(D/name)
units=subprocess.check_output(['systemctl','--user','list-units','--state=active,activating','--no-legend','onchain-replication-*.service'],text=True);assert not units.strip()
result={'decision':'accepted','ledger_retirement_actual_root_exit':0,'ledger_retired_bytes':6198239232,'ledger_removed_paths_absent':True,'restore_sidecar_equals_verified_kept':True,'get_selection_count':5,'get_selected_bytes':429403880,'original_arrays_retained':True,'current_rows':rows,'full_byte_and_ast_inverse':True,'bounded_evidence_count':len(evidence),'active_native_units':units,'one_use_get_namespace_unused':True,'large_payload_reads':0,'inherited_full_byte_review':str((P/'REVIEW01.json').relative_to(R)),'original_backup_cleanup_stop_returncode':5,'original_backup_HIGH_events':19369,'whole_lifetime_pid_history_known':False,'at':datetime.datetime.now(datetime.UTC).isoformat(),'evidence':evidence,'qualification':'Historical full BYTE recovery plus current sampled stat joins; no new remote availability, writer exclusion, POSIX reconstruction, numerical capacity or scientific authority. No deletion executed.'}
put('CHECK01.json',result)
print(json.dumps({k:v for k,v in result.items() if k not in ('evidence','current_rows')}))
