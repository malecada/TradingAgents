from pathlib import Path
import hashlib,json,stat,os,subprocess,shutil
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');B=R/'research/onchain-paper-replication-2026-09-24';F=B/'full_sources';T=B/'storage/real-pilot-may30-continuation-preservation-20261006-01';A=F/'real-data-pilot-may30-continuation-preservation-preparation01-2026-10-06';O=Path(__file__).resolve().parent;E={}
def raw(p,pin=None):
 assert p.resolve(strict=True)==p and p.is_file() and p.stat().st_nlink==1 and p.stat().st_size<=4*1024**2
 assert p.name!='connection.json'
 b=p.read_bytes();h=hashlib.sha256(b).hexdigest()
 if pin:assert h==pin
 E[str(p.relative_to(R))]=h;return b
def obj(p,pin=None):return json.loads(raw(p,pin))
def ref(d):return obj(R/d['path'],d['sha256'])
def put(n,v):(O/n).write_text(json.dumps(v,indent=2)+'\n')
pin='02c23b7b2adf0c341bce259724d7f00b26f609b85949809dab82a6fc59edbb70';e=obj(T/'envelope01.json',pin);s=ref(e['selection']);binding=obj(A/'ROOT_BINDING01.json');old=ref(binding['baseline'])
assert e['connection']==old['connection'] and e['local_only_evidence']==[e['connection']['path']] and e['connection']['path'] not in e['source_files']
assert len(e['source_files'])==12 and len(e['evidence'])==4
for p,h in e['source_files'].items():raw(R/p,h)
for d in e['evidence']:ref(d)
assert e['transport']==old['transport'] and e['scanner_sha256']==old['scanner_sha256'] and e['environment']==old['environment']
for p,h in old['source_files'].items():
 if p in binding['removed_old_entry_helper_pins']:continue
 assert e['source_files'][p]==(binding['approved_resource_change']['current'] if p.endswith('/resources.py') else h)
assert raw(T/'entry01.py')==raw(A/'entry01.py')
from tradingagents.research.onchain_replication.environment import inventory
assert inventory(R)==ref(e['environment'])
review=ref(s['graph_outcome_review']);bodies=ref(s['independent_body_hash']);assert review['decision']=='accepted' and review['cleanup']['original_guard_cleanup_verified'] and review['cleanup']['recorded_cgroup_absent'] and review['root_actual_exit']['exit_code']==0
assert review['evidence'][s['independent_body_hash']['path']]==s['independent_body_hash']['sha256']
assert s['identity']==e['identity']==binding['identity'] and s['count']==len(s['files'])==24 and len(s['directories'])==6 and sum(r['bytes'] for r in s['files'])==s['total_bytes']==432827661
assert s['transport_payload_budget_bytes']==8*1024**3 and s['owned_tree_limit_bytes']==5*1024**3 and s['disk_floor_bytes']==10*1024**3
assert s['total_bytes']+16*1024**2<5*1024**3 and 2*s['total_bytes']+16*1024**2<8*1024**3
payload={r['path']:r for r in bodies['files']};assert len(payload)==5 and sum(r['bytes'] for r in payload.values())==432741928
for row in s['files']:
 p=R/row['path'];assert p.resolve(strict=True)==p
 st=p.lstat();assert stat.S_ISREG(st.st_mode) and st.st_nlink==row['nlink']==1 and st.st_size==row['bytes'] and stat.S_IMODE(st.st_mode)==row['mode']
 assert [st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns]==row['stat_identity']
 if row['path'] in payload:
  v=payload[row['path']];assert row['bytes']==v['bytes'] and row['sha256']==v['sha256'] and [st.st_dev,st.st_ino,st.st_nlink,st.st_size,st.st_mtime_ns,st.st_ctime_ns]==v['stat_identity']
 else:raw(p,row['sha256'])
for d in s['directories']:
 p=R/d['path'];assert p.resolve(strict=True)==p and p.is_dir() and stat.S_IMODE(p.stat().st_mode)==d['mode']
N=review['identity'];roots=[R/'research_runs'/N,R/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/N,R/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/N]
actualfiles=set();actualdirs=set()
for root in roots:
 for base,dirs,names in os.walk(root,followlinks=False):
  actualdirs.add(str(Path(base).relative_to(R)))
  for n in dirs+names:assert not (Path(base)/n).is_symlink()
  actualfiles.update(str((Path(base)/n).relative_to(R)) for n in names)
assert actualfiles=={r['path'] for r in s['files']} and actualdirs=={d['path'] for d in s['directories']}
assert not subprocess.check_output(['systemctl','--user','list-units','--state=active,activating','--no-legend','onchain-replication-*.service'],text=True).strip()
for cp in (R/'research_runs').glob('*/claim.json'):
 if not cp.with_name('complete.json').exists() and not cp.with_name('failed.json').exists():
  assert cp.resolve(strict=True)==cp and cp.stat().st_size<4*1024**2; c=json.loads(cp.read_bytes());assert isinstance(c.get('program_id'),str) and c['program_id'] and c['program_id']!='onchain-paper-replication-2026-09-24'
for pid in review['all_known_recorded_pids_checked_absent']:assert not Path('/proc',str(pid)).exists()
for n in ['preflight01.json','launch-attempt01.json','guard01','intent.json','complete.json','failed.json','outer-exit01.json']:assert not os.path.lexists(T/n)
from tradingagents.research.onchain_replication.resources import mem_available
mem=mem_available();free=shutil.disk_usage(R).free;assert mem>=int(3.5*1024**3) and free>=10*1024**3+s['total_bytes']+16*1024**2
# Reuse already independently closed exact source inverses, bind their receipts.
Q=F/'real-data-pilot-may30-ledger-relocation-review01-2026-10-06/continuation-actual-outcome01'
for n in ['PRESERVATION_SOURCE_CHECK01.json','KEEP_SOURCE_CHECK01.json','OUTCOME_MANIFEST01.json']:obj(Q/n)
assert e['connection']['path'] not in E
check={'decision':'pass','selection_sha256':e['selection']['sha256'],'count':24,'directories':6,'payloads':5,'payload_bytes':432741928,'total_bytes':432827661,'source_pins':12,'current_memory_available_bytes':mem,'current_root_free_bytes':free,'active_native_units':0,'fresh_identity':True,'connection_body_reads':0,'real_payload_reads':0,'transport_or_native_executed':False}
put('CHECK01.json',check);E[str((O/'CHECK01.json').relative_to(R))]=hashlib.sha256((O/'CHECK01.json').read_bytes()).hexdigest()
put('RELEASE_REVIEW01.json',{'decision':'accepted','identity':e['identity'],'envelope_sha256':pin,'evidence':E,'scope':'One ordinary preservation of exact24new regulars+6directory name/mode descriptors; five genuine new graph arrays. All originals and complete fresh recoveries retained. Historical failed scope/relocated ledger excluded via existing accepted recovery. Current Git/source/Root caller evidence separately committed.','qualification':'Source/entry release only; genuine committed remote readback, native/RAM/disk/namespace checks repeat before one launch. BYTE fresh recovery and restoration descriptors only, not POSIX reconstruction or numerical/scientific authority. Connection reference inherited unchanged/local-only; reviewer did not open it.'})
print(json.dumps(check));print(hashlib.sha256((O/'RELEASE_REVIEW01.json').read_bytes()).hexdigest())
