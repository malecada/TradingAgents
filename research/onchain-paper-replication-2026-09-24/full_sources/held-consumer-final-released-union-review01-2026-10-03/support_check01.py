from pathlib import Path
import ast,hashlib,json,os,stat,subprocess
from flat_checks01 import read
R=Path(__file__).resolve().parent;B=R.parent;MAIN=B.parents[2];A=B/'held-consumer-final-released-support-root-recovery01-2026-10-03';F=B/'held-consumer-final-released-scope-root-remote-recovery01-2026-10-03'
H=lambda b:hashlib.sha256(b).hexdigest();J=lambda p:json.loads(read(p));q=J(A/'REMOTE_SUPPORT01.json');sel=J(A/'SELECTED_SUPPORT01.json');missing=J(R/'UNION_READBACK02.json')['missing_support']
assert H(read(A/'REMOTE_SUPPORT01.json'))=='07eefc0dacc699ed52513e3bf4c283170a200b6884090f7bbdbf739c634d1c7e'
assert H(read(A/'SELECTED_SUPPORT01.json'))==q['selection_sha256']=='3ce7d25bf7a5a606c1d17303c1ff0dc3f5e70819536a888fc34adec000604398'
assert sel['rows']==missing and len(missing)==1 and q['selected_count']==1 and q['selected_logical_bytes']==471 and q['remote_commit']==sel['remote_commit']=='a9f18fffbc06b9e3996b67fc2a0139ce98900709'
assert q['origin']=='git@github.com:malecada/TradingAgents.git' and q['branch']=='refs/heads/research/onchain-paper-replication-2026-09-24' and q['genuine_run_or_native_started'] is False
body=(q['remote_commit']+'\t'+q['branch']+'\n').encode();ops=q['operations'];assert len(ops)==13 and all(x['exit']==0 and x['cleanup_failures']==[] and not (Path('/proc')/str(x['pid'])).exists() for x in ops)
remotes=[x for x in ops if x['operation']=='ls-remote'];assert len(remotes)==2 and all(x['stdout_sha256']==H(body) and x['stdout_bytes']==len(body) for x in remotes)
source=read(A/'recover_support01.py');scope=J(A/'SOURCE_SCOPE01.json');assert H(source)==scope['source_support_sha256']
# Exact bounded process and owned-write implementations stay unchanged.
old=ast.parse(read(F/'recover_final03.py'));new=ast.parse(source)
for name in ('require','digest','encode','write','git'):
 def f(t):return ast.dump(next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name),include_attributes=False)
 assert f(old)==f(new)
repo=Path(q['fresh_git_root']);assert repo==A/'fresh-support01.git';env={'PATH':'/usr/bin:/bin','LC_ALL':'C','GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_ALLOW_PROTOCOL':'','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_TERMINAL_PROMPT':'0'}
def git(args):
 r=subprocess.run(['git','-c','protocol.allow=never',*args],cwd=repo,env=env,capture_output=True,timeout=10);assert r.returncode==0 and len(r.stdout)<=65536 and len(r.stderr)<=65536;return r.stdout
row=missing[0];n=row['path'];raw=git(['show',q['remote_commit']+':'+n]);assert len(raw)==471 and H(raw)==row['sha256']=='7b0fe49468d5219e0bc6a6a6ce7bee8457f87a551bac49ff4bfe17bf76e9aa14'
oid=hashlib.sha1(b'blob 471\0'+raw).hexdigest();tree=git(['ls-tree','-z',q['remote_commit'],'--',n]);assert tree==('100644 blob '+oid+'\t'+n).encode()+b'\0' and q['selected_blobs']==[dict(row,git_mode='100644',git_object=oid)]
assert read(A/'selected'/n)==raw==read(MAIN/n) and stat.S_IMODE((A/'selected'/n).lstat().st_mode)==0o600
actual=[p.relative_to(A/'selected').as_posix() for p in (A/'selected').rglob('*') if p.is_file()];assert actual==[n]
terminal=json.loads(raw);assert terminal['exit']==0 and terminal['proof_sha256']=='b4544ebb75a5411b99d07fccd5c34ed72e5c40f9f53a6e6558dfaf9bb3523c5c'
assert H(read(F/'REMOTE_RECOVERY03.json'))==J(R/'ORIGIN_READBACK01.json')['receipt_sha256'] and H(read(F/'flat01/recovery.json'))==J(R/'UNION_READBACK02.json')['recovery_sha256']
# Prior witness remains exactly frozen; no failed assertion or result is rewritten.
pre=J(R/'PRELIMINARY_MANIFEST01.json')
for x in pre['members']:assert len(read(R/x['path']))==x['bytes'] and H(read(R/x['path']))==x['sha256']
current=J(R/'UNION_READBACK02.json');P=Path(current['root_launch_command'][2]).parent;assert H(read(P/'request-final01.json'))==current['request_sha256'] and H(read(P/'release-final01.json'))==current['release_sha256'] and not os.path.lexists(P/'attempt')
result={'schema_version':1,'decision':'accepted_actual_supplement_closes_UFR1','supplement_sha256':H(read(A/'REMOTE_SUPPORT01.json')),'source_sha256':H(source),'remote_commit':q['remote_commit'],'actual_offline_commit_body_hash':H(raw),'git_object':oid,'bytes':471,'actual_operation_pids_absent':True,'original431_final950_unchanged':True,'prior_withheld_witness_unchanged':True,'no_network_or_helper_invocation':True,'no_claim_or_native':True}
(R/'SUPPORT_READBACK01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,sort_keys=True))
