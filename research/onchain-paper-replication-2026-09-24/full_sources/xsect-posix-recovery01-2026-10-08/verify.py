import copy,hashlib,importlib.util,json,os,resource,stat,sys
from pathlib import Path
assert resource.getrlimit(resource.RLIMIT_AS)==(268435456,268435456)
assert resource.getrlimit(resource.RLIMIT_FSIZE)==(4194304,4194304)
assert len(os.sched_getaffinity(0))==2 and os.getpriority(os.PRIO_PROCESS,0)==10
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P.parents[3]))
from tradingagents.research.onchain_replication import preservation
spec=importlib.util.spec_from_file_location('synthetic_recovery',P/'recover.py');R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
base=P/'fixture01';base.mkdir();original=base/'original';original.mkdir();(original/'nested').mkdir()
for name,raw in [('a.bin',b'abc'),('nested/b.bin',b'opaque\x00\xffbytes'),('nested/empty.bin',b'')]:
 path=original/name;path.write_bytes(raw);os.chmod(path,0o640);os.utime(path,ns=(1700000000000000000,1700000000000000000))
for path in [original/'nested',original]:os.chmod(path,0o750);os.utime(path,ns=(1690000000000000000,1690000000000000000))
rows=[];dirs=[]
for name in ['.','nested','a.bin','nested/b.bin','nested/empty.bin']:
 path=original if name=='.' else original/name;s=path.stat();isdir=path.is_dir()
 row={'kind':'directory' if isdir else 'regular','relative_path':name,'source_path':str(path),'mode':s.st_mode,'posix_mode':format(stat.S_IMODE(s.st_mode),'04o'),'mtime_ns':s.st_mtime_ns,'logical_bytes':s.st_size,'nlink':s.st_nlink}
 if not isdir:row.update(resolved_path=str(path),bytes=s.st_size,expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
 (dirs if isdir else rows).append(row)
limits=dict(original_root=str(original),max_files=8,max_total_bytes=1024,max_file_bytes=512)
archive=base/'bundle.tar';manifest=preservation.build_bundle(rows,archive,allowed_roots=[original],start_index=0)
preservation.verify_bundle(archive,manifest)
target=base/'restored';pin=R.create_new_tree(target,rows,dirs,**limits)
verify_calls=[];real_verify=R.verify_bundle
R.verify_bundle=lambda *args:(verify_calls.append(1),real_verify(*args))[1]
receipt=R.recover_bundle(archive,manifest,rows,target,directories=dirs,root_pin=pin,batch={'index':0,'start':0,'stop':3,'raw_bytes':sum(r['bytes'] for r in rows)},max_archive_bytes=65536,**limits)
assert len(verify_calls)==1
whole=R.verify_new_tree(target,rows,dirs,root_pin=pin,restore_directories=True,**limits)
again=R.verify_new_tree(target,rows,dirs,root_pin=pin,**limits);assert whole['files']==again['files']==3
refusals=[]
def refuses(name,fn):
 try:fn()
 except (ValueError,OSError,EOFError) as error:refusals.append({'name':name,'type':type(error).__name__})
 else:raise AssertionError(name+' accepted')
kwargs=dict(directories=dirs,root_pin=pin,batch={'index':0,'start':0,'stop':3,'raw_bytes':sum(r['bytes'] for r in rows)},max_archive_bytes=65536,**limits)
refuses('overwrite-recovery',lambda:R.recover_bundle(archive,manifest,rows,target,**kwargs))
refuses('existing-root',lambda:R.create_new_tree(target,rows,dirs,**limits))
for bad in ['../escape','/absolute','nested/../escape','nested//bad','nested/./bad','bad\\name','']:
 badrows=copy.deepcopy(rows);badrows[0]['relative_path']=bad
 refuses('path-'+repr(bad),lambda b=badrows:R.create_new_tree(base/'bad-target',b,dirs,**limits))
refuses('original-overlap',lambda:R.create_new_tree(original/'child',rows,dirs,**limits))
symlink_root=base/'symlink-root';symlink_root.symlink_to(target,target_is_directory=True)
refuses('symlink-root',lambda:R.create_new_tree(symlink_root,rows,dirs,**limits))
fresh=base/'symlink-file';freshpin=R.create_new_tree(fresh,rows,dirs,**limits);(fresh/'a.bin').symlink_to(base/'outside')
refuses('symlink-file',lambda:R.recover_bundle(archive,manifest,rows,fresh,**{**kwargs,'root_pin':freshpin}))
assert not (base/'outside').exists()
refuses('symlink-file-final',lambda:R.verify_new_tree(fresh,rows,dirs,root_pin=freshpin,restore_directories=True,**limits))
wrong=copy.deepcopy(manifest);wrong['members'][0]['mtime_ns']=float(wrong['members'][0]['mtime_ns'])
refuses('typed-metadata-mismatch',lambda:R.recover_bundle(archive,wrong,rows,target,**kwargs))
wrong=copy.deepcopy(manifest);wrong['members'][0]['member']='files/00000001'
refuses('member-order',lambda:R.recover_bundle(archive,wrong,rows,target,**kwargs))
wrong=copy.deepcopy(manifest);wrong['members']=wrong['members'][:-1]
refuses('missing-member',lambda:R.recover_bundle(archive,wrong,rows,target,**kwargs))
short=base/'short.tar';short.write_bytes(archive.read_bytes()[:513]);shortmanifest=copy.deepcopy(manifest);shortmanifest.update(archive_bytes=513,archive_sha256=hashlib.sha256(short.read_bytes()).hexdigest())
import tarfile
try:R.recover_bundle(short,shortmanifest,rows,target,**kwargs)
except (ValueError,OSError,EOFError,tarfile.ReadError) as error:refusals.append({'name':'short-member-bytes','type':type(error).__name__})
else:raise AssertionError('short accepted')
refuses('bound-file',lambda:R.create_new_tree(base/'bound-target',rows,dirs,**{**limits,'max_file_bytes':1}))
refuses('wrong-pin',lambda:R.verify_new_tree(target,rows,dirs,root_pin=(0,0),**limits))
(target/'extra').mkdir();refuses('extra-directory',lambda:R.verify_new_tree(target,rows,dirs,root_pin=pin,**limits))
# Two independent bundles retain original numeric indices; final directories only after both.
multi=base/'multibatch';multipin=R.create_new_tree(multi,rows,dirs,**limits)
for index,(start,stop) in enumerate([(0,1),(1,3)]):
 path=base/f'batch{index}.tar';part=preservation.build_bundle(rows[start:stop],path,allowed_roots=[original],start_index=start)
 R.recover_bundle(path,part,rows,multi,**{**kwargs,'root_pin':multipin,'batch':{'index':index,'start':start,'stop':stop,'raw_bytes':sum(r['bytes'] for r in rows[start:stop])}})
R.verify_new_tree(multi,rows,dirs,root_pin=multipin,restore_directories=True,**limits)
# Reconstructed hardlink topology is refused, never credited as an independent file.
hard=base/'hardlink-target';hardpin=R.create_new_tree(hard,rows,dirs,**limits);os.link(multi/'a.bin',hard/'a.bin')
refuses('hardlink-final',lambda:R.verify_new_tree(hard,rows,dirs,root_pin=hardpin,restore_directories=True,**limits))
assert not any(n in sys.modules for n in ['numpy','scipy','torch'])
result={'status':'PASS','verified_files':3,'directories_including_root':2,'refusals':refusals,'multibatch_original_indices':True,'real_preservation_verifier_calls':len(verify_calls),'affinity':sorted(os.sched_getaffinity(0)),'nice':os.getpriority(os.PRIO_PROCESS,0),'rlimit_as':resource.getrlimit(resource.RLIMIT_AS),'rlimit_fsize':resource.getrlimit(resource.RLIMIT_FSIZE),'numerical_imports':False,'actual_originals_read':False}
(P/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
