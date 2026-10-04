import ast,difflib,hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent
A=B/'financial-wrapper-storage-watch-concurrent-publication-correction02-2026-10-04';V=B/'financial-wrapper-storage-watch-concurrent-publication-review02-2026-10-04'
sha=lambda b:hashlib.sha256(b).hexdigest()
def put(n,x):(H/n).write_text(json.dumps(x,sort_keys=True,indent=2)+'\n')
refs=[]
for root,pin in ((A,'7010c22de559e838a7815260caf612f3ebcb9fad3a2bfa3a39509c63b5ce413b'),(V,'04fd1b3a58e88a7a45f215afffdd9952f0240abc7ed32c018727fd5b4bbded72')):
 raw=(root/'MANIFEST01.json').read_bytes();assert sha(raw)==pin;m=json.loads(raw)
 for r in m['members']:
  p=root/r['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==r['mode']
  if r['kind']=='file':assert stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'] and sha(p.read_bytes())==r['sha256']
  elif r['kind']=='directory':assert stat.S_ISDIR(s.st_mode)
  elif r['kind']=='symlink':assert stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['target']
  else:raise AssertionError(r['kind'])
 refs.append({'root':str(root),'manifest_sha256':pin,'declared_members_authenticated':len(m['members']),'declared_exclusions':m.get('excluded_execution_streams',[])})
old=(A/'workflow_storage.py').read_text();assert sha(old.encode())=='21e21dddc5b5008c3dc016839fc5b05c60dfbd345d224e91b8a9c3fb551c62cf'
changes=[];new=old
for indent in ('            ','                '):
 original=indent+"prior=getattr(error.__cause__ or error.__context__,'observation',{})"
 successor=indent+"# The body/cleanup already selected this fatal. Do not read\n"+indent+"# overridable cause/context/observation diagnostics first.\n"+indent+"if not isinstance(error,Exception) or isinstance(error,MemoryError):raise\n"+original
 assert new.count(original)==1;new=new.replace(original,successor);changes.append({'old':original,'new':successor})
rebuilt=new
for row in reversed(changes):assert rebuilt.count(row['new'])==1;rebuilt=rebuilt.replace(row['new'],row['old'])
assert rebuilt==old
x=ast.parse(old);y=ast.parse(new)
for tree in (x,y):
 w=next(n for n in tree.body if getattr(n,'name',None)=='StorageWatch');w.body=[n for n in w.body if getattr(n,'name',None) not in ('check','_check')]
assert ast.dump(x,include_attributes=False)==ast.dump(y,include_attributes=False)
(H/'original02_workflow_storage.py').write_text(old);(H/'workflow_storage.py').write_text(new)
put('INVERSE01.json',{'original_sha256':sha(old.encode()),'successor_sha256':sha(new.encode()),'literal_changes':changes,'full_literal_inverse':True,'all_other_ast_equal':True,'only_changed_methods':['StorageWatch.check','StorageWatch._check'],'cleanup_source_unchanged':True})
(H/'DELTA01.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='original02_workflow_storage.py',tofile='workflow_storage.py')))
for n in ('original_workflow_storage.py','predecessor_workflow_storage.py','DRAFT02_interleaved_rejoin.py','test05.py','test06.py','test07.py','nested_controls01.py','no_primary_controls02.py'):(H/n).write_bytes((A/n).read_bytes())
for n in ('REPORT01.md','MACHINE01.json','DIAGNOSTIC_BOUNDARY01.json','diagnostic_boundary01.py','HARNESS_CORRECTION01.json'):
 raw=(V/n).read_bytes();(H/('REVIEW02_'+n)).write_bytes(raw)
put('AUTHENTICATION01.json',{'original_scopes':refs,'actual_capsule_or_claim_bodies_read':False})
print(json.dumps({'source_sha256':sha(new.encode()),'authenticated_members':sum(r['declared_members_authenticated'] for r in refs),'full_inverse':True},indent=2))
