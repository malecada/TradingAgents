"""Offline extracted-method fixtures; no scientific authority or array imports."""
import ast,copy,hashlib,json,sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
SOURCE=ROOT/'tradingagents/research/onchain_replication/original_import_preparation.py'
CANDIDATE=HERE/'candidate/original_import_preparation.py'
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def require(v,s):
    if not v:raise ValueError(s)
def compile_fixture(path):
    tree=ast.parse(path.read_text());cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='PreparedImport')
    methods=[x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name in {'stage_contract','_stage_contract_metadata','execution_contract'}]
    tree=ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name='Fixture',bases=[],keywords=[],body=methods,decorator_list=[])],type_ignores=[]))
    ns={'__package__':'offline_fixture','canonical_bytes':canonical,'thaw':copy.deepcopy,'cache_key':lambda x:hashlib.sha256(canonical(x)).hexdigest(),'require':require}
    exec(compile(tree,str(path),'exec'),ns)
    return ns['Fixture'],ns
backend=types.ModuleType('offline_fixture.matching_pair');backend.BACKEND={'fixture':'metadata-only'}
sys.modules['offline_fixture.matching_pair']=backend
checks=[]
def case(path,mode):
    cls,ns=compile_fixture(path);f=cls();events=[];matching={'alpha':1.0};f._selection={'required_stages':['dictionary-import','mcm-fixture'],'selected':{'descriptor':{'configs':{'matching':matching}}}}
    f._input='original';f._job_input='job';f._source={'fixture.py':'fixed'}
    f._bound=types.SimpleNamespace(record={'workflow_identity':'fixed'},context={'runtime_hash':'fixed'})
    f._run=types.SimpleNamespace(admission=types.SimpleNamespace(source='fixed',inputs={'original':{'sha256':'fixed'},'job':{'sha256':'fixed'}}))
    f._cap=types.SimpleNamespace(_policy=canonical({'dictionary_identity':'fixed','refs':{'matching_config':{'input':'matching'}}}))
    initial=canonical({'selection':f._selection,'bound':f._bound.record,'source':f._source})
    def validate():
        events.append('full')
        require(mode!='entry_failure','entry failure')
        require(canonical({'selection':f._selection,'bound':f._bound.record,'source':f._source})==initial,'boundary mutation')
        if mode=='final_failure' and len(events)>1:raise ValueError('final failure')
    f._check=validate
    reads=[]
    def reader(run,key):
        reads.append(key)
        if mode=='source_mutation' and len(reads)==1:f._source['fixture.py']='changed'
        if mode=='descriptor_mutation' and len(reads)==1:f._selection['selected']['descriptor']['configs']['matching']={'alpha':2.0}
        if mode=='final_read_mutation' and len(reads)==2:return canonical({'alpha':3.0})
        return canonical(matching)
    ns['original']=types.SimpleNamespace(parse=json.loads,_read_registered=reader)
    try:value=f.execution_contract();return {'disposition':'pass','value':value,'checks':len(events),'reads':len(reads)}
    except ValueError as e:return {'disposition':'refuse','error':str(e),'checks':len(events),'reads':len(reads)}
old=case(SOURCE,'intact');new=case(CANDIDATE,'intact')
assert old['disposition']==new['disposition']=='pass' and old['value']==new['value']
assert old['checks']==3 and new['checks']==2 and old['reads']==new['reads']==2
checks.append({'case':'intact canonical identity unchanged; redundant middle full check removed','original':old,'candidate':new})
for mode in ('entry_failure','final_failure','source_mutation','descriptor_mutation','final_read_mutation'):
    a,b=case(SOURCE,mode),case(CANDIDATE,mode)
    assert a['disposition']==b['disposition']=='refuse'
    checks.append({'case':mode,'original':a,'candidate':b})
for path in (SOURCE,CANDIDATE):
    cls,ns=compile_fixture(path);f=cls();f._check=lambda:(_ for _ in ()).throw(ValueError('required full check'))
    try:f.stage_contract()
    except ValueError as e:assert str(e)=='required full check'
    else:raise AssertionError('public stage_contract omitted full check')
checks.append({'case':'public stage_contract preserves mandatory full-check refusal','original':'refuse','candidate':'refuse'})
s=SOURCE.read_text();c=CANDIDATE.read_text()
oldblock='''    def stage_contract(self):
        self._check()
        # Contract to be consumed by future Owner constructor BEFORE root birth.
'''
newblock='''    def stage_contract(self):
        self._check()
        return self._stage_contract_metadata()

    def _stage_contract_metadata(self):
        # Callback-free construction only. Callers retain genuine full checks:
        # stage_contract checks immediately before this helper; execution_contract
        # checks before all construction and again before returning any value.
        # Contract to be consumed by future Owner constructor BEFORE root birth.
'''
assert c.replace(newblock,oldblock).replace("'stage_contract':self._stage_contract_metadata(),'mcm_execution_admitted':False}","'stage_contract':self.stage_contract(),'mcm_execution_admitted':False}")==s
result={'status':'PASS','qualification':'Extracted-method synthetic fixture only; no genuine Owner/Binding/admission/arrays or callback capacity proof. Original extra full-call count is the performance RED; candidate removes exactly one middle invocation while original surrounding checks remain.','checks':checks,'exact_inverse':True}
(HERE/'CHECK_RESULT01.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':'PASS','cases':len(checks),'exact_inverse':True,'original_execution_contract_full_checks':3,'candidate_execution_contract_full_checks':2}))
