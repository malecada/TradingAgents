from pathlib import Path
import hashlib,json,os,stat,importlib.util,shutil
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';O=Path(__file__).resolve().parent;T=F/'real-data-pilot-may30-ledger-relocation01-2026-10-06'
evidence={}
def read(p,pin=None):
 assert p.resolve(strict=True)==p and p.stat().st_nlink==1 and p.stat().st_size<4*1024**2
 b=p.read_bytes();h=hashlib.sha256(b).hexdigest()
 if pin:assert h==pin
 evidence[str(p.relative_to(R))]=h;return b
def obj(p,pin=None):return json.loads(read(p,pin))
def sig(p):
 assert p.resolve(strict=True)==p
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1
 return [s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,stat.S_IMODE(s.st_mode)]
def put(n,v):(O/n).write_text(json.dumps(v,indent=2)+'\n')
pin='21c829f2176d92fddeef3279ea26001277e685d8da06074a444ac599734df47e';e=obj(T/'retire-envelope01.json',pin);old=obj(T/'copy-envelope01.json');bindings=obj(T/'ROOT_RETIRE_REVIEW_BINDINGS01.json')
assert e['phase']=='retire' and e['identity']==old['identity']==bindings['identity'] and bindings['envelope_sha256']==pin and bindings['decision'] is None and bindings['evidence'] is None
assert e['selection']==old['selection'] and e['environment']==old['environment']
assert len(e['source_files'])==13 and len(e['evidence'])==23 and all(e['source_files'][p]==h for p,h in old['source_files'].items())
assert e['evidence'][:17]==old['evidence']
for p,h in e['source_files'].items():read(R/p,h)
for ref in e['evidence']+[e['environment'],e['selection']]:read(R/ref['path'],ref['sha256'])
assert e['helper']['sha256']=='437332513140816249bc998fbc3fbc8f70a0d123acb0280934246120e1ffa3b1'
assert e['source_files'][e['helper']['path']]==e['helper']['sha256']
source=read(R/e['helper']['path'],e['helper']['sha256']);assert source==read(F/'real-data-pilot-may30-ledger-relocation-retire-disposition02-2026-10-06/relocate01.py')
from tradingagents.research.onchain_replication.environment import inventory
assert inventory(R)==obj(R/e['environment']['path'])
refs={k:bindings[k] for k in ['copy_receipt','copy_review','copy_native','copy_outer','copy_root']}
for ref in refs.values():assert evidence[ref['path']]==ref['sha256']
b={k:obj(R/v['path'],v['sha256']) for k,v in refs.items()}
q=b['copy_receipt'];g=b['copy_native'];r=b['copy_root'];v=b['copy_review'];x=b['copy_outer']
assert v['decision']=='accepted' and v['copy_receipt_sha256']==refs['copy_receipt']['sha256'] and v['full_destination_readback_verified'] is True
assert g['phase']=='complete' and g['child_exit_code']==0 and g['cleanup_verified'] is True and not Path(g['cgroup']).exists()
assert x['entry_selected_exit_code']==r['actual_root_tool_exit_code']==0
assert all(not Path('/proc',str(pid)).exists() for pid in r['actual_selected_recorded_pids'])
c=obj(R/e['selection']['path']);observed=[]
for row in c['recovery_selection']['rows']:
 a=row['original'];s=sig(R/a['path']);assert [s[i] for i in [0,1,3,4,5]]==a['stat_identity'] and s[6]==a['mode'];observed.append({'path':a['path'],'stat_identity7':s})
assert q['original']==c['recovery_selection']['rows'][0]['original'] and q['original_retired'] is False
p=Path(q['target']['path']);assert sig(p)==q['target']['stat_identity'] and sorted(z.name for z in p.parent.iterdir())==['ledger.sqlite']
for key,val in c['target'].items():assert q['target'][key]==val
assert q['target']['bytes']==3189231616 and q['target']['device']==66307 and observed[0]['stat_identity7'][0]==66310
for n in ['retire-preflight01.json','retire-launch-attempt01.json','retire-attempt01.json','retire-complete01.json','retire-failed01.json','retire-outer-exit01.json','relocation-receipt01.json']:assert not os.path.lexists(T/n),n
spec=importlib.util.spec_from_file_location('reviewed_retire',R/e['helper']['path']);m=importlib.util.module_from_spec(spec);exec(compile(source,str(R/e['helper']['path']),'exec'),vars(m))
m.base().inactive();m.room(c,0)
check={'decision':'pass','envelope_sha256':pin,'source_files':13,'evidence_inputs':23,'five_copy_refs_exact':True,'three_original_stat_joins':observed,'destination_stat_identity7':sig(p),'inactive_guard_passed':True,'fresh_retire_phase':True,'root_free_bytes':shutil.disk_usage(R).free,'data_free_bytes':shutil.disk_usage('/home/malecada/Data').free,'real_payload_reads':0,'deletions':0}
put('CHECK01.json',check)
evidence[str((O/'CHECK01.json').relative_to(R))]=hashlib.sha256((O/'CHECK01.json').read_bytes()).hexdigest()
release={**bindings,'decision':'accepted','evidence':evidence}
put('retire-RELEASE_REVIEW01.json',release)
print(json.dumps({'decision':'accepted','release_sha256':hashlib.sha256((O/'retire-RELEASE_REVIEW01.json').read_bytes()).hexdigest(),'real_payload_reads':0,'deletions':0}))
