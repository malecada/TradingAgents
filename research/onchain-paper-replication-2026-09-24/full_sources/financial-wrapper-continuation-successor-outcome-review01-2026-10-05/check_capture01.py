from pathlib import Path
import json,hashlib,stat,tarfile
M=Path.cwd();F=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=Path(__file__).parent;T=F/'financial-wrapper-continuation-successor-terminal-capture01-2026-10-05';C=F/'heartbeat-root-checkpoint10-2026-10-04';CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
H=lambda b:hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
def ref(p):b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':H(b)}
x=read(T/'snapshot/COMPOSITION01.json');old=read(F/'financial-wrapper-continuation-successor-current-capture01-2026-10-05/snapshot/COMPOSITION01.json');receipt=read(T/'CAPTURE01.json');root=read(T/'ACTUAL_ROOT_EXIT01.json');manifest=read(T/'archive-manifest.json');evidence=read(D/'RAW_EVIDENCE01.json')
assert ref(F/'financial-wrapper-continuation-successor-current-capture01-2026-10-05/snapshot/COMPOSITION01.json')['sha256']=='7cfa0ac13cb3c4e76f087b155ae4ce0d5f58097091f1165fac9011003e66e779'
assert x['source']==old['source']=='a5bcc943167ad035b45e12ddf9864d46e685b124' and x['basis']==receipt['basis']
assert ref(Path(x['basis']['path']))['sha256']==x['basis']['sha256']=='bdf0f39710054d34f2274eec35a192dc13200ff146b4a79d3f4822235efba7df'
oldrows={r['path']:r for r in old['capsule']['members']};rows={r['path']:r for r in x['capsule']['members']};assert all(rows[k]==v for k,v in oldrows.items());assert len(rows)==1079 and sum(r['kind']=='file' for r in rows.values())==848
new=set(rows)-set(oldrows);assert len(new)==11 and sum(rows[n]['kind']=='file' for n in new)==9
assert x['Git']==old['scopes']['Git'] and x['Git_logical_objects']==438 and stat.S_IMODE((CAP/'.git').stat().st_mode)==x['Git']['manifest']['root_mode']==509
mapped=x['materialized'];assert len(mapped)==87 and sum(r['bytes'] for r in mapped.values())==932041
origin_map={};rawmap={}
for name,r in mapped.items():
 label,rel=name.split('/',1);base=CAP if label=='CAP' else C if label=='Root' else Path(x['scopes'][label]['root']);origin=base/rel;raw=(T/'snapshot'/r['flat']).read_bytes();assert len(raw)==r['bytes'] and H(raw)==r['sha256'];assert origin.read_bytes()==raw;assert stat.S_ISREG(origin.lstat().st_mode) and not origin.is_symlink();origin_map[str(origin)]=name;rawmap[name]=raw
for row in evidence['files']:
 assert row['path'] in origin_map;n=origin_map[row['path']];assert H(rawmap[n])==row['sha256'] and len(rawmap[n])==row['bytes']
for label,scope in x['scopes'].items():
 expected={label+'/'+r['path'] for r in scope['manifest']['members'] if r['kind']=='file'};assert expected=={n for n in mapped if n.startswith(label+'/')}
 for row in scope['manifest']['members']:
  path=Path(scope['root'])/row['path'];assert stat.S_IMODE(path.stat().st_mode)==row['mode']
  if row['kind']=='file':assert H(rawmap[label+'/'+row['path']])==row['sha256'] and len(rawmap[label+'/'+row['path']])==row['bytes']
assert {n.removeprefix('CAP/') for n in mapped if n.startswith('CAP/')}=={n for n in new if rows[n]['kind']=='file'}
assert len([n for n in mapped if n.startswith('Root/')])==8
assert root['actual_root_exit']==0 and root['session_id'] is None and root['tool_chunk_id']=='fa1755'
for n in ['capture','command_entry','stdout','stderr']:
 assert ref(Path(root[n]['path']))==root[n]
assert ref(T/'increment.tar.gz')['sha256']==receipt['archive']['sha256']=='d26c3af64a99e21162df9effacd9249f749555da059cc19a4e882125810cde17';assert ref(T/'archive-manifest.json')['sha256']==receipt['archive']['manifest_sha256']=='993da2d26f6f83fa8a5e6f5e87b56b1cde66e7d1183bcef202e2ad1658182413'
expected={r['path']:r for r in manifest['members']};assert len(expected)==88 and all(r['kind']=='file' for r in expected.values())
with tarfile.open(T/'increment.tar.gz','r:gz') as tar:
 members=tar.getmembers();assert len(members)==88 and {m.name for m in members}==set(expected)
 for item in members:
  assert item.isfile() and not item.name.startswith('/') and '..' not in Path(item.name).parts
  b=tar.extractfile(item).read();r=expected[item.name];assert H(b)==r['sha256'] and len(b)==r['bytes'] and item.mode==r['mode']
assert json.loads(rawmap['Parent/attempt/parent-terminal.json'])['actual_parent_exit'] is None
assert json.loads(rawmap['CAP/research_artifacts/onchain-paper-replication-2026-09-24/runs/'+x['identity']+'/guard/final.json'])['child_exit_code'] is None
check={'schema_version':1,'decision':'accepted-actual-terminal-capture','identity':x['identity'],'source':x['source'],'composition':ref(T/'snapshot/COMPOSITION01.json'),'capture':ref(T/'CAPTURE01.json'),'actual_root_exit':ref(T/'ACTUAL_ROOT_EXIT01.json'),'archive':ref(T/'increment.tar.gz'),'archive_manifest':ref(T/'archive-manifest.json'),'new_original_bodies':87,'new_original_bytes':932041,'archive_regular_bodies':88,'new_raw_outcome_bodies_joined':27,'CAP_regular':848,'CAP_typed':1079,'unchanged_CAP_regular_reused':839,'new_CAP_regular':9,'Git_logical_objects_reused':438,'physical_Git_root_mode_sampled':509,'Parent_regular':29,'preparation_review_regular':36,'frozen_outcome_phase_regular':5,'Root_regular':8,'unknown_original_exits_preserved':True,'external_recovery':False,'numerical_authority':False,'qualification':'Actual source-to-snapshot and archive byte joins authenticated for changed terminal increment only. Accepted old CAP/Git body basis reused; no old body rescan, immutable writer exclusion, runtime/POSIX recovery, continuation agreement or fresh identity authority.'}
p=D/'TERMINAL_CAPTURE_CHECK01.json';assert not p.exists();p.write_text(json.dumps(check,sort_keys=True,indent=2)+'\n');p.chmod(0o444);print(ref(p))
