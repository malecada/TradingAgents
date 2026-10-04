import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('prepared_evidence',HERE/'check_evidence01.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=[]
def ok(test,name):
    if not test: raise AssertionError(name)
    checks.append(name)
def refuses(call,name):
    try: call()
    except (ValueError,TypeError): checks.append(name);return
    raise AssertionError('accepted '+name)
config={'remote':{'path':None,'sha256':None},'flat':{'path':None,'sha256':None},'terminal':{'path':None,'sha256':None},'root_output':None,'actual_commit':None}
refuses(lambda:m.verify(config),'unbound actual receipts refuse before actual IO')
(HERE/'REQUEST_TEMPLATE01.json').write_text(json.dumps(config,sort_keys=True,indent=2)+'\n')
root=HERE/'opaque01';root.mkdir(mode=0o700)
(root/'empty').mkdir(mode=0o700)
name='opaque-'+('x'*110)+'.body';body=b'finite opaque engineering bytes\x00\xff'
(root/name).write_bytes(body)
manifest=m.census(root)
encoded=m.canonical(manifest,lambda p:m.read(root/p))
with tarfile.open(fileobj=io.BytesIO(encoded),mode='r:gz') as archive:
    rows=archive.getmembers();ok([r.name for r in rows]==[r['path'] for r in manifest['members']],'full ordinary tiny archive membership')
    ok(archive.extractfile(name).read()==body,'opaque PAX body full bytes')
ok(encoded==m.canonical(manifest,lambda p:m.read(root/p)),'deterministic canonical footer and compression')
refuses(lambda:m.canonical(manifest,lambda p:body+b'x'),'changed body refusal')
for mutation in ('duplicate','order','traversal','extent','hash','mode','missing_parent'):
    bad=json.loads(json.dumps(manifest))
    if mutation=='duplicate':bad['members'].append(dict(bad['members'][0]))
    if mutation=='order':bad['members'].reverse()
    if mutation=='traversal':bad['members'][1]['path']='../body'
    if mutation=='extent':bad['members'][1]['bytes']=m.FILE+1
    if mutation=='hash':bad['members'][1]['sha256']=None
    if mutation=='mode':bad['members'][1]['mode']=None
    if mutation=='missing_parent':bad['members'][1]['path']='absent/file'
    refuses(lambda b=bad:m.validate(b),'manifest '+mutation+' refusal')
(root/'redirect').symlink_to(name)
refuses(lambda:m.read(root/'redirect'),'real lexical link read refused')
refuses(lambda:m.census(root),'scope link refused')
# No future receipt is fabricated. This compares existing immutable metadata only.
q=json.loads(m.read(m.CAP/'contract-snapshot/REQUEST_RELEASED01.json'))
c=json.loads(m.read(m.CAP/'CAPTURE01.json'))
raw=(json.dumps({k:v for k,v in q.items() if k!='final_review'},sort_keys=True,indent=2)+'\n').encode()
ok(m.sha(raw)==c['contract_sha256'],'actual immutable contract encode convention')
ok(m.sha(m.read(m.CAP/'CAPTURE01.json'))==m.CAP_SHA,'existing actual capture source pin')
print(json.dumps({'status':'PREPARATION_CONTROLS_ONLY','tests':len(checks),'checks':checks,'actual_remote_or_flat_verification_executed':False,'acceptance':None},indent=2))
