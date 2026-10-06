from pathlib import Path
import json,hashlib,difflib
H=Path(__file__).resolve().parent;F=H.parent;B=F/'real-data-pilot-may30-ledger-continuation-entry-preparation01-2026-10-06';inv=json.loads((H/'INVERSE01.json').read_text())
for name in ('prepare01.py','preflight01.py'):
 old=(B/name).read_text();s=old;edits=[]
 def edit(a,b):
  global s
  assert s.count(a)==1;s=s.replace(a,b);edits.append({'before':a,'after':b})
 if name=='prepare01.py':
  edit("p=HANDOFF/'candidate/graph_ledger_continuation.py'","p=ROOT/'tradingagents/research/onchain_replication/graph_ledger_continuation.py'")
  edit('b576dc363ce047c10c9fa3dbb45ccb87f0724a68c5bd60121d4685da67213e69',hashlib.sha256((H/'graph_ledger_continuation.py').read_bytes()).hexdigest())
  edit("m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m","m=importlib.util.module_from_spec(sp);m.__package__='tradingagents.research.onchain_replication';sp.loader.exec_module(m);return m")
  edit("'source_files','runtime_hashes'}","'source_files','runtime_hashes','relocation_receipt','relocation_review'}")
  edit("    r=read(b['recovery']);", """    need(p['schema_version']==2,'explicit fixed cross-volume plan required')
    def relocation_read(role):
        key={p['relocation_receipt_input']:'relocation_receipt',p['relocation_review_input']:'relocation_review'}[role]
        read(b[key]);return (ROOT/b[key]['path']).read_bytes()
    m.relocated_path(ROOT,p,relocation_read)
    r=read(b['recovery']);""")
  edit("'scratch_scope','storage_budget'},","'scratch_scope','storage_budget','data_store'},")
  edit("s['schema_version']==1", "s['schema_version']==2")
  edit("    e=read(b['extension']);", """    need(s['data_store']=={'storage_budget':m.data_budget(p),'device':m.DATA_DEVICE,'disk_floor_bytes':10*GIB,'free_reserve_bytes':m.DATA_RESERVE},'exact separately retained Data accounting required')
    import shutil
    need(shutil.disk_usage(m.DATA_ROOT).free>=10*GIB+m.DATA_RESERVE,'Data floor plus retained-store headroom unavailable')
    e=read(b['extension']);""")
  edit("job['resources']['storage_budget']=s['storage_budget']", "job['resources']['storage_budget']=s['storage_budget'];job['resources']['disk_paths']=[str(ROOT),str(m.DATA_ROOT)]")
  edit("('storage_policy',binding['storage_policy'])]", "('storage_policy',binding['storage_policy']),(p['relocation_receipt_input'],binding['relocation_receipt']),(p['relocation_review_input'],binding['relocation_review'])]")
 else:
  edit("    plan,policy,_=validate_binding(binding)","    plan,policy,control=validate_binding(binding)")
  edit("    if job['resources']!=baseline('execution-job01.json')['resources']:raise ValueError('unchanged native/storage controls differ')", "    expected_resources=baseline('execution-job01.json')['resources'];expected_resources['disk_paths']=[str(ROOT),str(control.DATA_ROOT)]\n    if job['resources']!=expected_resources:raise ValueError('unchanged native/storage controls or exact two-volume floors differ')")
  edit("('storage_policy','storage_policy')]", "('storage_policy','storage_policy'),(plan['relocation_receipt_input'],'relocation_receipt'),(plan['relocation_review_input'],'relocation_review')]")
  edit("    free=shutil.disk_usage(ROOT).free; available=mem_available()", "    data_storage=StorageWatch(**control.data_budget(plan)).check()\n    data_free=shutil.disk_usage(control.DATA_ROOT).free\n    if data_free<10*1024**3+control.DATA_RESERVE:raise ValueError('Data floor plus retained-store reserve unavailable')\n    free=shutil.disk_usage(ROOT).free; available=mem_available()")
  edit("'startup_free_requirement_bytes':policy['startup_free_requirement_bytes'],'storage_observation':storage,", "'startup_free_requirement_bytes':policy['startup_free_requirement_bytes'],'storage_observation':storage,\n        'Data_storage_observation':data_storage,'Data_free_disk_bytes':data_free,'retained_ledger_path':str(control.EXTERNAL),")
 (H/name).write_text(s);inv[name]={'baseline':str(B/name),'before_sha256':hashlib.sha256(old.encode()).hexdigest(),'after_sha256':hashlib.sha256(s.encode()).hexdigest(),'edits':edits}
 (H/(name+'.patch')).write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile=str(B/name),tofile=name)))
(H/'launch01.py').write_bytes((B/'launch01.py').read_bytes());(H/'INVERSE01.json').write_text(json.dumps(inv,indent=2)+'\n')
p=json.loads((F/'real-data-pilot-may30-ledger-continuation-handoff01-2026-10-06/PLAN_DRAFT01.json').read_text());p.update(schema_version=2,new_experiment_id='eth-paper-real-pilot-may30-ledger-continuation-20261006-01',relocation_receipt_input='ledger_relocation',relocation_review_input='ledger_relocation_review');(H/'PLAN_DRAFT01.json').write_text(json.dumps(p,indent=2)+'\n')
b=json.loads((B/'BINDINGS_DRAFT01.json').read_text());b.update(relocation_receipt=None,relocation_review=None);(H/'BINDINGS_DRAFT01.json').write_text(json.dumps(b,indent=2)+'\n')
s=json.loads((B/'STORAGE_TEMPLATE01.json').read_text());s.update(schema_version=2,data_store={'storage_budget':{'root':'/home/malecada/Data/onchain-pilot-retained-ledgers/eth-paper-real-pilot-graph-20220530-20261005-01','limits':{'max_logical_bytes':3256340480,'max_allocated_bytes':3256340480,'max_entries':2,'max_depth':1,'max_scan_seconds':5}},'device':66307,'disk_floor_bytes':10737418240,'free_reserve_bytes':67108864});(H/'STORAGE_TEMPLATE01.json').write_text(json.dumps(s,indent=2)+'\n')
