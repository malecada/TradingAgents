from pathlib import Path
import ast,json,hashlib,stat,os,shutil,subprocess,datetime
R=Path.cwd();B=R/'research/onchain-paper-replication-2026-09-24';F=B/'full_sources';H=Path(__file__).resolve().parent;D=B/'storage/real-pilot-july25-ledger-preservation-20261006-02';O=B/'storage/real-pilot-july25-ledger-preservation-20261006-01';A=F/'real-data-pilot-july25-ledger-preservation-binding02-2026-10-06';evidence={}
def sig(s):return[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
def raw(p,pin=None):
 p=Path(p);p=p if p.is_absolute() else R/p;rel=str(p.relative_to(R));assert 'connection.json' not in rel
 s=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2
 b=p.read_bytes();assert sig(s)==sig(p.lstat());sha=hashlib.sha256(b).hexdigest();assert pin is None or sha==pin,(rel,sha,pin);evidence[rel]=sha;return b
def obj(p,pin=None):return json.loads(raw(p,pin))
prior=obj(O/'RELEASE_REVIEW01.json','24bc3517127ebef1a6bf7c78bacffb8a5ac2351154d67ca1fca49e161b5aac6c')
for p,s in prior['evidence'].items():raw(p,s)
c=obj(D/'selection01.json','6fe51224e0b25f1767bc6f0f720a57262520cab031876e33164d21db31300ab0');e=obj(D/'envelope01.json','d0d8877bef6ae530157e0dd28ff50cc570aa46176efd63d00830156adb3c4b93');correction=obj(A/'CORRECTION02.json','ff26e84944df11bb5cbbad1315316e765eb05c911d818aeaf6f9581d5383cee0')
oldc=obj(O/'selection01.json');olde=obj(O/'envelope01.json');oldid=oldc['identity'];newid=c['identity'];assert newid=='real-pilot-july25-ledger-preservation-20261006-02'
expected=dict(oldc);expected.update(identity=newid,remote=oldc['remote'].replace(oldid,newid),predecessor_disposition=correction['predecessor']);assert expected==c
for oldref,newref in [({'path':str((O/'entry01.py').relative_to(R)),'sha256':'dc815a36031ca17f1bba16de04c6970db15276434312201cc0987e39bff0060f'},{'path':str((D/'entry01.py').relative_to(R)),'sha256':'932d951b7b533dc5aa293a0418c4a656189005380964bc2b2778d531cc3efb31'}),(olde['helper'],e['helper'])]:
 old=raw(oldref['path'],oldref['sha256']).decode();new=raw(newref['path'],newref['sha256']).decode();assert old.count(oldid)==new.count(newid)==1 and old.replace(oldid,newid)==new and ast.dump(ast.parse(old))==ast.dump(ast.parse(new.replace(newid,oldid)))
expected=json.loads(json.dumps(olde));expected['identity']=newid;expected['selection']=correction['selection'];expected['helper']=e['helper'];expected['source_files'].pop(olde['helper']['path']);expected['source_files'][e['helper']['path']]=e['helper']['sha256'];expected['source_files'].pop(str((O/'entry01.py').relative_to(R)));expected['source_files'][str((D/'entry01.py').relative_to(R))]='932d951b7b533dc5aa293a0418c4a656189005380964bc2b2778d531cc3efb31';expected['evidence'].append(correction['predecessor']['root_terminal']);assert expected==e
for p,s in e['source_files'].items():raw(p,s)
for ref in e['evidence']:raw(ref['path'],ref['sha256'])
t=obj(O/'ROOT_TERMINAL01.json','b217568b5d3b273515af1a1b6e64c25b2d10c8029177cb910659e8bf3f5e5f09')
assert t['actual_root_tool_exit_code']==1 and t['actual_root_tool_chunk']=='73d08d' and t['phase']=='PRE_ENTRY_FAILED_CLOSED_NO_RETRY' and t['no_relaunch_this_identity'] is True
assert t['actual_native_child_exit_code'] is None and t['actual_native_phase'] is None and t['original_native_outer_exit'] is None
assert correction['prior_closed_pre_entry_failed_attempts']==1 and correction['cumulative_ordinary_attempt_allowance']==2 and correction['fresh_native_allowance']==1 and correction['no_cap_ladder_refund_transfer_or_paper_claim'] is True
for path in correction['exact_missing_commit_bodies']:
 raw(path);r=subprocess.run(['git','cat-file','-e','3eab3d82f:'+path],capture_output=True);assert r.returncode!=0
for root in (O,D):
 for n in ['preflight01.json','launch-attempt01.json','guard01','intent.json','complete.json','failed.json','outer-exit01.json']:assert not os.path.lexists(root/n)
assert not os.path.lexists(D/'RELEASE_REVIEW01.json')
row=c['files'][0];p=R/row['path'];s=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and sig(s)==row['stat_identity'] and stat.S_IMODE(s.st_mode)==row['mode']
assert c['files']==oldc['files'] and c['total_bytes']==3755212800
units=subprocess.check_output(['systemctl','--user','list-units','--state=active,activating','--no-legend','onchain-replication-*.service'],text=True);assert not units.strip()
for claim in (R/'research_runs').glob('*/claim.json'):
 if claim.with_name('complete.json').exists() or claim.with_name('failed.json').exists():continue
 v=json.loads(raw(claim));assert isinstance(v.get('program_id'),str) and v['program_id']!='onchain-paper-replication-2026-09-24'
free=shutil.disk_usage(R).free;mem=int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024
assert free>=10*1024**3+c['total_bytes']+16*1024**2 and mem>=int(3.5*1024**3)
result={'decision':'accepted','identity':newid,'prior_identity_permanently_closed':oldid,'prior_root_exit':1,'prior_native_fields_remain_null':True,'prior_preflight_attempt_native_intent_absent':True,'ordinary_cumulative_attempt_allowance':2,'prior_closed_preentry_failures':1,'fresh_native_allowance':1,'scientific_budget_change':False,'full_source_literal_ast_inverses':True,'selection_only_identity_remote_ancestry_changed':True,'current_stat_identity':sig(s),'old_missing_git_bodies_confirmed':correction['exact_missing_commit_bodies'],'source_pins':len(e['source_files']),'disk_free_bytes':free,'host_mem_available_bytes':mem,'large_payload_reads':0,'connection_body_reads':0,'fresh_identity_unused':True,'actual_current_commit_all_release_evidence_join_required_before_launch':True,'at':datetime.datetime.now(datetime.UTC).isoformat(),'evidence':evidence}
with (H/'CHECK01.json').open('x') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k!='evidence'}))
