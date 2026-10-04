import ast,hashlib,importlib.util,json,os,time
from pathlib import Path
H=Path(__file__).resolve().parent;spec=importlib.util.spec_from_file_location('pure_compatibility',H/'operational_source_compatibility.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);rows=[]
def ck(n,v):
 rows.append({'check':n,'passed':bool(v)})
 assert v,n
old={'source_commit':m.HISTORICAL_SOURCE,'source_hashes':sorted(set(m.OLD_MAP.values())),'opaque_science':'fixed'}
readback=json.loads((H/'SOURCE_READBACK01.json').read_text());target=readback['target_map'];new=old|{'source_commit':'1'*40,'source_hashes':sorted(set(target.values()))}
for name,fn in [('original_financial_wrapper_fixture.py','_parent'),('original_training.py','_reserve')]:
 node=next(n for n in ast.parse((H/name).read_text()).body if isinstance(n,ast.FunctionDef) and n.name==fn)
 candidates=[n for n in ast.walk(node) if isinstance(n,ast.Compare) and isinstance(n.left,ast.DictComp) and 'source_commit' in ast.unparse(n)]
 ck('unique real original scientific expression '+name,len(candidates)==1)
 expr=candidates[0];result=eval(compile(ast.Expression(expr),name,'eval'),{}, {'value':{'provenance':old},'prov':new,'old':old,'provenance':new})
 ck('actual AST original source edge refuses '+name,result is (name=='original_training.py'))
 m.validate_relation(m.OLD_MAP,target,old,new);ck('exact map relation accepts opaque metadata after original RED '+name,True)
# Real nested descriptor closure. No authority objects are created.
body=H/'owned01'/'body';realclose=os.close;realread=os.read
primary=KeyboardInterrupt('original');errors=[OSError('first close'),SystemExit('second close')];seen=[]
def close(fd):
 realclose(fd);seen.append(fd)
 if len(seen)<=2:raise errors[len(seen)-1]
def read(fd,n):raise primary
m.os.close=close;m.os.read=read
try:
 try:m._read(body,{'begun':time.monotonic(),'bytes':0})
 except BaseException as caught:
  ck('nested two close failures retain first fatal',caught is primary)
  values=BaseException.__dict__['__dict__'].__get__(caught)
  ck('both exact secondary objects retained',values['storage_cleanup_errors']==tuple(errors))
 else:raise AssertionError('expected first fatal')
finally:m.os.close=realclose;m.os.read=realread
ck('nested descriptor cleanup attempts complete',len(seen)==len(body.parts))
for fd in seen:
 try:os.fstat(fd)
 except OSError:pass
 else:raise AssertionError('open descriptor')
ck('nested all descriptors absent',True)
# Copy source-only API evidence; no API is imported or called.
SRC=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');api=H/'original_api';api.mkdir();pins={}
for rel in ['tradingagents/research/lifecycle.py','tradingagents/research/admission.py','tradingagents/research/verify.py','tradingagents/research/onchain_replication/checkpoints.py','tradingagents/research/onchain_replication/cache.py','tradingagents/research/onchain_replication/job.py']:
 raw=(SRC/rel).read_bytes();assert len(raw)<4*1024**2;assert hashlib.sha256(raw).hexdigest()==m.OLD_MAP[rel];(api/Path(rel).name).write_bytes(raw);pins[rel]=hashlib.sha256(raw).hexdigest()
(H/'ORIGINAL_API_PINS01.json').write_text(json.dumps(pins,indent=2,sort_keys=True)+'\n')
closure=json.loads((SRC/'fixture_inputs/financial_wrapper_claimedrun01/source_closure.json').read_text());closure['installed']=target
(H/'SOURCE_CLOSURE_DRAFT01.json').write_text(json.dumps(closure,indent=2,sort_keys=True)+'\n')
proofs={r:{'schema_version':1,'kind':r,'policy_sha256':None,'historical_map_sha256':m.sha(m.canonical(m.OLD_MAP)),'target_map_sha256':m.sha(m.canonical(target)),'checker_sha256':readback['candidate_helper_sha256'],'decision':None} for r in m.PROOF_ROLES}
(H/'PROOF_ROLES_DRAFT01.json').write_text(json.dumps(proofs,indent=2,sort_keys=True)+'\n')
(H/'CHECKS03.json').write_text(json.dumps({'status':'PASS_OPAQUE_SOURCE_ONLY','rows':rows,'count':len(rows)},indent=2,sort_keys=True)+'\n')
print(json.dumps({'checks':len(rows),'status':'PASS_OPAQUE_SOURCE_ONLY'}))
