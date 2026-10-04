import ast,dataclasses as D,difflib,hashlib,json,os,stat,sys
from pathlib import Path
H=Path(__file__).resolve().parent;F=H.parent;A=F/'financial-batch-output-codec-spool-integration-preparation02-2026-10-04';B=F/'financial-batch-output-codec-spool-integration-preparation01-2026-10-04';V=F/'financial-batch-output-codec-spool-integration-source-review01-2026-10-04';sys.path.insert(0,str(A));import router05 as R
sha=lambda b:hashlib.sha256(b).hexdigest();checks=0

def ok(v):
 global checks
 assert v;checks+=1
def refused(fn):
 try:fn()
 except (ValueError,TypeError):ok(True);return
 raise AssertionError('expected schema refusal')
def seal(root,n,pin,count):
 ok(sha((root/n).read_bytes())==pin);rows=json.loads((root/n).read_text())['members'];ok(len(rows)==count)
 ok(sorted(str(p.relative_to(root)) for p in root.rglob('*') if p!=root/n)==sorted(r['path'] for r in rows))
 for r in rows:
  p=root/r['path'];s=p.lstat();mode=r['mode'];mode=int(mode,8) if type(mode)is str else mode;ok(stat.S_IMODE(s.st_mode)==mode)
  if r['kind']=='file':b=p.read_bytes();ok(stat.S_ISREG(s.st_mode) and len(b)==r['bytes'] and sha(b)==r['sha256'])
  elif r['kind']=='directory':ok(stat.S_ISDIR(s.st_mode))
  else:ok(r['kind'] in ('symlink','lexical-symlink') and stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['target'])
seal(A,'MANIFEST01.json','54f093aad27ee39824e9e2f99f35f5c81789bbf3455f29929706538bd711186b',1710)
seal(B,'MANIFEST01.json','086bf7c37b795e339ab9937265ef81b353a36cc12ff132cf2fd69c4ce60666e6',3431)
seal(V,'MANIFEST01.json','1119810eb6035aa92a563258597bc26e05d1c0012a137fb2c8e9b8dc0cb1b491',1673)
a=json.loads((B/'AUTHENTICATION01.json').read_text())
for r in a['frozen_scopes']:seal(Path(r['root']),r['manifest'],r['sha256'],r['complete_typed_members'])
for r in a['unchanged_copies']:
 b=Path(r['source']).read_bytes();new=(A/r['name']).read_bytes();ok(b==new and sha(new)==r['sha256']);ok(ast.dump(ast.parse(b))==ast.dump(ast.parse(new)))
for r in a['authority_sources']:p=Path(r['path']);b=p.read_bytes();ok(p.resolve()==p and sha(b)==r['sha256'] and len(b)==r['bytes'])
old=(B/'router04.py').read_text();new=(A/'router05.py').read_text();inv=json.loads((A/'INVERSE01.json').read_text());back=new.splitlines(True)
for e in reversed(inv['reverse_line_edits']):back[e['start']:e['end']]=e['replace']
ok(''.join(back)==old);ok(ast.dump(ast.parse(''.join(back)))==ast.dump(ast.parse(old)))
ok(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='predecessor/router04.py',tofile='successor/router05.py'))==(A/'INVERSE01.diff').read_text())
# Existing real source fixture from the independent IR3 witness.
src=H/'source';d=R.C.parse(R.R.read(src,'start.json'))['descriptor'];tp=sha(R.R.read(src,'terminal.json'));i=R.inspect(src,'b'*64,d,tp);route=R.route((i,),4)
for field in ('target_key','root','descriptor','terminal_sha256','raw_sha256','logical_bytes','files','original_signatures','root_identity'):
 for value in (None,False,0.0,[],{}):refused(lambda field=field,value=value:R._inventory_schema(D.replace(i,**{field:value})))
for pos in range(3):
 for value in (False,float(i.root_identity[pos]),str(i.root_identity[pos])):
  x=list(i.root_identity);x[pos]=value;refused(lambda x=x:R._inventory_schema(D.replace(i,root_identity=tuple(x))))
for file in (i.files[0],i.files[1]):
 for field in ('ordinal','name','kind','size','sha256','mode','raw_offset','raw_size','raw_sha256'):
  for value in (None,False,0.0,[],{}):refused(lambda file=file,field=field,value=value:R._file_schema(D.replace(file,**{field:value})))
for pos in range(7):
 x=list(i.original_signatures[0][1]);x[pos]=float(x[pos]);sig=((i.original_signatures[0][0],tuple(x)),)+i.original_signatures[1:]
 refused(lambda sig=sig:R._inventory_schema(D.replace(i,original_signatures=sig)))
for field in ('target','index','start','files','plan'):
 for value in (None,False,0.0,[],{}):
  p=D.replace(route.partitions[0],**{field:value});bad=D.replace(route,partitions=(p,)+route.partitions[1:]);refused(lambda bad=bad:R._route_schema(bad))
for field in ('inventories','partitions','members_per_plan'):
 for value in (None,False,0.0,[],{}):refused(lambda field=field,value=value:R._route_schema(D.replace(route,**{field:value})))
ok(all(n not in sys.modules for n in ('numpy','torch','pandas','tradingagents.research.lifecycle')))
(H/'AUTHENTICATION03.json').write_text(json.dumps({'checks':checks,'all_exact_sources_and_reviews':8436,'whole_byte_AST_inverse':True,'all_six_utility_copies_equal':True,'schema_types_refuse':True,'no_scientific_imports':True},sort_keys=True,indent=2)+'\n');print(checks,'checks passed')
