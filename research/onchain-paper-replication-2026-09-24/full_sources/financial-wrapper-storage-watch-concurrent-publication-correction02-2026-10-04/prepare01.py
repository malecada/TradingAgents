import ast,difflib,hashlib,json,os,stat
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent
A=B/'financial-wrapper-storage-watch-concurrent-publication-correction01-2026-10-04'
V=B/'financial-wrapper-storage-watch-concurrent-publication-review01-2026-10-04'
sha=lambda b:hashlib.sha256(b).hexdigest()
def put(n,v):(H/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
checks=[]
for root,pin in [(A,'ffbcc1efc6e56d1bf5b19830dd46a279e79f0a2b242e0e3a8ca182da421aaafb'),(V,'da3279ce476d772db5b5f1950cdd529bb673e2074b03e2c0a716b4dc0e569300')]:
 raw=(root/'MANIFEST01.json').read_bytes();assert sha(raw)==pin;m=json.loads(raw)
 for r in m['members']:
  p=root/r['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==r['mode']
  if r['kind']=='file':assert stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'] and sha(p.read_bytes())==r['sha256']
  elif r['kind']=='directory':assert stat.S_ISDIR(s.st_mode)
  elif r['kind']=='symlink':assert stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['target']
  else:raise AssertionError('unexpected original member type')
 checks.append({'root':str(root),'manifest_sha256':pin,'authenticated_declared_members':len(m['members']),'declared_excluded_execution_streams':m.get('excluded_execution_streams',[])})
old=(A/'workflow_storage.py').read_text();assert sha(old.encode())=='75cdf844080ec6d71e37ae81ce98f62e11beee19c81173fcd4f76ee1c1ac45d8'
a='''            try:primary.storage_cleanup_errors=(error,)
            except BaseException:pass
'''
b='''            try:
                # Use the builtin exception dictionary descriptor directly: no
                # overridden getattr/setattr/property or diagnostic callback.
                state=BaseException.__dict__['__dict__'].__get__(primary)
                previous=dict.get(state,'storage_cleanup_errors',())
                if type(previous) is not tuple:previous=(previous,)
                dict.__setitem__(state,'storage_cleanup_errors',previous+(error,))
            except BaseException as attachment_error:
                # Keep the original fatal even if evidence attachment fails.
                # The attachment error's context retains the current close error;
                # the previous tuple has not been overwritten before success.
                raise primary from attachment_error
'''
assert old.count(a)==1;new=old.replace(a,b);assert new.replace(b,a)==old
(H/'predecessor_workflow_storage.py').write_text(old);(H/'workflow_storage.py').write_text(new)
x=ast.parse(old);y=ast.parse(new)
x.body=[n for n in x.body if getattr(n,'name',None)!='_cleanup'];y.body=[n for n in y.body if getattr(n,'name',None)!='_cleanup']
assert ast.dump(x,include_attributes=False)==ast.dump(y,include_attributes=False)
put('INVERSE01.json',{'old_sha256':sha(old.encode()),'new_sha256':sha(new.encode()),'old_literal':a,'new_literal':b,'replacement_count':1,'full_byte_inverse':True,'all_other_ast_equal':True,'only_changed_function':'_cleanup'})
(H/'DELTA01.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='predecessor_workflow_storage.py',tofile='workflow_storage.py')))
for n in ('original_workflow_storage.py','DRAFT02_interleaved_rejoin.py','test05.py','test06.py','test07.py'):(H/n).write_bytes((A/n).read_bytes())
refs=[]
for root,names in [(A,['MANIFEST01.json','MACHINE01.json','REPORT01.md','MIGRATION_REQUIREMENTS01.json','SOURCE194_READBACK01.json']),(V,['MANIFEST01.json','MACHINE01.json','REPORT01.md','CLEANUP_PROBE01.json','cleanup_probe01.py','LATE_PROBE01.json'])]:
 for n in names:
  p=root/n
  if p.exists():
   raw=p.read_bytes();refs.append({'path':str(p),'bytes':len(raw),'sha256':sha(raw)})
put('ORIGINAL_READBACK01.json',{'scope_authentication':checks,'source_references':refs})
print(json.dumps({'status':'NARROW_SOURCE_PREPARATION','source_sha256':sha(new.encode()),'authenticated_members':sum(x['authenticated_declared_members'] for x in checks),'full_inverse':True},indent=2))
