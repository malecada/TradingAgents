"""Independent read-only source composition; stdlib/AST only."""
import ast,copy,hashlib,json,os,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
PREV=HERE.with_name('neural-cold-feature-handoff-proof-source-composition02-2026-10-03')
OUTER=HERE.with_name('neural-cold-feature-handoff-proof-outer-preparation03-2026-10-03')
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
manifest=read(HERE/'MANIFEST03.json')
assert sha((HERE/'MANIFEST03.json').read_bytes()).startswith('4c770e65')
assert len(manifest['files'])==203
for row in manifest['files']:
    b=(HERE/row['path']).read_bytes()
    assert len(b)==row['bytes'] and sha(b)==row['sha256'],row['path']
inv=read(HERE/'source_inventory03.json');old=read(PREV/'source_inventory02.json')
rows={r['target']:r for r in inv['source_inventory']}
oldrows={r['target']:r for r in old['source_inventory']}
assert len(rows)==len(inv['source_inventory'])==195 and set(rows)==set(oldrows)
assert sum(t.startswith('tradingagents/') for t in rows)==147
changed=[t for t in rows if rows[t]['sha256']!=oldrows[t]['sha256']]
assert changed==['proof_tools/proof_release01.py']
env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0',GIT_OPTIONAL_LOCKS='0')
gitjoins=0
for target,row in rows.items():
    b=(HERE/'source-bodies'/target).read_bytes()
    assert len(b)==row['bytes'] and sha(b)==row['sha256']
    assert b==(ROOT/row['origin']).read_bytes()==(ROOT/row['snapshot']).read_bytes()
    if row.get('git_commit'):
        got=subprocess.check_output(['git','-c','protocol.allow=never','show',row['git_commit']+':'+row['git_path']],cwd=ROOT,env=env)
        assert got==b;gitjoins+=1
assert sum(r['bytes'] for r in rows.values())==inv['logical_bytes']==3270731
assert (HERE/'source-bodies/proof_tools/proof_release01.py').read_bytes()==(OUTER/'proof_release01.py').read_bytes()
assert (HERE/'source_inventory03.json').read_bytes()==(OUTER/'source_inventory03.json').read_bytes()
for name in ['configs01.json','model01.json','recipe01.json','training01.json']:
    assert (HERE/name).read_bytes()==(PREV/name).read_bytes()
oldtree=ast.parse((PREV/'prepare_metadata_composed02.py').read_bytes())
tree=ast.parse((HERE/'prepare_metadata_composed03.py').read_bytes())
oldconst={n.value for n in ast.walk(oldtree) if isinstance(n,ast.Constant) and isinstance(n.value,str)}
newconst={n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str)}
removed=oldconst-newconst;added=newconst-oldconst
assert len(removed)==len(added)==2
class Normalize(ast.NodeTransformer):
    def visit_Constant(self,n):
        if isinstance(n.value,str) and n.value in removed|added:return ast.copy_location(ast.Constant('PIN_OR_STATUS'),n)
        return n
assert ast.dump(Normalize().visit(copy.deepcopy(tree)))==ast.dump(Normalize().visit(copy.deepcopy(oldtree)))
def mapping(t):
    names={'digest','raw','source_mapping'}
    ns={'Path':Path,'hashlib':hashlib,'json':json}
    exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'<source-mapping-only>','exec'),ns)
    return ns['source_mapping']
try:mapping(oldtree)(HERE/'source-bodies',inv)
except ValueError as e:assert str(e)=='frozen exact composition inventory differs'
else:raise AssertionError('old helper accepted new inventory')
assert len(mapping(tree)(HERE/'source-bodies',inv))==195

# Reuse only the bounded source-expression interpreter as an AST analyzer;
# replace its repository-origin read mapping with these exact local snapshots.
st=ast.parse((PREV/'source_symbols01.py').read_bytes())
st.body=[n for n in st.body if not (isinstance(n,ast.ImportFrom) and n.module=='discover_source01')]
ns={'ROOT':ROOT};exec(compile(st,'<source-expression-interpreter>','exec'),ns)
analysisrows={t:dict(r,origin=str((HERE/'source-bodies'/t).relative_to(ROOT))) for t,r in rows.items()}
w=ns['Symbols'](analysisrows)
required=w.module('tradingagents/research/onchain_replication/compact_native_producer.py').required_sources()
assert len(required)==47 and required<=set(rows)
declaration_count=len(w.modules)
edges=0;loaders=[]
for target,row in rows.items():
    if not target.endswith('.py'):continue
    mod=w.module(target);mod.cache['root']=ROOT
    for n in ast.walk(mod.tree):
        names=[]
        if isinstance(n,ast.ImportFrom) and n.level:
            base=Path(target).parent
            for _ in range(n.level-1):base=base.parent
            names=[str(base.joinpath(*s.split('.'))) for s in ([n.module] if n.module else [a.name for a in n.names])]
        elif isinstance(n,ast.ImportFrom) and n.module and n.module.startswith('tradingagents'):
            base=n.module.replace('.','/');names=[base]
            if base+'/__init__.py' in rows:names += [base+'/'+a.name for a in n.names if base+'/'+a.name+'.py' in rows]
        elif isinstance(n,ast.Import):names=[a.name.replace('.','/') for a in n.names if a.name.startswith('tradingagents')]
        for name in names:
            edges+=1;assert name+'.py' in rows or name+'/__init__.py' in rows,(target,n.lineno,name)
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ('load','_load','module') and len(n.args)>=2:
            if n.func.id in ('load','_load'):
                declared=next((f for f in mod.tree.body if isinstance(f,ast.FunctionDef) and f.name==n.func.id),None)
                if declared is None or not any(isinstance(c,ast.Call) and isinstance(c.func,ast.Attribute) and c.func.attr=='spec_from_file_location' for c in ast.walk(declared)):continue
            path=mod.evaluate(n.args[1]);name=str(Path(path).relative_to(ROOT));assert name in rows
            loaders.append([target,n.lineno,name])
assert 'resource_refusal' not in (HERE/'source-bodies/tradingagents/research/onchain_replication/compact_mcm.py').read_text()
assert not any(n.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for n in sys.modules)
print(json.dumps({'manifest_bodies':203,'sources':195,'package':147,'git_joins':gitjoins,'logical_source_bytes':3270731,'changed_targets':changed,'helper_only_removed_constants':sorted(removed),'helper_only_added_constants':sorted(added),'old_mapping_refused_new_mapping_passed':True,'required_pins':sorted(required),'declaration_modules':declaration_count,'static_edges':edges,'generic_loader_callers':loaders,'numeric_imports':False,'actual_claims_or_capsules_created':False},indent=2))
