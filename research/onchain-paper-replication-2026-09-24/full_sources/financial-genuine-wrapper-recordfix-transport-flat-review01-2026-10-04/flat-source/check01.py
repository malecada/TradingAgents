import copy,json,sys
from pathlib import Path
import restore01 as M
R=M.R;H=Path(__file__).resolve().parent;checks=[]
def ok(n,v):assert v,n;checks.append(n)
def refuse(n,fn):
 try:fn()
 except (ValueError,KeyError,TypeError,FileExistsError):ok(n,True)
 else:raise AssertionError(n)
q=json.loads((H/'REQUEST_TEMPLATE01.json').read_text());refuse('unknown actual remote/release refused',lambda:M.validate_request(q))
# Only read frozen metadata; no actual source archive is restored here.
b=H.parent/'financial-genuine-wrapper-root-recordfix-capture01-2026-10-04';bodies={n:(b/n).read_bytes() for n in M.EXPECTED}
for n,pin in M.EXPECTED.items():ok('actual body pin '+n,len(bodies[n])==pin['bytes'] and R.digest(bodies[n])==pin['sha256'])
m,a,t=M.joins(bodies);ok('actual capture metadata joins',len(m['members'])==986 and len(a['git_entries'])==325)
for name,field,value in [('terminal.json','source','0'*40),('terminal.json','status','FAILED'),('terminal.json','error_type','OSError'),('terminal.json','runtime_bodies',True),('terminal.json','observed_free_bytes',[0]*4),('source-authentication.json','tracked',324),('source-authentication.json','selected',323),('source-authentication.json','runtime_record_metadata_count',250),('source-authentication.json','changed',[]),('ACTUAL_TERMINAL02.json','actual_exit',1),('ACTUAL_TERMINAL02.json','native_or_numerical_claim_started',True)]:
 z=dict(bodies);v=json.loads(z[name]);v[field]=value;z[name]=R.encode(v);refuse('join refusal '+name+field,lambda:M.joins(z))
for name,pin in M.PINS.items():ok('unchanged R4 '+name,R.digest((H/name).read_bytes())==pin)
d=H/'owned01';d.mkdir();src=d/'source';src.mkdir();(src/'dir').mkdir();(src/'dir/a').write_bytes(b'opaque');(src/'b').write_bytes(b'byte');tiny=R.scan(src);info=R.pack(src,tiny,d/'tiny.tar.gz');flat=d/'flat';flat.mkdir(mode=0o700);r=R.restore(d/'tiny.tar.gz',info,tiny,flat);ok('actual tiny canonical archive/flat pipeline',r['regular_bodies']==2 and r['members']==3 and not r['instantiated_posix_tree']);refuse('flat one-use',lambda:R.restore(d/'tiny.tar.gz',info,tiny,flat))
wrong=dict(info,sha256='0'*64);refuse('corrupt archive binding',lambda:R.restore(d/'tiny.tar.gz',wrong,tiny,flat))
primary=KeyboardInterrupt('first fatal');calls=[]
def failed():calls.append('failure');raise OSError('secondary')
def later():calls.append('later')
try:R._cleanup((failed,later),primary=primary)
except BaseException as e:ok('first fatal retained',e is primary)
ok('all cleanup attempted',calls==['failure','later']);ok('no numerical imports',all(n not in sys.modules for n in ['numpy','torch','pandas','scipy']))
(H/'CHECKS01.json').write_bytes(R.encode({'count':len(checks),'checks':checks,'actual_source_restores':0,'network':0,'native':0}));print('PASS',len(checks))
