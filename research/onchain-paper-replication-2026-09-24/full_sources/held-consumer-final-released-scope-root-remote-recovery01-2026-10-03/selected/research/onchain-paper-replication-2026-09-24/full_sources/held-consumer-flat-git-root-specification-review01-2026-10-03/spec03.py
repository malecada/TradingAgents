"""Final exact spec read-only chain review. Never instantiate or execute ObjectStore."""
import ast,hashlib,json,os,shutil,stat,sys,time
from pathlib import Path
from unittest.mock import patch
O=Path(__file__).resolve().parent;F=O.parent;P=F/'held-consumer-flat-git-root-specification01-2026-10-03';H=F/'held-consumer-flat-git-recovery-preparation01-2026-10-03';R=F/'held-consumer-final-baseline-root-remote-recovery02-2026-10-03';sys.path.insert(0,str(H));import git_recovery01 as m
sha=lambda b:hashlib.sha256(b).hexdigest();checks=[];reads=[]
def ck(ok,label):
 assert ok,label
 checks.append(label)
spraw=(P/'SPEC01.json').read_bytes();ck(sha(spraw)=='1565b8533578ee862d019bdfe036b012011f6946bdcf3e22b1cbc4aaea877c4f','exact Root spec');s=json.loads(spraw);ck(m.a.encode(s)==spraw,'canonical spec');ck(set(s)=={'schema_version','bundle','flat_root','request_file','request_sha256','capture_sha256','recovery_sha256','output_root','expected_file','expected_sha256'} and type(s['schema_version']) is int and s['schema_version']==1 and all(v is not None for v in s.values()),'complete exact spec fields')
expected=m.checked_json(Path(s['expected_file']).parent,Path(s['expected_file']).name,s['expected_sha256']);ck(s['expected_sha256']=='d4c2ad952d50a4f3c813ca188a9ebded94c6f1c356b8c645c3b684a048244227' and len(expected['current'])==246 and len(expected['historical']['lookups'])==638 and len(expected['historical']['claims'])==4 and len(expected['selected_c6']['rows'])==26,'frozen complete worksheet')
q=json.loads(Path(s['request_file']).read_bytes());ck(sha(Path(s['request_file']).read_bytes())==s['request_sha256']=='3d5481584c69034d696276431465064d01788e0fd651bdc8fe7df203bc52bf71','fetched request');bundle=Path(s['bundle']);flat=Path(s['flat_root']);out=Path(s['output_root']);ck(flat==R/'flat03' and out==P/'git-proof01','exact fresh selected namespaces');ck(s['capture_sha256']=='b9f1d20bedb3e9eff6ca7390684c439de29f5eaab062663e8419f2a3b7a40227' and s['recovery_sha256']=='48c24f5b7c015cb902db19afbb2b171edefadb88a3bb10ef86d8815067c8bf34','actual capture/recovery pins')
roots=[bundle,flat,out,*[Path(q[k]) for k in ('capsule_root','external_root','output_root')]];ck(all(p.is_absolute() and p.resolve()==p for p in roots),'canonical roots');ck(all(not out.is_relative_to(p) and not p.is_relative_to(out) for p in roots if p!=out),'output entirely disjoint');ck(all(not x.is_relative_to(y) for i,x in enumerate([bundle,flat,out]) for j,y in enumerate([bundle,flat,out]) if i!=j),'proof root disjointness')
fd=os.open(out,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
try:
 before=os.fstat(fd);ck(before.st_uid==os.geteuid() and stat.S_IMODE(before.st_mode)==0o700 and out.lstat().st_ino==before.st_ino,'Root existing acquired private output');ck(list(os.scandir(fd))==[],'output genuinely empty');free=shutil.disk_usage(out).free;ck(free>=m.a.FLOOR,'current10GiBfloor')
finally:os.close(fd)
# Exact source04 correction does not affect proof's used archive helper functions.
a03=(H/'archive03.py').read_text();a04=(F/'held-consumer-final-recovery-preparation04-2026-10-03/recovery04.py').read_text();ck(sha(a03.encode())=='785b957f93e22b18b1d3c00a73cacc75b6028bab9566d737b40903dcffc4964e' and sha(a04.encode())=='b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a','exact old/corrected source pins')
trees=[ast.parse(x) for x in (a03,a04)];defs=[{n.name:n for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))} for t in trees]
ck(set(defs[0])==set(defs[1]),'same entire definition roster');changed=[name for name in defs[0] if ast.dump(defs[0][name])!=ast.dump(defs[1][name])];ck(changed==['framed_members'],'only corrected frame parser AST changed')
review=F/'held-consumer-final-recovery-review04-2026-10-03';ck(sha((review/'REVIEW04.md').read_bytes())=='11edd9d352edbcaef1fbf0a8d55778d8ea4cac83611d502efd29da056d448e39' and sha((review/'MANIFEST04.json').read_bytes())=='8ebeaa7dc5affcb6dbb00d0c71a28801c90463d1c37e6a82281da5577d9f09a1','exact source04 independent review')
terminal=json.loads((R/'FLAT_TERMINAL03.json').read_bytes());pins=json.loads((R/'FLAT_RUN_PINS03.json').read_bytes());ck(terminal['exit']==0 and terminal['recovery_sha256']==s['recovery_sha256'] and terminal['flat_root']==s['flat_root'],'actual terminal record');ck(pins['helper_sha256']==sha(a04.encode()) and pins['helper_review_sha256']==sha((review/'REVIEW04.md').read_bytes()),'actual recovery source/review pins')
for stream in ('stdout','stderr'):ck(sha((R/('FLAT03.'+stream)).read_bytes())==terminal[stream+'_sha256'],'terminal '+stream+' bytes')
original_read=m.a.read
forbidden=[Path(q['capsule_root']),Path(q['external_root'])]
def read(root,name,*a,**kw):
 root=Path(root);ck(not any(root.is_relative_to(p) for p in forbidden),'no original donor read');reads.append(str(root/name));return original_read(root,name,*a,**kw)
view=m.FlatView(flat)
try:
 view.begin()
 with patch.object(m,'ObjectStore',side_effect=AssertionError('actual proof forbidden')),patch.object(m.a,'framed_members',side_effect=AssertionError('old parser must be unused')),patch.object(m.a,'read',read):
  actualq=m.chain(view,bundle,Path(s['request_file']),s['request_sha256'],s['capture_sha256'],s['recovery_sha256'])
 ck(actualq==q,'exact full chain request');counts={role:{'manifest_members':len(view.manifests[role]['members']),'regular_bodies':len(view.maps[role]),'logical_bytes':sum(r['bytes'] for r in view.manifests[role]['members'] if r['kind']=='file')} for role in ('capsule','external')};ck(counts['capsule']['regular_bodies']==663 and counts['external']['regular_bodies']==10,'all673 flat regular bodies');ck(len(view.expected)==676,'entire676member flat scope')
 for row in expected['current']:
  current={r['path']:r for r in view.manifests['capsule']['members']}[row['path']];ck(current['kind']=='file' and current['bytes']==row['bytes'] and current['sha256']==row['sha256'] and ('100755' if current['mode']&0o100 else '100644')==row['git_mode'],'worksheet-to-recovered-manifest '+row['path'])
 view.finish()
finally:view.close()
ck(list(out.iterdir())==[] and out.stat().st_ino==before.st_ino and stat.S_IMODE(out.stat().st_mode)==0o700,'proof output remains unchanged/empty');ck(sha((P/'SPEC01.json').read_bytes())==sha(spraw),'spec unchanged');ck(not any(n.split('.')[0] in {'numpy','torch','scipy'} for n in sys.modules),'no numerical modules');ck((m.MAX_CALLS,m.WALL,m.TOTAL,m.a.FLOOR)==(4096,300,134217728,10737418240),'exact finite proof bounds')
result={'status':'ACCEPTED_EXACT_SPEC_FOR_ROOT_OFFLINE_GIT_PROOF_ONLY','spec_sha256':sha(spraw),'expected_sha256':s['expected_sha256'],'request_sha256':s['request_sha256'],'capture_sha256':s['capture_sha256'],'recovery_sha256':s['recovery_sha256'],'output':{'path':str(out),'device':before.st_dev,'inode':before.st_ino,'mode':stat.S_IMODE(before.st_mode),'uid':before.st_uid,'empty':True,'free_bytes_observed':free},'flat_roles':counts,'flat_members':676,'checks':len(checks),'read_operations':len(reads),'old_frame_decoder_invoked':False,'object_store_instantiated':False,'actual_git_proof_executed':False,'actual_source_body_donor_read':False,'native_release_or_research_authority':False,'scope':'exact data/spec joins only; external origin separately independently reviewed; Root must recheck freshness and floors before one actual offline proof'};(O/'SPEC_READBACK03.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');(O/'READ_PATHS03.json').write_text(json.dumps(reads,indent=2)+'\n');print(json.dumps(result,indent=2))
