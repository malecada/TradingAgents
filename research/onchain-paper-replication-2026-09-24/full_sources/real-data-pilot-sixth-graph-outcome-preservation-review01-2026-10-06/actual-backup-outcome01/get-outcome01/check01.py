from pathlib import Path
import hashlib,json,os,stat,subprocess,datetime
R=Path.cwd();H=Path(__file__).resolve().parent;P=H.parent;F=R/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'real-data-pilot-sixth-graph-get-duplicates-retirement01-2026-10-06';evidence={}
def raw(p,pin=None):
 p=Path(p);p=p if p.is_absolute() else R/p;s=p.lstat();assert p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2
 b=p.read_bytes();t=p.lstat();assert ident(s)==ident(t);sha=hashlib.sha256(b).hexdigest();assert pin is None or sha==pin;evidence[str(p.relative_to(R))]=sha;return b
def ident(s):return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
def obj(p,pin=None):return json.loads(raw(p,pin))
def current(path,sig,mode):
 p=R/path;s=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and ident(s)==sig and stat.S_IMODE(s.st_mode)==mode;return {'path':path,'stat_identity':ident(s),'mode':mode,'nlink':s.st_nlink}
complete=obj(D/'complete01.json','96a285d5c7cb4e0d2371eada9e3d7b1610b581928d7fda2153a47a8dafa302a3');root=obj(D/'ROOT_TERMINAL01.json','d943fd94ecdfba538a44035279d4096e3f458b45c873cda3d7daccc7f2ecb403');attempt=obj(D/'attempt01.json')
release=obj(D/'RELEASE_REVIEW01.json','baf73e0b9d59c683fecc2716812aeacf234684f57d290d80514049c0a3260a81');selection=obj(release['selection']['path'],release['selection']['sha256'])
assert complete['identity']==root['identity']==attempt['identity']==selection['identity']==release['retirement_identity']=='real-pilot-sixth-graph-get-duplicates-retirement-20261006-01'
assert root['actual_root_exit_code']==0 and root['actual_root_tool_session']==98181 and root['actual_root_tool_exit_chunk']=='bbf0b0' and root['complete_sha256']==evidence[str((D/'complete01.json').relative_to(R))]
assert attempt['review_sha256']==evidence[str((D/'RELEASE_REVIEW01.json').relative_to(R))] and attempt['selection']==release['selection']
assert complete['removed']==[r['recovered']['path'] for r in selection['rows']] and complete['payload_bytes_retired']==sum(r['recovered']['bytes'] for r in selection['rows'])==429403880
assert complete['original_arrays_retained'] is True and complete['all_other_recoveries_retained'] is True and complete['no_retry'] is True
assert complete['remote_disposition']==selection['remote_disposition']
assert not os.path.lexists(D/'failed01.json')
originals=[]
for row in selection['rows']:
 assert not os.path.lexists(R/row['recovered']['path']);v=row['original'];originals.append(current(v['path'],v['stat_identity'],v['mode']))
prior=obj(P/'REVIEW01.json','1e76c7a937cc3de2bd04491001ca408f5a09d2209fc3d5ff949bcaa2e93f55ee');others=[]
for row in prior['rows']:
 if row['index'] in [11,21,22,23,25,26]:continue
 others.append(current(row['recovered_path'],row['recovered_stat_identity'],row['recovered_mode']))
assert len(others)==30
for name in ['retire01.py','RELEASE_REVIEW01.json','SELECTION02.json']:
 assert subprocess.check_output(['git','show','281a284ff74fa3ce5a8832c3baf7306320b55b24:'+str((D/name).relative_to(R))])==raw(D/name)
for name in ['complete01.json','ROOT_TERMINAL01.json']:
 ref=selection['recovery_basis']['ledger_complete' if name=='complete01.json' else 'ledger_root'];obj(ref['path'],ref['sha256'])
for path in selection['removed_ledger_paths']:assert not os.path.lexists(R/path)
review={'decision':'accepted','identity':complete['identity'],'actual_root_exit_code':0,'actual_root_tool_session':98181,'actual_root_tool_exit_chunk':'bbf0b0','retired_only_five_verified_get_duplicates':True,'payload_bytes_retired':429403880,'removed':complete['removed'],'original_five_arrays_retained':True,'original_current_stats':originals,'other_thirty_recoveries_current_stats':others,'ledger_pair_remains_absent':True,'no_retry':True,'large_payload_reads_by_reviewer':0,'source_release_selection_committed_at':'281a284ff74fa3ce5a8832c3baf7306320b55b24','evidence':evidence,'qualification':'Actual ordinary duplicate retirement only; native child not used by this operation. Prior cleanup stop5, HIGH19369 and unknown whole-lifetime PID history unchanged. Historical full BYTE recovery retained; current remote availability, writer exclusion, POSIX/runtime reconstruction and numerical capacity not tested. No further retirement or empirical authority.','at':datetime.datetime.now(datetime.UTC).isoformat()}
with (H/'REVIEW01.json').open('x') as f:json.dump(review,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'decision':'accepted','bytes':429403880,'originals':len(originals),'other_gets':len(others),'payload_reads':0,'review_sha256':hashlib.sha256((H/'REVIEW01.json').read_bytes()).hexdigest()}))
