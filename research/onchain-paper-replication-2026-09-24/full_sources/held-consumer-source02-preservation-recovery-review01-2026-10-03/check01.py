"""Offline independent verification of already completed remote recovery."""
from pathlib import Path,PurePosixPath
import json,hashlib,subprocess,os,stat,re
D=Path(__file__).resolve().parent;F=D.parent;R=F.parents[2]
P=F/'held-consumer-source02-preservation-preparation01-2026-10-03'
recovery=P/'final-release-recovery02';saved=recovery/'selected';remote=recovery/'repository.git'
H=lambda b:hashlib.sha256(b).hexdigest()
env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_OPTIONAL_LOCKS':'0','GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'protocol.allow','GIT_CONFIG_VALUE_0':'never'}
def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args],env=env,stderr=subprocess.PIPE,timeout=15)
receiptbody=(P/'REMOTE_FINAL_RELEASE_RECOVERY02.json').read_bytes();assert H(receiptbody)=='3c9f713ead65606593ba28cce5f1ec60072af6aa5b9ccb76f1bb0adc9242350a'
receipt=json.loads(receiptbody);commit='8f703aabc495d65563980b8da5be9ef6fc9b58f8'
assert receipt['remote_commit']==commit==git(remote,'rev-parse','FETCH_HEAD').decode().strip()
tool=json.loads((P/'ACTUAL_RECOVERY_TOOL_EXIT02.json').read_bytes())
assert tool['actual_tool_session']==14746 and tool['actual_tool_exit_code']==0 and tool['receipt']['sha256']==H(receiptbody)
assert json.loads(tool['actual_tool_stdout'])['remote_commit']==commit
mp=P/'SELECTED_RELEASE_BODIES02.json';m=json.loads(mp.read_bytes());rows=m['rows'];assert len(rows)==239
assert receipt['selected_blobs']==rows and receipt['blobs_including_manifest']==240
assert m['status']=='selected-final-release-bodies' and m['schema_version']==1
allrows=[*rows,receipt['manifest']];names=[x['path'] for x in allrows]
assert len(names)==len(set(names))==240 and [x['path'] for x in rows]==sorted(x['path'] for x in rows)
logical=0
for row in allrows:
 name=row['path'];path=PurePosixPath(name)
 assert str(path)==name and not path.is_absolute() and '..' not in path.parts and '\\' not in name and '\x00' not in name and path.parts[0]=='research'
 assert type(row['bytes']) is int and 0<=row['bytes']<=4194304 and re.fullmatch('[0-9a-f]{64}',row['sha256'])
 actual=git(remote,'show',commit+':'+name)
 assert len(actual)==row['bytes'] and H(actual)==row['sha256']
 for base in (R,saved):
  p=base/name;assert p.resolve()==p and stat.S_ISREG(p.lstat().st_mode) and p.read_bytes()==actual
 logical+=len(actual)
assert logical==4794437+len(mp.read_bytes())==4872708
assert {str(x.relative_to(saved)) for x in saved.rglob('*') if x.is_file()}==set(names)
assert not any(x.is_symlink() for x in saved.rglob('*'))
scope=json.loads((saved/str((P/'SOURCE_SCOPE01.json').relative_to(R))).read_bytes())
meta=json.loads((saved/str((P/'SOURCE_BUNDLE_METADATA01.json').relative_to(R))).read_bytes())
bundle=saved/str((P/'source02.bundle').relative_to(R))
assert H(bundle.read_bytes())=='afc86dffc93190018c85a95e71aeb35a6253fa6049ac0a91021cc95eed120e21' and bundle.stat().st_size==1027170
clone=D/'actual-remote-bundle01.git';assert not clone.exists()
# Bundle is the independently authenticated REMOTELY SAVED body, not the
# previously checked local source or the earlier reviewer clone. No fetch.
result=subprocess.run(['git','clone','--bare',str(bundle),str(clone)],env=env,capture_output=True,timeout=20)
assert result.returncode==0,(result.returncode,result.stderr)
(D/'bundle-clone01.log').write_bytes(result.stdout+result.stderr)
S=meta['source_commit'];A=meta['anchor_commit'];O=meta['original_parent_commit'];C=Path(meta['source_root'])
assert (S,A,O)==('76a4bd766722e0f5177412f6945117d9c2b5fc45','b8c6c280fb229ffaa5195c95baf3f57485e972b0','fb9fad1d93836b4f92f2be8111da4adf22b7e069')
assert git(clone,'rev-parse','HEAD').decode().strip()==S==git(C,'rev-parse','HEAD').decode().strip()
assert not (clone/'objects/info/alternates').exists()
assert git(clone,'rev-list','--parents','-n','1',S).decode().split()==[S,A]
assert git(clone,'rev-list','--parents','-n','1',A).decode().split()==[A,O]
def tree(rev):
 out={}
 for row in git(clone,'ls-tree','-rz',rev).split(b'\0'):
  if not row:continue
  fields,name=row.split(b'\t',1);mode,typ,obj=fields.decode().split();assert typ=='blob';out[name.decode()]=(mode,obj)
 return out
st=tree(S);at=tree(A);assert len(st)==204 and len(at)==201
assert {r['path'] for r in meta['tracked_bodies']}==set(st)
sourceprefix=str((P/'source-bodies').relative_to(R));package=0
for row in meta['tracked_bodies']:
 name=row['path'];body=git(clone,'show',S+':'+name)
 assert body==(saved/sourceprefix/name).read_bytes()==(P/'source-bodies'/name).read_bytes()==(C/name).read_bytes()==git(C,'show',S+':'+name)
 assert len(body)==row['bytes'] and H(body)==row['sha256'] and st[name][0]==row['git_mode']=='100644'
 if name.startswith('tradingagents/'):
  assert git(clone,'show',A+':'+name)==body;package+=1
assert package==148
comp=json.loads((saved/scope['source_composition_reference']).read_bytes());entries=comp['source_entries'];assert len(entries)==199
for row in entries:
 body=git(clone,'show',S+':'+row['target']);assert H(body)==row['sha256'] and len(body)==row['bytes']
aux=set(st)-{x['target'] for x in entries};assert len(aux)==5
for name in aux:assert git(clone,'show',S+':'+name)==git(clone,'show',A+':'+name)==git(clone,'show',O+':'+name)
assert H((P/'recover_release02.py').read_bytes())==scope['helper_unchanged_sha256']=='b68870148fa6ada1ec04121b7716ea7179390362f9ec1e6489898d886c8f6060'
out=dict(schema_version=1,decision='accepted_actual_source_only_remote_recovery',remote_commit=commit,receipt_sha256=H(receiptbody),selected_blobs_including_manifest=240,selected_body_bytes=4794437,manifest_bytes=len(mp.read_bytes()),all_selected_bytes=logical,actual_tool_exit=0,tool_observation_qualification='Root transcription joined to receipt, not a native receipt; offline objects alone do not recreate network observation',bundle_sha256=H(bundle.read_bytes()),fresh_clone_from_actual_remotely_saved_bundle=True,tracked_git_bodies=204,source_entries=199,package_anchor_bodies=148,Git_blob_mode='100644',source=S,anchor=A,original_S2=O,sole_parent_lineage_verified=True,original_auxiliary_unchanged=sorted(aux),network_or_numerical_execution=False,qualification='File-body recovery and authentic source Git lineage only. No original directory modes, installed runtime, empirical stores, forthcoming fixture successor, live Owner or experiment release granted.')
(D/'READBACK01.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True))
