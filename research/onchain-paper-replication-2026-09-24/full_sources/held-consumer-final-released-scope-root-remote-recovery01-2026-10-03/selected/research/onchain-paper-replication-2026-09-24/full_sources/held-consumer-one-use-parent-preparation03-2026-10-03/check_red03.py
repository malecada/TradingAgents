import ast,hashlib,importlib.util,json,os,stat,sys,types,copy
from pathlib import Path
from unittest.mock import patch
R=Path(__file__).resolve().parent/'red-witness';R.mkdir();A=R.parent.parent/'held-consumer-one-use-parent-preparation02-2026-10-03';B=R.parent.parent/'held-consumer-one-use-parent-preparation01-2026-10-03';H=lambda b:hashlib.sha256(b).hexdigest()
assert H((A/'MANIFEST02.json').read_bytes())=='94662e0ee749a6c7793043e2d527c118e722479568b36fd0b768a98983cd6500'
source=(A/'launch_success01.py').read_bytes();assert H(source)=='e952f679c50b1a5b0dfd32a15281fe9a2dec8f6b0650b5834369e8b197286fdd'
rows=json.loads((A/'MANIFEST02.json').read_bytes());rows=rows.get('members',rows.get('files'));names=[]
for row in rows:
 p=A/row['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==row['mode']
 if row['type']=='file':assert stat.S_ISREG(s.st_mode) and s.st_nlink==row['links'] and s.st_size==row['bytes'] and H(p.read_bytes())==row['sha256']
 elif row['type']=='directory':assert stat.S_ISDIR(s.st_mode)
 else:assert row['type']=='symlink' and stat.S_ISLNK(s.st_mode) and os.readlink(p)==row['target']
 names.append(row['path'])
actual=[]
for p,ds,fs in os.walk(A,followlinks=False):actual.extend(str((Path(p)/n).relative_to(A)) for n in ds+fs if str((Path(p)/n).relative_to(A))!='MANIFEST02.json')
assert sorted(names)==sorted(actual)
def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=load(A/'launch_success01.py','parent02');semantic=load(A/'held_outcome02.py','selected_semantic');assert H((A/'held_outcome02.py').read_bytes())==p.PARSER_SHA
oldtree=ast.parse((B/'launch_success01.py').read_bytes());tree=ast.parse(source);olddefs={n.name:n for n in oldtree.body if isinstance(n,ast.FunctionDef)};defs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
changed={'fatal','select','prepared','write','reap_controller','finish_check','launch'}
inverse=copy.deepcopy(tree);inverse.body=[n for n in inverse.body if not (isinstance(n,ast.FunctionDef) and n.name=='directory_identity') and not (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SELECTED_CLEANUP_TYPES' for t in n.targets))]
for i,n in enumerate(inverse.body):
 if isinstance(n,ast.FunctionDef) and n.name in changed:inverse.body[i]=copy.deepcopy(olddefs[n.name])
assert ast.dump(inverse)==ast.dump(oldtree)
# Exact final-posttail namespace AST, original pinned function, scalar-only record.
cap=p.CAP;raw=(cap/'fixture_tools/raw_receipts01.py').read_bytes();release=json.loads((A/'release-unreleased01.json').read_bytes());assert H(raw)==release['source_files']['fixture_tools/raw_receipts01.py']
root=R/'posttail';root.mkdir();s=root.stat();value={'disk_floor_bytes':10*p.GIB,'disk_free_bytes':11*p.GIB,'excludes_own_file':True,'remaining_final_file_allowance':65536,'observation':{'root':str(root),'root_device':s.st_dev,'root_inode':s.st_ino,'allocated_bytes':0,'logical_file_bytes':0,'entries':0}};body=b'qualified-metadata-only'
reader=types.SimpleNamespace(body=lambda name:body,json=lambda name:value)
assignment=next(n for n in defs['finish_check'].body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ns' for t in n.targets));env=dict(p.__dict__,reader=reader);exec(compile(ast.Module([assignment],[]),'<actual-parent-namespace>','exec'),env);ns=env['ns']
fn=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='authenticate_post_tail');exec(compile(ast.Module([fn],[]),'<actual-posttail>','exec'),ns)
post=ns['authenticate_post_tail'](root,'synthetic-only',{'disk_floor_bytes':10*p.GIB,'storage_budget':{'limits':{'max_allocated_bytes':100,'max_logical_bytes':100,'max_entries':10}}});assert post['sha256']==H(body)
# Unexpected wait firstfatal now still escalates and independently reaps.
first=MemoryError('wait first');calls=[]
class Process:
 pid=12345
 def poll(self):calls.append('poll');return None
 def wait(self,timeout):
  calls.append('wait'+str(timeout))
  if timeout==60:raise first
  return -9
with patch.object(p,'ticks',return_value='known'),patch.object(p.os,'killpg',side_effect=lambda pid,sig:calls.append('signal'+str(sig))):
 try:p.reap_controller(Process(),'known')
 except BaseException as e:assert e is first
 else:raise AssertionError('firstfatal missing')
assert calls==['poll','signal15','wait60','signal9','wait5']
# Authentic selected parser type binding statement then uncertainty→firstfatal.
bind=next(n for n in defs['prepared'].body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SELECTED_CLEANUP_TYPES' for t in n.targets));p.__dict__['semantic']=semantic;exec(compile(ast.Module([bind],[]),'<actual-selected-type-binding>','exec'),p.__dict__)
assert p.select(semantic.CleanupFailure('uncertain'),first) is first
# Actual receipt path refuses the original redirect witness with acquired anchor.
directory=R/'owned';directory.mkdir();pin=p.directory_identity(directory);foreign=R/'foreign';foreign.mkdir();directory.rename(R/'owned-retained');directory.symlink_to(foreign,target_is_directory=True)
try:p.write(directory,'receipt.json',{'x':1},pin)
except ValueError:pass
else:raise AssertionError('receipt redirect accepted')
assert not (foreign/'receipt.json').exists()
# Same-mode fresh-directory replacement also refuses.
same=R/'same';same.mkdir();samepin=p.directory_identity(same);same.rename(R/'same-retained');same.mkdir()
try:p.write(same,'receipt.json',{'x':1},samepin)
except ValueError:pass
else:raise AssertionError('new inode accepted')
# Actual good receipt fsync/three-independent-FDclose control.
good=R/'good';good.mkdir();goodpin=p.directory_identity(good);fsync=os.fsync;sync=[]
def recorded_fsync(fd):sync.append({'directory':stat.S_ISDIR(os.fstat(fd).st_mode),'inode':os.fstat(fd).st_ino});return fsync(fd)
with patch.object(p.os,'fsync',recorded_fsync):p.write(good,'complete.json',{'opaque':True},goodpin)
assert len(sync)==2 and [r['directory'] for r in sync]==[False,True]
close=os.close;closed=[];bodyfatal=MemoryError('write first')
def close_later(fd):closed.append(fd);close(fd);raise OSError('after close')
with patch.object(p.os,'write',side_effect=bodyfatal),patch.object(p.os,'close',close_later):
 try:p.write(good,'partial.json',{'x':1},goodpin)
 except BaseException as e:assert e is bodyfatal
 else:raise AssertionError('writefatal missing')
assert len(closed)==len(set(closed))==3
# HUP3 residual: actual unchanged log-open AST ignores directory_pin entirely.
logs=next(n for n in ast.walk(defs['launch']) if isinstance(n,ast.For) and isinstance(n.iter,ast.Tuple) and [x.value for x in n.iter.elts if isinstance(x,ast.Constant)]==['stdout.log','stderr.log'])
namespace={'os':os,'directory':directory,'fds':[]};exec(compile(ast.Module([logs],[]),'<actual-log-loop>','exec'),namespace)
for fd in namespace['fds']:os.close(fd)
assert (foreign/'stdout.log').exists() and (foreign/'stderr.log').exists()
# Reservation and immediate anchor acquisition make no parent fsync call.
reservation=R/'reservation-parent';reservation.mkdir();syncs=[]
with patch.object(p.os,'fsync',side_effect=lambda fd:syncs.append(fd)):
 reserved=reservation/'fixed-identity';reserved.mkdir(exist_ok=False);p.directory_identity(reserved)
assert syncs==[]
assert not any(n in sys.modules for n in ('numpy','torch','scipy'))
result={'decision':'WITHHELD_RESIDUAL_HUP3','candidate_sha256':H(source),'manifest_members':len(rows),'inverse_elsewhere_ast':True,'HUP1_corrected_actual_namespace':True,'HUP2_corrected_wait_calls':calls,'HUP4_corrected_actual_class_binding':True,'receipt_redirect_and_same_mode_replacement_refused':True,'receipt_fsyncs':sync,'write_firstfatal_closes_once':3,'residual_log_redirect_created':['foreign/stdout.log','foreign/stderr.log'],'reservation_parent_fsyncs':syncs,'actual_native_or_claim_or_positive_prepared':False,'numerical_imports':False}
(R/'READBACK02.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print('PASS HUP1/HUP2/HUP4 correction and receipt HUP3 controls; REPRODUCED HUP3 residual unanchored log writes and absent reservation-parent fsync')
