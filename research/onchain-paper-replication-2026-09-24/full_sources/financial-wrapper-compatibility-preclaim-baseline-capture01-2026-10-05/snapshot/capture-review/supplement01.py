from pathlib import Path
import ast,hashlib,json,os,stat,types
H=Path(__file__).resolve().parent;B=H.parent;C=B/'heartbeat-root-checkpoint10-2026-10-04';D=B/'financial-wrapper-compatibility-current-source-parent-capture04-2026-10-04';S=D/'snapshot';CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
checks=[];origins=[]
def h(b):return hashlib.sha256(b).hexdigest()
def ok(x,s):
 if not x:raise AssertionError(s)
 checks.append(s)
def r(p):
 s=p.lstat();ok(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304,'bounded regular');return p.read_bytes()
def j(p):return json.loads(r(p))
q=j(S/'parent/REQUEST_DRAFT01.json');gate=j(S/'source-inputs/fixture_inputs/financial_wrapper_compatibility01/gates.json');e=gate['experiments'][q['identity']];old=j(CAP/'fixture_inputs/financial_wrapper_complete10001/gates.json') if (CAP/'fixture_inputs/financial_wrapper_complete10001/gates.json').exists() else None
# Locate the literal original twelve-definition gate by pinned body, never guessed API fields.
if old is None:
 for p in (CAP/'fixture_inputs').glob('*/gates.json'):
  if h(r(p))=='752c34dfad4df2ca36b5dc4dcb999846f8de01bd1a61c5356092c4e55fbd678c':old=j(p);break
ok(old is not None and len(old['experiments'])==12 and len(gate['experiments'])==13,'original12 and new13 experiment definitions')
for k,v in old['experiments'].items():ok(gate['experiments'][k]==v,'unaltered original definition '+k)
ok(q['source']==q['design_source']=='32d57eac5ea14435cd9d4aeb3e3b04d98bf16c41' and q['status']=='DRAFT_NOT_RELEASED','current exact draft context')
ok(q['proofs']['full_recovery'] is None and q['proofs']['independent_source_input_runtime'] is None and q['final_review'] is None,'genuine missing future proof fields')
ok(q['registration_sha256']==h(r(S/'source-inputs'/q['registration']))=='e1846c9fbd5d1964c867c9c7027e3e9a6009520c07841ed720c035374dbeb806','gate literal pin')
ok(q['source_files']==e['source_files'] and len(e['source_files'])==354,'complete354 self-gate excluded sourcepins')
for n,pin in e['source_files'].items():ok(h(r(CAP/n))==pin,'source pin '+n)
ok(q['registration'] not in e['source_files'],'selfgate excluded only')
ok(len(e['inputs'])==11 and q['input_hashes']=={k:v['sha256'] for k,v in e['inputs'].items()},'exact11 role hashes')
for role,v in e['inputs'].items():ok(h(r(CAP/v['path']))==v['sha256'],'role body '+role)
ok(e['parent'] is None,'reference independent parentNone')
for n,pin in q['helper_hashes'].items():ok(h(r(S/'parent'/n))==pin,'all7 declared helper pins '+n)
ok(len(q['helper_hashes'])==7 and h(r(S/'parent/parent01.py'))==q['caller_sha256'],'complete actualcaller helper closure')
# Genuine original mode metadata joins for all31 captured origin bodies.
for n,v in j(S/'ORIGINAL_ORIGINS01.json').items():
 p=Path(v['origin']);ok(h(r(p))==v['sha256'] and stat.S_IMODE(p.lstat().st_mode)==v['original_mode'],'original mode/hash maintained');origins.append(dict(v,snapshot_path=n))
# Actual owned original nested mkdir RED / explicit private chain GREEN.
owned=H/'owned01';owned.mkdir(mode=0o700)
def build(src,dest):
 tree=ast.parse(src);raw=next(ast.literal_eval(x.value) for x in tree.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='OWNED_IO_BYTES' for t in x.targets));io=types.ModuleType('exact_owned_io');exec(compile(raw,'<literal09d1>','exec'),io.__dict__)
 ns={'os':os,'stat':stat,'FILE':4194304,'DEST':dest,'IO':io,'require':lambda v,m:None if v else (_ for _ in ()).throw(ValueError(m))}
 node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='put');exec(compile(ast.Module(body=[node],type_ignores=[]),'<actualput>','exec'),ns);return ns['put']
mask=os.umask(0o002)
try:
 for v in ['03','04']:
  d=owned/v;d.mkdir(mode=0o700);f=build(r(C/('root_source_parent_capture'+v+'.py')),d);f(d/'level1/level2/body',b'opaque');ok(r(d/'level1/level2/body')==b'opaque','exact own body '+v);m=stat.S_IMODE((d/'level1').stat().st_mode);ok(m==(0o775 if v=='03' else 0o700),'old actual intermediate775/newprivate700 '+v)
 d=owned/'existing-mode';d.mkdir(mode=0o700);(d/'bad').mkdir(mode=0o755);f=build(r(C/'root_source_parent_capture04.py'),d)
 try:f(d/'bad/body',b'opaque')
 except ValueError:pass
 else:raise AssertionError('existing badmode accepted')
 ok(not (d/'bad/body').exists(),'existing nonprivate output parent refused before body')
finally:os.umask(mask)
# Literal evidence copies: no altered originals, preserve original paths/modes in a sidecar.
out=H/'evidence';out.mkdir(mode=0o700);evidence=[]
paths=[D/'CAPTURE01.json',D/'MANIFEST01.json',D/'ACTUAL_ROOT_EXIT01.json',C/'root_source_parent_capture03.py',C/'root_source_parent_capture04.py',C/'CAPTURE04_SOURCE_INVERSE01.json',B/'financial-wrapper-compatibility-current-source-parent-capture03-2026-10-04/FAILED_LOCAL_CAPTURE01.json']
for i,p in enumerate(paths):
 body=r(p);name=f'{i:02d}-'+p.name;(out/name).write_bytes(body);evidence.append({'path':str(p),'sha256':h(body),'bytes':len(body),'original_mode':stat.S_IMODE(p.stat().st_mode),'copy':'evidence/'+name})
result={'checks':checks,'assertions':len(checks),'genuine_missing_fields_preserved':True,'old12definitions_unchanged':True,'source_pins':354,'input_roles':11,'helper_pins':7,'origin_rows':origins,'literal_evidence_copies':evidence,'actual_root_operation_replayed':False,'numeric_authority':False}
(H/'SUPPLEMENT01.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'assertions':len(checks),'oldput_mode':509,'newput_mode':448,'actual_capture_replayed':False}))
