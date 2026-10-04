import dataclasses, importlib.util, json, os, sys, time
from pathlib import Path
import spool04 as new
P=Path(__file__).resolve().parent
oldpath=P.with_name('financial-batch-output-transport-spool-preparation01-2026-10-04')/'spool02.py'
spec=importlib.util.spec_from_file_location('old_spool',oldpath);old=importlib.util.module_from_spec(spec);sys.modules[spec.name]=old;spec.loader.exec_module(old)
rows=[]
def make(M,label):
    parent=P/label;parent.mkdir(mode=0o700);root=parent/'root';root.mkdir(mode=0o700)
    p=M.Plan((M.Member(0,0,1,M.digest(b'x')),),1,0,0);a,b=p.required();p=dataclasses.replace(p,logical_reservation=a,allocated_reservation=b)
    return M.Spool(root,p),parent

def ack(M,s):return M.Ack(s.identity,0,0,1,M.digest(b'x'),'a'*64)
def run(M,label,attack,expected):
    s,parent=make(M,label);original=s.consumed
    send=lambda *args:ack(M,s);recover=lambda a:M.Recovery(a,b'x');cleanup=lambda:None
    if attack=='SP1':
        moved=parent.with_name(parent.name+'-moved');parent.rename(moved);parent.symlink_to(moved.name,target_is_directory=True)
    if attack=='SP2':send=lambda *args:dataclasses.replace(ack(M,s),page=False,chunk=False,size=True)
    if attack=='SP3':
        def cleanup():time.sleep(max(0,s.deadline-time.monotonic())+0.02)
        s.deadline=time.monotonic()+0.15
    error=None
    try:s.transfer(b'x',send,recover,cleanup)
    except BaseException as e:error=e
    accepted=error is None
    assert accepted==expected,(label,error)
    assert s.consumed==original
    if not accepted:
        assert s.failed and 'ELIGIBLE' not in s.states
        before=s.calls
        try:s.transfer(b'x',send,recover)
        except ValueError:pass
        else:raise AssertionError('failed retry accepted')
        assert s.calls==before
    rows.append({'case':label,'accepted':accepted,'exception':None if error is None else type(error).__name__,'message':None if error is None else str(error),'states':s.states,'failed':s.failed,'reservation_unchanged':s.consumed==original})
    s.close()
for issue in ('SP1','SP2','SP3'):
    run(old,'old-'+issue,issue,True);run(new,'new-'+issue,issue,False)

mutations={'page':[False,0.0,-1], 'chunk':[False,0.0,-1], 'size':[True,1.0,0], 'plan':[b'x',False,'f'*64], 'sha256':[b'x',False,'f'*64], 'receipt_sha256':[b'x',False,'g'*64]}
for field,values in mutations.items():
    for j,value in enumerate(values):
        label='strict-'+field+'-'+str(j);s,parent=make(new,label)
        bad=dataclasses.replace(ack(new,s),**{field:value})
        try:s.transfer(b'x',lambda *args:bad,lambda a:new.Recovery(a,b'x'))
        except ValueError:pass
        else:raise AssertionError(label)
        assert s.failed and s.states==('PENDING',)
        rows.append({'case':label,'refused':True});s.close()
s,parent=make(new,'nested-bool')
bad=dataclasses.replace(ack(new,s),page=False)
try:s.transfer(b'x',lambda *a:ack(new,s),lambda a:new.Recovery(bad,b'x'))
except ValueError:pass
else:raise AssertionError('nested boolean ack')
assert s.failed and s.states==('ACK',);s.close();rows.append({'case':'nested-bool','refused':True})
# Real cleanup mutations are sampled after cleanup, before eligibility.
s,parent=make(new,'cleanup-redirect')
def redirect():
    moved=parent.with_name(parent.name+'-moved');parent.rename(moved);parent.symlink_to(moved.name,target_is_directory=True)
try:s.transfer(b'x',lambda *a:ack(new,s),lambda a:new.Recovery(a,b'x'),redirect)
except OSError:pass
else:raise AssertionError('cleanup redirected root')
assert s.failed and s.states==('RECOVERED',);s.close();rows.append({'case':'cleanup-redirect','refused':True})
# A pre-existing fatal stays the selected object even after deadline + cleanup fatal.
s,parent=make(new,'fatal-overrun');fatal=MemoryError('original');later=SystemExit('cleanup')
def send(*a):raise fatal
def cleanup():
    time.sleep(max(0,s.deadline-time.monotonic())+0.01);raise later
s.deadline=time.monotonic()+0.05
try:s.transfer(b'x',send,None,cleanup)
except BaseException as e:assert e is fatal
else:raise AssertionError('lost original fatal')
assert s.failed;s.close();rows.append({'case':'fatal-overrun','first_fatal_preserved':True})
(P/'WITNESS01.json').write_text(json.dumps({'rows':rows,'count':len(rows),'actual_sleep_not_deadline_interruption':True},sort_keys=True,indent=2)+'\n')
print(len(rows),'witnesses passed')
