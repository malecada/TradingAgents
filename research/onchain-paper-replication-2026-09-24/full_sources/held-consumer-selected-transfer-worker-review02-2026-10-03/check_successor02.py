import ast,builtins,hashlib,json,pathlib,shutil,subprocess,sys,types
P=pathlib.Path(__file__).resolve().parent;C=P.parent/'held-consumer-selected-transfer-worker-preparation02-2026-10-03';OLD=P.parent/'held-consumer-selected-transfer-worker-preparation01-2026-10-03'
def sha(b):return hashlib.sha256(b).hexdigest()
m=json.loads((C/'MANIFEST02.json').read_bytes());assert sha((C/'MANIFEST02.json').read_bytes())=='048a19325c31fbd07b18bf5baf5e7ede79d69683e41b6954058bf642a1df38c2'
for r in m['members']:
 b=(C/r['path']).read_bytes();assert sha(b)==r['sha256'] and len(b)==r['bytes']
rows=json.loads((C/'SOURCE_INVENTORY02.json').read_bytes())['entries']
for r in rows:
 b=pathlib.Path(r['origin']).read_bytes();assert sha(b)==r['sha256'] and len(b)==r['bytes']
assert len(rows)==len({r['target'] for r in rows})==201 and sum(r['package_source'] for r in rows)==150
old=(OLD/'held_score_consumer.py').read_text();new=(C/'held_score_consumer.py').read_text();line="        require(8*cells<=p['max_read_bytes'] and chunks<=p['max_members'],'held original population exceeds read policy before Context birth')\n"
assert new.count(line)==1 and new.replace(line,'')==old and ast.dump(ast.parse(new.replace(line,'')))==ast.dump(ast.parse(old))
assert (C/'resource_fixture.py').read_bytes()==(OLD/'resource_fixture.py').read_bytes()
work=P/'owned-source-replica';work.mkdir();rep=work/'candidate02';rep.mkdir()
for name in ['held_score_consumer.py','resource_fixture.py','held_score_consumer.py.baseline04.txt','resource_fixture.py.baseline04.txt','check01.py','check02.py','check03.py','check_stw1.py']:shutil.copyfile(C/name,rep/name)
engine_path=P.parent/'batch-output-selected-transfer-preparation01-2026-10-03/selected_non_tail_transport.py';e=work/engine_path.parent.name;e.mkdir();shutil.copyfile(engine_path,e/engine_path.name)
for name in ['check01.py','check02.py','check03.py','check_stw1.py']:
 r=subprocess.run([sys.executable,'-B',str(rep/name)],capture_output=True,timeout=30);(P/(name+'.log')).write_bytes(r.stdout+r.stderr);assert r.returncode==0,name
# Independent exact old/new functions and accepted rounding; no genuine handles.
def extract(path,names,ns):exec(compile(ast.Module([n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in names],[]),str(path),'exec'),ns)
eng={'BLOCK':32768};extract(engine_path,{'require','charge'},eng);pkg=types.SimpleNamespace(selected_non_tail_transport=types.SimpleNamespace(**eng))
def imports(name,*args,**kwargs):return pkg if name=='' else builtins.__import__(name,*args,**kwargs)
ns=[]
for d in [OLD,C]:
 env={'json':json,'__builtins__':{**vars(builtins),'__import__':imports}};extract(d/'held_score_consumer.py',{'require','_transfer_budget'},env);ns.append(env)
graphs=['a'*64,'b'*64];nodes=dict(zip(graphs,[2,3]));pop=dict(slots=[dict(graph=h,role='score-batches',max_members=32,max_bytes=200000) for h in graphs],max_parts=128,max_commands=128,max_rounded_bytes=2**27,deadline_seconds=1800,max_control_bytes=4*1024**2)
tx=dict(part_bytes=8192,stderr_bytes=1024,max_parts=128,max_commands=128,max_rounded_bytes=2**27,max_channel_bytes=2**27,command_seconds=1,cleanup_seconds=1,max_local_bytes=2**28,max_files=32768)
resources=dict(wall_seconds=1800,storage_budget=dict(limits=dict(max_logical_bytes=2**30,max_allocated_bytes=2**30)))
observations=[]
for chunk,bytes_,members,expected in [(64,1,2,False),(64,768,1,False),(64,767,2,False),(64,768,2,True),(32,768,2,False),(32,768,3,True),(128,768,1,True)]:
 p={'max_read_bytes':bytes_,'max_members':members};out=[]
 for env in ns:
  try:totals=env['_transfer_budget'](p,pop,tx,nodes,chunk,resources);out.append(True)
  except ValueError as e:assert 'held original population' in str(e);out.append(False)
 assert out==[True,expected];observations.append({'chunk':chunk,'read_bytes':bytes_,'members':members,'old_accepts':out[0],'new_accepts':out[1]})
# Source order remains before Context construction; the late real Target predicate is intact.
a=ast.parse(old);b=ast.parse(new)
for name in ['preflight','_TransferWorker','transfer_preflight','consume']:
 x=next(n for n in a.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name);y=next(n for n in b.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name);assert ast.dump(x)==ast.dump(y)
report={'status':'source-only accepted STW1 closed','manifest_bodies':len(m['members']),'source_count':201,'package_count':150,'admission_count':206,'output_count':10,'source_bytes':sum(r['bytes'] for r in rows),'author_tests':19,'independent_boundary_cases':observations,'actual_authority_or_network':False,'future_source_commit':None}
(P/'READBACK02.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps(report,sort_keys=True))
