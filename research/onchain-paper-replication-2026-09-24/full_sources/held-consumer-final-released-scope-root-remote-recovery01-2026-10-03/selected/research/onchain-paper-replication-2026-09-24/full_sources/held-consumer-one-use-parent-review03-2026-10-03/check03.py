import ast,copy,hashlib,importlib.util,json,os,stat,sys
from pathlib import Path
from unittest.mock import patch
R=Path(__file__).resolve().parent;A=R.parent/'held-consumer-one-use-parent-preparation03-2026-10-03';B=R.parent/'held-consumer-one-use-parent-preparation02-2026-10-03';H=lambda b:hashlib.sha256(b).hexdigest()
assert H((A/'MANIFEST03.json').read_bytes())=='28cffe50f86395f6e5145db28a87a383a27a7b0f3c577ed6735faf9f1ecacc00'
source=(A/'launch_success01.py').read_bytes();assert H(source)=='7a197e2f57db3fff44fce453356d187f62dce5f119125e6814831eb6008f38dc'
m=json.loads((A/'MANIFEST03.json').read_bytes());rows=m.get('members',m.get('files'));names=[]
for row in rows:
 p=A/row['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==row['mode']
 if row['type']=='file':assert stat.S_ISREG(s.st_mode) and s.st_nlink==row['links'] and s.st_size==row['bytes'] and H(p.read_bytes())==row['sha256']
 elif row['type']=='directory':assert stat.S_ISDIR(s.st_mode)
 else:assert row['type']=='symlink' and stat.S_ISLNK(s.st_mode) and os.readlink(p)==row['target']
 names.append(row['path'])
actual=[]
for p,ds,fs in os.walk(A,followlinks=False):actual.extend(str((Path(p)/n).relative_to(A)) for n in ds+fs if str((Path(p)/n).relative_to(A))!='MANIFEST03.json')
assert sorted(actual)==sorted(names)
def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);p=importlib.util.module_from_spec(s);s.loader.exec_module(p);return p
p=load(A/'launch_success01.py','parent03');semantic=load(A/'held_outcome02.py','semantic03');assert H((A/'held_outcome02.py').read_bytes())==p.PARSER_SHA
old=ast.parse((B/'launch_success01.py').read_bytes());tree=ast.parse(source);olddefs={n.name:n for n in old.body if isinstance(n,ast.FunctionDef)};defs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
inverse=copy.deepcopy(tree);inverse.body=[n for n in inverse.body if not(isinstance(n,ast.FunctionDef) and n.name in ('open_log','log_join'))]
for i,n in enumerate(inverse.body):
 if isinstance(n,ast.FunctionDef) and n.name in ('directory_identity','launch'):inverse.body[i]=copy.deepcopy(olddefs[n.name])
assert ast.dump(inverse)==ast.dump(old)
# Actual acquired current scope fsyncs parent entries BEFORE process release.
container=R/'parent';container.mkdir();attempt=container/'attempt';attempt.mkdir();syncs=[];fsync=os.fsync
def watched_sync(fd):s=os.fstat(fd);syncs.append((s.st_dev,s.st_ino));return fsync(fd)
with patch.object(p.os,'fsync',watched_sync):
 p.directory_identity(attempt);directory=attempt/'fixed';directory.mkdir();pin=p.directory_identity(directory)
expected=[(x.stat().st_dev,x.stat().st_ino) for x in (attempt,container,directory,attempt)];assert syncs==expected
# Exact original log-loop witness now refuses a replaced parent before writing.
foreign=R/'foreign';foreign.mkdir();directory.rename(attempt/'retained');directory.symlink_to(foreign,target_is_directory=True)
loop=next(n for n in ast.walk(defs['launch']) if isinstance(n,ast.For) and isinstance(n.iter,ast.Tuple) and [x.value for x in n.iter.elts if isinstance(x,ast.Constant)]==['stdout.log','stderr.log'])
ns={'directory':directory,'directory_pin':pin,'fds':[],'open_log':p.open_log}
try:exec(compile(ast.Module([loop],[]),'<actual-log-loop>','exec'),ns)
except ValueError:pass
else:raise AssertionError('redirected log accepted')
assert not list(foreign.iterdir()) and ns['fds']==[]
# Same-mode inode replacement before open also refuses.
same=R/'same';same.mkdir();samepin=p.directory_identity(same);same.rename(R/'same-retained');same.mkdir()
try:p.open_log(same,'stdout.log',samepin)
except ValueError:pass
else:raise AssertionError('same-mode new directory accepted')
# Returned log FD is live, supports actual writes and stable final path join.
good=R/'good';good.mkdir();gp=p.directory_identity(good);fd=p.open_log(good,'stdout.log',gp)
try:
 os.write(fd,b'opaque');ok=p.log_join(good,'stdout.log',fd,gp,final=True);assert ok['bytes']==6
 (good/'stdout.log').rename(good/'retained-stdout');(good/'stdout.log').write_bytes(b'foreign')
 os.write(fd,b'-more');assert (good/'stdout.log').read_bytes()==b'foreign' and (good/'retained-stdout').read_bytes()==b'opaque-more'
 try:p.log_join(good,'stdout.log',fd,gp,final=True)
 except ValueError:pass
 else:raise AssertionError('replacement log accepted')
finally:os.close(fd)
# All3 acquired log FDs close exactly once after firstfatal init failure.
partial=R/'partial';partial.mkdir();pp=p.directory_identity(partial);first=MemoryError('fsync first');close=os.close;closes=[]
def later(fd):closes.append(fd);close(fd);raise OSError('after actual close')
with patch.object(p.os,'fsync',side_effect=first),patch.object(p.os,'close',later):
 try:p.open_log(partial,'stdout.log',pp)
 except BaseException as e:assert e is first
 else:raise AssertionError('firstfatal absent')
assert len(closes)==len(set(closes))==3
# Both reservation-acquisition descriptors close after firstfatal fsync.
acq=R/'acquisition';acq.mkdir();closed=[]
def late_acq(fd):closed.append(fd);close(fd);raise OSError('late acquisition close')
with patch.object(p.os,'fsync',side_effect=first),patch.object(p.os,'close',late_acq):
 try:p.directory_identity(acq)
 except BaseException as e:assert e is first
 else:raise AssertionError('acquisition failure missing')
assert len(closed)==len(set(closed))==2
# Actual source/Git/current inputs readback only; no admission or outcome.
release=json.loads((A/'release-unreleased01.json').read_bytes());reader=semantic.Reader(p.CAP);reg=semantic.sources(reader,release);exp=reg['experiments'][p.IDENTITY];inputs={k:H(semantic.input_body(reader,exp,k)) for k in sorted(exp['inputs'])};reader.recheck();assert len(inputs)==33 and len(exp['outputs'])==6
assert not any(n in sys.modules for n in ('numpy','torch','scipy'))
result={'decision':'accepted_source_only','candidate_sha256':H(source),'author_manifest_members':len(rows),'inverse_other_ast':True,'reservation_fsync_device_inode_order':syncs,'redirect_and_same_mode_replacement_refused':True,'actual_log_join':ok,'returned_fd_stays_original_after_path_replacement':True,'firstfatal_log_closes_once':3,'firstfatal_acquisition_closes_once':2,'current_committed_bodies':205,'opaque_input_hashes':inputs,'outputs':exp['outputs'],'actual_positive_prepared_native_claim_outcome':False}
(R/'READBACK03.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print('PASS complete manifest/inverse AST; exact residualHUP3 witnesses now refuse;4parent/directory fsyncs;live returnedFD/final joins;3+2 firstfatal closeonce;actual205Git/33opaqueinputs/six outputs. SOURCE ONLY.')
