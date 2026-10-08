import ast,hashlib,json,os,resource,stat,sys
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[3];A=P.parent/'xsect-posix-recovery01-2026-10-08/recover.py';V=R/'tradingagents/research/onchain_replication/preservation.py'
os.nice(10);allowed=os.sched_getaffinity(0);chosen=set(sorted(allowed)[:2]);os.sched_setaffinity(0,chosen);resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(40,40))
assert hashlib.sha256(A.read_bytes()).hexdigest()=='dcd7e1ca1e7017541ad3635bc229d7bd9d6326ad819bb6762958f9e6df008d3a'
ns={};exec(compile(V.read_bytes(),str(V),'exec'),ns);t=ast.parse(A.read_bytes());t.body=[n for n in t.body if not (isinstance(n,ast.ImportFrom) and n.module=='tradingagents.research.onchain_replication.preservation')];exec(compile(t,str(A),'exec'),ns)
source=P/'toy-original';source.mkdir();(source/'sub').mkdir();(source/'a').write_bytes(b'abc');(source/'sub/b').write_bytes(b'z'*1025)
rows=[];dirs=[]
for f in [source/'a',source/'sub/b']:
 os.chmod(f,0o640);os.utime(f,ns=(100000000000,100000000000));s=f.stat();rows.append({'relative_path':str(f.relative_to(source)),'source_path':str(f),'resolved_path':str(f),'kind':'regular','mode':s.st_mode,'mtime_ns':s.st_mtime_ns,'bytes':s.st_size,'logical_bytes':s.st_size,'nlink':1,'expected_sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
for f in [source,source/'sub']:
 os.chmod(f,0o750);os.utime(f,ns=(110000000000,110000000000));s=f.stat();dirs.append({'relative_path':str(f.relative_to(source)),'source_path':str(f),'kind':'directory','mode':s.st_mode,'mtime_ns':s.st_mtime_ns})
archive=P/'toy.tar';manifest=ns['build_bundle'](rows,archive,allowed_roots=[source]);target=P/'new-tree';kw=dict(original_root=source,max_files=2,max_total_bytes=1028,max_file_bytes=1025);pin=ns['create_new_tree'](target,rows,dirs,**kw);checks=[]
def refuse(label,fn):
 try:fn()
 except (ValueError,FileExistsError,NotADirectoryError,OSError) as e:checks.append({'case':label,'refused':type(e).__name__})
 else:raise AssertionError(label)
refuse('fresh_target_exclusive',lambda:ns['create_new_tree'](target,rows,dirs,**kw))
batch={'index':0,'start':0,'stop':2,'raw_bytes':1028}
def recover(m=manifest,rpin=pin):return ns['recover_bundle'](archive,m,rows,target,directories=dirs,root_pin=rpin,batch=batch,max_archive_bytes=20480,**kw)
refuse('wrong_root_identity',lambda:recover(rpin=(0,0)))
bad=dict(manifest,members=list(reversed(manifest['members'])));refuse('member_order_refused',lambda:recover(bad))
recover();checks.append({'case':'two_file_exact_recovery','accepted':True});refuse('overwrite_refused',recover)
def verify(restore=False):return ns['verify_new_tree'](target,rows,dirs,root_pin=pin,restore_directories=restore,**kw)
(target/'extra').symlink_to(target/'a');refuse('unexpected_symlink',verify);(target/'extra').unlink()
os.link(target/'a',target/'extra');refuse('hardlink',verify);(target/'extra').unlink()
(target/'sub/b').write_bytes(b'x'*1025);os.chmod(target/'sub/b',0o640);os.utime(target/'sub/b',ns=(100000000000,100000000000));refuse('same_extent_wrong_content',verify)
(target/'sub/b').write_bytes(b'z'*1025);os.chmod(target/'sub/b',0o640);os.utime(target/'sub/b',ns=(100000000000,100000000000))
verify(True);final=verify(False);checks.append({'case':'final_hash_and_directory_modes_mtimes_including_root','result':final})
refuse('traversal',lambda:ns['_relative']('../escape'))
redirect=P/'redirect';redirect.symlink_to(target,target_is_directory=True);refuse('root_symlink',lambda:ns['_open_root'](redirect,source))
assert not any(n in sys.modules for n in ['numpy','torch','scipy']);out={'decision':'accepted_source_only','checks':checks,'actual_affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'candidate_sha256':hashlib.sha256(A.read_bytes()).hexdigest(),'unchanged_verifier_sha256':hashlib.sha256(V.read_bytes()).hexdigest(),'qualification':'Two synthetic files only; no real-store access, transport, authority or execution admission.'};(P/'CHECK01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
