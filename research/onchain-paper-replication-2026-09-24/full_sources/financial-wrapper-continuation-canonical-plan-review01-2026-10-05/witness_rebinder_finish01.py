"""Single actual owned FD-close counterexample; no Root/public builder execution."""
from pathlib import Path
import importlib.util,json,os,sys
H=Path(__file__).resolve().parent;A=H.parent/'financial-wrapper-continuation-canonical-parent-preparation01-2026-10-05';sys.path.insert(0,str(A))
spec=importlib.util.spec_from_file_location('frozen_rebinder',A/'build01.py');B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)
owned=H/'rebinder-owned';owned.mkdir(mode=0o700)
first=owned/'first';last=owned/'last'
for path,raw in ((first,b'original-a'),(last,b'original-b')):
 with B.R.new_file(path) as fd:os.write(fd,raw);os.fsync(fd)
reader=B.Reads();reader.read(first);reader.read(last)
pin=B.R.sig(first.lstat());last_inode=last.lstat().st_ino;close=os.close;events=[]
def later_close(fd):
 st=os.fstat(fd);close(fd)
 if st.st_ino==last_inode and not events:
  writer=os.open(first,os.O_WRONLY|os.O_TRUNC)
  try:os.write(writer,b'modified-a');os.fsync(writer)
  finally:close(writer)
  os.utime(first,ns=(pin[5]+1000000,pin[5]+1000000));events.append({'actual_later_fd':fd,'actual_close_completed':True,'earlier_body_mutated':True})
os.close=later_close
try:reader.finish()
finally:os.close=close
actual=B.R.read(owned,'first');assert events and reader.cache[str(first)]==b'original-a' and actual==b'modified-a' and B.R.sig(first.lstat())!=pin
value={'schema_version':1,'decision':'REFUTED_REBINDER_INPUT_FINISH_CURRENTNESS','source_sha256':B.sha(B.R.read(A,'build01.py')),'actual_finish_returned_success':True,'cached_earlier_sha256':B.sha(reader.cache[str(first)]),'actual_earlier_sha256':B.sha(actual),'signature_changed':True,'events':events,'Root_public_builder_executed':False,'Root_target_created':False,'all_owned_descriptors_closed':True}
B.R.put(H/'WITNESS_REBINDER_FINISH01.json',value);print(json.dumps(value))
