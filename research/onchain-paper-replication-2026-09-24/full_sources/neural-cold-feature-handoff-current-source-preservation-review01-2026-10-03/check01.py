from pathlib import Path,PurePosixPath
import json,hashlib,ast,os,stat,re
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';P=F/'neural-cold-feature-handoff-current-source-preservation01-2026-10-03';D=Path(__file__).parent;H=lambda b:hashlib.sha256(b).hexdigest()
mp=P/'SELECTED_RELEASE_BODIES02.json';assert H(mp.read_bytes())=='948ea903173b8505f4fdc971c12ba2c346c587eb879ed98767ac38a0799cef78';m=json.loads(mp.read_bytes());assert set(m)=={'schema_version','status','rows','qualification'} and type(m['schema_version']) is int and m['schema_version']==1 and m['status']=='selected-final-release-bodies';rows=m['rows'];assert len(rows)==138 and len(rows)<=512;names=[r['path'] for r in rows];assert names==sorted(set(names));total=0
for row in rows:
 assert set(row)=={'path','bytes','sha256'} and type(row['path']) is str and type(row['bytes']) is int and 0<=row['bytes']<=4194304 and re.fullmatch('[0-9a-f]{64}',row['sha256'])
 p=PurePosixPath(row['path']);assert str(p)==row['path'] and not p.is_absolute() and '..' not in p.parts and '\\' not in row['path'] and '\x00' not in row['path'] and p.parts[0]=='research'
 path=R/row['path'];assert path.resolve()==path and stat.S_ISREG(path.lstat().st_mode) and not path.is_symlink();b=path.read_bytes();assert len(b)==row['bytes'] and H(b)==row['sha256'];total+=len(b)
assert total==4371335 and total<=64*1024**2
scope=json.loads((P/'SOURCE_SCOPE01.json').read_bytes());assert len(scope['source_manifest_bindings'])==13 and len(scope['main_body_mappings'])==3
membership=set(names);manifest_members=0
for ref in scope['source_manifest_bindings']:
 p=R/ref['manifest_path'];assert ref['manifest_path'] in membership and H(p.read_bytes())==ref['sha256'];body=json.loads(p.read_bytes())
 for row in body['files']:
  target=p.parent/row['path'];name=target.relative_to(R).as_posix();assert name in membership;raw=target.read_bytes();assert H(raw)==row['sha256'] and len(raw)==row['bytes'];manifest_members+=1
for row in scope['main_body_mappings']:
 assert row['selected_body_path'] in membership;b=(R/row['main_path']).read_bytes();assert b==(R/row['selected_body_path']).read_bytes() and len(b)==row['bytes'] and H(b)==row['sha256']
helper=(P/'recover_release02.py').read_bytes();assert helper==(R/scope['original_accepted_helper_path']).read_bytes() and H(helper)==scope['unchanged_helper_sha256']=='b68870148fa6ada1ec04121b7716ea7179390362f9ec1e6489898d886c8f6060'
assert not os.path.lexists(P/'final-release-recovery02') and not os.path.lexists(P/'REMOTE_FINAL_RELEASE_RECOVERY02.json')
assert str((P/'recover_release02.py').relative_to(R)) in membership and str((P/'SOURCE_SCOPE01.json').relative_to(R)) in membership
out={'schema_version':1,'decision':'accepted_source_request_only','allowlist_sha256':H(mp.read_bytes()),'selected_rows':len(rows),'logical_bytes':total,'source_manifests':13,'manifest_member_references':manifest_members,'main_exact_mappings':3,'helper_byte_identical':True,'helper_sha256':H(helper),'fresh_destination_absent':True,'network_or_helper_execution':False,'scope':'Selected file bodies only, not entire checkout/modes/runtime/raw stores/outcomes or empirical release. Existing status strings are unchanged byte-transport schema. Actual remote transfer and fresh independent recovery still pending.'}
(D/'READBACK01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
