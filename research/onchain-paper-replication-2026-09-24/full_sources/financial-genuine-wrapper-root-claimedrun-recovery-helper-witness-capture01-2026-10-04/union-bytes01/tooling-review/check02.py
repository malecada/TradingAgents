import ast,hashlib,io,json,os,sys,tarfile
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parent;A=B/'financial-genuine-wrapper-claimedrun-witness-tooling-capture-preparation01-2026-10-04';P=B/'held-consumer-final-recovery-preparation04-2026-10-03';sys.path.insert(0,str(P));import recovery04 as R
checks=[]
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
for p in json.loads((H/'PROJECTION01.json').read_bytes()):
 raw=(H/(p['scope']+'-PROJECTED_ONLY.tar.gz')).read_bytes();ok(sha(raw)==p['archive_sha256'],'projection exact')
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as t:semantic=[(x.name,x.mode,x.type,t.extractfile(x).read() if x.isfile() else b'') for x in t]
 g=R.framed_members(raw)
 try:
  framed=[(n,t.mode,t.type,b) for n,t,b in g]
 finally:g.close()
 ok(len(framed)==len(semantic)==p['ordinary_members'],'both full decoders exact denominator')
 for x,y in zip(framed,semantic):ok(x==y,'full exact framed semantic tuple '+x[0])
s=(A/'capture_tooling01.py').read_text();ns={'__name__':'read_only_definitions','__file__':str(A/'capture_tooling01.py')};exec(compile(s,'candidate','exec'),ns)
q=json.loads((ns['PARENT']/'REQUEST_FINAL03.json').read_bytes());proofs={**q['proofs'],'final_review':q['final_review']}
for role,ref in proofs.items():ok(sha(Path(ref['path']).read_bytes())==ref['sha256'],'genuine current proof '+role)
ok(sha((ns['PARENT']/'parent01.py').read_bytes())==q['caller_sha256'],'actual caller source')
for n,h in q['helper_hashes'].items():ok(sha((ns['PARENT']/n).read_bytes())==h,'current parent helper '+n)
ok(sha((ns['SOURCE']/q['registration']).read_bytes())==q['registration_sha256'],'actual current gate')
ok(q['design_source']=='0a2e7639b42b9423b90743feadcda4078aa21816' and len(q['input_hashes'])==8 and len(q['runtime_mapping']['distribution_records'])==251,'context metadata counts')
ok(not os.path.lexists(ns['PARENT']/'attempt'),'actual parent prelaunch observation')
# Exact unchanged output primitive refuses overbound before creation and any existing target.
for label,body in [('over',bytes(4194305)),('existing',b'replacement'),('link',b'replacement')]:
 path=H/('negative-'+label)
 if label=='existing':path.write_bytes(b'original')
 if label=='link':path.symlink_to('unavailable')
 try:ns['put'](R,path,body)
 except (ValueError,FileExistsError):ok(True,'put refusal '+label)
 else:raise AssertionError(label)
 if label=='over':ok(not os.path.lexists(path),'overextent no file')
 if label=='existing':ok(path.read_bytes()==b'original','no existing overwrite')
 if label=='link':ok(path.is_symlink() and os.readlink(path)=='unavailable','no lexical link overwrite')
for n in ('capture_tooling01.py','original-capture01.py','INVERSE01.json','MANIFEST01.json'):
 with (H/('ORIGINAL_'+n)).open('xb') as f:f.write((A/n).read_bytes())
for n in ('recovery04.py','owned_io.py','bounded_git01.py'):
 with (H/('PRIMITIVE_'+n)).open('xb') as f:f.write((P/n).read_bytes())
with (H/'CHECKS02.json').open('x') as f:json.dump({'count':len(checks),'checks':checks,'context_proof_refs':proofs,'runtime_records_rehashed':False,'full_framed_semantics_checked':True},f,sort_keys=True,indent=2);f.write('\n')
print(len(checks))
