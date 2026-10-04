import hashlib,json,os
from pathlib import Path
M=Path.cwd();B=M/'research/onchain-paper-replication-2026-09-24/full_sources';H=B/'financial-genuine-wrapper-root-claimedrun-tooling-helper-flat01-2026-10-04'
assert not os.path.lexists(H);H.mkdir(mode=0o700)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(M).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
def put(p,v):
 with p.open('x')as f:json.dump(v,f,sort_keys=True,indent=2);f.write('\n')
P=B/'financial-genuine-wrapper-root-claimedrun-final-sharded-flat01-2026-10-04'
pins={'recovery04.py':'b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a','owned_io.py':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb','bounded_git01.py':'db4a65a450bf9930abac04ab794539ebd952b07826d7314b4aea4e989dd9240f'}
for n,s in pins.items():
 assert sha(P/n)==s
 with(H/n).open('xb')as f:f.write((P/n).read_bytes())
 os.chmod(H/n,0o600)
scopes=[]
for name in ['financial-genuine-wrapper-root-claimedrun-witness-tooling-capture01-2026-10-04','financial-genuine-wrapper-root-claimedrun-recovery-helper-witness-capture01-2026-10-04']:
 C=B/name;auth=json.loads((C/'UNION_AUTHENTICATION01.json').read_bytes())
 for label,x in sorted(auth['archives'].items()):
  scopes.append({'label':name+'/'+label,'archive':ref(C/x['archive']['path']),'manifest':ref(C/x['manifest']['path']),'original_metadata_sha256':x['original_metadata_sha256'],'ordinary_members':x['ordinary_members']})
assert len(scopes)==8
put(H/'REQUEST_DRAFT01.json',{'schema_version':1,'remote_root':str(B/'financial-genuine-wrapper-root-claimedrun-final-shards-remote01-2026-10-04'),'remote_receipt_sha256':None,'remote_commit':None,'scopes':scopes,'limits':{'whole_logical':64*1024**2,'body_archive':4*1024**2,'disk_floor':10*1024**3,'seconds':120},'actual_execution':False,'qualification':'Ordinary fresh byte restoration using unchanged accepted R4.restore. All eight archives were independently framed and canonically verified. Complete original modes/linktext/emptydir metadata remains ordinary bytes. No numerical authority, POSIX tree or installedruntime/empirical proof.'})
put(H/'ROOT_ADOPTION01.json',{'pins':pins,'source':str(P),'scopes':8,'status':'ordinary-byte-preparation-only','actual_execution':False})
print(json.dumps({'root':str(H),'request_draft_sha256':sha(H/'REQUEST_DRAFT01.json'),'scopes':8}))
