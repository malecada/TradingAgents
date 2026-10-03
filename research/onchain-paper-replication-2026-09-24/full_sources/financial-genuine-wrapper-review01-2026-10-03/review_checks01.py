"""Independent source-only witnesses. No Run/Owner/tensor/numerical stand-ins."""
import ast,copy,hashlib,json,stat,sys
from pathlib import Path
H=Path(__file__).resolve().parent
P=H.parent/'financial-genuine-wrapper-preparation01-2026-10-03'
ROOT=P.parents[3]
checks=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def check(label,ok):assert ok,label;checks.append(label)
raw=(P/'MANIFEST01.json').read_bytes();manifest=json.loads(raw)
check('exact typed subject manifest',sha(raw)=='f6bf2be20dd3e2cc77b53bf4c2c75ce4638da7e1600bd944addd4ed658d89b2d')
check('38 typed members',len(manifest['members'])==38)
for r in manifest['members']:
    p=P/r['path'];s=p.lstat()
    check('member mode '+r['path'],stat.S_IMODE(s.st_mode)==r['mode'])
    if r['kind']=='directory':check('directory '+r['path'],stat.S_ISDIR(s.st_mode));continue
    check('regular member '+r['path'],stat.S_ISREG(s.st_mode) and s.st_nlink==1)
    b=p.read_bytes();check('member body '+r['path'],len(b)==r['bytes'] and sha(b)==r['sha256'])
source=(P/'financial_wrapper_fixture.py').read_bytes()
check('exact wrapper body',sha(source)=='5e8face14c8624512692caf62b8f3f153c7ed90f720ce8bf43858ecf929d60bc')
for f in (P/'candidate02').glob('*.py'):
    check('actual accepted candidate02 origin '+f.name,f.read_bytes()==(H.parent/'financial-streamed-execution-candidate02-2026-10-02'/f.name).read_bytes())
check('seven exact candidate modules',len(list((P/'candidate02').glob('*.py')))==7)
installed=json.loads((P/'INSTALLATION01.json').read_bytes());closure=json.loads((P/'SOURCE_CLOSURE01.json').read_bytes())
check('194 exact closure targets',len(installed['sources'])==len(closure['installed'])==194 and set(installed['sources'])==set(closure['installed']))
origins=[]
for target,r in installed['sources'].items():
    p=ROOT/r['source'];assert not any(v in ('.env','keys','apis','.git','.venv','node_modules') for v in p.parts)
    s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<4*1024**2
    b=p.read_bytes();check('source origin '+target,sha(b)==r['sha256']==closure['installed'][target]);origins.append({'target':target,'origin':str(p),'bytes':len(b),'sha256':sha(b)})
for name,steps in json.loads((P/'adaptations.json').read_bytes()).items():
    text=(P/name).read_text()
    for step in reversed(steps):
        check('inverse occurrence '+name+' '+str(len(checks)),text.count(step['after'])==step.get('count',1));text=text.replace(step['after'],step['before'])
    baseline=P/('job.baseline.py' if name=='job.py' else 'candidate02/replay.py')
    check('full conditional byte inverse '+name,text.encode()==baseline.read_bytes())
tree=ast.parse(source);functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
execute=functions['execute'];auth=functions['authorize']
check('authorize is first executable wrapper call',isinstance(execute.body[0],ast.Assign) and ast.unparse(execute.body[0].value).startswith('authorize('))
check('no top-level numerical import',all(not (isinstance(n,ast.Import) and any(x.name.split('.')[0] in ('torch','numpy','scipy') for x in n.names)) for n in tree.body))
check('original hundred epoch fit called',any(isinstance(n,ast.Call) and ast.unparse(n.func)=='training.fit_cell' for n in ast.walk(execute)))
check('no synthetic authority class',not any(isinstance(n,ast.ClassDef) and n.name in ('Owner','ResearchRun','Binding') for n in ast.walk(tree)))
plans=json.loads((P/'PHASE_TEMPLATES01.json').read_bytes())['templates']
check('18 exact distinct prospective phases',len(plans)==len({(p['phase'],p['task'],p['execution']) for p in plans})==18)
check('all actual identities still null',all(p['experiment'] is p['cell_id'] is p['namespace'] is None for p in plans))
check('no installed authority fabricated',installed['genuine_installed_commit'] is installed['genuine_installed_capsule'] is installed['source_review'] is None)
model=json.loads((P/'model.json').read_bytes());training=json.loads((P/'training.json').read_bytes())
check('unchanged full schedule',training['epochs']==100 and training['batch_size']==16 and model['lookback_days']==28 and not model.get('graph_activation_checkpointing',False))

# FW1: run ONLY the exact newly added exception handler around an injected
# ordinary raise. The callback is a qualified failure-evidence writer double,
# never a Run, owner, checkpoint, tensor, native guard or authority provider.
outer=next(n for n in execute.body if isinstance(n,ast.Try))
check('one outer failure handler',len(outer.handlers)==1 and outer.handlers[0].name=='error')
test=ast.FunctionDef(name='exact_failure_handler',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg='primary'),ast.arg(arg='writer'),ast.arg(arg='directory')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=[ast.Assign(targets=[ast.Name(id='_immutable',ctx=ast.Store())],value=ast.Name(id='writer',ctx=ast.Load())),ast.Try(body=[ast.Raise(exc=ast.Name(id='primary',ctx=ast.Load()),cause=None)],handlers=[copy.deepcopy(outer.handlers[0])],orelse=[],finalbody=[])],decorator_list=[])
ns={};exec(compile(ast.fix_missing_locations(ast.Module([test],[])),'exact financial wrapper failure handler','exec'),ns)
fatal_witness=[]
for primary,later in [(MemoryError('first memory failure'),SystemExit('later publication interruption')),(SystemExit('first interruption'),MemoryError('later publication memory failure')),(MemoryError('first memory failure'),OSError('ordinary publication failure')),(ValueError('ordinary body failure'),MemoryError('later fatal'))]:
    calls=[]
    def writer(*args):calls.append(args[0]);raise later
    observed=None
    try:ns['exact_failure_handler'](primary,writer,H/'owned-opaque-control')
    except BaseException as e:observed=e
    expected=primary if isinstance(primary,MemoryError) or not isinstance(primary,Exception) else later if isinstance(later,MemoryError) or not isinstance(later,Exception) else primary
    fatal_witness.append({'primary':type(primary).__name__,'later':type(later).__name__,'observed':type(observed).__name__,'preserves_primary_identity':observed is primary,'required_identity_retained':observed is expected,'writer_calls':len(calls),'original_retained_as_cause':observed.__cause__ is primary})
check('FW1 exact firstfatal RED reproduced',sum(not r['required_identity_retained'] for r in fatal_witness)==2)

# FW2: original scalar cursor rejection and loop condition, extracted without
# importing training.py. This is metadata only; no synthetic checkpoint or model.
train=ast.parse((P/'candidate02/training.py').read_bytes());fit=next(n for n in train.body if isinstance(n,ast.FunctionDef) and n.name=='fit_cell');body=next(n for n in fit.body if isinstance(n,ast.Try)).body
cursor=next(n for n in body if isinstance(n,ast.If) and 'checkpoint cursor outside registered fit' in ast.unparse(n))
loop=next(n for n in body if isinstance(n,ast.While))
code=compile(ast.Expression(cursor.test),'actual original fit cursor predicate','eval');condition=compile(ast.Expression(loop.test),'actual original fit loop predicate','eval')
cursor_rows=[]
for epoch in (0,1,2,99,100,101):
    scope={'epoch':epoch,'batch':0,'epochs':100,'batches':1}
    cursor_rows.append({'epoch':epoch,'batch':0,'rejected_by_original_cursor':bool(eval(code,scope)),'enters_training_loop':bool(eval(condition,scope)),'remaining_epochs':max(0,100-epoch)})
check('FW2 epoch100 cursor accepted and zero-update loop',cursor_rows[-2]['rejected_by_original_cursor'] is False and cursor_rows[-2]['enters_training_loop'] is False)
parent_text=ast.unparse(functions['_parent'])
check('FW2 parent has no phase or checkpoint cursor requirement',not any(s in parent_text for s in ("['epoch']","['batch']","['phase'] == 'interrupt1'","'wrapper_plan'","'schedule.json'")))
order=[ast.unparse(n) for n in ast.walk(fit) if isinstance(n,ast.Call)]
source_training=(P/'candidate02/training.py').read_text()
check('genuine final callback occurs after checkpoint before completion',source_training.index('checkpoint=save_checkpoint')<source_training.index('after_batch(epoch,batch,checkpoint)')<source_training.index("_immutable(directory/'complete.json'"))
check('wrapper complete100 callback can fail on lease before return','lease()' in ast.unparse(next(n for n in ast.walk(execute) if isinstance(n,ast.FunctionDef) and n.name=='after')))
check('no numerical module imported',not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')))
record={'status':'WITHHELD','source_manifest_sha256':sha(raw),'source_sha256':sha(source),'check_count':len(checks),'checks':checks,'source_origins':origins,'FW1_exact_failure_handler':fatal_witness,'FW2_actual_cursor_predicates':cursor_rows,'qualification':'Only exact source AST/pure scalar metadata/exception controls. No numerical module, array, label, fake Run/Owner, real checkpoint, native claim or network operation.'}
(H/'INDEPENDENT_RESULTS01.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':'WITHHELD','checks':len(checks),'FW1':fatal_witness,'FW2_epoch100':cursor_rows[-2]},sort_keys=True))
