from pathlib import Path
import ast,hashlib,importlib.util,json,os,shutil,stat
from tradingagents.research.onchain_replication.environment import inventory
D=Path(__file__).resolve().parent;F=D.parent;M=F.parents[2];B=F.parent;C=F/'real-data-pilot-fourth-graph-preservation-preparation01-2026-10-06';S=B/'storage/real-pilot-fourth-graph-preservation-20261006-01';evidence={}
def raw(p):
 s=p.lstat();assert p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<4*1024**2
 b=p.read_bytes();assert all(getattr(p.lstat(),k)==getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns'));evidence[str(p.relative_to(M))]=hashlib.sha256(b).hexdigest();return b
def h(p):return hashlib.sha256(raw(p)).hexdigest()
def read(p):return json.loads(raw(p))
assert h(S/'envelope01.json')=='faa3c4926f3694d1542cdad108e679a1ba97a4e743e1152051c11b4d117658ee';env=read(S/'envelope01.json');assert h(S/'selection01.json')=='a0f725bc4155b9b2e68a28b37c3ded8264c22c61235bb1f5da5f2863b2d18c7e';selection=read(S/'selection01.json')
assert h(S/'entry01.py')==h(C/'entry01.py')=='44a394c90961aa528674e401686aeed12ff0ba72c730cec2ccfba0786e7f0da8'
assert len(env['source_files'])==12
for path,sha in env['source_files'].items():assert h(M/path)==sha
for ref in env['evidence']+[env['environment'],env['helper'],env['transport'],env['selection']]:assert h(M/ref['path'])==ref['sha256']
assert env['scanner_sha256']==env['source_files']['tradingagents/research/onchain_replication/workflow_storage.py']=='a6323c64c903931d7f2c7d18c5d81d8479d377c82e9eaeacc8580a5c4e99d67f'
old=read(B/'storage/real-pilot-third-graph-preservation-20261006-01/envelope01.json');assert env['connection']==old['connection'] and env['local_only_evidence']==[env['connection']['path']] and env['connection']['path'] not in env['source_files']
oldcore={p:v for p,v in old['source_files'].items() if 'real-data-pilot-third-graph-preservation-preparation01' not in p and 'storage/real-pilot-third-graph-preservation-' not in p};newcore={p:v for p,v in env['source_files'].items() if 'real-data-pilot-fourth-graph-preservation-preparation01' not in p and 'storage/real-pilot-fourth-graph-preservation-' not in p};assert oldcore==newcore
assert inventory(M)==read(M/env['environment']['path'])
# Actual bounded selector; metadata/current stat only, never payload content.
p=C/'prepare01.py';spec=importlib.util.spec_from_file_location('actual_fourth_preservation_selector',p);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
actual=mod.select(M,selection['graph_outcome_review'],selection['independent_body_hash']);assert actual==selection
assert selection['count']==len(selection['files'])==36 and len(selection['directories'])==8 and selection['total_bytes']==3720766030
body=read(D/'BODY_HASH01.json');by={r['path']:r for r in body['files']};assert len(by)==6
for row in selection['files']:
 p=M/row['path'];s=p.lstat();assert [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]==row['stat_identity'] and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==row['mode']
 if row['path'] in by:assert row['sha256']==by[row['path']]['sha256'] and row['bytes']==by[row['path']]['bytes']
 else:assert h(p)==row['sha256']
for row in selection['directories']:
 p=M/row['path'];assert p.resolve()==p and p.is_dir() and stat.S_IMODE(p.lstat().st_mode)==row['mode']
for name in ('preflight01.json','launch-attempt01.json','guard01','intent.json','complete.json','failed.json','outer-exit01.json'):assert not os.path.lexists(S/name)
# Execute only exact entry frozen/body predicates; no launch/worker/transport/native call.
funcs=[x for x in ast.parse(raw(S/'entry01.py')).body if isinstance(x,ast.FunctionDef) and x.name in ('body','frozen')];g={'Path':Path,'ROOT':M,'HERE':S,'ID':S.name,'json':json,'hashlib':hashlib,'inventory':inventory};exec(compile(ast.Module(body=funcs,type_ignores=[]),'actual-entry-frozen-functions','exec'),g);returned=g['frozen']();assert returned==(env,selection,h(S/'envelope01.json'))
root=read(F/'real-data-pilot-fourth-graph01-2026-10-06/ROOT_TERMINAL01.json');assert root['actual_root_tool_exit_code']==0 and len(root['selected_recorded_pids'])==3 and all(not Path('/proc',str(x)).exists() for x in root['selected_recorded_pids'])
raw(S/'ROOT_BINDING01.json');read(D/'SOURCE_REVIEW01.json');read(D/'OUTCOME_REVIEW01.json')
free=shutil.disk_usage(M).free;mem=int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
result={'decision':'pass-source-entry-binding','envelope_sha256':h(S/'envelope01.json'),'selection_sha256':h(S/'selection01.json'),'source_pins':12,'selected_files':36,'selected_bytes':3720766030,'directories':8,'six_body_proofs_reused':6,'payload_reads':0,'actual_selector_and_frozen_predicates_passed':True,'connection':'Inherited exact private reference only; body not read or parsed by reviewer, no credential inspection. Actual worker validates local hash before using transport.','namespace_absent':True,'observed_free_bytes':free,'required_free_bytes':10*1024**3+selection['total_bytes']+16*1024**2,'observed_mem_available_bytes':mem,'required_startup_bytes':int(3.5*1024**3),'future_fresh_preflight_required':True,'no_backup_execution_or_recovery_claim':True,'evidence':evidence}
(D/'ENTRY_CHECK01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='evidence'}))
