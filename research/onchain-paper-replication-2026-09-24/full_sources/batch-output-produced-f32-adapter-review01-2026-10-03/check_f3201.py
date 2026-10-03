import ast,hashlib,json,os,pathlib,shutil,subprocess,sys,types
P=pathlib.Path(__file__).resolve().parent;C=P.parent/'batch-output-produced-f32-adapter-preparation01-2026-10-03'
def sha(b):return hashlib.sha256(b).hexdigest()
m=json.loads((C/'MANIFEST01.json').read_bytes());assert sha((C/'MANIFEST01.json').read_bytes())=='d60d5c8fd0604c8d31d3f3bc5046b628568e3f161a297db1d9895cfafbb10855'
for r in m['members']:
 b=(C/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
rows=json.loads((C/'SOURCE_INVENTORY01.json').read_bytes())['entries']
for r in rows:
 b=pathlib.Path(r['origin']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
assert len(rows)==len({r['target'] for r in rows})==202 and sum(r['package_source'] for r in rows)==151
work=P/'owned-source-replica';work.mkdir();rep=work/'candidate';rep.mkdir()
for name in ['completed_f32.py','compact_mcm.py','compact_mcm.py.baseline.txt','archive_non_tail.py','archive_non_tail.py.baseline.txt','selected_non_tail_transport.py','selected_non_tail_transport.py.baseline.txt','check_adapter01.py','check_bytes01.py','check_parity01.py','check_policy01.py']:shutil.copyfile(C/name,rep/name)
d=work/'neural-cold-feature-handoff-held-score-reader-preparation01-2026-10-03';d.mkdir()
for name in ['owned_io.py','exact_members02.py']:shutil.copyfile(P.parent/d.name/name,d/name)
for name in ['check_adapter01.py','check_bytes01.py','check_parity01.py','check_policy01.py']:
 r=subprocess.run([sys.executable,'-B',str(rep/name)],capture_output=True,timeout=30);(P/(name+'.log')).write_bytes(r.stdout+r.stderr);assert r.returncode==0,name
# Actual engine entrypoints and actual extracted Context/Operation classes.
# __init__/authority checks are deliberately not invoked. These isolate schema
# dispatch/close gates and cannot supply an admitted positive capability.
ds={}
tree=ast.parse((C/'archive_non_tail.py').read_text())
exec(compile(ast.Module([n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ('require','Context','Operation')],[]),'actual-durable-classes','exec'),ds)
durable=types.SimpleNamespace(**ds);Context=ds['Context'];Operation=ds['Operation']
engine={'durable':durable}
tree=ast.parse((C/'selected_non_tail_transport.py').read_text())
exec(compile(ast.Module([n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('require','dispatch','close_context')],[]),'actual-engine-entrypoints','exec'),engine)
ctx=object.__new__(Context);ctx.policy={'schema_version':3};ctx.closed=False;ctx.failed=False;ctx.fd=os.open(P,os.O_RDONLY|os.O_DIRECTORY)
op=object.__new__(Operation);op.ledger=types.SimpleNamespace(context=ctx);called=[];op.check=lambda:called.append('qualified authority check stand-in')
observations=[]
try:
 try:engine['dispatch'](op)
 except NotImplementedError as e:observations.append({'entry':'dispatch','schema':3,'error_type':type(e).__name__,'reason':str(e),'Session_reached':False})
 else:raise AssertionError('expected unchanged schema2 dispatch refusal')
 try:engine['close_context'](ctx)
 except ValueError as e:
  os.fstat(ctx.fd)
  observations.append({'entry':'close_context','schema':3,'error_type':type(e).__name__,'reason':str(e),'original_fd_still_open':True,'closed_flag':ctx.closed})
 else:raise AssertionError('expected unchanged schema2 close refusal')
finally:os.close(ctx.fd)
assert len(called)==1 and len(observations)==2
result={'candidate_bodies':len(m['members']),'candidate_bytes':sum(r['bytes'] for r in m['members']),'source_count':202,'package_count':151,'prospective_admission_count':207,'author_tests':15,'counterexamples':observations,'qualification':'actual extracted class/function control flow; construction and authority deliberately bypassed for branch isolation, no genuine capability or remote/native invocation','status':'WITHHELD two raw schema3 engine entrypoint blockers'}
(P/'READBACK01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,sort_keys=True))
