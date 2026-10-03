"""Independent source-only review. No authority construction or numerical imports."""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import threading
import types
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
P = HERE.parent / 'batch-output-combined-worker-preparation01-2026-10-03'
D = HERE.parent / 'batch-output-produced-f32-adapter-preparation02-2026-10-03'
H = HERE.parent / 'batch-output-full-source-helper-preparation01-2026-10-03'
results = []
def check(label, value):
    assert value, label
    results.append(label)
def refused(label, fn):
    try: fn()
    except (ValueError, TypeError, KeyError): results.append(label); return
    raise AssertionError(label)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def extract(path, names, ns):
    tree = ast.parse(path.read_bytes())
    nodes = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in names]
    assert {n.name for n in nodes} == set(names)
    exec(compile(ast.Module(nodes, []), str(path), 'exec'), ns)
    return ns
def functions(path):
    return {n.name: n for n in ast.parse(path.read_bytes()).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}

manifest_raw = (P/'MANIFEST01.json').read_bytes()
check('exact author manifest', sha(manifest_raw)=='3f4a765ecc6314790e3c2e5e7e9a234b27094aedc56d871835e0a189f58e956f')
manifest = json.loads(manifest_raw)
check('36 distinct author evidence bodies', len(manifest['files'])==len({x['path'] for x in manifest['files']})==36)
for item in manifest['files']:
    path=P/item['path']; raw=path.read_bytes()
    check('manifest body '+item['path'], len(raw)==item['bytes'] and sha(raw)==item['sha256'])
inventory=json.loads((P/'SOURCE_INVENTORY01.json').read_bytes())
origins=[]
for item in inventory['entries']:
    path=Path(item['origin'])
    assert not any(s in ('keys','apis','.env','.git','.venv','node_modules') for s in path.parts)
    st=path.lstat(); assert stat.S_ISREG(st.st_mode) and st.st_nlink==1 and st.st_size<4*1024**2
    raw=path.read_bytes()
    check('origin '+item['target'], len(raw)==item['bytes'] and sha(raw)==item['sha256'])
    origins.append({'target':item['target'],'origin':str(path),'bytes':len(raw),'sha256':sha(raw)})
check('202 distinct source bodies', len(origins)==len({x['target'] for x in origins})==202)
check('151 actual package entries', sum(x['target'].startswith('tradingagents/') for x in origins)==151)
check('readback aggregate actual bytes', sum(x['bytes'] for x in origins)==json.loads((P/'SOURCE_READBACK01.json').read_bytes())['logical_source_bytes'])
prior=json.loads(Path(inventory['origin_inventory']['path']).read_bytes())
check('prior origin inventory hash', sha(Path(inventory['origin_inventory']['path']).read_bytes())==inventory['origin_inventory']['sha256'])
prior_entries={x['target']:x for x in prior['entries']}
changed=[x['target'] for x in inventory['entries'] if x['sha256']!=prior_entries[x['target']]['sha256']]
check('only two source body successor changes',set(changed)=={'tradingagents/research/onchain_replication/'+x for x in ('held_score_consumer.py','resource_fixture.py')})
fixed=next(n.value for n in ast.parse((H/'capsule_builder01.py').read_bytes()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='FULL_FIXED_SOURCES' for t in n.targets))
fixed=ast.literal_eval(fixed)
for name in ('held_score_consumer.py','resource_fixture.py'):
    key='tradingagents/research/onchain_replication/'+name
    check('old fixed helper correctly requires successor '+name, fixed[key]==sha((P/(name+'.baseline')).read_bytes()) and fixed[key]!=sha((P/name).read_bytes()))

old=functions(P/'held_score_consumer.py.baseline');new=functions(P/'held_score_consumer.py')
for name,node in old.items():
    if name in ('_policy','preflight','_transfer_closure','_worker_current'): continue
    new_name='_transfer_preflight_legacy' if name=='transfer_preflight' else name
    candidate=copy.deepcopy(new[new_name]);candidate.name=name
    check('unchanged original AST '+name,ast.dump(node)==ast.dump(candidate))
oldr=functions(P/'resource_fixture.py.baseline');newr=functions(P/'resource_fixture.py')
for name,node in oldr.items():
    if name in ('preflight','execute'):continue
    check('unchanged fixture AST '+name,ast.dump(node)==ast.dump(newr[name]))
check('byte identical completed adapter', (P/'completed_f32.py').read_bytes()==(P/'completed_f32.py.baseline').read_bytes()==(D/'completed_f32.py').read_bytes())
check('default local branch AST unchanged',ast.dump(oldr['execute'].body[2])==ast.dump(newr['execute'].body[2]))

ns={'Path':Path,'json':json,'hashlib':hashlib,'COMBINED_KIND':'selected-combined-f64-f32-source-closure-v2','RAW_KIND':'original-import-held-score-completed-f32-v3','TRANSFER_KIND':'original-import-held-score-selected-transfer-v2','KIND':'original-import-held-score-readback-v1'}
extract(P/'held_score_consumer.py',('require','_combined_closure','_transfer_closure','_policy','_combined_budget','_transfer_outputs'),ns)
code={f'opaque/source/{i}.py':sha(str(i).encode()) for i in range(201)}
code['tradingagents/research/onchain_replication/completed_f32.py']='a'*64
package=dict(list(code.items())[:150]);package['tradingagents/research/onchain_replication/completed_f32.py']='a'*64
aux={f'opaque/aux/{i}.json':'b'*64 for i in range(5)}
c={'schema_version':2,'kind':ns['COMBINED_KIND'],'implementation_source_count':202,'package_count':151,'source_files':code,'package_files':package,'auxiliary_source_files':aux}
check('independent exact202 closure',ns['_transfer_closure'](c,code|aux,package)==code)
for key,values in {'schema_version':[True,2.0,1,None],'kind':['selected-held-transfer-source-closure-v1','other',None],'implementation_source_count':[True,202.0,201,203],'package_count':[True,151.0,150,152]}.items():
    for value in values:
        q=copy.deepcopy(c);q[key]=value
        refused('typed closure '+key+' '+repr(value),lambda q=q:ns['_transfer_closure'](q,code|aux,package))
for name in ('../bad.py','/absolute.py','a//b.py','a/./b.py','a/../b.py'):
    q=copy.deepcopy(c);q['source_files'][name]=q['source_files'].pop('opaque/source/200.py')
    refused('closure path '+name,lambda q=q:ns['_transfer_closure'](q,q['source_files']|aux,package))
for variant in range(7):
    q=copy.deepcopy(c);r=code|aux;required=dict(package)
    if variant==0:q['source_files']['extra']='c'*64
    if variant==1:q['package_files']['opaque/source/0.py']='c'*64
    if variant==2:q['auxiliary_source_files']['opaque/source/0.py']=q['auxiliary_source_files'].pop('opaque/aux/0.json')
    if variant==3:r['opaque/source/1.py']='c'*64
    if variant==4:required.pop('opaque/source/2.py')
    if variant==5:q['package_files'].pop('tradingagents/research/onchain_replication/completed_f32.py')
    if variant==6:q['extra']='not-authority'
    refused('closure join mutation '+str(variant),lambda q=q,r=r,required=required:ns['_transfer_closure'](q,r,required))
legacy=copy.deepcopy(c);legacy.update(schema_version=1,kind='selected-held-transfer-source-closure-v1',implementation_source_count=201,package_count=150)
legacy['source_files'].pop('tradingagents/research/onchain_replication/completed_f32.py');legacy['package_files'].pop('tradingagents/research/onchain_replication/completed_f32.py')
check('independent original201/206 closure',ns['_transfer_closure'](legacy,legacy['source_files']|aux,legacy['package_files'])==legacy['source_files'])
g=['a'*64,'b'*64];p={'schema_version':3,'kind':ns['RAW_KIND'],'targets':{g[0]:{'output':'first.json'},g[1]:{'output':'second.json'}},'part_bytes':512,'max_read_bytes':768,'max_members':2,'population_input':'population','network_release_input':'release','source_closure_input':'source'}
check('explicit schema3 policy',ns['_policy'](p,g,['first.json','second.json']) is p)
for key,values in {'schema_version':[True,3.0,None],'kind':[ns['TRANSFER_KIND'],'unknown'],'part_bytes':[True,7,12,1048584],'max_members':[True,0,32768],'max_read_bytes':[True,0,2**40+1],'source_closure_input':['population',None,''],'network_release_input':['population']}.items():
    for value in values:
        q=copy.deepcopy(p);q[key]=value
        refused('policy mutation '+key+' '+repr(value),lambda q=q:ns['_policy'](q,g,['first.json','second.json']))
for variant in range(3):
    q=copy.deepcopy(p)
    if variant==0:q['targets'].pop(g[0])
    if variant==1:q['targets'][g[1]]['output']='first.json'
    if variant==2:q['targets'][g[1]]['output']='unregistered.json'
    refused('policy population/output '+str(variant),lambda q=q:ns['_policy'](q,g,['first.json','second.json']))
ns['_combined_budget'](p,dict(zip(g,[2,3])),64);results.append('held full original32 readback bounds')
for nodes,chunk,q in [(dict(zip(g,[2,4])),64,p),(dict(zip(g,[2,3])),True,p),(dict(zip(g,[2,3])),0,p),(dict(zip(g,[2,3])),64,dict(p,max_members=1)),(dict(zip(g,[2,3])),64,dict(p,max_read_bytes=767))]:
    refused('held extent bound '+repr((nodes,chunk,q['max_read_bytes'],q['max_members'])),lambda nodes=nodes,chunk=chunk,q=q:ns['_combined_budget'](q,nodes,chunk))

# Exact new exit, actual inherited reducer, qualified cleanup control doubles.
# These are deliberately not Context, ResearchRun, Owner, Ledger or Operation.
io_path=HERE.parent/'batch-output-exact-member-reader-candidate02-2026-10-03/owned_io.py'
io_ns={};exec(compile(io_path.read_bytes(),str(io_path),'exec'),io_ns)
dn={'CleanupFailure':io_ns['CleanupFailure']};extract(D/'archive_non_tail.py',('fatal','select','close_all'),dn)
raw=copy.deepcopy(new['_RawWorker']);raw.body=[n for n in raw.body if isinstance(n,ast.FunctionDef) and n.name=='__exit__']
wn={'__package__':'review_control','threading':threading,'_LOCK':threading.RLock(),'require':ns['require']}
exec(compile(ast.Module([raw],[]),'exact_raw_worker_exit','exec'),wn)
pkg=types.ModuleType('review_control');pkg.archive_non_tail=types.SimpleNamespace(select=dn['select'])
for index,(primary,later,wrong_thread) in enumerate([(None,None,False),(ValueError('body'),None,False),(MemoryError('body'),OSError('close'),False),(MemoryError('body'),SystemExit('close'),False),(ValueError('body'),KeyboardInterrupt('close'),False),(None,OSError('close'),False),(None,None,True),(MemoryError('body'),SystemExit('close'),True)]):
    calls=[]
    def close(*args):
        calls.append(args)
        if later is not None:raise later
    w=wn['_RawWorker']();w.thread=threading.get_ident()+int(wrong_thread);w.cm=types.SimpleNamespace(__exit__=close);wn['_WORKER']=w
    with patch.dict(sys.modules,{'review_control':pkg}):
        got=None
        try:w.__exit__(None if primary is None else type(primary),primary,None)
        except BaseException as e:got=e
    expected=primary
    if wrong_thread:expected=dn['select'](expected,ValueError('ownership'))
    if later is not None:expected=dn['select'](expected,later)
    check('firstfatal cleanup '+str(index),len(calls)==1 and wn['_WORKER'] is None and ((isinstance(got,ValueError) and wrong_thread and primary is None) or got is expected))

# Real tiny owned opaque bytes exercise the inherited reader now used by the new seam.
fixture=HERE/'opaque-utility-fixtures';fixture.mkdir(exist_ok=False)
body=fixture/'body.bin';body.write_bytes(b'opaque-source-only\x00\xff')
pkg.owned_io=types.SimpleNamespace(_cleanup=io_ns['_cleanup'])
reader_ns={'__package__':'review_control','os':os,'stat':stat,'require':ns['require']};extract(P/'held_score_consumer.py',('_body',),reader_ns)
with patch.dict(sys.modules,{'review_control':pkg}):
    check('real owned opaque source read',reader_ns['_body'](body)==body.read_bytes())
    link=fixture/'symbolic.bin';link.symlink_to(body.name)
    refused('source symlink refusal',lambda:reader_ns['_body'](link))
    hard=fixture/'hard.bin';os.link(body,hard)
    refused('source hardlink refusal',lambda:reader_ns['_body'](body))
    # Keep adversarial fixtures as evidence; use a separate singly-linked body.
    single=fixture/'single.bin';single.write_bytes(b'owned-byte')
    original_close=os.close;closed=[]
    def tracked_close(fd):closed.append(fd);original_close(fd)
    with patch.object(os,'close',tracked_close):check('second owned read',reader_ns['_body'](single)==b'owned-byte')
    check('both owned FDs released once',len(closed)==len(set(closed))==2)
    empty=fixture/'empty.bin';empty.write_bytes(b'')
    refused('empty source refusal',lambda:reader_ns['_body'](empty))

check('no numerical modules imported',not any(x in sys.modules for x in ('numpy','torch','scipy','pandas')))
record={'status':'PASS','check_count':len(results),'checks':results,'origins':origins,'source_manifest_sha256':sha(manifest_raw),'actual_source_bytes':sum(x['bytes'] for x in origins),'inventory_aggregate_field':inventory['implementation_bytes'],'known_stale_inventory_aggregate':inventory['implementation_bytes']!=sum(x['bytes'] for x in origins),'execution_admitted':False,'real_authority_objects_constructed':False,'network_or_numerical_execution':False}
(HERE/'CHECK_RESULTS01.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k not in ('checks','origins')},sort_keys=True))
