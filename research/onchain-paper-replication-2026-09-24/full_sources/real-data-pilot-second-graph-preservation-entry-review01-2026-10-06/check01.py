import datetime,hashlib,json,os,stat,subprocess,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
B=ROOT/'research/onchain-paper-replication-2026-09-24';F=B/'full_sources';HERE=Path(__file__).parent
S=B/'storage/real-pilot-second-graph-preservation-20261006-01'
P=F/'real-data-pilot-second-graph-preservation-preparation01-2026-10-06'
R=F/'real-data-pilot-second-graph-preservation-root01-2026-10-06'
def sha(p):
 assert p.stat().st_size<4*1024**2 and p.name!='connection.json'
 return hashlib.sha256(p.read_bytes()).hexdigest()
def j(p):return json.loads(p.read_bytes())
E=j(S/'envelope01.json');C=j(S/'selection01.json')
assert sha(S/'envelope01.json')=='8cf53e8ad2373d3bbd7c5f0d0b49a37d233a7e81521ae9c1116479bf7496da79'
assert sha(S/'selection01.json')=='96f5605613d4d9c537d4d130917d3af04f9a8005cc385b5a0576c60cf673c43a'
old=B/'storage/real-pilot-first-graph-preservation-20261006-01/entry03.py'
s=old.read_text()
assert sha(old)=='fc733b766a86c176e6572432e20129b2e584a289c59e673bbad599d14ce54b37'
for a,b in [('real-pilot-first-graph-preservation-20261006-01',C['identity']),('envelope03.json','envelope01.json'),('RELEASE_REVIEW03.json','RELEASE_REVIEW01.json'),('entry03.py','entry01.py')]:s=s.replace(a,b)
assert s==(S/'entry01.py').read_text()==(P/'entry01.py').read_text()
oldkeep=F/'real-data-pilot-first-graph-preservation-worker01-2026-10-06/keep.py'
assert sha(oldkeep)=='56550299510bb99c3b01eb29e648cd7206ccc475d826af498b54a256e2d36b88'
assert oldkeep.read_text().replace('real-pilot-first-graph-preservation-20261006-01',C['identity'])==(P/'keep.py').read_text()
original=(P/'prepare01.py').read_text();current=(R/'prepare02.py').read_text()
assert current==original.replace("review['cleanup']['guard_cleanup_verified']","review['cleanup']['original_guard_cleanup_verified']")
correction=j(R/'CORRECTION02.json');assert sha(P/'prepare01.py')==correction['original_sha256'] and sha(R/'prepare02.py')==correction['successor_sha256']
for p,h in E['source_files'].items():assert sha(ROOT/p)==h,p
for ref in E['evidence']+[E['environment'],E['selection']]:assert sha(ROOT/ref['path'])==ref['sha256']
review=j(ROOT/C['graph_outcome_review']['path']);bod=j(ROOT/C['independent_body_hash']['path'])
assert review['decision']=='accepted' and review['cleanup']['original_guard_cleanup_verified'] is True
assert review['evidence'][C['independent_body_hash']['path']]==C['independent_body_hash']['sha256']
known={r['path']:r for r in bod['files']};seen=set();small=0
for r in C['files']:
 p=ROOT/r['path'];st=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(st.st_mode)
 assert [st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns]==r['stat_identity']
 assert stat.S_IMODE(st.st_mode)==r['mode'] and st.st_nlink==r['nlink']==1 and st.st_size==r['bytes']
 if r['path'] in known:
  k=known[r['path']];assert [st.st_dev,st.st_ino,st.st_nlink,st.st_size,st.st_mtime_ns,st.st_ctime_ns]==k['stat_identity']
  assert all(r[x]==k[x] for x in ('path','sha256','bytes','mode'));seen.add(r['path'])
 else:assert sha(p)==r['sha256'];small+=1
assert seen==set(known) and len(seen)==6 and small==30
actualfiles=set();actualdirs=set()
graph=review['experiment']
roots=[ROOT/'research_runs'/graph,ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/graph,ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/graph]
for base in roots:
 for directory,dirs,files in os.walk(base,followlinks=False):
  p=Path(directory);assert p.resolve(strict=True)==p;actualdirs.add(str(p.relative_to(ROOT)))
  for name in files:actualfiles.add(str((p/name).relative_to(ROOT)))
assert actualfiles=={r['path'] for r in C['files']} and actualdirs=={r['path'] for r in C['directories']}
for r in C['directories']:
 st=(ROOT/r['path']).lstat();assert stat.S_ISDIR(st.st_mode) and stat.S_IMODE(st.st_mode)==r['mode']
assert len(actualfiles)==C['count']==36 and len(actualdirs)==8
assert sum(r['bytes'] for r in C['files'])==C['total_bytes']==4204068745
assert C['transport_payload_budget_bytes']==8*1024**3 and 2*C['total_bytes']+16*1024**2<8*1024**3
assert C['owned_tree_limit_bytes']==5*1024**3 and C['total_bytes']+16*1024**2<5*1024**3
assert C['disk_floor_bytes']==10*1024**3
assert E['local_only_evidence']==[E['connection']['path']] and E['connection']['path'] not in E['source_files']
# Execute only metadata selector to authenticate the one-field correction against actual closed evidence.
ns={'__name__':'reviewed_metadata_selector'};exec(compile(current,str(R/'prepare02.py'),'exec'),ns)
assert ns['select'](ROOT,C['graph_outcome_review'],C['independent_body_hash'])==C
names=('preflight01.json','launch-attempt01.json','guard01','intent.json','complete.json','failed.json','outer-exit01.json')
assert not any(os.path.lexists(S/n) for n in names)
units=subprocess.run(['systemctl','--user','list-units','--state=active,activating','--no-legend','onchain-replication-*.service'],capture_output=True,text=True,check=True).stdout
assert not units.strip()
active=[]
for p in (ROOT/'research_runs').glob('*/claim.json'):
 if not p.with_name('complete.json').exists() and not p.with_name('failed.json').exists():
  assert not p.is_symlink() and p.stat().st_size<4*1024**2
  q=j(p);program=q.get('program_id');assert isinstance(program,str) and program
  assert program!='onchain-paper-replication-2026-09-24';active.append({'claim':str(p.relative_to(ROOT)),'program_id':program})
mem=int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024
free=shutil.disk_usage(ROOT).free;required=10*1024**3+C['total_bytes']+16*1024**2
assert mem>=int(3.5*1024**3) and free>=required
out={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'decision':'pass','entry_literal_inverse':True,'keep_identity_only_inverse':True,'selector_single_key_inverse':True,'actual_corrected_metadata_selection_equal':True,'original_selector_refusal':correction['actual_red'],'root_reported_green_tool':'a2b40c','source_pins':len(E['source_files']),'payload_hashes_reused':6,'payload_bytes_read':0,'small_metadata_hashes':small,'current_file_stat_mode_joins':36,'current_directory_mode_joins':8,'selected_bytes':C['total_bytes'],'transport_put_get_body_bytes':2*C['total_bytes'],'transport_control_allowance_bytes':16*1024**2,'transport_total_bound_bytes':8*1024**3,'owned_scratch_bound_bytes':5*1024**3,'fresh_namespaces_absent':list(names),'active_native_units':[],'unrelated_open_claims':active,'mem_available_bytes':mem,'disk_free_bytes':free,'startup_disk_required_bytes':required,'connection_read':False,'runtime_inventory_repeated':False,'qualification':'Instantaneous stat/resource observations, not writer exclusion, transfer success or whole capacity. Entry revalidates actual committed/remote source, runtime and native resources before its sole attempt.'}
(HERE/'CHECK01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps(out,sort_keys=True))
