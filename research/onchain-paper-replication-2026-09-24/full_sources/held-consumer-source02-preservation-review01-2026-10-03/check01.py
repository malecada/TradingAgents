from pathlib import Path,PurePosixPath
import json,hashlib,subprocess,os,stat,re
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';P=F/'held-consumer-source02-preservation-preparation01-2026-10-03';D=Path(__file__).parent;H=lambda b:hashlib.sha256(b).hexdigest()
mp=P/'SELECTED_RELEASE_BODIES02.json';m=json.loads(mp.read_bytes());assert set(m)=={'schema_version','status','rows','qualification'} and type(m['schema_version']) is int and m['schema_version']==1 and m['status']=='selected-final-release-bodies';rows=m['rows'];assert len(rows)==239<=512;names=[x['path'] for x in rows];assert names==sorted(set(names));total=0
for row in rows:
 assert set(row)=={'path','sha256','bytes'} and type(row['bytes']) is int and 0<=row['bytes']<=4194304 and re.fullmatch('[0-9a-f]{64}',row['sha256']);p=PurePosixPath(row['path']);assert str(p)==row['path'] and not p.is_absolute() and '..' not in p.parts and '\\' not in row['path'] and '\x00' not in row['path'] and p.parts[0]=='research';path=R/row['path'];assert path.resolve()==path and stat.S_ISREG(path.lstat().st_mode);b=path.read_bytes();assert len(b)==row['bytes'] and H(b)==row['sha256'];total+=len(b)
assert total==4794437 and total<=64*1024**2
scope=json.loads((P/'SOURCE_SCOPE01.json').read_bytes());meta=json.loads((P/'SOURCE_BUNDLE_METADATA01.json').read_bytes());C=Path(meta['source_root']);S=meta['source_commit'];A=meta['anchor_commit'];O=meta['original_parent_commit'];assert (S,A,O)==('76a4bd766722e0f5177412f6945117d9c2b5fc45','b8c6c280fb229ffaa5195c95baf3f57485e972b0','fb9fad1d93836b4f92f2be8111da4adf22b7e069')
bundle=P/'source02.bundle';assert H(bundle.read_bytes())=='afc86dffc93190018c85a95e71aeb35a6253fa6049ac0a91021cc95eed120e21' and bundle.stat().st_size==1027170
env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_OPTIONAL_LOCKS':'0','GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'protocol.allow','GIT_CONFIG_VALUE_0':'never'}
repo=D/'offline-bundle01.git';assert not repo.exists();r=subprocess.run(['git','-c','protocol.file.allow=always','clone','--bare',str(bundle),str(repo)],env=env,capture_output=True,timeout=30);(D/'clone01.stdout').write_bytes(r.stdout);(D/'clone01.stderr').write_bytes(r.stderr);assert r.returncode==0

def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],env=env,stderr=subprocess.PIPE,timeout=10)
assert git(repo,'rev-parse','HEAD').decode().strip()==git(C,'rev-parse','HEAD').decode().strip()==S and not (repo/'objects/info/alternates').exists()
assert git(repo,'rev-list','--parents','-n','1',S).decode().split()==[S,A] and git(repo,'rev-list','--parents','-n','1',A).decode().split()==[A,O]
def tree(commit):
 out={}
 for row in git(repo,'ls-tree','-rz',commit).split(b'\0'):
  if not row:continue
  fields,name=row.split(b'\t',1);mode,typ,obj=fields.decode().split();assert typ=='blob';out[name.decode()]={'mode':mode,'object':obj}
 return out
st=tree(S);at=tree(A);assert len(st)==204 and len(at)==201
assert len(meta['tracked_bodies'])==204 and {r['path'] for r in meta['tracked_bodies']}==set(st)
for row in meta['tracked_bodies']:
 p=row['path'];b=(P/'source-bodies'/p).read_bytes();assert b==(C/p).read_bytes()==git(repo,'show',S+':'+p)==git(C,'show',S+':'+p) and H(b)==row['sha256'] and len(b)==row['bytes'] and st[p]['mode']==row['git_mode'];assert stat.S_IMODE((P/'source-bodies'/p).stat().st_mode)==(0o755 if row['git_mode']=='100755' else 0o644)
assert {p.relative_to(P/'source-bodies').as_posix() for p in (P/'source-bodies').rglob('*') if p.is_file()}==set(st)
comp=json.loads((R/scope['source_composition_reference']).read_bytes());sr=comp['source_entries'];assert len(sr)==199 and sum(r['target'].startswith('tradingagents/') for r in sr)==148
for row in sr:
 p=row['target'];b=git(repo,'show',S+':'+p);assert H(b)==row['sha256'] and len(b)==row['bytes']
 if p.startswith('tradingagents/'):assert git(repo,'show',A+':'+p)==b
aux=set(st)-{r['target'] for r in sr};assert len(aux)==5
for p in aux:assert git(repo,'show',S+':'+p)==git(repo,'show',A+':'+p)==git(repo,'show',O+':'+p)
helper=(P/'recover_release02.py').read_bytes();old=F/'neural-cold-feature-handoff-root-compare-request02-2026-10-03/recover_release02.py';assert helper==old.read_bytes() and H(helper)=='b68870148fa6ada1ec04121b7716ea7179390362f9ec1e6489898d886c8f6060';assert not os.path.lexists(P/'final-release-recovery02') and not os.path.lexists(P/'REMOTE_FINAL_RELEASE_RECOVERY02.json')
out={'schema_version':1,'decision':'accepted_local_source_bundle_and_selected_backup_request_only','manifest_sha256':H(mp.read_bytes()),'selected_files':239,'selected_body_bytes':total,'tracked_source_bodies':204,'source_inventory':199,'package_anchor_bodies':148,'source':S,'anchor':A,'original_S2':O,'sole_parent_lineage_verified':True,'bundle_sha256':H(bundle.read_bytes()),'fresh_offline_bundle_clone':True,'auxiliary_unchanged_from_original':sorted(aux),'source_body_Git_modes_and_copy_modes_verified':True,'helper_unchanged':True,'destination_absent':True,'network_or_source_execution':False,'scope':'Local source-only preservation readiness; future fixture helper successor/registration/runtime/native/current writable tree and external recoverability not proved.'};(D/'READBACK01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
