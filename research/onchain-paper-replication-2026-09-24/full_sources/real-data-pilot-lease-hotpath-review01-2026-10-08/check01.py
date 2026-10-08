import ast,contextlib,hashlib,json,sys,types
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[3];A=P.parent/'real-data-pilot-lease-hotpath01-2026-10-08';M=R/'tradingagents/research/onchain_replication/imported_authority_lease.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before=(A/'baseline.py').read_text();after=(A/'imported_authority_lease.py').read_text();inverse=after.replace("optimize=sys.flags.optimize);codes={}","optimize=sys.flags.optimize);codes=[]").replace('codes.setdefault(code.co_name,[]).append(code)','codes.append(code)').replace('for candidate in codes.get(code.co_name,())','for candidate in codes')
assert inverse==before==M.read_text();assert sha(A/'imported_authority_lease.py')=='bf3c3669a6907305b351adb43867822f9500d84d2c5d3b66b16a5650a0291b0a'
def require(ok,why):
 if not ok:raise ValueError(why)
def extract(text):
 t=ast.parse(text);ns=dict(contextlib=contextlib,hashlib=hashlib,sys=sys,types=types,Path=Path,require=require,AUTHORITY_CLASSES={'Owner'})
 exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in ['_loaded','_authenticate_loaded']],type_ignores=[]),'isolated_source','exec'),ns);return ns
B=extract(before);C=extract(after);p=P/'fixture.py';p.write_text('import contextlib\ndef same(): return 1\ndef outer():\n def same(): return 2\n return same\nclass Owner:\n def same(self): return 3\n @property\n def prop(self): return 4\n@contextlib.contextmanager\ndef held():\n yield 5\n@contextlib.contextmanager\ndef other():\n yield 6\n')
m=types.ModuleType('tiny_fixture');m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),vars(m));sys.modules[m.__name__]=m;root=P;sources={'fixture.py':sha(p)};loaded=B['_loaded'](root,sources);checks=[]
read_original=Path.read_bytes
def compare(label,values=loaded,pins=sources):
 outcomes=[]
 for module in [B,C]:
  events=[]
  def read(path):events.append(('read',str(path)));return read_original(path)
  Path.read_bytes=read
  try:module['_authenticate_loaded'](values,pins,root);result=None
  except Exception as e:result=(type(e).__name__,str(e))
  finally:Path.read_bytes=read_original
  outcomes.append((result,events))
 assert outcomes[0]==outcomes[1],(label,outcomes);checks.append({'case':label,'outcome':outcomes[0]})
compare('authored_duplicate_names_properties_repeated_wrappers')
for code in [m.same.__code__,m.outer().__code__,m.Owner.same.__code__]:
 compare('equal_name_distinct_nested_members',{m.__name__:(m,p,(('member',m.same,code),))})
for label,code in [('wrong_name',m.same.__code__.replace(co_name='absent')),('wrong_filename',m.same.__code__.replace(co_filename='wrong')),('wrong_constants',m.same.__code__.replace(co_consts=(None,999)))]:
 compare(label,{m.__name__:(m,p,(('bad',m.same,code),))})
compare('source_hash_precedes_code_refusal',{m.__name__:(m,p,(('bad',m.same,m.same.__code__.replace(co_name='absent')),))},{'fixture.py':'0'*64})
m.held.__wrapped__=m.same;compare('wrapper_refusal_order')
m.held.__wrapped__=m.held.__closure__[0].cell_contents
p.write_text(p.read_text()+'\n# changed between calls\n');compare('next_call_source_change_refused')
# Actual registered .py source census: compile only, never import/execute bodies.
gate=R/'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-final22-2026-10-08/gate01.json';g=json.loads(gate.read_bytes());pins=g['experiments']['eth-paper-real-data-end-to-end-resource-20261008-22']['source_files'];census=[]
for name,pin in pins.items():
 if not name.endswith('.py'):continue
 path=R/name;raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==pin
 compiled=compile(raw,str(path),'exec',dont_inherit=True,optimize=sys.flags.optimize);codes=[];buckets={}
 def walk(code):
  codes.append(code);buckets.setdefault(code.co_name,[]).append(code)
  for v in code.co_consts:
   if type(v) is types.CodeType:walk(v)
 walk(compiled)
 # Membership partition equivalence exhaustively on every actual compiled code.
 assert all(any(c==v for v in codes)==any(c==v for v in buckets[c.co_name]) for c in codes)
 old=sys.getsizeof(codes);new=sys.getsizeof(buckets)+sum(sys.getsizeof(v) for v in buckets.values())
 census.append({'path':name,'source_bytes':len(raw),'codes':len(codes),'names':len(buckets),'old_list_bytes':old,'bucket_container_bytes':new,'extra_container_bytes':new-old})
result={'decision':'accepted','candidate_sha256':sha(A/'imported_authority_lease.py'),'baseline_sha256':sha(M),'checks':checks,'literal_inverse':True,'actual_source_census':census,'max_extra_container_bytes':max(x['extra_container_bytes'] for x in census),'max_bucket_container_bytes':max(x['bucket_container_bytes'] for x in census),'qualification':'CPython getsizeof container census on authenticated registered Python sources, compile only. References reuse existing code names/code objects; no code-body import. Per-module transient containers, not RSS/allocator bound or performance measurement. No Lease/Owner/Admission instance.'}
assert not any(n in sys.modules for n in ['numpy','torch','scipy']);(P/'CHECK01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['actual_source_census','checks']}));print('cases',len(checks),'source_modules',len(census))
