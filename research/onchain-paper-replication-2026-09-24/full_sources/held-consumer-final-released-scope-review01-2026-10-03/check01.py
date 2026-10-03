from pathlib import Path
import ast,hashlib,json,os,stat,time,shutil
R=Path(__file__).resolve().parent;B=R.parent;MAIN=B.parents[2]
A=B/'held-consumer-final-released-scope-root-capture01-2026-10-03';OLD=B/'held-consumer-final-composition-root-preparation01-2026-10-03'
C=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source');P=C.parent.parent/'held-score-consumer-root-launch-20261003-01'
H=lambda b:hashlib.sha256(b).hexdigest();J=lambda p:json.loads(p.read_bytes())
q=J(A/'REQUEST01.json');scope=J(A/'PRECAPTURE_SCOPE01.json');cm=J(A/'CAPSULE_MANIFEST01.json');pm=J(A/'PARENT_MANIFEST01.json')
assert H((A/'REQUEST01.json').read_bytes())==scope['request_sha256']=='660a715bc4da9bfd93e4076cee4d82730301024b9fa95668c8182a48d9ac2061'
assert H((A/'CAPSULE_MANIFEST01.json').read_bytes())==q['capsule_manifest_sha256']=='0ed39e3bb1f374f5eb3df1ff2053e0533804cc18df152dc8179b26598d94169e'
assert H((A/'PARENT_MANIFEST01.json').read_bytes())==q['external_manifest_sha256']=='1b96c4ab4cddf2c89e711b130aa46be71e2dc27604f68353162652331997e2a8'
assert cm==q['capsule_manifest']==J(OLD/'CAPSULE_BASELINE_OBSERVATION01.json') and pm==q['external_manifest']
oldpm=J(OLD/'ACTUAL_PARENT_BASELINE01.json');old={r['path']:r for r in oldpm['members']};new={r['path']:r for r in pm['members']}
assert len(old)==12 and len(new)==25 and all(new[p]==r for p,r in old.items()) and pm['root_mode']==oldpm['root_mode']
delta=sorted(set(new)-set(old));assert delta==scope['added_files'] and len(delta)==13 and all(new[p]['kind']=='file' for p in delta)
assert q['external_members']=={p:r['sha256'] for p,r in new.items() if r['kind']=='file'}
# Reuse only the independently written bounded opaque inventory function.
prior=B/'held-consumer-final-composition-review01-2026-10-03/check01.py';tree=ast.parse(prior.read_bytes());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='scan');exec(compile(ast.Module([node],type_ignores=[]),str(prior),'exec'),globals())
caps=scan(C,cm);parent=scan(P,pm);assert caps['files']==663 and caps['directories_excluding_root']==262 and parent['files']==23 and parent['directories_excluding_root']==2
assert caps['allocated_including_root']+parent['allocated_including_root']<=128*1024**2 and shutil.disk_usage(A).free>=10*1024**3
for row in scope['new13bodies']:
 actual=(P/row['path']).read_bytes();assert len(actual)==row['bytes'] and H(actual)==row['sha256'] and stat.S_IMODE((P/row['path']).stat().st_mode)==0o600
 if row['source'].startswith('research/'):
  assert (MAIN/row['source']).read_bytes()==actual
release=J(P/'release-final01.json');request=J(P/'request-final01.json');unreleased=J(P/'request-unreleased01.json');proposal=J(OLD/'NATIVE_CONTRACT_PROPOSAL01.json')
assert H((P/'release-final01.json').read_bytes())==scope['actual_final_release_sha256']=='eeac08eef932caccea1346149ec8a7f7473de03e774e0285634a74ae71b8774f'
assert H((P/'request-final01.json').read_bytes())==scope['actual_final_request_sha256']=='bc482b1196e691d8a0a06e3c866a11877b8cf8556ef407e5d3da72743412e4d4'
proofs=('release_review_sha256','external_capsule_recovery_sha256','external_recovery_review_sha256')
assert {k:v for k,v in release.items() if k not in proofs}=={k:v for k,v in proposal.items() if k not in proofs}
assert {k:v for k,v in request.items() if k not in ('status','remaining','release','evidence')}=={k:v for k,v in unreleased.items() if k not in ('status','remaining','release','evidence')}
assert request['status']=='released-one-use-native-parent' and request['remaining']==[] and request['case']=='success' and request['identity']=='original-import-held-success-20261003-01'
assert set(request['evidence'])=={'external_recovery','external_recovery_review','release_review'}
for row in [request['caller'],request['semantic_parser'],request['release'],*request['evidence'].values()]:assert row=={'path':row['path'],'sha256':new[row['path']]['sha256']} and H((P/row['path']).read_bytes())==row['sha256']
for field,key in zip(proofs,('release_review','external_recovery','external_recovery_review')):assert release[field]==request['evidence'][key]['sha256']
canonical=lambda v:json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode();contract=H(canonical({k:v for k,v in release.items() if k not in proofs}));assert contract==scope['release_contract_sha256']=='17e513bb0fa4ae667c822d80118578ae487138a3c6ad1cdd1123b7d68c435110'
for field,source_name in [('release_review','NATIVE_PARENT_RELEASE_REVIEW01.json'),('external_recovery_review','EXTERNAL_BASELINE_RECOVERY_REVIEW01.json')]:assert (P/request['evidence'][field]['path']).read_bytes()==(B/'held-consumer-final-native-proof-review01-2026-10-03'/source_name).read_bytes()
assert (P/request['evidence']['external_recovery']['path']).read_bytes()==(B/'held-consumer-final-native-proof-root-preparation01-2026-10-03/ACTUAL_EXTERNAL_FINAL_BASELINE_RECOVERY01.json').read_bytes()
# Actual source request validation only: compile pure metadata definitions, no imports/capture.
helper=B/'held-consumer-final-recovery-preparation04-2026-10-03/recovery04.py';raw=helper.read_bytes();assert H(raw)=='b40e5f06a0fd57b689e44ae82afd73ca8fe6721c43400beefe992ec12b17c18a'
from pathlib import PurePosixPath
ns={'Path':Path,'PurePosixPath':PurePosixPath,'json':json,'hashlib':hashlib,'FILE':4194304,'BASE':128*1024**2,'SOURCE':q['source'],'CAP':str(C)}
t=ast.parse(raw);names={'require','digest','encode','path_name','validate','request'};exec(compile(ast.Module([n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),str(helper),'exec'),ns)
assert ns['request'](q)==[C,P,Path(q['output_root'])] and ns['encode'](q)==(A/'REQUEST01.json').read_bytes()
assert not os.path.lexists(q['output_root']) and not os.path.lexists(P/'attempt') and scope['final_union_preservation_recovery_review_complete'] is False and scope['genuine_run_or_native_started'] is False
for case in release['cases'].values():
 for base in ('research_runs','fixture_outer','research_artifacts/onchain-paper-replication-2026-09-24/runs'):assert not os.path.lexists(C/base/case['identity'])
assert scan(C,cm)==caps and scan(P,pm)==parent
out={'schema_version':1,'decision':'accepted_exact_full950_member_capture_prerequisite_only','request_sha256':H((A/'REQUEST01.json').read_bytes()),'capsule':caps,'parent':parent,'root_modes':{'capsule':cm['root_mode'],'parent':pm['root_mode']},'original_capsule925_unchanged':True,'original_parent12_unchanged':True,'new_parent_file_count':13,'new_parent_paths':delta,'release_contract_sha256':contract,'final_request_sha256':H((P/'request-final01.json').read_bytes()),'final_release_sha256':H((P/'release-final01.json').read_bytes()),'recovery04_sha256':H(raw),'actual_capture_invoked':False,'native_release_or_claim_invoked':False,'whole_final_external_recovery_accepted':False,'root_launch_hold_required':True}
(R/'READBACK01.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps(out,sort_keys=True))
