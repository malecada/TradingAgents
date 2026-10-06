import ast, hashlib, importlib.util, json, os, re, stat, threading, types
from pathlib import Path
P=Path(__file__).resolve().parent
C=P.parent/'real-data-pilot-control-history-candidate01-2026-10-06'
sha=lambda b:hashlib.sha256(b).hexdigest()
manifest=C/'MANIFEST01.json'
assert sha(manifest.read_bytes())=='00f9eb91ea6d1e3f55eedb4e4a64aa2dbc3b4b55d07a83e84503533c30ba0141'
for name,r in json.loads(manifest.read_bytes())['members'].items():
 b=(C/name).read_bytes(); assert len(b)==r['bytes'] and sha(b)==r['sha256'],name
for name,r in json.loads((C/'INVERSE01.json').read_bytes()).items():
 lines=(C/'candidate'/name).read_text().splitlines(keepends=True)
 for h in reversed(r['hunks']):
  a,b=h['candidate_start'],h['candidate_end'];assert lines[a:b]==h['candidate'];lines[a:b]=h['original']
 assert ''.join(lines).encode()==(C/'baseline'/name).read_bytes(),name
sp=importlib.util.spec_from_file_location('history_review',C/'candidate/archive_control_history.py');h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h)
def signature(s):return tuple(getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_size','st_mtime_ns','st_ctime_ns','st_blocks'))
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
ns=dict(require=h.need,canonical_bytes=canonical,digest=sha,re=re,stat=stat,low=types.SimpleNamespace(archive=types.SimpleNamespace(io=types.SimpleNamespace(_signature=signature)),sync_directory=lambda p:None),_retain=lambda primary,secondary:primary)
tree=ast.parse((C/'candidate/archive_dispatch.py').read_text());ctx=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Context');method=next(n for n in ctx.body if isinstance(n,ast.FunctionDef) and n.name=='_call');exec(compile(ast.Module(body=[method],type_ignores=[]),str(C/'candidate/archive_dispatch.py'),'exec'),ns)
rows=[]
# Execute exact orchestration method with local mechanical state, never a Run/Owner.
for label,payload,publication_failure in [('success',b'',False),('publication-failure',b'',True),('opaque-refusal',b'opaque',False)]:
 root=P/('history-'+label);root.mkdir();(root/'diagnostics').mkdir();file=root/'diagnostics/command-0001.bin'
 journal=h.Journal(root/'records',record_bytes=2048,total_bytes=16384,records=8,shard_bytes=4096)
 s=types.SimpleNamespace(root=root,_lock=threading.Lock(),_cap={'view':None,'remote_prefix':'actual','claim_sha256':'0'*64},_failed=False,_spent={'commands':0},_limits={'max_commands':1},_history=object(),_diagnostic_receipts=0,_diagnostic_pins={},_live=lambda:None)
 def receive(*a):file.write_bytes(payload);s._diagnostic_receipts+=1
 s._transport=types.SimpleNamespace(mkdir=receive)
 def snapshot():return {file.name:{'signature':list(signature(file.lstat())),'bytes':file.stat().st_size,'sha256':sha(file.read_bytes())}} if file.exists() else {}
 s._diagnostics=snapshot
 fatal=OSError('result publication failure')
 def publish(name,value):
  if name.startswith('result-'):
   assert file.exists()
   if publication_failure:raise fatal
  journal.append(name,canonical(value))
 s._publish=publish
 error=None
 try:ns['_call'](s,None,'mkdir','actual-000000000001')
 except BaseException as e:error=e
 if label=='success':
  assert error is None and not file.exists();journal.audit()
  raw=b''.join(x.read_bytes() for x in sorted(journal.root.iterdir()));assert b'empty_staging' in raw and b'command-0001.bin' in raw and sha(b'').encode() in raw
 else:
  assert error is not None and file.read_bytes()==payload and s._failed
  if publication_failure:assert error is fatal
 assert not s._lock.locked()
 rows.append({'case':label,'original_staging_retained':file.exists(),'failed':s._failed,'error_type':type(error).__name__ if error else None,'journal_count':journal.count})
policy={'schema_version':1,'format':h.FORMAT,'assumption':h.ASSUMPTION,'success_control_bytes':1024,'success_diagnostic_bytes':2048,'shard_bytes':4194304,'full_interval_ms':1000,'max_stale_ms':5000,'max_callbacks_between_full':100}
now=[0.];interval=h.Interval(policy,clock=lambda:now[0]);audit=[];interval.check(lambda:audit.append(1));now[0]=.1;interval.check(lambda:audit.append(1));assert len(audit)==1
interval.check(lambda:audit.append(1),force=True);assert len(audit)==2
result={'status':'passed-source-only','five_exact_inverses':True,'manifest_sha256':sha(manifest.read_bytes()),'checks':rows,'forced_boundary_audit':True,'illustrative_capacity':h.capacity(policy,472000),'not_authority_or_capacity_evidence':True}
(P/'HISTORY_CHECK01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
