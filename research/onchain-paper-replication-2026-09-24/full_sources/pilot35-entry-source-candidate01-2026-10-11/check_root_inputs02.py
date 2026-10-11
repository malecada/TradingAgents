"""Only authentic newly supplied Root-map seam; prior37 source checks reused."""
import ast,difflib,hashlib,json,os,resource
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10);resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2];E=F/'real-data-pilot-full35-entry-preparation01-2026-10-11';O=F/'real-data-pilot-full34-entry-preparation01-2026-10-11';refs={}
def ref(p):
 b=p.read_bytes();v={'path':str(p.relative_to(R)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};refs[v['path']]=v;return v
initial=(P/'INITIAL_SOURCE_BEFORE_ROOT_MAP01.py.txt').read_text();current=(P/'prepare_source01.py').read_text();old="    save(HERE/'CAPACITY_SOURCE_MAP01.json',mapping)"
new="    # The real Root map is already frozen; authenticate rather than republish.\n    map_path=HERE/'CAPACITY_SOURCE_MAP01.json'\n    assert ref(map_path)['sha256']=='713bfa99920959ce0807b2e3c987ad79a11aaa2fb39d767f39da5757210d37be'\n    actual_map=load(map_path)\n    assert actual_map['source_files']==pins and actual_map['source_anchor']==ANCHOR"
assert initial.replace(old,new)==current and ast.dump(ast.parse(current.replace(new,old)))==ast.dump(ast.parse(initial))
prior=json.loads((P/'SOURCE_CHECK01.json').read_bytes());assert len(prior['checks'])==37 and all(x['pass'] for x in prior['checks']) and ref(P/'INITIAL_SOURCE_BEFORE_ROOT_MAP01.py.txt')['sha256']==prior['references'][str((P/'prepare_source01.py').relative_to(R))]['sha256']
pins={'CAPACITY_SOURCE_MAP01.json':'713bfa99920959ce0807b2e3c987ad79a11aaa2fb39d767f39da5757210d37be','CAPACITY_DECLARATION_ROOT01.json':'ab58496b354cd4b0bd97fa514d715383fb578235f53e8462ad52940f4647b179'}
for n,h in pins.items():assert ref(E/n)['sha256']==h
mapping=json.loads((E/'CAPACITY_SOURCE_MAP01.json').read_bytes());capacity=json.loads((E/'CAPACITY_DECLARATION_ROOT01.json').read_bytes());assert len(mapping['source_files'])==423 and mapping['source_files']==capacity['source_body_pins'] and mapping['source_anchor']==capacity['source_anchor']=='53b8890630765d06f8a44e3e8fbaee1f4b00bdfb'
baseline=json.loads((O/'CAPACITY_DECLARATION_ROOT01.json').read_bytes())
for key in ('new_logical_growth_bytes','new_allocated_growth_bytes','non_directory_new_allocated_growth_bytes','new_entries','directory_allocated_bound_bytes','other_writer_reserved_bytes','allocation_semantics','directory_and_other_writers_included','runtime_residuals_included'):assert capacity[key]==baseline[key]
budget=F/'pilot35-cumulative-machine-review01-2026-10-11/EXTENSION106_REVIEW01.json';assert ref(budget)['sha256']=='606114a28d18d01843c0b27db95dcaaeb18357a78229fe50dce39c8ac3f70b9d';v=json.loads(budget.read_bytes());assert set(v)=={'schema_version','decision','extension_sha256','reviewer','scope'} and v['decision']=='accepted' and v['extension_sha256']=='e0a1e3f89926094373e6c58022627e5861cda03064657e88a245129756810b9a'
for n in ('prepare_source01.py','prepare_registration01.py','SOURCE_CHECK01.json'):ref(P/n)
forward=[];inverse=[]
for n in ('prepare_source01.py','prepare_registration01.py'):
 a=(O/n).read_text();b=(P/n).read_text();forward.extend(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='full34/'+n,tofile='candidate35/'+n));inverse.extend(difflib.unified_diff(b.splitlines(True),a.splitlines(True),fromfile='candidate35/'+n,tofile='full34/'+n))
for n,t in [('FORWARD02.patch',''.join(forward)),('INVERSE02.patch',''.join(inverse))]:
 with (P/n).open('x') as f:f.write(t)
with (P/'SOURCE_CHECK02.json').open('x') as f:json.dump({'status':'PASS_AUTHENTIC_ROOT_INPUT_SEAM_ONLY','prior37_source_checks_reused':True,'literal_and_AST_map_seam_inverse':True,'actual423_map_capacity_and106_refs_authenticated':True,'references':refs,'builders_executed':False,'limitations':['Actual Root declaration is conditional prospective metadata, not measured capacity or independent entry acceptance.','No builder, Git join, binder, admission, Owner, numerical import or claim executed.']},f,sort_keys=True,indent=2);f.write('\n')
print('PASS_ROOT_INPUT_SEAM_ONLY; prior37 reused; builders unexecuted')
