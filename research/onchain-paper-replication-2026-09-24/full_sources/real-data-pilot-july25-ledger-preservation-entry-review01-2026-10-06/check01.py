from pathlib import Path
import ast,hashlib,json,os,stat,shutil,subprocess,platform,importlib.metadata,datetime
R=Path.cwd();B=R/'research/onchain-paper-replication-2026-09-24';F=B/'full_sources';H=Path(__file__).resolve().parent;D=B/'storage/real-pilot-july25-ledger-preservation-20261006-01';A=F/'real-data-pilot-july25-ledger-preservation-preparation01-2026-10-06';evidence={}
def sig(s):return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
def raw(p,pin=None):
 p=Path(p);p=p if p.is_absolute() else R/p;relative=str(p.relative_to(R));assert 'connection.json' not in relative and '/keys/' not in relative and '/apis/' not in relative
 s=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2
 b=p.read_bytes();assert sig(s)==sig(p.lstat());sha=hashlib.sha256(b).hexdigest();assert pin is None or pin==sha,(relative,sha,pin);evidence[relative]=sha;return b
def obj(p,pin=None):return json.loads(raw(p,pin))
e=obj(D/'envelope01.json','2956aaa5390e96708d80e02356154d328ee216a138ffb83387ed197707fc6190');c=obj(D/'selection01.json','46994cdd6add610e1c0c32dd2bcaeb7b79a9067fa39cdc0539692e8bef52b446');binding=obj(D/'BINDING01.json')
manifest=obj(A/'MANIFEST01.json','7ef7ebc2e7e1ccd16686fad6ad209593d2d01a3a58744d105eaec5e3a46b9f42')
for name,row in manifest['files'].items():assert len(raw(A/name,row['sha256']))==row['bytes']
inv=obj(A/'INVERSE01.json')
for name,row in inv['files'].items():
 old=raw(row['before']['path'],row['before']['sha256']).decode();new=raw(row['candidate']['path'],row['candidate']['sha256']).decode()
 before='real-pilot-sixth-graph-preservation-20261006-01';after='real-pilot-july25-ledger-preservation-20261006-01'
 assert old.count(before)==new.count(after)==1 and old.replace(before,after)==new
 assert ast.dump(ast.parse(old))==ast.dump(ast.parse(new.replace(after,before)))
assert raw(D/'entry01.py')==raw(A/'entry01.py')
for path,sha in e['source_files'].items():raw(path,sha)
for ref in e['evidence']:raw(ref['path'],ref['sha256'])
for key in ('entry','envelope','selection','source_manifest','historical_local_byte_audit'):raw(binding[key]['path'],binding[key]['sha256'])
assert e['local_only_evidence']==[e['connection']['path']] and e['connection']['path'] not in e['source_files']
oldenv=obj(B/'storage/real-pilot-sixth-graph-preservation-20261006-01/envelope01.json')
assert e['connection']==oldenv['connection'] and e['environment']==oldenv['environment']
env=obj(e['environment']['path'],e['environment']['sha256'])
actual_env={'python':platform.python_version(),'cpu_count':os.cpu_count(),'lock_sha256':hashlib.sha256(raw('uv.lock')).hexdigest(),'packages':{p:importlib.metadata.version(p) for p in ('numpy','scipy','pyarrow','torch','scikit-learn')}}
assert env==actual_env
# Current None/native-default API bodies are the independently reviewed unchanged candidates.
review03=obj(F/'real-data-pilot-residual-enforcement-review01-2026-10-06/candidate-review03/REVIEW01.json','58475dfbb52798c98751dbbfa502828f08c98c366b7e7a9ef2e299f212f83fb2')
assert review03['decision']=='accepted-source-only-exact-boundary-successor'
for name in ('resources.py','workflow_storage.py'):
 assert raw('tradingagents/research/onchain_replication/'+name)==raw(F/'real-data-pilot-residual-enforcement-candidate02-2026-10-06'/name)
assert c['count']==len(c['files'])==1 and c['total_bytes']==c['max_body_bytes']==3755212800
assert c['identity']==e['identity']==binding['historical_disposition'].get('new_identity',e['identity'])=='real-pilot-july25-ledger-preservation-20261006-01'
row=c['files'][0];p=R/row['path'];s=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and sig(s)==row['stat_identity'] and stat.S_IMODE(s.st_mode)==row['mode']==420
assert s.st_size==row['bytes']==3755212800 and row['sha256']=='ef3dd69023de071cdaec0780b2fbd35463f2832c816ad204aa07cf2c88594235'
invest=obj(e['evidence'][0]['path'],e['evidence'][0]['sha256']);assert invest['exact_original']['stat7']==[s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,stat.S_IMODE(s.st_mode)]
audit=obj(binding['historical_local_byte_audit']['path']);assert audit=={'status':'verified','path':str(p),'bytes':row['bytes'],'sha256':row['sha256']}
closed=B/'pilot_successor_02/closure-01';contract=obj(closed/'hash-audit-01-contract.json');complete=obj(closed/'hash-audit-01-complete.json')
assert complete['status']=='complete' and complete['members']==17 and complete['contract_sha256']==evidence[str((closed/'hash-audit-01-contract.json').relative_to(R))]
assert contract['members'][str(p)]=={'bytes':row['bytes'],'sha256':row['sha256']}
index=obj(contract['artifact_index'],contract['artifact_index_sha256']);assert index[str(p)]==contract['members'][str(p)]
failed=obj('research_runs/eth-paper-resource-pilot-20260924-02/failed.json');assert failed['status']=='failed' and failed['claim_sha256']==binding['original_failed_claim_sha256']=='05d769f6f50a65c2cf3eeed569077eb84e3871b1e7c23ad3504eed461a0565ca'
ledger=obj(R/'research_artifacts/onchain-paper-replication-2026-09-24/pilot-02/postmortem/cell-ledger.json');july=[v for v in ledger if v['id']=='decode_graph-2022-07-25'];assert len(july)==1 and july[0]['status']=='unavailable'
assert binding['historical_disposition']['committed_ledger_row_count'] is None and binding['historical_disposition']['ledger_is_admitted_recovery_prefix'] is False
assert c['disk_floor_bytes']==10*1024**3 and c['owned_tree_limit_bytes']==5*1024**3 and c['transport_payload_budget_bytes']==8*1024**3
# Existing GET rounds up by one32KiB block; reserve another16MiB for metadata framing.
minimum_payload=row['bytes']+(row['bytes']//32768+1)*32768;assert minimum_payload+16*1024**2<8*1024**3 and row['bytes']+16*1024**2<5*1024**3
for name in ('preflight01.json','launch-attempt01.json','guard01','intent.json','complete.json','failed.json','outer-exit01.json','RELEASE_REVIEW01.json'):assert not os.path.lexists(D/name)
units=subprocess.check_output(['systemctl','--user','list-units','--state=active,activating','--no-legend','onchain-replication-*.service'],text=True);assert not units.strip()
active=[]
for claim in (R/'research_runs').glob('*/claim.json'):
 if claim.with_name('complete.json').exists() or claim.with_name('failed.json').exists():continue
 v=obj(claim);assert isinstance(v.get('program_id'),str) and v['program_id']!='onchain-paper-replication-2026-09-24';active.append(v['program_id'])
mem=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))*1024;free=shutil.disk_usage(R).free
assert mem>=int(3.5*1024**3) and free>=10*1024**3+row['bytes']+16*1024**2
result={'decision':'accepted','identity':c['identity'],'count':1,'selected_bytes':row['bytes'],'current_stat_identity':sig(s),'mode':420,'nlink':1,'historical_status':'failed','july25_decode_graph_status':'unavailable','recovery_prefix_admitted':False,'ledger_row_count':None,'literal_and_ast_inverse':True,'current_source_pins':len(e['source_files']),'runtime_inventory_equal':True,'payload_minimum_with_rounded_get':minimum_payload,'metadata_margin_bytes':16*1024**2,'host_mem_available_bytes':mem,'disk_free_bytes':free,'no_active_native_units':True,'other_active_programs':active,'namespace_unused':True,'payload_reads':0,'connection_body_reads':0,'qualification':'Ordinary exact-ledger preservation only; no prior external recovery, SQLite consistency, scientific validity, completed graph, immutable-writer or capacity claim. Actual future entry must recheck committed remote head, source/runtime, resources, one-use namespace and genuine guard. Both original and fresh GET remain retained. Envelope qualification retains template prose about null refs; actual hashed nonnull refs and current-bound status govern this exact review.','evidence':evidence,'at':datetime.datetime.now(datetime.UTC).isoformat()}
with (H/'CHECK01.json').open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k!='evidence'}))
