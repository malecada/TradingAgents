import ast,hashlib,json,pathlib,shutil,subprocess,sys,time,types
from unittest.mock import patch
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[3]
C=HERE.parent/'batch-output-selected-transfer-preparation01-2026-10-03'
def sha(b):return hashlib.sha256(b).hexdigest()
def pinned(path,row):
 b=path.read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256'],str(path);return b
m=json.loads((C/'MANIFEST01.json').read_bytes())
assert sha((C/'MANIFEST01.json').read_bytes())=='fb02c157dd994430b2688d5eef7450b99663a3d88c1fa38840a50407740bf203'
for r in m['files']:pinned(C/r['path'],r)
for r in json.loads((C/'DEPENDENCIES01.json').read_bytes())['references']:pinned(ROOT/r['path'],r)
i=json.loads((C/'PROSPECTIVE_SOURCE_INVENTORY01.json').read_bytes())
rows=i['source_inventory'];assert len(rows)==201 and len({r['target'] for r in rows})==201
for r in rows:pinned(ROOT/r['origin'],r)
assert sum(r['bytes'] for r in rows)==3408803
assert sum(r['target'].startswith('tradingagents/') and r['target'].endswith('.py') for r in rows)==150
f=json.loads((C/'FINAL_CHECKS02.json').read_bytes())
for r in f['checks']:assert sha((C/r['log']).read_bytes())==r['sha256'] and r['exit_code']==0
# Execute unchanged author corpus only in a fresh review-owned replica.
w=HERE/'owned-source-replica';w.mkdir();rep=w/C.name;rep.mkdir()
for name in ['selected_non_tail_transport.py','archive_non_tail.py','archive_non_tail.baseline03.txt','test_transport01.py','test_controls01.py','test_roundtrip01.py','test_selection01.py']:shutil.copyfile(C/name,rep/name)
d=w/'batch-output-exact-member-reader-candidate02-2026-10-03';d.mkdir();shutil.copyfile(HERE.parent/d.name/'owned_io.py',d/'owned_io.py')
for name in ['test_selection01.py','test_transport01.py','test_controls01.py','test_roundtrip01.py']:
 p=subprocess.run([sys.executable,'-B',str(rep/name)],capture_output=True,timeout=30)
 (HERE/(name+'.review.log')).write_bytes(p.stdout+p.stderr);assert p.returncode==0,name
sys.path.insert(0,str(rep));import test_transport01 as t
s=object.__new__(t.Session);s.root=HERE/'synthetic-command';s.root.mkdir();s.deadline=time.monotonic()+20;s.check=lambda:None
s.p=dict(connection=dict(host='fixture.invalid',user='fixture',port=23,identity_file='/not-opened/key',known_hosts_file='/not-opened/known'),stderr_bytes=64,cleanup_seconds=1,max_commands=2,max_parts=2,max_rounded_bytes=1000000,max_channel_bytes=1000000)
s.op=types.SimpleNamespace(ledger=types.SimpleNamespace(identity='a'*64));s.pending_files={};records={}
s.c=types.SimpleNamespace(_transfer_active=None,_transfer_spent=dict(commands=0,parts=0,rounded_bytes=0,channel_bound=0),_transfer_observed=t.new_observed(),publish=lambda n,v:records.update({n:v}))
original=MemoryError('synthetic original pump fatal')
def pump(session,cmd,data,expected,out,err,observed):
 observed.update(commands_started=1,stdin_bytes=3,stdout_bytes=2,stderr_bytes=1,command_argument_bytes_started=7)
 session.process_evidence={'pid':None,'direct_child_reaped':False,'returncode':None,'qualification':'synthetic injection, no child'}
 raise original
with patch.dict(t.ns,_pump=pump):
 try:s._command('upload','safe',b'abc',3)
 except BaseException as e:assert e is original
 else:raise AssertionError('fatal suppressed')
assert s.c._transfer_spent['commands']==1 and s.c._transfer_spent['parts']==1
assert records['transfer-result-00000001.json']['observed']==s.c._transfer_observed
assert records['transfer-result-00000001.json']['status']=='failed' and s.c._transfer_active is None
# Successful pipe-operation observations remain accumulated even when their durable result cannot publish.
def publish(name,value):
 if name.startswith('transfer-result'):raise OSError('synthetic result publication failure')
 records[name]=value
s.c.publish=publish
with patch.dict(t.ns,_pump=pump):
 try:s._command('upload','safe',b'abc',3)
 except BaseException as e:assert e is original
 else:raise AssertionError('fatal replaced')
assert s.c._transfer_spent['commands']==2 and s.c._transfer_observed['stdin_bytes']==6
assert 'transfer-reservation-00000002.json' in records and 'transfer-result-00000002.json' not in records
try:s._reserve('mkdir',1,0,0)
except ValueError:pass
else:raise AssertionError('spent attempts refunded')
# Boundary arithmetic independently reconstructs reservation coverage, including EOF/overrun probes.
for tx in [0,1,32767,32768,65536,1048576]:
 for rx in [0,1,32767,32768,65536,1048576]:
  for dg in [1,64,16384]:
   for control in [1,32768,32769]:
    actual=tx+(rx+1)+(dg+1)+control
    assert t.ns['charge'](tx,rx,dg,control)>=actual
result={'status':'passed source-only','candidate_manifest_sha256':sha((C/'MANIFEST01.json').read_bytes()),'manifest_files':len(m['files']),'manifest_bytes':sum(r['bytes'] for r in m['files']),'source_count':len(rows),'package_count':150,'source_bytes':sum(r['bytes'] for r in rows),'author_checks':31,'independent_bound_combinations':324,'actual_network':False,'actual_authority':False,'notes':['Every referenced source body rehashed; no future Git source assumed.','Synthetic actual _command test retains first fatal across result publication failure, all spent attempts, and observed successful pipe operations.','No subprocess/pipe boundary stands in for a genuine admitted Context.']}
(HERE/'READBACK01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
