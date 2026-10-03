"""Independent read-only helper-map review: stdlib, no authority or numerical work."""
import ast,copy,hashlib,json,stat,sys
from pathlib import Path
H=Path(__file__).resolve().parent
P=H.parent/'batch-output-full-source-helper-preparation02-2026-10-03'
B=H.parent/'batch-output-full-source-helper-preparation01-2026-10-03'
W=H.parent/'batch-output-combined-worker-preparation01-2026-10-03'
checks=[]
def check(label,condition):assert condition,label;checks.append(label)
def sha(body):return hashlib.sha256(body).hexdigest()
def refuses(label,fn):
    try:fn()
    except (ValueError,TypeError,KeyError):checks.append(label);return
    raise AssertionError(label)
def extract(path):
    tree=ast.parse(path.read_bytes());ns={'Path':Path,'MAX':4*1024**2}
    nodes=[]
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('FULL_MODE','FULL_HELPERS','FULL_FIXED_SOURCES') for t in node.targets):nodes.append(node)
        if isinstance(node,ast.FunctionDef) and node.name in ('require','full_mode','full_package','full_rows'):nodes.append(node)
    exec(compile(ast.Module(nodes,[]),str(path),'exec'),ns);return ns
manifest_raw=(P/'MANIFEST02.json').read_bytes();manifest=json.loads(manifest_raw)
check('exact subject manifest',sha(manifest_raw)=='3f38075bb3ecdf342367374b6655ff3d74764eaf6fa010af1ff4104d81d5a798')
check('19 distinct evidence bodies',len(manifest['files'])==len({r['path'] for r in manifest['files']})==19)
for r in manifest['files']:
    raw=(P/r['path']).read_bytes();check('evidence '+r['path'],len(raw)==r['bytes'] and sha(raw)==r['sha256'])
old=extract(B/'capsule_builder01.py');new=extract(P/'capsule_builder01.py')
check('same exact source roster',old['FULL_FIXED_SOURCES'].keys()==new['FULL_FIXED_SOURCES'].keys())
changed={k:(old['FULL_FIXED_SOURCES'][k],v) for k,v in new['FULL_FIXED_SOURCES'].items() if old['FULL_FIXED_SOURCES'][k]!=v}
check('only intended two fixed hashes',set(changed)=={'tradingagents/research/onchain_replication/'+s for s in ('held_score_consumer.py','resource_fixture.py')})
inverse=(P/'capsule_builder01.py').read_bytes()
for path,(before,after) in changed.items():
    check('actual accepted worker body '+path,sha((W/Path(path).name).read_bytes())==after)
    check('single literal substitution '+path,inverse.count(after.encode())==1)
    inverse=inverse.replace(after.encode(),before.encode())
check('full byte inverse exactly predecessor',inverse==(B/'capsule_builder01.py').read_bytes()==(P/'capsule_builder01.py.baseline.txt').read_bytes())
for name in ('capsule_builder01.py','generate_inputs01.py','build_release_draft01.py'):
    a=ast.parse((P/name).read_bytes());b=ast.parse((B/name).read_bytes())
    aa=[ast.dump(n) for n in a.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))];bb=[ast.dump(n) for n in b.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))]
    check('every function/class AST unchanged '+name,aa==bb)
    check('genuine supplied predecessor '+name,(P/(name+'.baseline.txt')).read_bytes()==(B/name).read_bytes())
    if name!='capsule_builder01.py':check('entire unchanged helper '+name,(P/name).read_bytes()==(B/name).read_bytes())
check('unchanged explicit mode',new['FULL_MODE']==old['FULL_MODE']=='completed-f32-and-held-f64-source-closure-v1')
check('exact three helper path roster',new['FULL_HELPERS']==old['FULL_HELPERS']==('fixture_tools/capsule_builder01.py','fixture_tools/generate_inputs01.py','proof_tools/build_release_draft01.py'))
inventory_raw=(P/'SOURCE_INVENTORY02.json').read_bytes();inventory=json.loads(inventory_raw);template=json.loads((P/'ROOT_TEMPLATE02.json').read_bytes())
check('exact inventory pin',sha(inventory_raw)=='6f695a2f4935bd8d06ecc0e97d58aa63e11a1a98d6df69fb6d8074a45e3612b1')
rows=template['rows'];mode=template['closure_mode'];code,package=new['full_rows'](rows,mode)
check('202source151package shapes',len(code)==202 and len(package)==151)
check('inventory and template same full map',{r['target']:r['sha256'] for r in inventory['entries']}==code)
check('template exact future null authority',all(template[k] is None for k in ('current_source','design_source','genuine151_anchor','registration','native_release','role_references')) and template['execution_admitted'] is False)
for name,digest in mode['helper_source_files'].items():
    check('actual externally pinned helper '+name,digest==sha((P/Path(name).name).read_bytes()))
origins=[]
for r in inventory['entries']:
    p=Path(r['origin']);assert not any(v in ('.env','keys','apis','hf_token.txt','.git','.venv','node_modules') for v in p.parts)
    st=p.lstat();assert stat.S_ISREG(st.st_mode) and st.st_nlink==1 and 0<st.st_size<=4*1024**2
    raw=p.read_bytes();check('actual source '+r['target'],len(raw)==r['bytes'] and sha(raw)==r['sha256'])
    origins.append({'target':r['target'],'origin':r['origin'],'sha256':sha(raw),'bytes':len(raw)})
check('actual distinct source origins',len(origins)==len({r['target'] for r in origins})==202)
check('correct aggregate fixes prior P3',sum(r['bytes'] for r in origins)==inventory['implementation_bytes']==3543144)
check('metadata prospective207 remains separate',inventory['prospective_admission_count']==207 and inventory['package_count']==151 and inventory['source_count']==202)
for variant,value in enumerate([None,{},dict(mode,schema_version=True),dict(mode,schema_version=1.0),dict(mode,schema_version=2),dict(mode,kind='selected-combined-f64-f32-source-closure-v2'),dict(mode,extra=True)]):
    refuses('mode refusal '+str(variant),lambda value=value:new['full_mode'](value))
for variant in range(8):
    q=copy.deepcopy(mode);pins=q['helper_source_files']
    if variant==0:pins.pop(next(iter(pins)))
    if variant==1:pins['extra_helper.py']='a'*64
    if variant==2:pins[next(iter(pins))]=True
    if variant==3:pins[next(iter(pins))]='A'*64
    if variant==4:pins[next(iter(pins))]='a'*63
    if variant==5:pins[next(iter(pins))]=None
    if variant==6:q['helper_source_files']=list(pins.items())
    if variant==7:pins['../fixture_tools/capsule_builder01.py']=pins.pop('fixture_tools/capsule_builder01.py')
    refuses('helper pin refusal '+str(variant),lambda q=q:new['full_mode'](q))
for variant in range(12):
    rr=copy.deepcopy(rows)
    if variant==0:rr.pop()
    if variant==1:rr.reverse()
    if variant==2:rr[0]['path']=rr[1]['path']
    if variant==3:rr[0]['sha256']='f'*64
    if variant==4:rr[0]['bytes']=True
    if variant==5:rr[0]['bytes']=0
    if variant==6:rr[0]['bytes']=4*1024**2+1
    if variant==7:rr[0]['bytes']=8.0
    if variant==8:rr[0]['extra']='not-authority'
    if variant==9:rr[0]['path']='unknown_helper.py'
    if variant==10:rr[0]['sha256']=None
    if variant==11:
        for row in rr:row['bytes']=4*1024**2
    refuses('source row refusal '+str(variant),lambda rr=rr:new['full_rows'](rr,mode))
# Identical accepted source rows and original external helper pins isolate the
# two changed worker entries, independent of either author's test expectations.
combined=json.loads((W/'SOURCE_INVENTORY01.json').read_bytes())
pair_rows=[{'path':r['target'],'sha256':r['sha256'],'bytes':r['bytes']} for r in combined['entries']]
old_mode=json.loads((B/'ROOT_TEMPLATE01.json').read_bytes())['closure_mode']
refuses('original fixed map refuses accepted combined pair',lambda:old['full_rows'](pair_rows,old_mode))
accepted=new['full_rows'](pair_rows,old_mode)
check('successor accepts same combined pair',len(accepted[0])==202 and len(accepted[1])==151)
for field in ('FULL_HELPERS','FULL_MODE'):check('no mode constant expansion '+field,new[field]==old[field])
check('no numerical modules imported',not any(k in sys.modules for k in ('numpy','scipy','torch','pandas')))
result={'status':'PASS','check_count':len(checks),'checks':checks,'changed_map':changed,'origins':origins,'actual_implementation_bytes':sum(r['bytes'] for r in origins),'execution_admitted':False,'qualification':'Independent literal-map extraction, full byte/AST inverse, actual source hash reads and pure metadata mutations only. No Git process, network, numerical job or authority construction.'}
(H/'INDEPENDENT_RESULTS02.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':'PASS','checks':len(checks),'actual_implementation_bytes':result['actual_implementation_bytes']}))
