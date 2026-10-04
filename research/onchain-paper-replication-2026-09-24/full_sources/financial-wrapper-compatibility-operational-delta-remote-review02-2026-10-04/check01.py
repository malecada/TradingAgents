"""Independent remote selection/source review, never main/entry/Git/network."""
from pathlib import Path
import ast,copy,gzip,hashlib,importlib.util,io,json,os,stat,sys,tarfile,time,traceback
D=Path(__file__).resolve().parent;B=D.parent;MAIN=B.parents[2];A=B/'financial-wrapper-compatibility-operational-delta-remote-successor02-2026-10-04';V=B/'financial-wrapper-operational-forensic-watch-review04-2026-10-04';H=lambda b:hashlib.sha256(b).hexdigest();rows=[]
def ck(n,v,**kw):
 assert v,n;rows.append(dict(name=n,**kw));(D/'CHECKS01.json').write_text(json.dumps(rows,indent=2)+'\n')
def refuse(n,fn):
 try:fn()
 except Exception as e:ck(n,True,refusal=type(e).__name__,reason=str(e))
 else:raise AssertionError(n)
for root,pin in [(A,'e461c94e5e39880a809454a32fe76e50fc13941524407a536a1f7b62f8ddcbd3'),(V,'7a94ef046588cb9a10a978d63865302e0b12a25e60db98190aea9927ecc59f47')]:
 raw=(root/'MANIFEST01.json').read_bytes();ck('exact manifest:'+root.name,H(raw)==pin);m=json.loads(raw)
 for r in m['members']:
  p=root/r['path'];s=p.lstat();valid=stat.S_IMODE(s.st_mode)==r['mode']
  if r['kind']=='file':valid=valid and stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'] and H(p.read_bytes())==r['sha256']
  elif r['kind']=='directory':valid=valid and stat.S_ISDIR(s.st_mode)
  elif r['kind']=='symlink':valid=valid and stat.S_ISLNK(s.st_mode) and os.readlink(p)==r['target']
  else:valid=False
  ck('authenticated '+root.name+':'+r['path'],valid)
wm=json.loads((V/'MACHINE01.json').read_bytes());ck('genuine different-author watcher acceptance',H((V/'MACHINE01.json').read_bytes())=='aed1248d003fbe19ccbd5f0f57b6801e6cf08713bb01d6d9fa56a145e172bb57' and wm['decision']=='ACCEPTED_NARROW_SOURCE_ONLY_FIXED_PUBLICATION_RETRY_SCHEDULE' and wm['watch_sha256']==H((D/'watch01.py').read_bytes())=='bdeacaadc053e615245b3e2175089842708719448ec7da970d981e5dc077ca18')
for n,p in [('WATCH_REVIEW_MACHINE01.json',V/'MACHINE01.json'),('WATCH_REVIEW_MANIFEST01.json',V/'MANIFEST01.json'),('WATCH_REVIEW_REPORT01.md',V/'REPORT01.md')]:ck('literal accepted review dependency:'+n,(D/n).read_bytes()==p.read_bytes())
original=(D/'ORIGINAL_recover01.py').read_text();source=(D/'recover01.py').read_text();inv=json.loads((D/'AUTHOR_SOURCE_INVERSE01.json').read_bytes());rebuilt=source
ck('exact four inverse records',len(inv['edits'])==4)
for e in reversed(inv['edits']):assert rebuilt.count(e['new'])==1;rebuilt=rebuilt.replace(e['new'],e['old'])
ck('full source literal inverse and genuine failed predecessor',rebuilt==original and H(original.encode())=='b08f6c2667d28d5415449807fd91dcb8bd898b784f981e209cfc042cca6ed290' and original.encode()==(B/'financial-wrapper-compatibility-operational-delta-root-remote02-2026-10-04/recover01.py').read_bytes())
ck('exact candidate and author machine',H(source.encode())=='ada3dafc7250452cb6db2eb33cdd5b5ecddb776511e247efcbc858dbb446aabf' and H((D/'AUTHOR_MACHINE01.json').read_bytes())=='2418253db51dddd3a895cd804b1881615a247f50de575f41f6a6ad5b3dcca8d4')
old=ast.parse(original);new=ast.parse(source);oldf={x.name:ast.dump(x) for x in old.body if isinstance(x,ast.FunctionDef)};newf={x.name:ast.dump(x) for x in new.body if isinstance(x,ast.FunctionDef)}
ck('exact changed functions',set(oldf)==set(newf) and sorted(k for k in oldf if oldf[k]!=newf[k])==['main','validate_fixed_selection'])
for name in set(oldf)-{'main','validate_fixed_selection'}:ck('unchanged function AST:'+name,oldf[name]==newf[name])
def rest(t):return ast.dump(ast.Module(body=[x for x in t.body if not (isinstance(x,ast.FunctionDef) and x.name in ('main','validate_fixed_selection')) and not (isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id=='REQUIRED' for y in x.targets))],type_ignores=[]))
ck('all other module AST exact',rest(old)==rest(new))
sys.path.insert(0,str(D));s=importlib.util.spec_from_file_location('independent_remote',D/'recover01.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
selected=[]
for name,pin in sorted(M.REQUIRED.items()):
 p=MAIN/name;st=p.lstat();body=p.read_bytes();ck('literal actual selected:'+name,stat.S_ISREG(st.st_mode) and st.st_nlink==1 and st.st_size==pin['bytes'] and H(body)==pin['sha256']);selected.append(dict(path=name,**pin,git_blob_sha1=hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()))
ck('exact15 total507946 original10subset',len(selected)==15 and sum(x['bytes'] for x in selected)==507946 and all(M.REQUIRED[n]==v for n,v in ast.literal_eval(next(x.value for x in old.body if isinstance(x,ast.Assign) and any(isinstance(z,ast.Name) and z.id=='REQUIRED' for z in x.targets))).items()))
unique=len({x['git_blob_sha1'] for x in selected});ck('concrete prospective denominator55 not53',unique==15 and 10+unique+2*len(selected)==55)
(D/'SELECTED_READBACK01.json').write_text(json.dumps({'rows':selected,'unique_git_blob_oids':unique,'prospective_expected_operations':55,'actual_root_selection':None,'actual_observed_operations':None},indent=2)+'\n')
q={'remote_commit':'0'*40,'rows':[{k:r[k] for k in ('path','bytes','sha256')} for r in selected]};M.validate_fixed_selection(q);ck('pure exact fixed selector',True)
for i in range(15):
 for field,value in [('bytes',True),('bytes',float(q['rows'][i]['bytes'])),('bytes',-1),('bytes',M.FILE+1),('sha256','0'*64),('path','research/foreign-'+str(i))]:
  z=copy.deepcopy(q);z['rows'][i][field]=value;refuse('selected mutation '+str(i)+':'+field+':'+repr(value),lambda z=z:M.validate_fixed_selection(z))
 z=copy.deepcopy(q);z['rows'].pop(i);refuse('each missing row '+str(i),lambda z=z:M.validate_fixed_selection(z))
for label,z in [('duplicate16',dict(q,rows=q['rows']+[q['rows'][0]])),('duplicate15',dict(q,rows=q['rows'][:-1]+[q['rows'][0]])),('extra field',dict(q,qualification='not authority')),('null',None),('missing remote_commit',{'rows':q['rows']})]:refuse(label,lambda z=z:M.validate_fixed_selection(z))
# Extract exact original guards rather than calling a live entry with synthetic receipts.
main=next(x for x in new.body if isinstance(x,ast.FunctionDef) and x.name=='main')
def guard(message):
 return next(x.args[0] for x in ast.walk(main) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='require' and len(x.args)>1 and isinstance(x.args[1],ast.Constant) and x.args[1].value==message)
def test_guard(label,node,env,want):ck(label,bool(eval(compile(ast.Expression(node),'<original pure guard>','eval'),dict(M.__dict__,**env)))==want)
for v in (None,False,1,'','A'*40,'0'*39,'0'*41,'g'*40,'0'*40):test_guard('commit guard:'+repr(v),guard('commit pin'),{'COMMIT':v},v=='0'*40)
test_guard('sorted names guard accepts exact',guard('selected unique sorted scope'),{'rows':q['rows']},True);test_guard('sorted names guard refuses reorder',guard('selected unique sorted scope'),{'rows':q['rows'][::-1]},False)
for n in (54,55,56):test_guard('operation count guard:'+str(n),guard('exact finite operation denominator'),{'CALLS':[None]*n,'wanted':list(range(15)),'rows':q['rows']},n==55)
ck('fixed fresh receiver and actual origin/selection guards',"repo = HERE / 'fresh-operational-source-policy02.git'" in source and all(guard(msg) is not None for msg in ['explicit frozen selection pin','frozen canonical selection','actual configured origin join','actual remote HEAD join','fresh Git namespace absent','fresh fetched commit join','actual remote selected body pins','actual Git blob OID','original-to-remote exact body join','final actual remote HEAD join']))
# Independently authenticate both actual captured scopes and canonical compressed archives.
for folder,manname,arcname,expected in [('financial-wrapper-compatibility-operational-delta-capture02-2026-10-04','PAYLOAD_MANIFEST01.json','operational-delta01.tar.gz',(41,33,943578)),('financial-wrapper-compatibility-operational-delta-failed-remote-capture02-2026-10-04','FAILED_PAYLOAD_MANIFEST01.json','failed-remote02.tar.gz',(42,31,114237))]:
 C=B/folder;c=json.loads((C/'CAPTURE01.json').read_bytes());m=json.loads((C/manname).read_bytes());snap=Path(c['snapshot']);ck('scope denominator:'+folder,(len(m['members']),sum(r['kind']=='file' for r in m['members']),sum(r.get('bytes',0) for r in m['members']))==expected and {str(p.relative_to(snap)) for p in snap.rglob('*')}=={r['path'] for r in m['members']});out=io.BytesIO()
 with gzip.GzipFile(filename='',mode='wb',fileobj=out,mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tar:
   for r in m['members']:
    p=snap/r['path'];st=p.lstat();info=tarfile.TarInfo(r['path']);info.mode=r['mode'];info.uid=info.gid=info.mtime=0;info.uname=info.gname='';ck('actual captured mode:'+folder+':'+r['path'],stat.S_IMODE(st.st_mode)==r['mode'])
    if r['kind']=='directory':assert stat.S_ISDIR(st.st_mode);info.type=tarfile.DIRTYPE;tar.addfile(info)
    else:
     body=p.read_bytes();ck('actual captured body:'+folder+':'+r['path'],stat.S_ISREG(st.st_mode) and st.st_nlink==1 and len(body)==r['bytes'] and H(body)==r['sha256']);info.size=len(body);tar.addfile(info,io.BytesIO(body))
 ck('full literal compressed archive:'+folder,out.getvalue()==(C/arcname).read_bytes() and H(out.getvalue())==c['archive']['sha256']);ck('capture not recovery:'+folder,c['actual_external_or_flat_receipt'] is None)
 if 'failed-remote' in folder:
  original_scope=json.loads((C/'ORIGINAL_FAILED_ROOT_SCOPE43.json').read_bytes());ck('root43 projected all42 exact',len(original_scope['members'])==43 and [{k:v for k,v in r.items() if k!='allocated_bytes'} for r in original_scope['members'] if r['path']!='.']==m['members']);root=Path(c['original_root']);f=json.loads((root/'FAILED01.json').read_bytes());ck('actual failed provenance nulls',H((root/'FAILED01.json').read_bytes())==c['actual_FAILED_sha256']=='7491cc3c1940b68cab9b218e972a13c925f5ce1ff21d9f0a2f32ee416246268a' and f['operations'][2]['exit'] is None and f['operations'][2]['actual_reaped_exit']==0 and c['Root_outer_exit']==1 and c['historical_changed_directory_path_or_field'] is None)
# Real bounded write/fatal cleanup without a Git child or entry.
owned=D/'owned01';owned.mkdir(mode=0o700);M.HERE=owned;M.START=time.monotonic();M.write(owned/'opaque',b'opaque\0\xff');ck('original real saved body', (owned/'opaque').read_bytes()==b'opaque\0\xff')
for i,P in enumerate((ValueError,MemoryError,SystemExit)):
 for j,S in enumerate((ValueError,MemoryError,SystemExit)):
  p=P('primary');s=S('secondary');path=owned/f'failure-{i}-{j}';origwrite=os.write;origclose=os.close;before=len(os.listdir('/proc/self/fd'));closed=[]
  def write(fd,b):raise p
  def close(fd):origclose(fd);closed.append(fd);raise s
  os.write=write;os.close=close
  try:
   try:M.write(path,b'opaque')
   except BaseException as e:
    expected=next((x for x in (p,s) if isinstance(x,MemoryError) or not isinstance(x,Exception)),p);ck(f'real write firstfatal {i}/{j}',e is expected,traceback=traceback.format_exc())
   else:raise AssertionError('fatal accepted')
  finally:os.write=origwrite;os.close=origclose
  ck(f'actual close/retained partial {i}/{j}',bool(closed) and path.is_file() and path.stat().st_size==0 and len(os.listdir('/proc/self/fd'))==before)
ck('no entry or Git child',M.CALLS==[] and M.COMMIT is None and not (D/'REMOTE_RECOVERY01.json').exists());ck('no numerical modules',not any(n in sys.modules for n in ('torch','numpy','pandas','scipy')))
print(json.dumps({'checks':len(rows),'no_main_entry_git_network':True,'prospective_operations_only':55}))
