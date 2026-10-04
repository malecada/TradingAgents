from pathlib import Path
import json,hashlib,sys,os,copy,stat
D=Path(__file__).resolve().parent;F=D.parent;C=F/'financial-wrapper-complete100-baseline-capture01-2026-10-04';Q=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-final-contract-20261004-01/REQUEST_CANDIDATE01.json');q=json.loads(Q.read_bytes());P=Path(q['parent_root']);S=Path(q['capsule_root']);sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ok(v,n):assert v,n;checks.append(n)
ok(sha(Q.read_bytes())=='fa87b0875c79035c9f36fc637706cbdeaa2d392a146c6046b0196bf5ab4097b8','actual candidate pin')
ok(sha((P/'parent01.py').read_bytes())==q['caller_sha256']=='7f28cee688b661584e57466838ecdb79f0e17aa52be7d6f2c04f374326de9fb3','actual caller')
for n,h in q['helper_hashes'].items():ok(sha((P/n).read_bytes())==h,'helper '+n)
sys.path.insert(0,str(P));import parent01 as parent
ok(parent.R.scan(P)==json.loads((C/'PARENT_MANIFEST01.json').read_bytes()),'whole original nine Parent unchanged')
ok(parent.contract(q)=='6da30ea89cdf08a90de914fabdbc0616a4832cdbfaa363dec286ae43ff7751e4','actual full recovery bound before contract')
try:parent.validate_release(q)
except ValueError as e:ok('unresolved release field final_review'in str(e),'actual null candidate refused');(D/'NULL_REFUSAL01.txt').write_text(str(e)+'\n')
else:raise AssertionError('null accepted')
proofs={}
for role,ref in q['proofs'].items():
 b=parent.reference(ref);proofs[role]=sha(b);(D/(role.upper()+'_PROOF01.json')).write_bytes(b)
full=json.loads(parent.reference(q['proofs']['full_recovery']));ok(full['actual_baseline_full_recovery']is True and full['original_git_objects']==385 and full['original_regular_bodies']==863 and full['source']==q['source']and full['final_request_or_release_recovered']is False,'genuine full baseline proof excludes final supplement')
review=Path(q['proofs']['full_recovery']['path']).parent
for row in json.loads((review/'MANIFEST01.json').read_bytes())['members']:
 if row['kind']=='file':ok(sha((review/row['path']).read_bytes())==row['sha256'],'actual full recovery review member '+row['path'])
gate=json.loads((S/q['registration']).read_bytes());e=gate['experiments'][q['identity']];ok(sha((S/q['registration']).read_bytes())==q['registration_sha256'],'current gate')
ok(e['source_files']==q['source_files']and len(q['source_files'])==338,'exact338 source pins')
for n,h in q['source_files'].items():ok(sha((S/n).read_bytes())==h,'current source '+n)
for n,ref in e['inputs'].items():ok(sha((S/ref['path']).read_bytes())==ref['sha256']==q['input_hashes'][n],'actual input '+n)
for name,ref in [('charter',e['charter']),*e['cumulative_budget_extension'].items()]:ok(sha((S/ref['path']).read_bytes())==ref['sha256'],'genuine budget '+name)
plan=json.loads((S/e['inputs']['wrapper_plan']['path']).read_bytes());train=json.loads((S/e['inputs']['training']['path']).read_bytes());job=json.loads((S/e['inputs']['execution_job']['path']).read_bytes());ok(plan['prior_input']is None and plan['reference_input']is None and plan['phase']=='complete100'and plan['execution']=='eager'and train['epochs']==100,'independent original100epoch plan')
r=job['resources'];ok(r['wall_seconds']==1800 and r['memory_max_bytes']==r['memory_high_bytes']==3*1024**3 and r['disk_floor_bytes']==10*1024**3 and r['native_unit_limits']['file_size_bytes']==4*1024**2,'fixed native resource policy metadata')
runtime=json.loads((S/e['inputs']['runtime_mapping']['path']).read_bytes());ok(runtime==q['runtime_mapping']and len(runtime['distribution_records'])==251,'complete251 runtime metadata')
for row in runtime['distribution_records']:
 p=Path(row['record']);ok(p.stat().st_size<=4*1024**2 and sha(p.read_bytes())==row['record_sha256'],'current RECORD '+row['name'])
ad=json.loads(parent.reference(q['proofs']['independent_source_input_runtime']));ok(ad['source']==ad['design_source']==q['source']and ad['effective_attempt_budget']==19 and ad['actual_spent_claims']==2,'genuine exact prior readonly admission')
claims=list((S/'research_runs').glob('*/claim.json'));ok(len(claims)==2,'onlytwo genuine claims')
for p in claims:
 f=json.loads((p.parent/'failed.json').read_bytes());ok(f['status']=='failed'and f['claim_sha256']==sha(p.read_bytes())and not(p.parent/'complete.json').exists(),'permanent failed '+p.parent.name)
for p in (P/'attempt',S/'research_runs'/q['identity'],S/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/q['identity']):ok(not os.path.lexists(p),'actual unreserved directory '+str(p))
release={'schema_version':1,'decision':'accepted-exact-one-use-financial-parent','contract_sha256':parent.contract(q),'proof_sha256':proofs,'identity':q['identity'],'source':q['source'],'caller_sha256':q['caller_sha256']}
(D/'RELEASE01.json').write_text(json.dumps(release,indent=2,sort_keys=True)+'\n');bound=copy.deepcopy(q);bound['final_review']={'path':str(D/'RELEASE01.json'),'sha256':sha((D/'RELEASE01.json').read_bytes())};ok(parent.validate_release(bound)==release,'actual validator accepts genuine independent release')
for key,value in [('source','0'*40),('identity','old-spent'),('status','DRAFT_NOT_RELEASED')]:
 x=copy.deepcopy(bound);x[key]=value
 try:parent.validate_release(x)
 except ValueError:checks.append('refused mutation '+key)
 else:raise AssertionError(key)
ok(not any(n in sys.modules for n in ('numpy','torch','scipy','pandas')),'no numerical imports');ok(parent.R.scan(P)==json.loads((C/'PARENT_MANIFEST01.json').read_bytes()),'Parent unchanged after validator')
(D/'READBACK01.json').write_text(json.dumps({'checks':len(checks),'checks_detail':checks,'candidate_sha256':sha(Q.read_bytes()),'release_sha256':sha((D/'RELEASE01.json').read_bytes()),'actual_validate_release_calls':5,'preflight_or_admission_or_start_called':False,'final_supplement_recovery_pending':True},indent=2,sort_keys=True)+'\n');print(json.dumps({'checks':len(checks)}))
