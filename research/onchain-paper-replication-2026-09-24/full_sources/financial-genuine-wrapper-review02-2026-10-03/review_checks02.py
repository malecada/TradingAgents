"""Independent narrow financial02 review: exact source and scalar control only."""
import ast,copy,hashlib,json,stat,sys
from pathlib import Path
H=Path(__file__).resolve().parent;P=H.parent/'financial-genuine-wrapper-preparation02-2026-10-03';O=H.parent/'financial-genuine-wrapper-preparation01-2026-10-03';ROOT=P.parents[3]
checks=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def check(label,ok):assert ok,label;checks.append(label)
def refuses(label,fn):
    try:fn()
    except (ValueError,TypeError,KeyError):checks.append(label);return
    raise AssertionError(label)
def funcs(path):return {n.name:n for n in ast.parse(path.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
raw=(P/'MANIFEST02.json').read_bytes();manifest=json.loads(raw)
check('exact46 subject manifest',sha(raw)=='664ca3075fe1c3eff3b66e8219af44331b2d3ffb082f86977231971a5e5d517b' and len(manifest['members'])==46)
for r in manifest['members']:
    path=P/r['path'];s=path.lstat();check('member mode '+r['path'],stat.S_IMODE(s.st_mode)==r['mode'])
    if r['kind']=='directory':check('directory '+r['path'],stat.S_ISDIR(s.st_mode));continue
    body=path.read_bytes();check('regular '+r['path'],stat.S_ISREG(s.st_mode) and s.st_nlink==1);check('body '+r['path'],len(body)==r['bytes'] and sha(body)==r['sha256'])
source=(P/'financial_wrapper_fixture.py').read_bytes();check('exact new fixture',sha(source)=='e13d7170a55165f1c5d2313223cf972dc102d0beac95ba49c493c146ed4a4897')
inverse=source.decode()
for i,step in enumerate(reversed(json.loads((P/'fixture_adaptations02.json').read_bytes()))):
    check('exact inverse occurrence '+str(i),inverse.count(step['after'])==1);inverse=inverse.replace(step['after'],step['before'])
check('full complete text inverse',inverse.encode()==(O/'financial_wrapper_fixture.py').read_bytes())
a=funcs(P/'financial_wrapper_fixture.py');b=funcs(O/'financial_wrapper_fixture.py')
for name in b:
    if name not in ('execute','_parent'):check('unchanged original AST '+name,ast.dump(a[name])==ast.dump(b[name]))
for name in ('job.py','replay.py','model.json','training.json','check_source01.py'):
    check('unchanged companion '+name,(P/name).read_bytes()==(O/name).read_bytes())
for path in sorted((P/'candidate02').glob('*.py')):
    check('unchanged genuine candidate02 '+path.name,path.read_bytes()==(O/'candidate02'/path.name).read_bytes()==(H.parent/'financial-streamed-execution-candidate02-2026-10-02'/path.name).read_bytes())
installed=json.loads((P/'INSTALLATION01.json').read_bytes());closure=json.loads((P/'SOURCE_CLOSURE01.json').read_bytes());oldclosure=json.loads((O/'SOURCE_CLOSURE01.json').read_bytes())
check('same194 roster',set(closure['installed'])==set(oldclosure['installed'])==set(installed['sources']) and len(closure['installed'])==194)
check('only fixture source target changed',[k for k in closure['installed'] if closure['installed'][k]!=oldclosure['installed'][k]]==['tradingagents/research/onchain_replication/financial_wrapper_fixture.py'])
origins=[]
for name,r in installed['sources'].items():
    path=ROOT/r['source'];assert not any(v in ('.env','keys','apis','.git','.venv','node_modules') for v in path.parts)
    st=path.lstat();assert stat.S_ISREG(st.st_mode) and st.st_nlink==1 and st.st_size<4*1024**2
    body=path.read_bytes();check('actual declared origin '+name,sha(body)==r['sha256']==closure['installed'][name]);origins.append({'target':name,'origin':str(path),'bytes':len(body),'sha256':sha(body)})
check('prior WITHHELD preserved',sha((H.parent/'financial-genuine-wrapper-review01-2026-10-03/REVIEW01.md').read_bytes())=='650ae08f25da1e519a390231a876cfcc6d2080a5aaadafccf4be163d4750127e')

# Execute only pure scalar helpers, and the exact failure handler. Nothing
# impersonates ResearchRun, Owner, Binding, checkpoint loader or tensor APIs.
ns={'PHASES':('agreement','interrupt1','complete100','continue100','predict')}
nodes=[a[n] for n in ('Unavailable','require','validate_plan','_select_failure','_one_epoch_state','_interrupt_case')]
exec(compile(ast.Module(nodes,[]),str(P/'financial_wrapper_fixture.py')+':pure-controls','exec'),ns)
def handler(node):
    outer=next(n for n in node.body if isinstance(n,ast.Try))
    f=ast.FunctionDef(name='failure_control',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='primary'),ast.arg(arg='writer'),ast.arg(arg='directory')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[ast.Assign(targets=[ast.Name(id='_immutable',ctx=ast.Store())],value=ast.Name(id='writer',ctx=ast.Load())),ast.Try(body=[ast.Raise(exc=ast.Name(id='primary',ctx=ast.Load()),cause=None)],handlers=[copy.deepcopy(outer.handlers[0])],orelse=[],finalbody=[])],decorator_list=[])
    local={'_select_failure':ns['_select_failure']};exec(compile(ast.fix_missing_locations(ast.Module([f],[])),'exact failure handler','exec'),local);return local['failure_control']
old_handler=handler(b['execute']);new_handler=handler(a['execute']);witness=[]
for version,call in [('old',old_handler),('new',new_handler)]:
    for first_type in (ValueError,OSError,MemoryError,SystemExit,KeyboardInterrupt):
        for later_type in (ValueError,OSError,MemoryError,SystemExit,KeyboardInterrupt):
            primary=first_type('first');later=later_type('later');calls=[]
            def writer(*args):calls.append(1);raise later
            try:call(primary,writer,H/'opaque-control')
            except BaseException as actual:pass_value=actual
            else:raise AssertionError('failure swallowed')
            expected=primary if isinstance(primary,MemoryError) or not isinstance(primary,Exception) else later if isinstance(later,MemoryError) or not isinstance(later,Exception) else primary
            ok=pass_value is expected
            witness.append({'version':version,'first':first_type.__name__,'later':later_type.__name__,'observed':type(pass_value).__name__,'correct_identity':ok})
            if version=='new':check('firstfatal pair '+first_type.__name__+'/'+later_type.__name__,ok and len(calls)==1)
check('original RED cases retained',sum(not x['correct_identity'] for x in witness if x['version']=='old')==9)
class FatalStr(MemoryError):
    def __str__(self):raise SystemExit('later-str')
class OrdinaryStr(ValueError):
    def __str__(self):raise MemoryError('first-str-fatal')
class FatalNote(MemoryError):
    def add_note(self,value):raise SystemExit('later-note')
class OrdinaryNote(ValueError):
    def add_note(self,value):raise MemoryError('first-note-fatal')
class ReprFailure(OSError):
    def __repr__(self):raise KeyboardInterrupt('repr-fatal')
for i,(primary,later,expected_type,same,max_calls) in enumerate([(FatalStr(),OSError(),FatalStr,True,0),(OrdinaryStr(),OSError(),MemoryError,False,0),(FatalNote(),SystemExit(),FatalNote,True,1),(OrdinaryNote(),OSError(),MemoryError,False,1),(MemoryError(),ReprFailure(),MemoryError,True,1),(ValueError(),ReprFailure(),KeyboardInterrupt,False,1)]):
    calls=[]
    def writer(*args):calls.append(1);raise later
    try:new_handler(primary,writer,H/'opaque-control')
    except BaseException as actual:observed=actual
    check('diagnostic priority '+str(i),isinstance(observed,expected_type) and (observed is primary)==same and len(calls)==max_calls)

valid={'epoch':1,'batch':0,'epoch_count':0,'epoch_loss':0.,'logs':[{'epoch':0,'loss':.25,'examples':16,'seed':11}]}
ns['_one_epoch_state'](valid);checks.append('valid scalar original1 epoch')
for key,values in {'epoch':[0,2,99,100,101,True,1.0,None],'batch':[1,True,0.0,None],'epoch_count':[1,True,0.0,None],'epoch_loss':[1,True,float('nan'),float('inf'),None],'logs':[[],(),[valid['logs'][0]]*2,None]}.items():
    for value in values:
        mutated=copy.deepcopy(valid);mutated[key]=value;refuses('cursor refusal '+key+' '+repr(value),lambda mutated=mutated:ns['_one_epoch_state'](mutated))
for key,values in {'epoch':[1,True,0.0],'examples':[15,True,16.0],'seed':[12,True,11.0],'loss':[True,float('nan'),float('inf'),None]}.items():
    for value in values:
        mutated=copy.deepcopy(valid);mutated['logs'][0][key]=value;refuses('log refusal '+key+' '+repr(value),lambda mutated=mutated:ns['_one_epoch_state'](mutated))
plans=json.loads((P/'PHASE_TEMPLATES01.json').read_bytes())['templates'];parent=next(copy.deepcopy(p) for p in plans if p['phase']=='interrupt1');parent.update(experiment='opaque-parent',cell_id='opaque-cell',namespace='opaque-namespace');current=dict(parent,phase='continue100',experiment='opaque-next',prior_input='prior',reference_input='reference')
ns['_interrupt_case'](current,parent,'opaque-parent');checks.append('pure parent phase metadata accepted')
for key,values in {'phase':['complete100','agreement','predict','continue100'],'task':['regression'],'execution':['selected'],'experiment':['wrong'],'cell_id':['wrong'],'prior_input':['unexpected']}.items():
    for value in values:
        q=dict(parent);q[key]=value;refuses('phase refusal '+key+' '+value,lambda q=q:ns['_interrupt_case'](current,q,'opaque-parent'))

# Source-order/interface assertions: no positive fake authority invocation.
execute=ast.unparse(a['execute']);parent_text=ast.unparse(a['_interrupt_parent'])
check('genuine loaded state before pure cursor',execute.index('loaded = checkpoints.load_checkpoint')<execute.index('_one_epoch_state(loaded)')<execute.index('training.fit_cell('))
check('reference load before original reservation',execute.index('reference_state = _reference_state')<execute.index('training.fit_cell('))
check('original fit still called once',execute.count('training.fit_cell(')==1)
check('real claim-selected inputs API',"inputs = claim['inputs']" in parent_text and "inputs['execution_job']" in parent_text and "inputs[job['payload']['plan_input']]" in parent_text)
for phrase in ("claim_info['sha256'] == sha(raw)","fit / 'claim.json'","fit / 'failed.json'","fit / 'schedule.json'","_interrupt_case(p, old, parent)","'PlannedInterruption'","'parent_checkpoint': None","'interrupted-checkpoint.json'"):
    check('authentic parent obligation '+phrase,phrase in parent_text)
verify_source=ROOT/installed['sources']['tradingagents/research/verify.py']['source'];lifecycle=ROOT/installed['sources']['tradingagents/research/lifecycle.py']['source']
check('actual claim exposes resolved inputs','"inputs": admitted.inputs' in lifecycle.read_text() and 'claim["inputs"] != inputs' in verify_source.read_text())
check('nonmutated100 epoch engine',(P/'candidate02/training.py').read_bytes()==(O/'candidate02/training.py').read_bytes())
check('all18 still unreserved',len(plans)==18 and all(p['experiment'] is p['cell_id'] is p['namespace'] is None for p in plans))
check('no numerical module imported',not any(n in sys.modules for n in ('torch','numpy','scipy','pandas')))
result={'status':'PASS_SOURCE_ONLY','source_manifest_sha256':sha(raw),'source_sha256':sha(source),'check_count':len(checks),'checks':checks,'firstfatal_old_new':witness,'origins':origins,'no_genuine_run_owner_tensor_native_or_network':True,'qualification':'Static source joins and independent pure scalar/exception controls; actual genuine lifecycle/checkpoint execution unperformed.'}
(H/'INDEPENDENT_RESULTS02.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({'status':result['status'],'checks':len(checks),'old_firstfatal_RED_cases':sum(not x['correct_identity'] for x in witness if x['version']=='old')}))
