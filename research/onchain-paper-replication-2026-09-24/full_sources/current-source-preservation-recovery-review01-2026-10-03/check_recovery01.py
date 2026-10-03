from pathlib import Path
import json,hashlib,subprocess,os,stat
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';P=F/'neural-cold-feature-handoff-current-source-preservation01-2026-10-03';D=Path(__file__).parent;H=lambda b:hashlib.sha256(b).hexdigest();M='1a975e02e333f0fceba3a7a19680851795289e74'
receiptpath=P/'REMOTE_FINAL_RELEASE_RECOVERY02.json';receipt=json.loads(receiptpath.read_bytes());assert receipt['remote_commit']==M and receipt['actual_numerical_jobs']==0 and receipt['status']=='fresh-actual-remote-final-release-bodies-recovered'
repo=P/'final-release-recovery02/repository.git';saved=P/'final-release-recovery02/selected'
env={**os.environ,'GIT_NO_LAZY_FETCH':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_OPTIONAL_LOCKS':'0','GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'protocol.allow','GIT_CONFIG_VALUE_0':'never'}
def git(*args):return subprocess.check_output(['git','-C',str(repo),*args],env=env,stderr=subprocess.PIPE,timeout=10)
assert git('rev-parse','FETCH_HEAD').decode().strip()==M and not (repo/'objects/info/alternates').exists()
manifestpath=P/'SELECTED_RELEASE_BODIES02.json';manifestname=manifestpath.relative_to(R).as_posix();raw=manifestpath.read_bytes();assert H(raw)=='948ea903173b8505f4fdc971c12ba2c346c587eb879ed98767ac38a0799cef78';assert receipt['manifest']=={'path':manifestname,'sha256':H(raw),'bytes':len(raw)}
manifest=json.loads(raw);rows=manifest['rows'];assert len(rows)==138 and receipt['selected_blobs']==rows and receipt['blobs_including_manifest']==139
allrows=rows+[{'path':manifestname,'bytes':len(raw),'sha256':H(raw)}];expected={r['path'] for r in allrows};assert len(expected)==139
actual={p.relative_to(saved).as_posix() for p in saved.rglob('*') if p.is_file()};assert actual==expected
for row in allrows:
 p=saved/row['path'];assert stat.S_ISREG(p.lstat().st_mode) and not p.is_symlink();b=p.read_bytes();assert b==(R/row['path']).read_bytes() and len(b)==row['bytes'] and H(b)==row['sha256'];assert git('cat-file','-t',M+':'+row['path'])==b'blob\n' and git('show',M+':'+row['path'])==b
assert sum(r['bytes'] for r in rows)==receipt['logical_bytes_without_manifest']==4371335
scope=json.loads((saved/(P/'SOURCE_SCOPE01.json').relative_to(R)).read_bytes());assert len(scope['source_manifest_bindings'])==13 and len(scope['main_body_mappings'])==3
members=0
for ref in scope['source_manifest_bindings']:
 p=saved/ref['manifest_path'];assert H(p.read_bytes())==ref['sha256'];m=json.loads(p.read_bytes())
 for row in m['files']:
  q=p.parent/row['path'];assert q.relative_to(saved).as_posix() in expected;b=q.read_bytes();assert H(b)==row['sha256'] and len(b)==row['bytes'];members+=1
for row in scope['main_body_mappings']:
 b=(saved/row['selected_body_path']).read_bytes();assert b==(R/row['main_path']).read_bytes() and H(b)==row['sha256'] and len(b)==row['bytes']
assert H((saved/(P/'recover_release02.py').relative_to(R)).read_bytes())=='b68870148fa6ada1ec04121b7716ea7179390362f9ec1e6489898d886c8f6060'
out={'schema_version':1,'decision':'accepted_actual_selected_byte_recovery','actual_remote_receipt_sha256':H(receiptpath.read_bytes()),'actual_fixed_FETCH_HEAD':M,'Git_blobs_original_saved_exact':139,'selected_nonmanifest_body_bytes':4371335,'manifest_bytes':len(raw),'complete_saved_membership':True,'original_manifest_roles':13,'source_manifest_member_references':members,'Main_exact_current_mappings':3,'offline_no_lazy_fetch':True,'network_or_helper_invocation_by_reviewer':False,'scope':'Exact selected remote Git/original/saved file bodies; no directory modes/entire checkout/runtime/raw/outcomes/native/scientific authority claim. Root actual remote request/terminal evidence is separate from local FETCH_HEAD proof.'}
(D/'READBACK01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
