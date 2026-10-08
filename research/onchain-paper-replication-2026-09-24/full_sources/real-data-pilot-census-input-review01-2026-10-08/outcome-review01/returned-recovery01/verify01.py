import hashlib,json,os,subprocess,tarfile
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[5];BASE=H.parents[2]
I=BASE/'real-data-pilot-seven-graph-census-increment01-2026-10-08'
sha=lambda b:hashlib.sha256(b).hexdigest()
raw=(I/'FRESH_GIT_RECOVERY01.json').read_bytes();assert sha(raw)=='3ce562af33897a04f929099a7ee45032f7f0195a839022a7e141d2d327ce38ff'
f=json.loads(raw);bare=Path(f['fresh_bare']);commit='78e8527d99bfc855216dfada0cc5f5c52ba1f50b'
assert f['actual_remote_head']==f['actual_fetched_head']==f['source_commit']==commit
assert len(f['git_operations'])==9 and all(x['exit_code']==0 for x in f['git_operations'])
assert not (bare/'objects/info/alternates').exists() and not (bare/'objects/info/http-alternates').exists()
env=dict(os.environ);env.update(GIT_NO_LAZY_FETCH='1',GIT_ALLOW_PROTOCOL='',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_ALTERNATE_OBJECT_DIRECTORIES='')
def git(*args):
 p=subprocess.run(['git','-c','protocol.allow=never','--git-dir',str(bare),*args],env=env,capture_output=True,timeout=30);assert p.returncode==0,(args,p.stderr);return p.stdout
assert git('rev-parse','--is-bare-repository').strip()==b'true'
assert git('rev-parse','FETCH_HEAD').decode().strip()==commit
assert git('config','--get','remote.origin.promisor').strip()==b'true'
assert git('config','--get','remote.origin.partialclonefilter').strip()==b'blob:none'
assert git('config','--get','remote.origin.url').strip()==b'git@github.com:malecada/TradingAgents.git'
assert commit in (bare/'shallow').read_text().splitlines()
assert list((bare/'objects/pack').glob('*.promisor'))
archive=R/f['returned_archive'];a=archive.read_bytes();assert len(a)==5657046 and sha(a)==f['returned_sha256']=='57f51aecf096ea42319d730012613e58434a1b55ccc5d6c2eb38b8eee42d9a6c'
blobpath=str((I/'census-increment01.tar.gz').relative_to(R));blob=git('cat-file','blob',commit+':'+blobpath);assert len(blob)==len(a) and sha(blob)==sha(a);del blob,a
selectionraw=(H.parent/'SELECTION01.json').read_bytes();assert sha(selectionraw)=='77099f890e62c43d7b2ca940b0ede055897de4a49b9a164c8b53712c064b86bb'
selection=json.loads(selectionraw);expected={x['path']:x for x in selection['entries']};seen=set();files=total=0
with tarfile.open(archive,'r|gz') as t:
 for member in t:
  name=member.name;assert name in expected and name not in seen;seen.add(name);e=expected[name]
  assert member.mode==e['mode'] and member.uid==member.gid==member.mtime==0
  assert member.uname==member.gname==''
  if e['type']=='directory':assert member.isdir() and member.size==0
  else:
   assert member.isfile() and member.size==e['bytes'];h=hashlib.sha256();n=0
   stream=t.extractfile(member)
   while block:=stream.read(65536):h.update(block);n+=len(block)
   assert n==e['bytes'] and h.hexdigest()==e['sha256'];files+=1;total+=n
assert seen==set(expected) and len(seen)==87 and files==77 and total==104125047
result={'status':'PASS externally recovered selected archive bytes','commit':commit,'fresh_bare':str(bare),'fetch_head_verified_offline':True,'alternates_absent':True,'promisor_blob_none_metadata_verified':True,'archive_sha256':f['returned_sha256'],'archive_bytes':5657046,'members':87,'regular_files':77,'directories':10,'verified_body_bytes':total,'exact_names_modes_body_hashes':True,'deterministic_uid_gid_mtime_zero_names_empty':True,'scope':'offline local Git with GIT_NO_LAZY_FETCH=1, empty protocol allowlist and protocol.allow=never; tar streamed without extraction; no original payload reread or numerical decoding','qualification':'Matches selected actual ownedroot only; no unchanged historical/input/runtime backup claim; pilot19 remains FAILED'}
(H/'CHECKS01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
