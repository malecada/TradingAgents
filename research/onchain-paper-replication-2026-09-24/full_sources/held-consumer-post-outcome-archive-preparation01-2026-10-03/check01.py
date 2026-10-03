"""Bounded stdlib opaque controls. Never read active capsule or Parent roots."""
import copy
import json
import os
from pathlib import Path
import post_outcome01 as P
R=P.R
HERE=Path(__file__).resolve().parent
checks=[]
def ok(name,condition):
    if not condition:raise AssertionError(name)
    checks.append(name)
def refuses(name,fn):
    try:fn()
    except (ValueError,FileExistsError,FileNotFoundError):checks.append(name);return
    raise AssertionError(name+' accepted')
def manifest(rows):return {'schema_version':1,'root_mode':448,'members':rows}
def body(name,raw):return {'path':name,'mode':384,'kind':'file','bytes':len(raw),'sha256':R.digest(raw)}
old=manifest([body('original',b'original opaque')])
now=manifest(old['members']+[body('terminal',b'unknown outcome opaque')])
ok('append-only subset accepts actual additional member',P.subset(old,now)['added_members']==1)
for field,value in [('sha256','0'*64),('bytes',99),('mode',420),('kind','directory')]:
    changed=copy.deepcopy(now);changed['members'][0][field]=value
    if field=='kind':changed['members'][0].pop('sha256');changed['members'][0].pop('bytes')
    refuses('changed original '+field,lambda:P.subset(old,changed))
refuses('original absent',lambda:P.subset(old,manifest([])))
changed=copy.deepcopy(now);changed['root_mode']=493
refuses('root mode change',lambda:P.subset(old,changed))
for n in ['../bad','/abs','a//b','.git/../x','keys/password','x.pem']:
    refuses('unsafe '+n,lambda n=n:R.validate(manifest([body(n,b'x')])) )
# No authority or native receipt is fabricated: these are labelled surrogate
# bytes used only against the pure evidence predicate, never the live API.
q={'current_manifest_sha256':{'capsule':'1'*64,'external':'2'*64},'evidence':{}}
bodies={'terminal':b'SYNTHETIC OPAQUE TERMINAL', 'cleanup':b'SYNTHETIC OPAQUE CLEANUP'}
review={'schema_version':1,'decision':'accepted-closed-tree-byte-preservation','identity':P.IDENTITY,'source':R.SOURCE,
        'baseline_sha256':P.BASELINE_SHA256,'current_manifest_sha256':q['current_manifest_sha256'],
        'terminal_sha256':R.digest(bodies['terminal']),'cleanup_sha256':R.digest(bodies['cleanup']),
        'processes_absent':True,'cgroup_absent':True,'writer_quiescence_verified':True,'outcome':'UNKNOWN'}
def bind(value):
    values=dict(bodies);values['closed_tree_review']=R.encode(value)
    spec=copy.deepcopy(q);spec['evidence']={n:{'path':'/synthetic-unused/'+n,'sha256':R.digest(b)} for n,b in values.items()}
    return spec,values
for state in ('COMPLETE','FAILED','UNAVAILABLE','UNKNOWN'):
    value=dict(review,outcome=state);spec,values=bind(value)
    ok('noncoerced outcome '+state,P.evidence(spec,values)['outcome']==state)
for k,v in [('processes_absent',False),('cgroup_absent',False),('writer_quiescence_verified',None),('processes_absent',1),('identity','other'),('source','0'*40),('decision','approved'),('baseline_sha256','0'*64),('terminal_sha256','0'*64),('cleanup_sha256','0'*64),('outcome','RUNNING'),('current_manifest_sha256',{})]:
    value=dict(review);value[k]=v;spec,values=bind(value)
    refuses('evidence rejects '+k+' '+str(v),lambda:P.evidence(spec,values))
spec,values=bind(review);values['terminal']+=b'corruption'
refuses('opaque terminal mismatch',lambda:P.evidence(spec,values))
# Actual tiny archive and flat restore, owned exclusively by this author scope.
root=HERE/'synthetic01';root.mkdir(mode=0o700)
src=root/'source';src.mkdir(mode=0o700)
(src/'original').write_bytes(b'original opaque')
os.chmod(src/'original',0o600)
m0=R.scan(src)
(src/'terminal').write_bytes(b'failed outcome retained\0\xff')
os.chmod(src/'terminal',0o600)
m1=R.scan(src)
try:R.same(src,m0)
except ValueError as exc:(root/'ORIGINAL_FULL_EQUALITY_RED01.txt').write_text(str(exc)+'\n');checks.append('original baseline full equality rejects appended terminal')
else:raise AssertionError('baseline unexpectedly unchanged')
ok('new subset allows unchanged original plus terminal',P.subset(m0,m1)['added_regular_files']==1)
archive=root/'current.tar.gz';info=R.pack(src,m1,archive)
flat=root/'flat';flat.mkdir(mode=0o700)
result=R.restore(archive,info,m1,flat,prefix='capsule')
ok('actual tiny full canonical restore',result['regular_bodies']==2 and result['members']==2 and result['instantiated_posix_tree'] is False)
meta=json.loads((flat/'capsule-metadata.json').read_bytes())
ok('new terminal bytes restored',R.read(flat,meta['flat_members']['terminal'])==b'failed outcome retained\0\xff')
refuses('flat namespace cannot be reused',lambda:R.restore(archive,info,m1,flat,prefix='capsule'))
(src/'original').write_bytes(b'changed')
refuses('pack detects original source mutation',lambda:R.pack(src,m1,root/'must-not-write.tar.gz'))
# Byte-exact inherited primitives, not a purported inverse of new wrapper logic.
original=HERE.parent/'held-consumer-final-recovery-preparation04-2026-10-03'
for n in ('recovery04.py','owned_io.py','bounded_git01.py'):
    ok('exact inherited '+n,(HERE/n).read_bytes()==(original/n).read_bytes())
ok('original helper fixed pin',R.digest((HERE/'recovery04.py').read_bytes())==P.HELPER_SHA256)
report={'profile':'stdlib-only opaque synthetic; no live roots or numerical imports','checks':checks,'count':len(checks),'new_wrapper_full_actual_capture_executed':False,'scientific_claim':False}
(HERE/'CHECKS01.json').write_bytes(R.encode(report))
print(json.dumps({'checks':len(checks),'status':'passed'}))
