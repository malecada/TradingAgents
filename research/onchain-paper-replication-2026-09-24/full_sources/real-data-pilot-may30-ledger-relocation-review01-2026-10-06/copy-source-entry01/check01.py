"""COPY-only source/entry review, tiny offline bytes only; no real body or native call."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,stat,sys
from tradingagents.research.onchain_replication.environment import inventory
R=Path.cwd().resolve();D=Path(__file__).resolve().parent;F=D.parents[1];A=F/'real-data-pilot-may30-ledger-relocation-preparation01-2026-10-06';T=F/'real-data-pilot-may30-ledger-relocation01-2026-10-06'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert h(A/'MANIFEST01.json')=='c14d4fb16e3ec0801d7506baa4f74cf665c83f9b82ce9afc1662750327393195'
for n,row in json.loads((A/'MANIFEST01.json').read_bytes())['files'].items():assert h(A/n)==row['sha256'] and (A/n).stat().st_size==row['bytes']
for n in ('relocate01.py','entry01.py','SELECTION01.json'):assert (A/n).read_bytes()==(T/n).read_bytes()
assert h(T/'copy-envelope01.json')=='d18a382896fe9e2b57a001e373ae173c9a5c25e25e3be7fcf58dd574fbc48d5a'
e=json.loads((T/'copy-envelope01.json').read_bytes());E=dict(e['source_files'])
for v in e['evidence']+[e['selection'],e['environment']]:E[v['path']]=v['sha256']
for p,pin in E.items():assert h(R/p)==pin
assert len(e['source_files'])==12 and len(e['evidence'])==17 and e['phase']=='copy'
assert inventory(R)==json.loads((R/e['environment']['path']).read_bytes())
sp=importlib.util.spec_from_file_location('candidate_copy',T/'relocate01.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
c=json.loads((T/'SELECTION01.json').read_bytes());assert c['status']=='FROZEN_FOR_REVIEW';_,row=m.validate(c);m.room(c,m.BYTES)
assert not os.path.lexists(m.TARGET.parent)
for n in ('copy-preflight01.json','copy-launch-attempt01.json','copy-attempt01.json','copy-complete01.json','copy-failed01.json','copy-outer-exit01.json','copy-guard01'):assert not os.path.lexists(T/n)
# Exact small source function on owned synthetic files, without native/authority calls.
fixture=D/'synthetic';fixture.mkdir();source=fixture/'source.bin';data=bytes(range(251))*261+bytes(range(26));source.write_bytes(data);source.chmod(0o640);s=source.stat()
r={'path':str(source),'bytes':len(data),'sha256':h(source),'stat_identity':[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns],'mode':stat.S_IMODE(s.st_mode)}
target=fixture/'copy.bin';result=m.stream_copy(source,target,r,tick=lambda remaining:None,chunk=4096);assert target.read_bytes()==data and source.read_bytes()==data and result['stat_identity'][6]==0o640
cases=[]
def fails(label,func):
 try:func()
 except (ValueError,FileExistsError,RuntimeError) as ex:cases.append({'case':label,'error':type(ex).__name__,'message':str(ex)})
 else:raise AssertionError(label+' accepted')
fails('exclusive-existing',lambda:m.stream_copy(source,target,r,tick=lambda _:None))
link=fixture/'link.bin';link.symlink_to(source.name);fails('symlink-target',lambda:m.stream_copy(source,link,r,tick=lambda _:None))
bad=copy.deepcopy(r);bad['sha256']='0'*64;fails('wrong-content',lambda:m.stream_copy(source,fixture/'wrong.bin',bad,tick=lambda _:None))
def interrupt(_):raise RuntimeError('synthetic interruption')
fails('interruption',lambda:m.stream_copy(source,fixture/'partial.bin',r,tick=interrupt))
assert source.read_bytes()==data and (fixture/'wrong.bin').exists() and (fixture/'partial.bin').exists()
tree=ast.parse((T/'relocate01.py').read_bytes())
for node in tree.body:
 if isinstance(node,ast.FunctionDef) and node.name in ('copy','stream_copy'):
  assert not any(isinstance(n,ast.Attribute) and n.attr in ('unlink','remove','rmdir') for n in ast.walk(node))
assert not any(x in sys.modules for x in ('numpy','torch','sqlite3','pyarrow'))
result={'decision':'accepted-copy-only','source_manifest':h(A/'MANIFEST01.json'),'installed_sources_selection_exact':True,'source_pins':12,'envelope_evidence':17,'current_runtime_metadata_equal':True,'actual_original_stat_joins':3,'exclusive_destination_absent':True,'copy_source_has_no_unlink':True,'synthetic_bytes':len(data),'synthetic_refusals':cases,'actual_payload_reads':0,'native_network_or_git_calls':0,'retire_phase':'WITHHELD: post-unlink failure accounting requires correction'}
(D/'CHECK01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
for p in [T/'copy-envelope01.json',A/'MANIFEST01.json',D/'CHECK01.json']:E[str(p.relative_to(R))]=h(p)
release={'decision':'accepted','identity':m.ID,'phase':'copy','envelope_sha256':h(T/'copy-envelope01.json'),'evidence':dict(sorted(E.items())),'scope':'ONE exclusive fixed-destination COPY plus independent fresh destination readback; original retained, no unlink. RETIRE explicitly not released.','preconditions':['Exact committed source/envelope/selection/release and actual remote HEAD readback enforced by entry','Fresh inactive-native/registered-consumer/current-stat checks and physical floor/RAM/startup checks','Both Root/Data native floor controls and exact worker guard; one-use identity'],'data_body_scope':{'bytes':m.BYTES,'sha256':m.SHA,'target':str(m.TARGET),'device':66307,'source_retained':True,'outside_control_watch':'Fixed bounded Data payload outside HERE watch; exact copy extent/hash/readback and both-volume floor checks apply'},'historical_recovery':'Accepted failed-scope full30 BYTE c6edef and original-body proof reused; no new scientific integrity or capacity assertion','retirement_authority':False,'numerical_authority':False}
(D/'copy-RELEASE_REVIEW01.json').write_text(json.dumps(release,sort_keys=True,indent=2)+'\n');print(json.dumps({'release_sha256':h(D/'copy-RELEASE_REVIEW01.json'),'check_sha256':h(D/'CHECK01.json'),'synthetic_refusals':len(cases),'synthetic_bytes':len(data)}))
