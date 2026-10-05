"""Candidate-only exact authority dependency port. No imported research code."""
from pathlib import Path
import hashlib,json,difflib,ast
D=Path(__file__).resolve().parent
M=D.parents[3]
C=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-canonical-native-20261005-01/source')
P=Path('tradingagents/research/onchain_replication')
F=D.parent
prior=F/'real-data-pilot-main-import-port01-2026-10-05/candidate'/P
native=F/'real-data-pilot-main-native-port01-2026-10-05'
changed=['matching_owner.py','feature_journal.py','compact_owner.py','compact_mcm.py','mcm_score_stream.py','score_batches.py','compact_mcm_publication.py']
absent=sorted(p.name for p in prior.glob('*.py') if p.name!='job.py')
assert len(absent)==15
assert not (D/'candidate').exists()
sha=lambda b:hashlib.sha256(b).hexdigest()
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def emit(n,v):put(D/n,(json.dumps(v,sort_keys=True,indent=2)+'\n').encode())
rows=[]
for name in changed:
 old=(M/P/name).read_bytes();new=(C/P/name).read_bytes()
 ast.parse(new)
 put(D/'baseline'/name,old);put(D/'candidate'/P/name,new)
 patch=''.join(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),fromfile='a/'+str(P/name),tofile='b/'+str(P/name)))
 put(D/'patches'/(name+'.patch'),patch.encode())
 # Exact finite line replacement inverse, including deletions and additions.
 a=old.decode().splitlines(True);b=new.decode().splitlines(True)
 edits=[{'old_start':i,'old_end':j,'new_start':k,'new_end':l,'old':a[i:j],'new':b[k:l]} for op,i,j,k,l in difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes() if op!='equal']
 restored=b[:]
 for e in reversed(edits):assert restored[e['new_start']:e['new_end']]==e['new'];restored[e['new_start']:e['new_end']]=e['old']
 assert ''.join(restored).encode()==old
 rows.append({'path':str(P/name),'baseline_sha256':sha(old),'candidate_sha256':sha(new),'cap_sha256':sha(new),'edits':edits})
reuse=[]
for name in absent:
 raw=(prior/name).read_bytes();assert raw==(C/P/name).read_bytes()
 put(D/'candidate'/P/name,raw);reuse.append({'path':str(P/name),'origin':str(prior/name),'sha256':sha(raw)})
for name,pin in [('job.py','4dca6079896dd1394ccf65fbcd1a9bc601608fc8be22675b6f0f496e51ddd5e9'),('resources.py','9410243896ebc21ee445ea17b6fd56b5c28942661dced6427674f124713b22f4')]:
 raw=(native/name).read_bytes();assert sha(raw)==pin
 put(D/'candidate'/P/name,raw);reuse.append({'path':str(P/name),'origin':str(native/name),'sha256':pin})
protected={str(p.relative_to(M)):sha(p.read_bytes()) for p in sorted((M/P).glob('*.py')) if p.name not in changed+['job.py','resources.py']}
# No existing modules outside this explicit seven-body closure are patched.
emit('SOURCE_DELTA01.json',{'changed':rows,'reused':reuse,'main_unchanged_package':protected,'integration_authority':False})
print(json.dumps({'changed':len(rows),'reused':len(reuse),'untouched_main_modules':len(protected),'candidate_bodies':len(list((D/'candidate'/P).glob('*.py')))}))
