"""Linux owned subreaper: live PID/start-time joins, finite TERM/KILL/reap."""
import ctypes,os,signal,time
from pathlib import Path
import recovery04 as R

def pin(pid):
 try:raw=Path('/proc',str(pid),'stat').read_bytes()
 except FileNotFoundError:return None
 R.require(len(raw)<=4096,'proc stat extent');tail=raw.rsplit(b')',1)[1].split()
 return {'pid':pid,'ppid':int(tail[1]),'pgrp':int(tail[2]),'session':int(tail[3]),'ticks':tail[19].decode(),'state':tail[0].decode()}
def snapshot():
 rows={};deadline=time.monotonic()+2
 with os.scandir('/proc') as it:
  for e in it:
   R.require(time.monotonic()<deadline and len(rows)<32768,'bounded proc census')
   if e.name.isdigit():
    row=pin(int(e.name))
    if row is not None:rows[row['pid']]=row
 return rows
class OwnedTree:
 def __init__(self):self.pid=os.getpid();self.known={};self.reaped=[];self.previous=None;self.lib=None
 def begin(self):
  rows=snapshot();R.require(not any(r['ppid']==self.pid for r in rows.values()),'cannot own pre-existing children')
  self.lib=ctypes.CDLL(None,use_errno=True);old=ctypes.c_int()
  R.require(self.lib.prctl(37,ctypes.byref(old),0,0,0)==0,'get subreaper');self.previous=old.value
  R.require(self.lib.prctl(36,1,0,0,0)==0,'set subreaper')
 def scan(self):
  rows=snapshot();selected={self.pid};changed=True
  while changed:
   changed=False
   for pid,row in rows.items():
    if row['ppid'] in selected and pid not in selected:selected.add(pid);changed=True
  selected.remove(self.pid)
  for pid in selected:
   row=rows[pid];old=self.known.get(pid)
   R.require(old is None or old['ticks']==row['ticks'],'owned PID reused during live census');self.known[pid]=row
  return {pid:rows[pid] for pid in selected}
 def signal(self,rows,number):
  for pid,row in rows.items():
   current=pin(pid)
   if current is None:continue
   R.require(current['ticks']==row['ticks'],'refuse foreign reused PID')
   try:os.kill(pid,number)
   except ProcessLookupError:pass
 def drain(self,process):
  # Root's dedicated supervisor owns no unrelated children. Subreaping covers
  # double-fork/setsid escape even after the original session leader exits.
  end=time.monotonic()+6;sent_term=False;term_at=None
  while True:
   live=self.scan()
   if live:
    if not sent_term:self.signal(live,signal.SIGTERM);sent_term=True;term_at=time.monotonic()
    elif time.monotonic()-term_at>=3:self.signal(live,signal.SIGKILL)
   if process is not None:process.poll()
   for candidate,row in self.scan().items():
    if row['ppid']!=self.pid or (process is not None and candidate==process.pid):continue
    try:pid,status=os.waitpid(candidate,os.WNOHANG)
    except ChildProcessError:continue
    if pid:self.reaped.append({'pid':pid,'wait_status':status})
   if not self.scan():break
   R.require(time.monotonic()<end,'owned descendants cleanup deadline');time.sleep(.02)
  if process is not None:process.wait(timeout=.1)
  remaining=[]
  for pid,row in self.known.items():
   current=pin(pid)
   if current is not None and current['ticks']==row['ticks']:remaining.append(pid)
  R.require(not remaining,'original owned PID identity remains')
  return {'owned_pid_start_records':list(self.known.values()),'reaped_descendants':self.reaped,'remaining_original_identities':remaining,'subreaper_used':True,'dedicated_no_preexisting_children':True}
 def close(self):
  if self.previous is not None:R.require(self.lib.prctl(36,self.previous,0,0,0)==0,'restore original subreaper state');self.previous=None
