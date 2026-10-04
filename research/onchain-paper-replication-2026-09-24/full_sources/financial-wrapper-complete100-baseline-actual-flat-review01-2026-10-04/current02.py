from pathlib import Path
import json,os,stat,hashlib
D=Path(__file__).resolve().parent;T=D.parent/'financial-wrapper-complete100-baseline-remote01-2026-10-04';C=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-root-launch-20261004-01');sha=lambda b:hashlib.sha256(b).hexdigest();checks=[]
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def meta(label):return json.loads((T/('flat-'+label+'01')/'body-metadata.json').read_bytes())
def body(label,n):return (T/('flat-'+label+'01')/meta(label)['flat_members'][n]).read_bytes()
for label,root in [('capsule',C),('parent',P)]:
 m=meta(label);actual=set()
 for path,dirs,files in os.walk(root,followlinks=False):
  if Path(path)==root and '.git' in dirs:dirs.remove('.git')
  actual.update((Path(path)/n).relative_to(root).as_posix() for n in dirs+files)
 ok(actual=={x['path'] for x in m['manifest']['members']},'exact current whole '+label)
 for row in m['manifest']['members']:
  p=root/row['path'];s=p.lstat();ok(stat.S_IMODE(s.st_mode)==row['mode'],'current literal mode')
  if row['kind']=='file':ok(stat.S_ISREG(s.st_mode) and p.read_bytes()==body(label,row['path']),'complete current body')
  else:ok(stat.S_ISDIR(s.st_mode),'current directory')
q=json.loads(body('parent','REQUEST_DRAFT01.json'));g=json.loads(body('capsule',q['registration']));e=g['experiments'][q['identity']];cl=json.loads(body('capsule',e['inputs']['source_closure']['path']))['installed'];ok(len(cl)==194 and sum(n.startswith('tradingagents/') for n in cl)==149,'194149 implementation')
for name,pin in cl.items():ok(sha(body('capsule',name))==pin,'source closure')
claimnames=[n for n in meta('capsule')['flat_members'] if n.startswith('research_runs/') and n.endswith('/claim.json')];claims=[json.loads(body('capsule',n)) for n in claimnames];ok({sha(body('capsule',n)) for n in claimnames}=={'4c543d71fad5255be61087eaa3619d9e88cbbdc12fa1398bd7fa7fe6fb75c128','d390980c956aab64d5521698cbb6123ccf01ece94a95277b97755f019adf692b'},'actual two immutable failedclaims')
failed={sha(body('capsule',n.replace('/claim.json','/failed.json'))) for n in claimnames};ok(failed=={'35158c0ecebfe4dc75203ba87d5372f2f85643c0b5f828a99e17aa28fe79c450','4b2d7b0d162e80fe2074997baed35f2d6e6c86e5f660872fc2b8e97bb9622558'},'actual original failed markers')
# Declared effective budgets in genuine claims are inspected, no admission invoked.
ok(sorted(c['effective_attempt_budget'] for c in claims)==[18,19],'actual claim highest19')
support=meta('support');admission=[n for n in support['flat_members'] if sha(body('support',n))=='6a3b48b546ccbd10e1176cc1b5b06f0143934766778761655fdc2a22d60b4473'];ok(len(admission)>=1,'genuine admission6a3 recovered');ok(q['final_review'] is None and q['proofs']['full_recovery'] is None,'originaldraft null unchanged')
(D/'CURRENT02.json').write_text(json.dumps({'checks':len(checks),'names':checks,'admission_recovered_paths':admission,'actual_claims_spent':2,'highest_actual_budget':19,'complete_current_whole_trees_equal':True},indent=2)+'\n');print(json.dumps({'checks':len(checks)}))
