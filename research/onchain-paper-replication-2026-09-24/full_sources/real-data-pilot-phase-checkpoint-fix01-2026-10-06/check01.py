"""Extracted real call paths with explicit synthetic authority/clock fixtures."""
import ast,copy,hashlib,json,sys,types
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
P=ROOT/'tradingagents/research/onchain_replication'
def enc(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def require(v,s):
    if not v:raise ValueError(s)
def extract(path,name,methods,ns):
    c=next(x for x in ast.parse(path.read_text()).body if isinstance(x,ast.ClassDef) and x.name==name)
    tree=ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(name=name,bases=[],keywords=[],body=[x for x in c.body if isinstance(x,ast.FunctionDef) and x.name in methods],decorator_list=[])],type_ignores=[]))
    exec(compile(tree,str(path),'exec'),ns);return ns[name]
backend=types.ModuleType('offline_fixture.matching_pair');backend.BACKEND={'fixture':'no-numerical-import'};sys.modules['offline_fixture.matching_pair']=backend
interval=types.ModuleType('offline_interval');exec(compile((P/'imported_authority_interval.py').read_bytes(),str(P/'imported_authority_interval.py'),'exec'),vars(interval))
policy={'schema_version':1,'kind':interval.KIND,'live_interval_ms':1000,'fingerprint_interval_ms':2000,'full_interval_ms':10000,'max_stale_ms':30000,'max_calls_between_full':100,'assumption':interval.ASSUMPTION}
def fixture(candidate,mode='intact'):
    path=HERE/'candidate' if candidate else P;clock=[0.];events=[];armed=[False];matching={'alpha':1.0};current={'generation':0};readcount=[0]
    def digest(v):return hashlib.sha256(enc(v)).hexdigest()
    ns={'__package__':'offline_fixture','canonical_bytes':enc,'thaw':copy.deepcopy,'cache_key':digest,'require':require}
    Prepared=extract(path/'original_import_preparation.py','PreparedImport',{'stage_contract','_stage_contract_metadata','execution_contract','_execution_contract_metadata'},ns)
    prepared=Prepared();prepared._selection={'required_stages':['dictionary-import','mcm-fixture'],'selected':{'descriptor':{'configs':{'matching':matching}}}};prepared._input='original';prepared._job_input='job';prepared._source={'fixture.py':'fixed'}
    prepared._bound=types.SimpleNamespace(record={'workflow_identity':'fixed'},context={'runtime_hash':'fixed'});prepared._run=types.SimpleNamespace(admission=types.SimpleNamespace(source='fixed',inputs={'original':{'sha256':'fixed'},'job':{'sha256':'fixed'}}));prepared._cap=types.SimpleNamespace(_policy=enc({'dictionary_identity':'fixed','refs':{'matching_config':{'input':'matching'}}}))
    def check():
        events.append('prepared.full');clock[0]+=2.3
        require(mode!='entry_refusal' or not armed[0],'entry refusal')
        require(current['generation']==0,'state changed')
        if mode=='final_callback_mutation' and armed[0] and readcount[0]>=1:current['generation']=1
    prepared._check=check
    def read(run,role):
        events.append('matching.read');readcount[0]+=1
        if armed[0] and readcount[0]==1 and mode=='construction_mutation':current['generation']=1
        if armed[0] and readcount[0]==2 and mode=='reread_mutation':return enc({'alpha':2.0})
        return enc(matching)
    original=types.SimpleNamespace(parse=json.loads,_read_registered=read);ns['original']=original
    expected=prepared.execution_contract();events.clear();readcount[0]=0;clock[0]=0.;armed[0]=True
    class ImportStage:
        def lease(self):events.append('stage.lease');prepared._check();self.integrity()
        def integrity(self):events.append('stage.integrity');require(current['generation']==0,'state changed during final rejoin')
    stage=ImportStage();owner=types.SimpleNamespace(bound=prepared._bound);numeric={'original_dictionary':expected['original_dictionary'],'original_matching':expected['original_matching']}
    materialized=types.SimpleNamespace(_integrity=lambda:dict(numeric));stage.owner=owner;stage.materialized=materialized;stage.prepared=prepared;stage.reference='fixed';stage.inode=(1,2)
    def content(s):events.append('content');s.integrity()
    def verify(o):events.append('owner.final');require(current['generation']==0,'owner changed during callback')
    ens={'__package__':'offline_fixture','canonical_bytes':enc,'cache_key':digest,'require':require,'ImportStage':ImportStage,'content':content,'owners':types.SimpleNamespace(verify_current=verify),'original':original}
    Execution=extract(path/'original_import_stage.py','ImportedExecution',{'check'},ens);e=Execution();e._stage=stage;e._owner=owner;e._bound=prepared._bound;e._materialized=materialized;e._pin=(id(stage),id(owner),id(e._bound),id(materialized),stage.reference,stage.inode);e._execution=expected;e._execution_pin=enc(expected)
    return e,prepared,clock,events,ens
checks=[]
for mode in ['intact','entry_refusal','construction_mutation','final_callback_mutation','reread_mutation']:
    rows=[]
    for candidate in (False,True):
        e,prepared,clock,events,ns=fixture(candidate,mode)
        try:value=e.check();row={'status':'pass','value':value}
        except ValueError as err:row={'status':'refuse','reason':str(err)}
        row['events']=list(events);rows.append(row)
    assert rows[0]['status']==rows[1]['status']
    if mode=='intact':
        assert rows[0]['value']==rows[1]['value'];assert rows[0]['events'].count('prepared.full')==3;assert rows[1]['events'].count('prepared.full')==2
        assert rows[1]['events']==['stage.lease','prepared.full','stage.integrity','content','stage.integrity','matching.read','prepared.full','matching.read','owner.final','stage.integrity']
    else:assert all(r['status']=='refuse' for r in rows)
    checks.append({'case':mode,'original':rows[0],'candidate':rows[1]})
# Actual Interval.validate + actual ImportedExecution.check bodies; all authorities
# and timing costs are explicit fixture stubs, not scientific capabilities.
rows=[]
for candidate in (False,True):
    e,prepared,clock,events,ns=fixture(candidate);scheduler=interval.Interval(policy,clock=lambda:clock[0]);scheduler.validate(lambda:None,lambda:None,lambda:None,boundary=True);clock[0]=23.631386558
    try:scheduler.validate(e.check,lambda:None,lambda:None,boundary=True);row={'status':'pass'}
    except ValueError as err:row={'status':'refuse','reason':str(err),'notes':getattr(err,'__notes__',[])}
    row.update(closed=scheduler.closed,full=scheduler.full,end_clock=clock[0],full_check_count=events.count('prepared.full'));rows.append(row)
assert rows[0]['status']=='refuse' and rows[0]['closed'];assert rows[1]['status']=='pass' and not rows[1]['closed'];checks.append({'case':'real-call-path fake-clock RED to GREEN','original':rows[0],'candidate':rows[1],'qualification':'Uniform2.3second Prepared-check costs are synthetic, not inferred from actual10 callback internals. The23.631386558 age is retained actual10 aggregate prior age. No measured saving follows.'})
# Standalone public contract must still perform both full checks and two reads.
for candidate in (False,True):
    e,prepared,clock,events,ns=fixture(candidate);v=prepared.execution_contract();assert events==['prepared.full','matching.read','prepared.full','matching.read']
checks.append({'case':'standalone public execution_contract exact surrounding full checks and rereads','status':'pass'})
# Unmodified stage.lease remains the sole validated entry in the candidate path.
candidate_stage=(HERE/'candidate/original_import_stage.py').read_text();replacement=(HERE/'STAGE_REPLACEMENT01.txt').read_text();assert candidate_stage.replace(replacement,'        stage.lease();content(stage)\n        current=stage.prepared.execution_contract()\n')==(P/'original_import_stage.py').read_text()
s=(HERE/'candidate/original_import_preparation.py').read_text();a=s.index('    def execution_contract(self):');b=s.index('\n    def materialize(',a);assert s[:a]+(HERE/'ORIGINAL_EXECUTION_CONTRACT01.txt').read_text()+s[b:]==(P/'original_import_preparation.py').read_text()
result={'status':'PASS','checks':checks,'exact_two_file_inverse':True,'qualification':'No arrays, genuine scientific authority, claim, native execution or empirical replay. No elapsed capacity proof. Interval predicates/timestamps/caps unchanged; observations from test clock are explicitly synthetic.'}
(HERE/'CHECK_RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':'PASS','cases':len(checks),'exact_inverse':True}))
