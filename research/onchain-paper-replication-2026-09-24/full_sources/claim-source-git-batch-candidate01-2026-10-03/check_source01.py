import ast,difflib,hashlib,json,pathlib
P=pathlib.Path(__file__).parent;B=P.parent
base=(P/'baseline.py').read_bytes();new=(P/'candidate01.py').read_bytes();sha=lambda x:hashlib.sha256(x).hexdigest()
origins=[pathlib.Path('tradingagents/research/verify.py'),B/'original-import-native-successor-preparation06-2026-10-03/capsule04/tradingagents/research/verify.py',B/'neural-cold-feature-handoff-proof-source-composition03-2026-10-03/source-bodies/tradingagents/research/verify.py']
for p in origins:assert p.read_bytes()==base,str(p)
a=ast.parse(base);b=ast.parse(new);bf={n.name:n for n in b.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
for n in a.body:
 if isinstance(n,ast.FunctionDef):
  nn=bf[n.name]
  if n.name=='verify_claim':
   loops=[i for i,x in enumerate(n.body) if isinstance(x,ast.For) and isinstance(x.target,ast.Tuple) and ast.unparse(x.target)=='(path, expected)'];assert len(loops)==1
   i=loops[0];assert ast.unparse(nn.body[i])=="_verify_sources(root, pinned, {claim['source'], claim['design_source']})"
   nn.body[i]=n.body[i]
  assert ast.dump(n)==ast.dump(nn),n.name
 else:assert any(ast.dump(n)==ast.dump(x) for x in b.body)
(P/'candidate01.patch').write_text(''.join(difflib.unified_diff(base.decode().splitlines(True),new.decode().splitlines(True),fromfile='tradingagents/research/verify.py',tofile='tradingagents/research/verify.py')))
(P/'origins01.json').write_text(json.dumps({'baseline_sha256':sha(base),'candidate_sha256':sha(new),'origins':[{'path':str(p),'sha256':sha(p.read_bytes())} for p in origins],'scope':'Only original pinned source loop replaced; every other original AST identical; no numerical imports.'},indent=2)+'\n')
print(json.dumps({'baseline_sha256':sha(base),'candidate_sha256':sha(new),'source_origins_equal':len(origins),'other_original_AST':'identical'}))
