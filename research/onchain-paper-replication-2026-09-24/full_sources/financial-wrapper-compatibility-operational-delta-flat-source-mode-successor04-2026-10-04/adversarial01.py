from pathlib import Path
import importlib.util,sys,json,hashlib,copy,types,stat,os,time,traceback
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));s=importlib.util.spec_from_file_location('mode_adversarial',D/'restore01.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M);I=D.parent/'financial-wrapper-compatibility-operational-delta-root-remote03-2026-10-04';H=lambda b:hashlib.sha256(b).hexdigest();remote=json.loads((I/'REMOTE_RECOVERY01.json').read_bytes());selection=json.loads((I/'SELECTED_BODIES01.json').read_bytes());pin=H((I/'SELECTED_BODIES01.json').read_bytes());rows=[]
def ck(n,v,**kw):
 assert v,n;rows.append(dict(name=n,**kw));(D/'ADVERSARIAL01.json').write_text(json.dumps(rows,indent=2)+'\n')
def no(n,fn):
 try:fn()
 except (ValueError,OSError,KeyError,TypeError) as e:ck(n,True,refused=type(e).__name__,reason=str(e))
 else:raise AssertionError(n)
root=D/'adversarial-owned01';root.mkdir(mode=0o700)
no('wrong actual receiver cannot use profile',lambda:M.authenticate_selected(root,remote,selection,pin))
no('wrong selection hash',lambda:M.authenticate_selected(I,remote,selection,'0'*64))
for field,val in [('selected_count',14),('status','other'),('fresh_git_root',str(root/'wrong.git')),('genuine_run_or_native_started',True)]:
 altered=copy.deepcopy(remote);altered[field]=val;no('wrong literal actual remote:'+field,lambda altered=altered:M.authenticate_selected(I,altered,selection,pin))
q=copy.deepcopy(selection);q['rows'][0]['sha256']='0'*64;no('wrong literal selection body',lambda:M.authenticate_selected(I,remote,q,pin))
# Adversarial read substitution only: actual profile/receipt/original bytes never change.
profile_name='COMPLETED_REMOTE03_READ_ONLY_SELECTED_MODE_PROFILE01.json';profile=json.loads((D/profile_name).read_bytes())
for field,val in [('actual_receiver_root',str(root)),('expected_owner_uid',1001),('actual_remote_receipt_sha256','0'*64),('selection_sha256','0'*64),('raw_directory_mode_history_preserved',False),('status','invented')]:
 altered=copy.deepcopy(profile);altered[field]=val;c=M.VerifiedCohort();real=c.read
 def read(p,n,limit=M.R.FILE):
  b=real(p,n,limit);return M.R.encode(altered) if n==profile_name else b
 c.read=read;no('changed profile pinned bytes:'+field,lambda c=c:M.authenticate_selected(I,remote,selection,pin,c))
for n in ['COMPLETED_REMOTE_REVIEW_MACHINE01.json','COMPLETED_REMOTE_REVIEW_MANIFEST01.json','ROOT_REMOTE03_EXIT01.json']:
 c=M.VerifiedCohort();real=c.read
 def read(p,name,limit=M.R.FILE):
  b=real(p,name,limit);return b+b' ' if name==n else b
 c.read=read;no('changed authentic supporting body:'+n,lambda c=c:M.authenticate_selected(I,remote,selection,pin,c))
# Bind only authentic bytes, then sample deliberately bad metadata without changing the original tree.
c=M.VerifiedCohort();M.authenticate_selected(I,remote,selection,pin,c);real_lstat=Path.lstat;selected=I/'selected';file=selected/next(iter(M.REQUIRED));directory=selected/'research'
for kind,path,field,val in [('root-mode',selected,'st_mode',stat.S_IFDIR|0o700),('directory-mode',directory,'st_mode',stat.S_IFDIR|0o777),('file-mode',file,'st_mode',stat.S_IFREG|0o644),('owner',file,'st_uid',1001),('directory-owner',directory,'st_uid',1001),('hardlink',file,'st_nlink',2),('file-type',file,'st_mode',stat.S_IFLNK|0o777),('device',file,'st_dev',file.stat().st_dev+1),('size',file,'st_size',file.stat().st_size+1),('mtime',file,'st_mtime_ns',file.stat().st_mtime_ns+1)]:
 def changed(p,*a,**k):
  st=real_lstat(p,*a,**k)
  if p==path:
   attrs={n:getattr(st,n) for n in dir(st) if n.startswith('st_')};attrs[field]=val;return types.SimpleNamespace(**attrs)
  return st
 Path.lstat=changed
 try:no('observed original metadata drift:'+kind,c.check)
 finally:Path.lstat=real_lstat
c.check();ck('genuine input restores clean observation after synthetic metadata controls',True)
# Additional names cannot be adopted after binding, even when an exact profile exists.
no('changed tree expected population',lambda:c.tree(selected,set(M.REQUIRED)-{next(iter(M.REQUIRED))}))
no('unexpected profile directory lookup',lambda:c.input_directory_mode(selected/'unselected-directory'))
# A read-only profile cannot relax any real owned output graph.
for mode in (0o775,0o755,0o777):
 out=root/('output-'+str(mode));out.mkdir(mode=mode);out.chmod(mode);no('private output root stays0700:'+str(mode),lambda out=out:c.tree(out,set()))
for kind in ('bad-file-mode','symlink','hardlink','foreign','bad-child-mode'):
 out=root/kind;out.mkdir(mode=0o700);p=out/'opaque';p.write_bytes(b'opaque');p.chmod(0o600);expected={'opaque'}
 if kind=='bad-file-mode':p.chmod(0o644)
 elif kind=='symlink':p.unlink();p.symlink_to(file)
 elif kind=='hardlink':os.link(p,out/'extra')
 elif kind=='foreign':(out/'extra').write_bytes(b'foreign')
 else:(out/'child').mkdir(mode=0o775);(out/'child').chmod(0o775)
 no('real private output regression:'+kind,lambda out=out,expected=expected:c.tree(out,expected))
# Keep each finite control isolated after intentional pinning of negative fixtures.
for kind in ('deadline','member-ceiling'):
 x=M.VerifiedCohort()
 if kind=='deadline':x.deadline=time.monotonic()-1
 else:x.pins={str(i):() for i in range(32769)}
 no('original finite cohort:'+kind,x.tick)
ck('fixed primitive and watcher limits',M.R.FILE==4194304 and M.LOGICAL==67108864 and M.ALLOCATION==100663296 and M.W.POLICY=={'logical':67108864,'allocated':100663296,'file':4194304,'members':32768,'depth':32,'samples':8192,'sample_seconds':5,'floor':10737418240})
ck('no public Root restoration outcomes',not (I/'FLAT_INTENT01.json').exists() and not (I/'FLAT_RECOVERY01.json').exists() and not (I/M.OUTPUT).exists() and not (I/M.FAILED_OUTPUT).exists())
print(json.dumps({'rows':len(rows),'actual_original_inputs_modified':False,'public_run_or_entry':False}))
