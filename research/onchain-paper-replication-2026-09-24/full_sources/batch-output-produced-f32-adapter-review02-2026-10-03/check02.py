import ast,hashlib,json,os,pathlib,shutil,subprocess,sys,importlib.util
P=pathlib.Path(__file__).resolve().parent; C=P.parent/'batch-output-produced-f32-adapter-preparation02-2026-10-03'; O=P.parent/'batch-output-produced-f32-adapter-preparation01-2026-10-03'
def sha(b):return hashlib.sha256(b).hexdigest()
m=json.loads((C/'MANIFEST02.json').read_bytes());assert sha((C/'MANIFEST02.json').read_bytes())=='97343a23f1b53c92f8d1af7856455ae81585e2f82d3662578c39e9cc3d9afd99'
for r in m['members']:
 b=(C/r['path']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
rows=json.loads((C/'SOURCE_INVENTORY02.json').read_bytes())['entries']
for r in rows:
 b=pathlib.Path(r['origin']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256']
assert len(rows)==len({r['target'] for r in rows})==202 and sum(r['package_source'] for r in rows)==151
for f in ['completed_f32.py','compact_mcm.py','archive_non_tail.py']:assert (C/f).read_bytes()==(O/f).read_bytes()
a=(O/'selected_non_tail_transport.py').read_text();b=(C/'selected_non_tail_transport.py').read_text()
old1="require(type(c) is durable.Context and c.policy['schema_version']==2,'genuine selected Context required')"
new1="require(type(c) is durable.Context and (c.policy['schema_version']==2 or (type(c.policy['schema_version']) is int and c.policy['schema_version']==3)),'genuine selected Context required')"
old2="if operation.ledger.context.policy.get('schema_version')!=2:raise NotImplementedError('selected pipe dispatcher absent')"
new2="if not (operation.ledger.context.policy.get('schema_version')==2 or (type(operation.ledger.context.policy.get('schema_version')) is int and operation.ledger.context.policy['schema_version']==3)):raise NotImplementedError('selected pipe dispatcher absent')"
assert b.count(new1)==b.count(new2)==1
inverse=b.replace(new1,old1).replace(new2,old2);assert inverse==a and ast.dump(ast.parse(inverse))==ast.dump(ast.parse(a))
work=P/'owned-replicas';work.mkdir(); dep=work/'neural-cold-feature-handoff-held-score-reader-preparation01-2026-10-03';dep.mkdir()
for f in ['owned_io.py','exact_members02.py']:shutil.copyfile(P.parent/dep.name/f,dep/f)
results=[]
for label in ('old','new'):
 rep=work/label;rep.mkdir()
 for f in C.iterdir():
  if f.is_file() and (f.suffix=='.py' or f.name.endswith('.txt')):shutil.copyfile(f,rep/f.name)
 if label=='old':shutil.copyfile(O/'selected_non_tail_transport.py',rep/'selected_non_tail_transport.py')
 names=['check_entrypoints02.py'] if label=='old' else ['check_entrypoints02.py','check_adapter01.py','check_bytes01.py','check_parity01.py','check_policy01.py']
 for name in names:
  r=subprocess.run([sys.executable,'-B',str(rep/name)],capture_output=True,timeout=30);(P/(label+'-'+name+'.log')).write_bytes(r.stdout+r.stderr);assert (r.returncode!=0)==(label=='old'),(label,name,r.stderr)
  results.append({'source':label,'check':name,'exit':r.returncode})
# Independent actual close_context injection: close succeeds then reports uncertainty;
# body first-fatal must remain identical and FD may not be retried.
spec=importlib.util.spec_from_file_location('entry',work/'new/check_entrypoints02.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
checks=mod.Checks(); independent=[]
for primary in (MemoryError('body'),KeyboardInterrupt('body'),SystemExit('body')):
 e,c,op,calls=checks.setup_engine(3);c.fd=os.open(P,os.O_RDONLY|os.O_DIRECTORY);closed=[]
 def close(fd):closed.append(fd);os.close(fd);raise OSError('uncertain after actual close')
 e['os'].close=close
 try:e['close_context'](c,primary)
 except BaseException as error:assert error is primary
 else:raise AssertionError('fatal lost')
 assert closed==[c.fd] and c.closed
 try:os.fstat(c.fd)
 except OSError:pass
 else:raise AssertionError('descriptor leaked')
 independent.append(type(primary).__name__)
assert not any(x in sys.modules for x in ('numpy','torch','scipy'))
result={'status':'accepted source-only narrow F32-1/F32-2 correction','manifest_sha256':sha((C/'MANIFEST02.json').read_bytes()),'members':len(m['members']),'bytes':sum(r['bytes'] for r in m['members']),'sources':202,'package':151,'prospective_admission_pins':207,'two_guard_inverse':True,'other_three_bodies_identical':True,'checks':results,'independent_close_error_firstfatal':independent,'qualified_tests':23,'authority':'test construction bypass only; actual Session stops at rejecting original authority boundary; no genuine positive capability or process/network'}
(P/'READBACK02.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))
