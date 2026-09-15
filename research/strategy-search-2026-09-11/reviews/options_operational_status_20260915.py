"""Read-only dedicated VPS status; no raw bodies, Greeks or financial evaluation.

Run by piping this source into the dedicated isolated Python over authenticated SSH.
Statuses are a bounded operational sample, not returned-source admission.
"""
import base64
from collections import Counter
from datetime import datetime, timezone
import json
import os
import stat
from pathlib import Path
import subprocess

base=Path('/opt/thesis-research/options-episode-20260911'); data=base/'data'
def read(path,cap):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        info=os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size>cap:
            raise ValueError('unsafe or oversized operational member')
        with os.fdopen(fd,'rb',closefd=False) as stream:body=stream.read(cap+1)
        if len(body)>cap:raise ValueError('growing operational member exceeds cap')
        return body
    finally:os.close(fd)
result={'checked_at':datetime.now(timezone.utc).isoformat(),'scope':'operational only; no scientific/source admission','data_root_exists':data.exists()}
proc=subprocess.run(['tmux','-L','thesis-options-20260915','list-panes','-t','options-episode-20260911','-F','#{pane_pid} #{pane_current_command} #{pane_dead}'],capture_output=True,text=True,timeout=5)
result['tmux']={'exit_code':proc.returncode,'stdout':proc.stdout[:1000],'stderr':proc.stderr[:1000]}
pids=[int(line.split()[0]) for line in proc.stdout.splitlines() if line.split() and line.split()[0].isdigit()]
processes=[]
while pids:
    pid=pids.pop()
    if len(processes)>=32:raise ValueError('process tree bound')
    try:
        p=Path('/proc')/str(pid)
        command=read(p/'cmdline',8192).replace(b'\0',b' ').decode(errors='replace')
        status=read(p/'status',65536).decode().splitlines()
        processes.append({'pid':pid,'command':command[:2000],'status':[s for s in status if s.startswith(('State:','PPid:','VmRSS:','Threads:'))]})
        pids.extend(map(int,read(p/'task'/str(pid)/'children',4096).decode().split()))
    except (FileNotFoundError,ProcessLookupError):pass
result['processes']=processes
log=base/'launch-options-20260915.log'
result['launch_log']=read(log,65536).decode(errors='replace') if log.exists() else None
journals={}
for name in ('bootstrap','known','selected','daily','final'):
    directory=data/name
    if not directory.exists():continue
    receipts=sorted(directory.glob('receipt-*.json'));sample=receipts[-32:]
    states=Counter();http=Counter();entries=[]
    for p in sample:
        row=json.loads(read(p,16*1024**2));meta=row.get('metadata',{})
        states[str(row.get('status'))]+=1;http[str(meta.get('http_status'))]+=1
        entries.append({'slot':row.get('slot'),'status':row.get('status'),'http_status':meta.get('http_status'),'body_complete':meta.get('body_complete'),'error':meta.get('error'),'body_bytes':row.get('body_bytes'),'clock_consistent':meta.get('clock_consistent'),'within_controller_deadline':meta.get('within_controller_deadline')})
    journals[name]={'receipt_count':len(receipts),'sample_count':len(sample),'sample_statuses':dict(states),'sample_http_statuses':dict(http),'sample':entries,'seal_exists':(directory/'seal.json').exists()}
result['journals']=journals
p=data/'selection.json'
if p.exists():
    row=json.loads(read(p,1024**2));result['selection_statuses']={k:{'status':v.get('status'),'reason':v.get('reason'),'scheduled_exit_ms':(v.get('selected') or {}).get('exit_ms')} for k,v in row['result'].items() if isinstance(v,dict)}
p=data/'source-seal.json'
if p.exists():
    row=json.loads(read(p,16*1024**2));result['source_seal']={k:row.get(k) for k in ('status','reason','quiescent_ms','intended_slot_count','unresolved_selected_slots')}
exits=[]
for p in sorted(data.glob('supervisor-exit-*.json')):
    row=json.loads(read(p,128*1024));row['stderr_text']=base64.b64decode(row.pop('stderr_base64')).decode(errors='replace');exits.append({'file':p.name,**row})
result['supervisor_exits']=exits
print(json.dumps(result,indent=2))
