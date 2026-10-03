import ast,hashlib,importlib.util,json,os,stat,sys,gzip,tarfile,copy
from pathlib import Path
from unittest.mock import patch
BASE=Path(__file__).resolve().parent;R=BASE/'red-witness';R.mkdir();A=BASE.parent/'held-consumer-final-recovery-preparation01-2026-10-03';H=lambda b:hashlib.sha256(b).hexdigest()
assert H((A/'MANIFEST01.json').read_bytes())=='0dd6e61973fa0b2773a656f41910893d49153188e230c21af71635320b78fa21'
assert H((A/'recovery01.py').read_bytes())=='37555604c4edbb884754d07b8216568ff3cdd2bdebbf3f9377f6a21860631d40'
rows=json.loads((A/'MANIFEST01.json').read_bytes())['members']
for row in rows:
 p=A/row['path'];assert p.is_file() and len(p.read_bytes())==row['bytes'] and H(p.read_bytes())==row['sha256']
assert sorted(row['path'] for row in rows)==sorted(str(p.relative_to(A)) for p in A.rglob('*') if p.is_file() and p.name!='MANIFEST01.json')
sys.path.insert(0,str(A));spec=importlib.util.spec_from_file_location('review_recovery01',A/'recovery01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assert Path(sys.modules['owned_io'].__file__).resolve()==A/'owned_io.py';assert Path(sys.modules['bounded_git01'].__file__).resolve()==A/'bounded_git01.py'
# Tiny opaque local roundtrip only, never actual capsule/history/runtime archive.
root=R/'tiny-source';root.mkdir(mode=0o750);(root/'empty').mkdir(mode=0o750);(root/'body').write_bytes(b'opaque-byte-fixture');os.chmod(root/'body',0o640)
manifest=m.scan(root);archive=R/'tiny.tar.gz';info=m.pack(root,manifest,archive);restored=R/'tiny-restored';m.restore(archive,info,manifest,restored);assert m.scan(restored)==manifest
assert manifest['root_mode']==stat.S_IMODE(root.stat().st_mode)
assert all(set(x)=={'path','kind','mode'} for x in manifest['members'] if x['kind']=='directory')
# HFR1: actual tar parser requests a huge PAX body before manifest limits.
# Header only, no huge data/array. Intercept before large decompression/allocation.
t=tarfile.TarInfo('extended');t.type=tarfile.XHDTYPE;t.size=64*1024**2;t.mode=0o600
compressed=gzip.compress(t.tobuf(format=tarfile.USTAR_FORMAT),mtime=0);bad=R/'pax-header-only.tar.gz';bad.write_bytes(compressed)
empty={'schema_version':1,'root_mode':0o700,'members':[]};badinfo={'bytes':len(compressed),'sha256':H(compressed),'manifest_sha256':H(m.encode(empty))};requested=[];original_read=gzip.GzipFile.read
class BoundedReadWitness(RuntimeError):pass
def guarded_read(self,size=-1):
 requested.append(size)
 if size>m.FILE:raise BoundedReadWitness('refused before large allocation')
 return original_read(self,size)
with patch.object(gzip.GzipFile,'read',guarded_read):
 try:m.restore(bad,badinfo,empty,R/'pax-partial')
 except BoundedReadWitness:pass
 else:raise AssertionError('large extended-header read was not observed')
assert max(requested)==64*1024**2,requested
print('REPRODUCED HFR1: compressed header',len(compressed),'bytes requests',max(requested),'decompressed bytes before entry validation; intercepted safely')
# HFR2: final directory chmod follows replacement symlink before scan refusal.
# Both source and replacement are owned tiny review fixtures; no original changed.
outside=R/'unrelated-owned-directory';outside.mkdir(mode=0o700);dest=R/'redirected-restore';before=stat.S_IMODE(outside.stat().st_mode);chmod=os.chmod;changed=[]
def redirect(path,mode,*args,**kwargs):
 p=Path(path)
 if p==dest/'empty' and not changed:
  p.rename(dest/'retained-original-empty');p.symlink_to(outside,target_is_directory=True);changed.append(str(p))
 return chmod(path,mode,*args,**kwargs)
with patch.object(m.os,'chmod',redirect):
 try:m.restore(archive,info,manifest,dest)
 except ValueError as e:after_error=str(e)
 else:raise AssertionError('later scan should reject redirection')
after=stat.S_IMODE(outside.stat().st_mode);assert before==0o700 and after==0o750,(before,after)
print('REPRODUCED HFR2: outside owned mode',oct(before),'→',oct(after),'before later refusal:',after_error)
# Shared descriptor cleanup control: real tiny read, firstfatal, both closes.
first=MemoryError('original read');close=os.close;seen=[]
def late(fd):seen.append(fd);close(fd);raise OSError('late close')
with patch.object(m.os,'read',side_effect=first),patch.object(m.os,'close',late):
 try:m.read(root,'body')
 except BaseException as e:assert e is first
 else:raise AssertionError('first fatal missing')
assert len(seen)==len(set(seen))==2
# Every scope remains local byte-only; no native/source execution or remote proof.
assert not any(n in sys.modules for n in ('numpy','torch','scipy'))
result={'decision':'WITHHELD_HFR1_HFR2','candidate_sha256':H((A/'recovery01.py').read_bytes()),'author_manifest_bodies':len(rows),'tiny_roundtrip':{'manifest':manifest,'archive':info,'actual_local_only':True},'HFR1':{'compressed_header_bytes':len(compressed),'requested_decompressed_bytes':requested,'intercepted_before_large_allocation':True},'HFR2':{'outside_mode_before':before,'outside_mode_after':after,'later_refusal':after_error,'only_reviewer_owned_directories':True},'real_read_firstfatal_two_closes':True,'actual_capsule_scan_archive_restore':False,'remote_origin_or_recovery_proved':False,'numerical_imports':False}
(R/'READBACK01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print('PASS manifest/tiny local roundtrip/realFDfirstfatal controls; WITHHELD two exact recovery counterexamples')
