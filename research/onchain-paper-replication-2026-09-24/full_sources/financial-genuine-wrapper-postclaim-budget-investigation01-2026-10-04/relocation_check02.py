import ast,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-native-20261004-01/source');PARENT=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-recordfix-root-launch-20261004-01');ID='financial-wrapper-classification-eager-interrupt1-recordfix-20261004-01';checks=[]
def check(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def sha(b):return hashlib.sha256(b).hexdigest()
claim=json.loads((CAP/'research_runs'/ID/'claim.json').read_bytes());failed=json.loads((CAP/'research_runs'/ID/'failed.json').read_bytes());q=json.loads((PARENT/'REQUEST_FINAL02.json').read_bytes())
check(sha((CAP/'research_runs'/ID/'claim.json').read_bytes())=='4c543d71fad5255be61087eaa3619d9e88cbbdc12fa1398bd7fa7fe6fb75c128','original actual claim unchanged')
check(sha((CAP/'research_runs'/ID/'failed.json').read_bytes())=='35158c0ecebfe4dc75203ba87d5372f2f85643c0b5f828a99e17aa28fe79c450','original failed unchanged')
sources={}
for rel in ('tradingagents/research/verify.py','tradingagents/research/admission.py','tradingagents/research/budget_extensions.py','tradingagents/research/onchain_replication/financial_wrapper_fixture.py','tradingagents/research/onchain_replication/job.py'):
 b=(CAP/rel).read_bytes();check(sha(b)==q['source_files'][rel],'authentic source '+rel);sources[rel]=dict(path=str(CAP/rel),sha256=sha(b));
v=ast.parse((CAP/'tradingagents/research/verify.py').read_bytes());funcs={n.name:n for n in v.body if isinstance(n,ast.FunctionDef)};vc=ast.unparse(funcs['verify_claim']);vr=ast.unparse(funcs['verify_run'])
check('root = directory.parent.parent' in vc,'verify_claim root inferred from supplied canonical directory')
check("directory.parent.name != 'research_runs'" in vc and "claim['experiment_id'] != directory.name" in vc,'relocated relative identity shape required')
check("_blob(root, claim['source'], claim['registration'])" in vc and "_blob(root, claim['design_source'], claim['registration'])" in vc,'historical old commits selected in destination Git')
check("_verify_sources(root, pinned, {claim['source'], claim['design_source']})" in vc,'historical full source body verification retained')
check('admit(' not in vc and 'HEAD' not in vc,'verify_claim no fresh admission/currentHEAD dependency')
check('root' not in claim and 'directory' not in claim and claim['source']==claim['design_source']=='649fb8a11089524aaef7843dffeeb90a3a55ca17','actual claim no root field; source identities immutable')
check(all(not Path(i['path']).is_absolute() and '..' not in Path(i['path']).parts for i in claim['inputs'].values()),'actual claim input descriptor paths relative')
check("outputs = list((directory / 'outputs').iterdir())" in vr and "if status == 'complete':" in vr,'failed verify_run retains exact relative outputs directory')
check(failed['output_sha256']=={} and list((CAP/'research_runs'/ID/'outputs').iterdir())==[],'actual closed failed empty output denominator')
a=ast.parse((CAP/'tradingagents/research/admission.py').read_bytes());af={n.name:ast.unparse(n) for n in a.body if isinstance(n,ast.FunctionDef)}
check('claim = verify_claim(child)' in af['claims'],'destination claims require genuine provenance verifier')
check("source must equal the full current HEAD" in af['admit'],'fresh future run currentHEAD binding')
check("parent_claim['experiment'] != experiments[exp['parent']]" in af['admit'],'original failed parent definition immutable in future gate')
e=(CAP/'tradingagents/research/budget_extensions.py').read_text();check("directory=root/'research_runs'/name" in e and "claim_raw=(directory/'claim.json').read_bytes()" in e,'extension snapshot destination historical bytes')
check("seen!=set(claims)" in e,'new capsule cannot drop closed claim from extension census')
p=(PARENT/'parent01.py').read_text();check("q['capsule_root']==str(CAP)" in p and "q['parent_root']==str(PARENT)" in p and "q['identity']==IDENTITY" in p,'old caller cannot silently relocate')
f=(CAP/'tradingagents/research/onchain_replication/financial_wrapper_fixture.py').read_text();check("(ad.root/'.git').is_dir()" in f and "job['resources']['disk_paths']==[str(ad.root)]" in f,'new capsule own Git directory and exact new resource root required')
check("Path(complete['checkpoint']).resolve()==refcp.resolve()" in f,'later completed checkpoint absolute ancestry remains nonportable without separate correction')
check(not (CAP/'research_artifacts/financial_wrapper_engineering'/ID).exists(),'this failed parent has no wrapper/checkpoint tree to relocate')
result={'decision':'CONDITIONALLY_ADMISSIBLE_NEW_CAPSULE_HISTORICAL_CLOSED_CLAIM_RELOCATION_REQUIRES_REVIEWED_PREPARATION','checks':len(checks),'check_names':checks,'authenticated_sources':sources,'original_source':claim['source'],'historical_claim_sha256':sha((CAP/'research_runs'/ID/'claim.json').read_bytes()),'historical_failed_sha256':sha((CAP/'research_runs'/ID/'failed.json').read_bytes()),'original_physical_source_must_remain_unchanged':True,'new_capsule_path':None,'new_git_head':None,'actual_relocation_mapping':None,'actual_history_copy':None,'actual_destination_verify_claim':None,'actual_destination_verify_run':None,'actual_destination_closed_history_count':None,'current_ceiling':18,'proposed_finite_ceiling':19,'same_unique_global_spent_claims':1,'new_budget_or_launch_authority':False,'owner_or_checkpoint_authority_relocated':False,'clone_performed':False,'claim_copied_or_rewritten':False,'admission_called':False,'numerical_execution':False}
with (HERE/'RELOCATION_SUPPLEMENT02.json').open('x') as out:json.dump(result,out,sort_keys=True,indent=2);out.write('\n')
print(json.dumps({'checks':len(checks),'decision':result['decision']}))
