import gzip,hashlib,io,json,os,stat,sys,tarfile
from pathlib import Path
D=Path(__file__).resolve().parent;F=D.parent;B=F/'financial-wrapper-complete100-final-supplement-capture01-2026-10-04';Q=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-final-contract-20261004-01');P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-root-launch-20261004-01');sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
ok(sha((P/'recovery04.py').read_bytes())=='b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a','original bounded R4');sys.path.insert(0,str(P));import recovery04 as R
capraw=(B/'CAPTURE01.json').read_bytes();ok(sha(capraw).startswith('86b787'),'actual capture pin');cap=json.loads(capraw);roots=json.loads((B/'SUPPORT_ROOTS01.json').read_bytes());ok(sha((B/'SUPPORT_ROOTS01.json').read_bytes())==cap['support_roots_sha256'] and len(roots)==9,'complete nine root mapping');manifests={}
for label in ('contract','support'):
 mraw=(B/(label.upper()+'_MANIFEST01.json')).read_bytes();m=json.loads(mraw);R.validate(m);snap=B/(label+'-snapshot');rec=cap['scopes'][label];ok(sha(mraw)==rec['manifest_sha256'],'manifest pin');ok(stat.S_IMODE(snap.stat().st_mode)==m['root_mode'],'snapshot rootmode');ok({p.relative_to(snap).as_posix() for p in snap.rglob('*')}=={r['path'] for r in m['members']},'whole snapshot exactmembership');files=[r for r in m['members'] if r['kind']=='file'];ok(len(files)==rec['files'] and len(m['members'])==rec['members'] and sum(r['bytes'] for r in files)==rec['logical_bytes'],'complete denominator')
 for row in m['members']:
  p=snap/row['path'];s=p.lstat();ok(stat.S_IMODE(s.st_mode)==row['mode'],'literal snapshotmode')
  if row['kind']=='file':ok(stat.S_ISREG(s.st_mode) and s.st_size==row['bytes'] and sha(p.read_bytes())==row['sha256'],'snapshot body')
  else:ok(stat.S_ISDIR(s.st_mode),'snapshot directory')
 archive=(B/('complete-'+label+'01.tar.gz')).read_bytes();ok(len(archive)==rec['archive']['bytes'] and sha(archive)==rec['archive']['sha256'],'archive pin');tf=tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz');frames=[(t.name,t,b'' if t.isdir() else tf.extractfile(t).read()) for t in tf];tf.close();ok(len(frames)==len(m['members']),'fullfooter framecount')
 for (name,t,body),row in zip(frames,m['members'],strict=True):
  ok(name==row['path'] and t.mode==row['mode'] and (t.isdir() if row['kind']=='directory' else t.isfile()),'canonicalpath/modetype');
  if row['kind']=='file':ok(body==(snap/name).read_bytes(),'frame snapshotbytes')
 out=io.BytesIO()
 with gzip.GzipFile(filename='',mode='wb',fileobj=out,mtime=0) as gz:
  with tarfile.open(fileobj=gz,mode='w|',format=tarfile.PAX_FORMAT) as tf:
   for row in m['members']:
    t=tarfile.TarInfo(row['path']);t.mode=row['mode'];t.uid=t.gid=0;t.uname=t.gname='';t.mtime=0
    if row['kind']=='directory':t.type=tarfile.DIRTYPE;t.size=0;tf.addfile(t)
    else:b=(snap/row['path']).read_bytes();t.size=len(b);tf.addfile(t,io.BytesIO(b))
 ok(out.getvalue()==archive,'exact canonical reencoding');manifests[label]=m
ok({p.name for p in Q.iterdir()}=={r['path'] for r in manifests['contract']['members']} and stat.S_IMODE(Q.stat().st_mode)==manifests['contract']['root_mode'],'complete original external contract')
for row in manifests['contract']['members']:
 p=Q/row['path'];ok(p.read_bytes()==(B/'contract-snapshot'/row['path']).read_bytes() and stat.S_IMODE(p.stat().st_mode)==row['mode'],'exact original request modebytes')
for label,ref in roots.items():
 root=Path(ref['original']);snap=B/'support-snapshot'/label;ok(root==F/label and stat.S_IMODE(root.stat().st_mode)==ref['original_root_mode']==stat.S_IMODE(snap.stat().st_mode),'original rootidentity/mode');ok({p.relative_to(root).as_posix() for p in root.rglob('*')}=={p.relative_to(snap).as_posix() for p in snap.rglob('*')},'full original closedreview membership')
 for p in root.rglob('*'):
  x=snap/p.relative_to(root);ok(p.lstat().st_mode==x.lstat().st_mode,'original literaltype/mode')
  if p.is_file():ok(p.read_bytes()==x.read_bytes(),'original fullreview body')
cumulative=json.loads((B/'support-snapshot/CUMULATIVE_ORIGINAL_PATH01.json').read_bytes());p=Path(cumulative['original']);ok(stat.S_IMODE(p.stat().st_mode)==cumulative['mode'] and p.read_bytes()==(B/'support-snapshot/CUMULATIVE19_REVIEW01.json').read_bytes() and sha(p.read_bytes())==cumulative['sha256'],'genuine cumulative originalmapping')
qraw=(Q/'REQUEST_RELEASED01.json').read_bytes();q=json.loads(qraw);ok(sha(qraw)==cap['request_sha256']=='34d1a85660af70706bd52fd8187c9a48edec39841246f03b12e88051f92e56f9','final actual request');contract=sha(R.encode({k:v for k,v in q.items() if k!='final_review'}));ok(contract==cap['contract_sha256']=='6da30ea89cdf08a90de914fabdbc0616a4832cdbfaa363dec286ae43ff7751e4','exact no selfreference contract');proofs={}
for role,ref in q['proofs'].items():
 p=Path(ref['path']);b=p.read_bytes();ok(sha(b)==ref['sha256'],'genuine proof '+role);proofs[role]=sha(b);matches=[r for r in manifests['support']['members'] if r['kind']=='file' and r['sha256']==sha(b)];ok(bool(matches),'proof body complete support '+role)
ok(proofs['full_recovery']==cap['baseline_full_recovery_sha256']=='49e0ad65d23f34496963b09e82cb8744d0e56c6d5c1a598af48f7154bd0e9122','baselineproof unchanged supplement separate');rr=Path(q['final_review']['path']).read_bytes();ok(sha(rr)==q['final_review']['sha256']==cap['release_sha256']=='f7e5b3d304090df7aaf3d6e107a2b401d752747160b9e4514708a7da6a45ef1b','exact actual release');ok(json.loads(rr)=={'schema_version':1,'decision':'accepted-exact-one-use-financial-parent','contract_sha256':contract,'proof_sha256':proofs,'identity':q['identity'],'source':q['source'],'caller_sha256':q['caller_sha256']},'exact sevenfield independentrelease')
C=Path(q['capsule_root']);ok(q['source']==q['design_source']==cap['source']=='9dc5c79f738920b52947b4e63fed0397f1b5b207' and sha((C/q['registration']).read_bytes())==q['registration_sha256'],'current sourcegate');base=F/'financial-wrapper-complete100-baseline-remote01-2026-10-04';meta=json.loads((base/'flat-parent01/body-metadata.json').read_bytes());ok({x.name for x in P.iterdir()}==set(meta['flat_members']) and len(meta['flat_members'])==9,'unchanged ninefile Parent')
for name,flatname in meta['flat_members'].items():ok((P/name).read_bytes()==(base/'flat-parent01'/flatname).read_bytes(),'Parent baseline body')
required=json.loads((B/'REQUIRED_BODIES01.json').read_bytes());ok(len(required)==7 and sum(x['bytes'] for x in required.values())==1063336 and 11+2*len(required)==25,'exact7 selected bytes25ops');
for path,row in required.items():
 p=F.parents[2]/path;ok(p.read_bytes()==(B/p.name).read_bytes() and len(p.read_bytes())==row['bytes'] and sha(p.read_bytes())==row['sha256'],'requiredbody binding')
ok(all(x['free_bytes']>=10*1024**3 and x['seconds']<120 for x in cap['floor_observations']),'original finitefloors');ok(cap['actual_external_recovery'] is False and cap['native_or_claim_started'] is False,'local capture no launch')
(D/'READBACK01.json').write_text(json.dumps({'checks':len(checks),'names':checks,'capture_sha256':sha(capraw),'contract':cap['scopes']['contract'],'support':cap['scopes']['support'],'full_recovery_bound':proofs['full_recovery'],'actual_external_recovery':None,'native_release':None},indent=2)+'\n');print(json.dumps({'checks':len(checks),'local_only':True}))
