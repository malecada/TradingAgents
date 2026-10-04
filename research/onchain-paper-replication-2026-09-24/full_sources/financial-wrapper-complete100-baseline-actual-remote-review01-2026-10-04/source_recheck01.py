from pathlib import Path
import hashlib,json,os,stat
D=Path(__file__).resolve().parent;F=D.parent;C=F/'financial-wrapper-complete100-baseline-capture01-2026-10-04';cap=json.loads((C/'CAPTURE01.json').read_bytes());S=Path(cap['scopes']['capsule']['origin']);B=C/'capsule-snapshot';P=C/'parent-snapshot';support=C/'support-snapshot';sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ok(v,n):assert v,n;checks.append(n)
draft=json.loads((P/'REQUEST_DRAFT01.json').read_bytes());gate=json.loads((B/draft['registration']).read_bytes());entries=gate['experiments'];e=next(v for v in entries if v['id']==draft['identity'])if isinstance(entries,list)else entries[draft['identity']]
ok(sha((B/draft['registration']).read_bytes())==draft['registration_sha256']=='752c34dfad4df2ca36b5dc4dcb999846f8de01bd1a61c5356092c4e55fbd678c','exact current752c gate')
ok(e['source_files']==draft['source_files']and len(e['inputs'])==8,'exact registered338/eight roles')
for n,r in e['inputs'].items():ok(sha((B/r['path']).read_bytes())==r['sha256']==draft['input_hashes'][n],'input metadata body '+n)
runtime=json.loads((B/e['inputs']['runtime_mapping']['path']).read_bytes());ok(runtime==draft['runtime_mapping']and len(runtime['distribution_records'])==251,'complete251 RECORD mapping equality')
closure=json.loads((B/e['inputs']['source_closure']['path']).read_bytes());ok(len(closure['installed'])==194 and sum(k.startswith('tradingagents/')for k in closure['installed'])==149,'actual unchanged194implementation149package')
for name,pin in closure['installed'].items():ok(sha((B/name).read_bytes())==pin,'implementation pin '+name)
admission=support/'financial-wrapper-complete100-reference-adoption-review01-2026-10-04/ACTUAL_ADMISSION01.json';ad=json.loads(admission.read_bytes());ok(sha(admission.read_bytes())==draft['proofs']['independent_source_input_runtime']['sha256']=='6a3b48b546ccbd10e1176cc1b5b06f0143934766778761655fdc2a22d60b4473','genuine actual previous readonly admission bytes');ok(ad['source']==ad['design_source']==cap['source']and ad['ready']is True and ad['effective_attempt_budget']==19 and ad['actual_spent_claims']==2,'previous metadata admission scope')
claims=list((B/'research_runs').glob('*/claim.json'));ok(len(claims)==2,'both FAILED claims preserved')
for p in claims:
 f=json.loads((p.parent/'failed.json').read_bytes());ok(f['status']=='failed'and f['claim_sha256']==sha(p.read_bytes())and not(p.parent/'complete.json').exists(),'original failed binding '+p.parent.name)
for base in ('research_runs','research_artifacts/onchain-paper-replication-2026-09-24/runs'):ok(not os.path.lexists(S/base/draft['identity']),'unused complete100 namespace '+base)
ok(not os.path.lexists(Path(cap['scopes']['parent']['origin'])/'attempt'),'new Parent has noattempt')
mode_rows=[]
for p in sorted((support/'root-receipts').iterdir()):
 original=F/'heartbeat-root-checkpoint10-2026-10-04'/p.name;mode_rows.append({'name':p.name,'original':str(original),'snapshot':str(p),'original_mode':stat.S_IMODE(original.stat().st_mode),'snapshot_archive_mode':stat.S_IMODE(p.stat().st_mode),'sha256':sha(p.read_bytes()),'bytes':len(p.read_bytes())})
(D/'MODE_FINDING01.json').write_text(json.dumps({'finding':'seven actual Root receipt copies retain exact bytes but explicitly map0664→0600; original POSIX permissions not reproduced for these seven files','rows':mode_rows,'initial_trace':'CHECK01.err','original_capture_untouched':True},indent=2,sort_keys=True)+'\n')
(D/'READBACK03.json').write_text(json.dumps({'checks':len(checks),'checks_detail':checks,'mode_finding_sha256':sha((D/'MODE_FINDING01.json').read_bytes()),'genuine_new_admission_called':False,'new_claim':False,'installed_runtime_bodies_recovered':False,'original_NULL_final_review':draft['final_review'],'original_NULL_full_recovery':draft['proofs']['full_recovery']},indent=2,sort_keys=True)+'\n');print(json.dumps({'checks':len(checks)}))
