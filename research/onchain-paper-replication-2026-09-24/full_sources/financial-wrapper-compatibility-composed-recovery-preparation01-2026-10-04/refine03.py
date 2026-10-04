from pathlib import Path
import hashlib,json,re
D=Path(__file__).resolve().parent;cfg=json.loads((D/'INPUTS01.json').read_bytes());O=D.parent/'financial-wrapper-compatibility-operational-delta-flat-outcome-review05-2026-10-04';cfg['paths']['flat_outcome_review']=str(O)
for n in ['MACHINE01.json','MANIFEST01.json','REPORT01.md']:
 p=O/n;b=p.read_bytes();cfg['fixed'][str(p)]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
assert cfg['fixed'][str(O/'MACHINE01.json')]['sha256']=='a0c19210a486194de02dc43631c64e40e9c6ae9e688b423496de230d801d7685'
assert cfg['fixed'][str(O/'MANIFEST01.json')]['sha256']=='1f3e7209b060275748685b31811f743feebb71987109c7aa71174f74423a951a'
cfg['future_independent_outcome_review']='Now actual independently accepted narrow two-scope review05; complete composed proof remains unissued.'
(D/'INPUTS01.json').write_text(json.dumps(cfg,sort_keys=True,indent=2)+'\n');p=D/'verify01.py';s=p.read_text();s=re.sub("INPUTS_PIN='[0-9a-f]+'","INPUTS_PIN='"+hashlib.sha256((D/'INPUTS01.json').read_bytes()).hexdigest()+"'",s)
needle=" require(sum(n.startswith('tradingagents/') for n in newmap)==150,'150 package bodies')"
addition="""
 roles=r.j(P['policy']/'HISTORICAL_ROLE_MAP01.json')
 for role,x in roles.items():require(h(old[safe(x['path'])])==x['sha256'] and len(old[x['path']])==x['bytes'] and composition[x['path']]==old[x['path']],'historical exact role source bytes')
 cpname=roles[policy['historical']['checkpoint_input']]['path'];cp=decode(old[cpname]);require(cp['provenance']==policy['historical']['provenance'],'honest complete old checkpoint provenance')
 for n,x in cp['members'].items():
  raw=old[str(Path(cpname).parent/safe(n))];require(len(raw)==x['bytes'] and h(raw)==x['sha256'],'opaque original checkpoint member')
"""
assert needle in s;s=s.replace(needle,needle+addition)
needle=" require(post['recovery_sha256']==h(r.read(D/'FLAT_RECOVERY01.json')),'actual postwrite sidecar')"
addition="""
 peer=seal(r,P['flat_outcome_review']);require(peer['decision']=='ACCEPTED_ACTUAL_TWO_SCOPE_BYTE_RECOVERY','genuine independent actual narrow outcome')
 for field,filename in [('flat_receipt_sha256','FLAT_RECOVERY01.json'),('sidecar_sha256','FLAT_POSTWRITE_OBSERVATION01.json'),('root_exit_sha256','ROOT_FLAT05_EXIT01.json'),('remote_receipt_sha256','REMOTE_RECOVERY01.json'),('selection_sha256','SELECTED_BODIES01.json')]:require(peer[field]==h(r.read(D/filename)),'actual peer receipt join')
 require(peer['owned_root']==str(D) and peer['source_commit']==SOURCE and peer['policy_sha256']==POLICY and peer['source_sha256']==draft['source_sha256'] and peer['caller_sha256']==intent['outer_caller_sha256'] and peer['release_sha256']==intent['entry_review_sha256'],'actual peer source/caller/entry')
 require(peer['original_regular_bodies']==64 and peer['physical_regular_files']==66 and peer['typed_descendants']==83 and peer['actual_child_exit']==peer['actual_outer_exit']==0 and peer['cleanup_failures']==[] and peer['composed_git385_plus9_proof'] is None and peer['numerical_authority'] is False and peer['posix_tree'] is False and peer['runtime_package_bodies'] is False,'narrow outcome boundaries')
"""
assert needle in s;s=s.replace(needle,needle+addition)
s=s.replace("('entry_review',['MACHINE01.json','MANIFEST01.json','REPORT01.md']),", "('entry_review',['MACHINE01.json','MANIFEST01.json','REPORT01.md']),('flat_outcome_review',['MACHINE01.json','MANIFEST01.json','REPORT01.md']),")
p.write_text(s)
