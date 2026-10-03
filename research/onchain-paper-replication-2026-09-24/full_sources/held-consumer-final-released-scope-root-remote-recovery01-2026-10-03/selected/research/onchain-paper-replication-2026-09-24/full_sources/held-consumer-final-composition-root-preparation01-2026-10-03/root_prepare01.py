import hashlib,json,os,stat
from pathlib import Path
from datetime import datetime,timezone
B=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes/research/onchain-paper-replication-2026-09-24/full_sources');D=B/'held-consumer-final-composition-root-preparation01-2026-10-03';P=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-root-launch-20261003-01');CAP=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source');H=lambda b:hashlib.sha256(b).hexdigest();E=lambda v:(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
assert not (P/'attempt').exists();assert b'ValueError: unreleased or different finite parent' in (D/'DEFAULT_UNRELEASED_CHECK01.stderr').read_bytes()
rows=[]
for p in sorted(P.rglob('*')):
 s=p.lstat();r={'path':str(p.relative_to(P)),'mode':stat.S_IMODE(s.st_mode)}
 if stat.S_ISDIR(s.st_mode):r['kind']='directory'
 else:assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4194304;r.update(kind='file',bytes=s.st_size,sha256=H(p.read_bytes()))
 rows.append(r)
m={'schema_version':1,'root_mode':stat.S_IMODE(P.stat().st_mode),'members':rows};(D/'ACTUAL_PARENT_BASELINE01.json').write_bytes(E(m))
rel=json.loads((P/'release-unreleased01.json').read_bytes());assert set(rel['cases'])=={'success','second_target_publication_failure'};rel['status']='released-native-engineering';rel['remaining']=[]
for key in ('release_review_sha256','external_capsule_recovery_sha256','external_recovery_review_sha256'):rel[key]=None
(D/'NATIVE_CONTRACT_PROPOSAL01.json').write_bytes(E(rel));contract=H(json.dumps({k:v for k,v in rel.items() if k not in ('release_review_sha256','external_capsule_recovery_sha256','external_recovery_review_sha256')},sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode())
(D/'PROTOCOL01.md').write_text('''# Actual source composition and prospective native contract

Root copied the exact independently accepted parent03, accepted success02 parser, unchanged original unreleased two-case envelope and request template, and source-review bodies to the fixed external parent directory. Ten actual file bodies were verified and directory entries fsynced. No attempt identity directory, controller, native job, claim or genuine admission exists. The current actual files remain explicitly unreleased. Default actual-origin check exited1 with the expected unreleased-parent refusal; it made no claim or reservation. This is an unregistered engineering preflight observation, not a failed numerical research attempt or one of the full mutation/legacy acceptance cases.

ACTUAL_PARENT_COMPOSITION01 had an inexact release-status observation label;02 preserves01 and corrects the label from the real unchanged body. All copied bytes and dispositions are unchanged. Actual parent baseline contains ten regular files and two directories, no special members. Review manifests refer to retained adversarial source-review utility trees in Main; those trees are not substituted into production baseline membership.

NATIVE_CONTRACT_PROPOSAL01 is a separate prospective contract stored only in Main. Its target released status/empty remaining fields define the proposed future native behavior for independent review; its three proof references remain null. It is not installed as the actual parent release and grants no authorization or research authority. Every original source/input/runtime/registration/family/resource/case field is unchanged. The native contract hash excludes exactly three later proof references, as the accepted parent documentary protocol specifies.

Independent actual composition/contract review must precede any release. Complete capsule and actual caller/unreleased envelope baseline capture can be prepared after scope review. Actual release/request/proof bodies written later require separately authenticated external preservation/fresh recovery. Whole final scope must be explicitly the verified immutable baseline plus every separately pinned appended/changed proof, release and request body. Nothing outside that full scope is presumed recovered. The final exact request SHA passed to the one-use caller must derive from independently reviewed actually recovered bytes. No recursive self-hash or repeated push-proof claim is introduced.

Accepted recovery03 can recover full archive bytes/logical names/types/modes, not instantiate original POSIX directories or perform fresh recovered Git. Separate actual offline reconstructed Git object-store/source/current/design/anchor/history joins are required and a concrete finite helper is being implemented. Current/source/runtime/eligibility/execution decisions remain separate; all original failed/spent claims and budgets remain unchanged. Root alone performs live composition, registration/accounting, actual external preservation/fresh recovery and one eligible genuine numerical launcher. No scientific representation, full graph capacity, financial fit or external recovery follows from this source composition.
''')
r={'schema_version':1,'observed_utc':datetime.now(timezone.utc).isoformat(),'actual_parent_root':str(P),'actual_parent_manifest_sha256':H(E(m)),'current_release_status':json.loads((P/'release-unreleased01.json').read_bytes())['status'],'current_request_status':json.loads((P/'request-unreleased01.json').read_bytes())['status'],'caller_sha256':H((P/'launch_success01.py').read_bytes()),'semantic_parser_sha256':H((P/'held_outcome02.py').read_bytes()),'native_contract_proposal_sha256':H(E(rel)),'native_contract_without_three_later_proofs_sha256':contract,'default_actual_origin_check':{'tool_chunk':'0ac255','actual_exit_code':1,'expected_refusal':'unreleased or different finite parent','claim_created':False,'attempt_reserved':False,'native_started':False},'proposal_installed':False,'full_current_baseline_captured':False,'full_external_recovery':False,'fresh_recovered_git_proof':False,'execution_released':False}
(D/'PREPARATION_SUMMARY01.json').write_bytes(E(r))
# Preserve the exact stdlib Root operation sources for independent audit.
for origin,name in ((Path('/tmp/onchain_composition_scan.py'),'root_scan01.py'),(Path('/tmp/onchain_parent_actual_compose.py'),'root_compose01.py'),(Path('/tmp/onchain_parent_composition_freeze.py'),'root_prepare01.py')):
 (D/name).write_bytes(origin.read_bytes())
rr=[]
for p in sorted(D.rglob('*')):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1;rr.append({'path':str(p.relative_to(D)),'type':'file','mode':stat.S_IMODE(s.st_mode),'links':1,'bytes':s.st_size,'sha256':H(p.read_bytes())})
manifest={'schema_version':1,'status':'ACTUAL_SOURCE_COMPOSITION_AND_PROSPECTIVE_CONTRACT_UNRELEASED','files':rr,'original_capsule_unchanged':True,'actual_parent_created':True,'attempt_or_native_claim_created':False,'external_recovery':False};out=D/'MANIFEST01.json';out.write_bytes(E(manifest));print('composition manifest',H(out.read_bytes()),'contract',contract,'parentbaseline',H(E(m)))
