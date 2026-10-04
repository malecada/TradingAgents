import ast,copy,hashlib,json,stat,types
from pathlib import Path
D=Path(__file__).resolve().parent;F=D.parent;A=F/'financial-wrapper-complete100-root-parent-preparation01-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
b=(A/'parent01.py').read_bytes();qraw=(A/'REQUEST_DRAFT01.json').read_bytes();q=json.loads(qraw);P=Path(q['parent_root']);C=Path(q['capsule_root'])
ok(sha(b)=='7f28cee688b661584e57466838ecdb79f0e17aa52be7d6f2c04f374326de9fb3' and sha(qraw)=='7f506c00e5e148ee24793412955056f71eb820059385588517fa4355c81a1763','actual pinned caller/draft')
entries=[]
for p in sorted(P.iterdir()):
 s=p.lstat();raw=p.read_bytes();ok(stat.S_ISREG(s.st_mode) and raw==(A/p.name).read_bytes(),'actual installed caller body '+p.name);entries.append({'path':str(p),'mode':stat.S_IMODE(s.st_mode),'bytes':len(raw),'sha256':sha(raw)})
ok(len(entries)==9 and not (P/'attempt').exists(),'nine-file never attempted caller')
for scope,pin in [('financial-wrapper-complete100-parent-source-review01-2026-10-04','ad059e61ac51433b1d5e21153711d3875bffb6dd0830e906d3a4d9de03d3d9af'),('financial-wrapper-complete100-reference-adoption-review01-2026-10-04','614267c53c0598fb03437cf4356b28084f008f8911e11eec4d67448f45ed6a36')]:
 p=F/scope/'MANIFEST01.json';raw=p.read_bytes();ok(sha(raw)==pin,'review seal '+scope);members=json.loads(raw)['members'];ok({x.relative_to(p.parent).as_posix() for x in p.parent.rglob('*') if x!=p}=={x['path'] for x in members}-{'.'},'complete review membership')
 for row in members:
  x=p.parent/row['path'];s=x.lstat();mode=int(row['mode'],8) if isinstance(row['mode'],str) else row['mode'];ok(stat.S_IMODE(s.st_mode)==mode,'review mode')
  if row['kind']=='file':ok(s.st_size==row['bytes'] and sha(x.read_bytes())==row['sha256'],'review body')
  else:ok(stat.S_ISDIR(s.st_mode),'review directory')
for role in ('cumulative','independent_source_input_runtime'):
 x=q['proofs'][role];ok(sha(Path(x['path']).read_bytes())==x['sha256'],'actual existing proof '+role)
ok(q['proofs']['full_recovery'] is None and q['final_review'] is None,'genuine missing proof/release null')
ok(q['source']==q['design_source']=='9dc5c79f738920b52947b4e63fed0397f1b5b207' and sha((C/q['registration']).read_bytes())==q['registration_sha256']=='752c34dfad4df2ca36b5dc4dcb999846f8de01bd1a61c5356092c4e55fbd678c','actual current source/gate context')
source=ast.parse(b);functions={n.name:n for n in source.body if isinstance(n,ast.FunctionDef)};ns={'sha':sha,'R':types.SimpleNamespace(encode=lambda x:(json.dumps(x,sort_keys=True,indent=2)+'\n').encode())};exec(compile(ast.Module(body=[functions['contract']],type_ignores=[]),'contract-metadata-only','exec'),ns)
base=ns['contract'](q)
# Only metadata dependency probes; no released request or proof fixture is produced.
x=copy.deepcopy(q);x['final_review']='UNBOUND_METADATA_ONLY';ok(ns['contract'](x)==base,'final_review sole exclusion')
for key in q:
 if key=='final_review':continue
 x=copy.deepcopy(q);x[key]='UNBOUND_METADATA_ONLY';ok(ns['contract'](x)!=base,'contract includes '+key)
validate=functions['validate_release'];review_require=next(n for n in ast.walk(validate) if isinstance(n,ast.Compare) and isinstance(n.left,ast.Name) and n.left.id=='review');literal=review_require.comparators[0];ok(isinstance(literal,ast.Dict),'exact release dict');keys=[ast.literal_eval(k) for k in literal.keys];ok(keys==['schema_version','decision','contract_sha256','proof_sha256','identity','source','caller_sha256'],'seven-field exact release schema')
refsrc=ast.get_source_segment(b.decode(),functions['reference']);ok('set(ref)=={\'path\',\'sha256\'}' in refsrc and 'p.resolve()==p' in refsrc,'canonical exact reference schema')
old=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-root-launch-20261004-01/REQUEST_FINAL03.json');oq=json.loads(old.read_bytes());oldreview=json.loads(Path(oq['final_review']['path']).read_bytes());ok(sha(Path(oq['final_review']['path']).read_bytes())==oq['final_review']['sha256'] and oldreview['contract_sha256']==ns['contract'](oq),'previous genuine request/release nonrecursive contract')
(D/'PARENT_SOURCE01.py').write_bytes(b);(D/'REQUEST_DRAFT01.json').write_bytes(qraw)
(D/'SOURCE_SCHEMA01.json').write_text(json.dumps({'parent_sha256':sha(b),'request_sha256':sha(qraw),'installed_nine_members':entries,'function_joins':{k:{'line':n.lineno,'end_line':n.end_lineno,'ast_sha256':sha(ast.dump(n,include_attributes=False).encode())} for k,n in functions.items()},'release_exact_keys':keys,'contract_excluded_keys':['final_review'],'actual_future_recovery':None,'actual_future_release':None,'proof_semantics':'reference verifies bytes, not substantive recovery or reviewer independence; genuine independent review must assess semantics','previous_genuine_reference':{'request_path':str(old),'request_sha256':sha(old.read_bytes()),'final_review':oq['final_review']}},indent=2)+'\n')
(D/'READBACK01.json').write_text(json.dumps({'checks':len(checks),'names':checks,'preflight_called':False,'admission_called':False,'final_request_generated':False,'native_called':False,'network':False},indent=2)+'\n');print(json.dumps({'checks':len(checks),'source_only':True}))
