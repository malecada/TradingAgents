import ast,copy,hashlib,json,os,shutil,stat,sys
from pathlib import Path
import recipe01 as R
D=Path(__file__).resolve().parent;checks=[]
def check(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def refuse(n,fn):
 try:fn()
 except (ValueError,OSError,KeyError):checks.append(n);return
 raise AssertionError(n)
base=json.loads((D/'BASELINE01.json').read_bytes());final=json.loads((D/'CLOSURE01.json').read_bytes());target='/home/malecada/master_thesis/onchain-treatment-isolation/paper-treatment-source-20261004-01/source';roles={k:None for k in R.ROLE_NAMES}
plan=R.prepare(target,roles);check('complete concrete source-copy plan',len(plan['copy'])==138 and plan['authority'] is None and plan['future_source_commit'] is None)
check('source count135 to138 not137',len(base['sources'])==135 and len(final['sources'])==138 and len(final['producer_static_pins'])==137)
for record in plan['copy']:
 path=Path(record['from']);raw=R.bounded(path);check('exact final source/hash/OID/mode '+record['relative'],R.sha(raw)==record['sha256'] and R.blob(raw)==record['git_blob_oid'] and len(raw)==record['bytes'] and stat.S_IMODE(path.stat().st_mode)==record['mode'])
for p in ['/',str(R.MAIN),str(R.MAIN.parent),str(R.PARENT),str(R.PARENT/'unit'),str(R.PARENT/'unit/source/child'),str(R.PARENT/'../elsewhere/unit/source'),'/home/malecada/master_thesis/onchain-financial-isolation/new-unit/source','relative/unit/source',target+'/',target.replace('paper-treatment-source-20261004-01','UPPER')]:refuse('unsafe/out-of-scope target '+p,lambda p=p:R.target_path(p))
for mutant in [{},{**roles,'unknown':None},{k:v for k,v in roles.items() if k!='registration'},{**roles,'historical_cohort_policy':'current-cohort'},{**roles,'registration':{'status':'accepted'}}]:refuse('role mismatch '+str(len(mutant)),lambda mutant=mutant:R.role_map(mutant))
refuse('release without genuine evidence refuses',lambda:R.release(plan))
for field,value in [('sha256','0'*64),('bytes',0),('mode',0o777),('git_blob_oid','0'*40),('git_mode','100755')]:
 wrong=copy.deepcopy(final['sources']);rel=next(iter(wrong));wrong[rel][field]=value;refuse('candidate source mismatch '+field,lambda wrong=wrong:R.verify_source(D/'candidate',wrong))
for mutation in ('missing','extra'):
 wrong=copy.deepcopy(final['sources'])
 if mutation=='missing':wrong.pop(next(iter(wrong)))
 else:wrong['tradingagents/research/onchain_replication/extra.py']=next(iter(wrong.values()))
 refuse('source role closure '+mutation,lambda wrong=wrong:R.verify_source(D/'candidate',wrong))
# Evaluate only original source-enumeration function, no package imports.
job=D/'candidate/tradingagents/research/onchain_replication/job.py';tree=ast.parse(job.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='required_sources');ns={'Path':Path,'__file__':str(job)};exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual-required-sources-AST','exec'),ns);check('actual job required_sources exact138',ns['required_sources']()==set(final['sources']))
module=D/'candidate'/final['producer_dynamic_self_path'];tree=ast.parse(module.read_text());assignment=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PRODUCER_SOURCE_PINS' for t in n.targets));actualpins=ast.literal_eval(assignment.value)
check('actual source static pins exact137',actualpins==final['producer_static_pins'] and final['producer_dynamic_self_path'] not in actualpins)
check('dynamic admitted-self source closes138 without hash cycle',{**actualpins,final['producer_dynamic_self_path']:R.sha(module.read_bytes())}=={rel:r['sha256'] for rel,r in final['sources'].items()})
inv=json.loads((D/'COMPOSITION_INVERSE01.json').read_text());s=module.read_text()
for e in reversed(inv['edits']):check('exact inverse substitution',s.count(e['new'])==1);s=s.replace(e['new'],e['old'])
check('full consumer byte inverse',R.sha(s.encode())==inv['origin_sha256']);check('full consumer AST inverse',ast.dump(ast.parse(s))==ast.dump(ast.parse(Path(inv['origin']).read_bytes())))
# Every original source outside four reviewed modifications is unchanged.
changed={r['path'] for r in json.loads((D/'ADOPTION_DELTAS01.json').read_text())}
for rel,pin in base['sources'].items():
 if rel not in changed:check('original source/model/filter unchanged '+rel,final['sources'][rel]==pin)
for rel in ('tradingagents/research/onchain_replication/subsets.py','tradingagents/research/onchain_replication/btc_subsets.py','tradingagents/research/onchain_replication/model.py','tradingagents/research/onchain_replication/calendar.py'):
 check('original method exact bytes '+rel,(D/'baseline'/rel).read_bytes()==(D/'candidate'/rel).read_bytes())
check('fund still explicitly refused',"raise ValueError('UNADMITTED: exact historical cohort and known_at policy independent admission required')" in module.read_text())
check('only source pins and self join altered',len(inv['edits'])==3)
check('no numerical module imported',not any(k in sys.modules for k in ('numpy','torch','scipy')))
(D/'CHECKS01.json').write_text(json.dumps({'count':len(checks),'checks':checks,'scope':'source-body/mode/OID maps and exact AST metadata only; no Run/Owner/claim'},indent=2)+'\n');print(len(checks),'passed')
