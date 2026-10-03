import importlib.util,json,os,stat,sys
from pathlib import Path
from unittest.mock import patch
O=Path(__file__).resolve().parent;P=O.parent/'held-consumer-final-recovery-preparation02-2026-10-03';sys.path.insert(0,str(P));s=importlib.util.spec_from_file_location('candidate',P/'recovery01.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
W=O/'birth-fixture';W.mkdir();src=W/'source';src.mkdir();(src/'empty').mkdir(mode=0o750);manifest=m.scan(src);archive=W/'tiny.gz';info=m.pack(src,manifest,archive)
dest=W/'restore';outside=W/'unrelated-original';outside.mkdir(mode=0o700);old_ino=outside.stat().st_ino;real=os.mkdir;events=[]
def swap(path,mode=0o777,*,dir_fd=None):
 result=real(path,mode,dir_fd=dir_fd)
 if str(path)=='empty' and dir_fd is not None and not events:
  target=dest/'empty';target.rename(W/'original-created-empty');outside.rename(target);events.append('created inode retained; separate preexisting inode moved into created path before first birth stat')
 return result
with patch.object(m.os,'mkdir',swap):result=m.restore(archive,info,manifest,dest)
after=dest/'empty';receipt={'result':result,'events':events,'preexisting_inode':old_ino,'accepted_inode':after.stat().st_ino,'preexisting_mode':0o700,'accepted_mode':stat.S_IMODE(after.stat().st_mode),'created_inode_retained':(W/'original-created-empty').stat().st_ino,'scope':'tiny reviewer-owned directories only'}
assert receipt['preexisting_inode']==receipt['accepted_inode'] and receipt['accepted_mode']==0o750
(O/'BIRTH_RACE01.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
