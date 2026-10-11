"""Read-only finite source/inverse controls; never executes candidate helpers."""
from pathlib import Path
import ast,json,hashlib,difflib
R=Path(__file__).resolve().parents[4];F=R/'research/onchain-paper-replication-2026-09-24/full_sources';H=F/'real-data-pilot-full24-preparation-increment01-2026-10-09';C=H/'full36increment32';O=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest();scope=json.loads((C/'TOOL_SCOPE01.json').read_text());manifest=json.loads((C/'HELPERS_MANIFEST01.json').read_text())
for p,h in manifest.items():assert sha((R/p).read_bytes())==h
new=(C/'select32.py').read_text();tree=ast.parse(new);values={}
for node in tree.body:
    if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
        try:values[node.targets[0].id]=ast.literal_eval(node.value)
        except (ValueError,TypeError):pass
assert len(values['owned'])==len(set(values['owned']))==14 and set(values['owned'])==set(scope['public_roots'])
assert values['main_source_pins']==scope['changed_source_pins'] and len(values['main_source_pins'])==19
assert values['main_source_names']==sorted(scope['changed_source_pins'])
assert set(values['fixed_public_names'])==set(scope['fixed_public_names']) and list(values['helper_names'])==scope['helpers']
assert values['prior_generated_names']==scope['prior_generated_names']
for p,h in values['main_source_pins'].items():assert sha((R/p).read_bytes())==h
private_relative=scope['private_scope'][0];private=R/private_relative;assert len(scope['private_scope'])==1
ns=dict(ROOT=R,private_relative=private_relative,private=private,allowed_files={private_relative},excluded=set(),allowed_roots=[F/n for n in scope['public_roots']],scopes=[private.parent])
asserts=[n for n in ast.walk(tree) if isinstance(n,ast.Assert)]
scope_expr=next(n.test for n in asserts if isinstance(n.msg,ast.Constant) and n.msg.value=='Git delta outside declared full36increment32 scope')
private_expr=next(n.test for n in asserts if isinstance(n.test,ast.BoolOp) and 'relative.startswith' in ast.unparse(n.test))
controls=[]
for suffix,expected in [('archive_transport01.json',True),('unrelated-synthetic-sibling.json',False),('connection.json',False)]:
    relative=str((private.parent/suffix).relative_to(R));ns.update(relative=relative,path=R/relative,names={relative})
    x=eval(compile(ast.Expression(scope_expr),'scope_membership','eval'),ns);y=eval(compile(ast.Expression(private_expr),'private_membership','eval'),ns)
    assert x==y==expected;controls.append(dict(leaf=suffix,accepted=expected))
assert 'allowed_roots=[F/name for name in owned]\n' in new and '|{private_relative}' in new
maps={};patch=[];reverse=[]
for name in ('select','capture','recover'):
    old=(H/'full35outcome31'/(name+'31.py')).read_text();current=(C/(name+'32.py')).read_text()
    patch.extend(difflib.unified_diff(old.splitlines(True),current.splitlines(True),fromfile=name+'31.py',tofile=name+'32.py'))
    reverse.extend(difflib.unified_diff(current.splitlines(True),old.splitlines(True),fromfile=name+'32.py',tofile=name+'31.py'))
    if name=='select':continue
    a=ast.parse(old);b=ast.parse(current);an=list(ast.walk(a));bn=list(ast.walk(b));assert len(an)==len(bn);mapping={}
    for x,y in zip(an,bn):
        assert type(x)==type(y)
        if isinstance(x,ast.Constant) and x.value!=y.value:
            assert isinstance(x.value,str) and isinstance(y.value,str);mapping[y.value]=x.value;y.value=x.value
    assert ast.dump(a)==ast.dump(b)
    inverse=current
    for newer,older in sorted(mapping.items(),key=lambda kv:len(kv[0]),reverse=True):inverse=inverse.replace(repr(newer),repr(older))
    if name=='recover':inverse=inverse.replace('"""Recover the one declared full36increment32 public increment from the actual remote."""','"""Recover the one declared full35outcome31 public increment from the actual remote."""')
    assert inverse==old;maps[name]=mapping
assert ''.join(patch)==(C/'LITERAL_PATCH01.diff').read_text()
assert ''.join(reverse)==(C/'LITERAL_INVERSE01.diff').read_text()
assert not Path(scope['fresh_bare']).exists() and not Path(scope['fresh_bare']).is_symlink()
for name in ('SELECTION32.json','CAPTURE32.json','FRESH_GIT_RECOVERY32.json','pilot36-preparation-increment32.tar','fresh-git-recovered-full36increment32.tar'):
    assert not (C/name).exists() and not (C/name).is_symlink()
result=dict(status='PASS_FINITE_SOURCE_ONLY',private_membership_controls=controls,owned_public_roots=14,changed_source_pins=19,capture_recover_literal_and_AST_inverse=True,exact_patches=True,fresh_names_absent=True,approved_literal_map=maps,source_snapshot={str(p.relative_to(R)):sha(p.read_bytes()) for p in sorted(C.iterdir()) if p.is_file()},selector_executed=False,capture_executed=False,recovery_executed=False,git_or_network=False,private_body_read=False)
with (O/'CHECK03.json').open('x') as h:json.dump(result,h,indent=2);h.write('\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('approved_literal_map','source_snapshot')}))
