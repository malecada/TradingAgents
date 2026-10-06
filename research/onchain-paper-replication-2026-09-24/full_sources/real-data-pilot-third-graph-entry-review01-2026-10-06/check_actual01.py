from pathlib import Path
import ast,copy,hashlib,json,shutil
R=Path.cwd();F=R/'research/onchain-paper-replication-2026-09-24/full_sources';P=F/'real-data-pilot-third-graph01-2026-10-06';O=Path(__file__).parent;C=F/'real-data-pilot-third-graph-entry-candidate01-2026-10-06'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
g=json.loads((P/'gate01.json').read_bytes());name='eth-paper-real-pilot-graph-20220516-20261005-01';e=g['experiments'][name]
assert h(P/'gate01.json')=='3194ea0da02941e0615915a895264717c465331df274438be9a373f9cb2777e6'
assert len(g['experiments'])==1 and e['parent'] is None and e['cells']==['source-000000','graph-2022-05-16']
assert len(e['source_files'])==178 and len(e['inputs'])==35
for n in ('prepare01.py','preflight01.py','launch01.py','CHARTER01.md'):assert (P/n).read_bytes()==(C/n).read_bytes()
for n,v in e['source_files'].items():assert h(R/n)==v,n
for role,info in e['inputs'].items():
 p=R/info['path'];assert p.stat().st_size<4*1024**2 and h(p)==info['sha256'],role
old=json.loads((F/'real-data-pilot-second-graph01-2026-10-06/gate01.json').read_bytes());oe=next(iter(old['experiments'].values()))
assert e['cumulative_budget_extension']==oe['cumulative_budget_extension'] and e['runtime_hashes']==oe['runtime_hashes']
j=json.loads((P/'execution-job01.json').read_bytes());oj=json.loads((F/'real-data-pilot-second-graph01-2026-10-06/execution-job01.json').read_bytes())
a=copy.deepcopy(j);b=copy.deepcopy(oj);a['resources'].pop('storage_budget');b['resources'].pop('storage_budget');assert a==b and j['kind']=='graphs'
extent=json.loads((P/'RAW_EXTENT01.json').read_bytes());count=0
assert extent['declared_rows']==7794344 and extent['segments']==232 and len(extent['daily_members'])==7
for day in extent['daily_members']:
 assert h(R/day['mapping_path'])==day['mapping_sha256']
 for s in day['segments']:
  p=Path(s['path']);st=p.lstat();assert p.is_file() and not p.is_symlink()
  assert (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)==tuple(s[k] for k in ('device','inode','bytes','mtime_ns','ctime_ns'));count+=1
source=ast.parse((P/'preflight01.py').read_text());fn=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='preceding_storage');ns={'Path':Path,'ROOT':R,'json':json,'file_hash':h};exec(compile(ast.Module(body=[fn],type_ignores=[]),'<actual source preceding_storage>','exec'),ns)
joined=ns['preceding_storage'](e['inputs']);bad=copy.deepcopy(e['inputs']);bad['storage_closure_review']['sha256']='0'*64
try:ns['preceding_storage'](bad)
except ValueError:pass
else:raise AssertionError('corrupt union input accepted')
for p in (R/'research_runs'/name,R/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/name,R/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/name,P/'launch-attempt01.json',P/'outer-exit01.json'):assert not p.exists() and not p.is_symlink(),p
policy=json.loads((P/'STORAGE_POLICY01.json').read_bytes());projection=json.loads((P/'STORAGE_PROJECTION01.json').read_bytes());assert policy['startup_free_requirement_bytes']==18339489630==projection['prospective_startup_free_bytes'];assert policy['free_disk_observed_bytes']==19398299648
out={'gate_sha256':h(P/'gate01.json'),'source_pins':178,'input_pins':35,'raw_stats':count,'raw_body_reads':0,'rows':7794344,'preceding_storage':joined,'corrupt_union_pin_refused':True,'fixed_namespace_unused':True,'native_limits_unchanged':True,'runtime_map_unchanged':True,'startup_free_requirement_bytes':18339489630,'current_free_bytes':shutil.disk_usage(R).free,'launch_fresh_preflight_required':True}
(O/'ACTUAL_CHECK01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
