"""Actual changed-AST stdlib regression only; no native/scientific imports."""
import ast,hashlib,json
from pathlib import Path
from types import SimpleNamespace
P=Path(__file__).resolve().parent;OLD=P.parent/'matching-compiled-uncached-edge-chunk01-2026-10-11'
class Matrix(dict):
    def __missing__(self,k):return 1.
class Edges:
    def __getitem__(self,key):return key[1],key[1]
def extract(path):
    tree=ast.parse(path.read_text())
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_advance_checked')
    branch=next(n for n in ast.walk(fn) if isinstance(n,ast.If) and any(isinstance(s,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='native_progress' for t in s.targets) for s in n.orelse))
    return compile(ast.Module(body=branch.orelse,type_ignores=[]),str(path),'exec')
programs={'old':extract(OLD/'matching_annealing.py'),'new':extract(P/'matching_annealing.py')}
rows=[]
def run(version,case):
    primary=KeyboardInterrupt('prefill original fatal') if case.startswith('fatal') else MemoryError('prefill original memory')
    q=Matrix();graph=SimpleNamespace(edge_features=[0.,1.,2.,3.],edge_index=Edges())
    calls=[0]
    def agreement(a,b):
        calls[0]+=1
        if calls[0]==3:raise primary
        return 2.
    def filler(w,a,b,l,r,count,fn,progress):
        if case=='decline':return False
        if case=='partial':
            w[0]=1.;w[1]=1.;progress[0]=2
        raise primary
    def guard():
        if case=='eligibility':raise primary
        return True
    env=dict(edge_chunk_fill=filler,reuse=False,cached=None,valid=None,count=4,start=0,total=4,weights=[0.]*4,left=list(range(4)),right=list(range(4)),a=graph,b=graph,_reuse_runtime=guard,_immutable_edges=lambda g:True,agreement=agreement,state={'Q':q,'M':Matrix(),'cursor':0},used=0)
    if case in ('stale','fatal_stale'):env['offset']=3
    caught=None
    try:exec(programs[version],env)
    except BaseException as error:caught=error
    expected_prefix=2 if case in ('decline','partial') else 0
    ok=caught is primary and env['state']['cursor']==expected_prefix and env['used']==expected_prefix and len(q)==expected_prefix
    row={'version':version,'case':case,'primary_identity':caught is primary,'caught_type':type(caught).__name__,'cursor':env['state']['cursor'],'used':env['used'],'written_destinations':len(q),'passes':ok}
    rows.append(row);return ok
for case in ('prefill','stale','fatal','fatal_stale','eligibility','decline','partial'):
    old_ok=run('old',case);new_ok=run('new',case)
    assert new_ok,(case,rows[-1])
    if case in ('prefill','stale','fatal','fatal_stale','eligibility'):assert not old_ok
    else:assert old_ok
old=(OLD/'matching_annealing.py').read_text();new=(P/'matching_annealing.py').read_text()
restored=new.replace('                            offset=0;native_progress=None\n','                            native_progress=None\n',1).replace('                                    native_progress=[0]\n','                                    native_progress=[None]\n',1).replace('                                if not native_used:\n                                    native_progress=None\n','                                if not native_used:\n',1)
assert restored==old
for p in P.glob('*.py'):ast.parse(p.read_bytes())
result={'status':'PASS_FOCUSED_SOURCE_REGRESSION','cases':rows,'literal_inverse_to01':True,'native_loaded':False,'scientific_imports':False,'numeric_fixture_executed':False}
(P/'RESULT02.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
