from pathlib import Path
import ast,hashlib,json,os,stat,copy
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';A=F/'financial-wrapper-compatibility-operational-delta-tooling01-2026-10-04';W=F/'financial-wrapper-operational-forensic-watch-correction04-2026-10-04';V=F/'financial-wrapper-operational-forensic-watch-review04-2026-10-04';T=F/'financial-wrapper-compatibility-operational-delta-flat-successor02-2026-10-04';N=F/'financial-wrapper-compatibility-operational-delta-remote-successor02-2026-10-04';N.mkdir(mode=0o700);sha=lambda b:hashlib.sha256(b).hexdigest()
def put(n,v):(N/n).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
assert sha((W/'watch01.py').read_bytes())=='bdeacaadc053e615245b3e2175089842708719448ec7da970d981e5dc077ca18'
assert sha((V/'MACHINE01.json').read_bytes())=='aed1248d003fbe19ccbd5f0f57b6801e6cf08713bb01d6d9fa56a145e172bb57'
assert sha((V/'MANIFEST01.json').read_bytes())=='7a94ef046588cb9a10a978d63865302e0b12a25e60db98190aea9927ecc59f47'
required=ast.literal_eval(next(n.value for n in ast.parse((T/'restore01.py').read_bytes()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='REQUIRED' for t in n.targets)))
assert len(required)==15 and sum(v['bytes'] for v in required.values())==507946
for p,v in required.items():assert (R/p).stat().st_size==v['bytes'] and sha((R/p).read_bytes())==v['sha256']
s=(A/'recover01.py').read_text();oldline=next(l for l in s.splitlines() if l.startswith('REQUIRED = '));edits=[(oldline,'REQUIRED = '+repr(required)),("rows=selection['rows'];require(type(rows) is list and 1<=len(rows)<=506, 'finite selected paths')","rows=selection['rows'];require(type(rows) is list and len(rows)==len(REQUIRED)==15, 'exact fifteen selected paths')"),("repo = HERE / 'fresh-operational-source-policy01.git'","repo = HERE / 'fresh-operational-source-policy02.git'"),("Exact frozen operational source/policy delta and genuine independent policy review bytes recovered.","Exact frozen operational source/policy delta, genuine independent policy review and complete closed failed forensic Root02 scope recovered.")]
for a,b in edits:assert s.count(a)==1;s=s.replace(a,b,1)
inverse=s
for a,b in reversed(edits):assert inverse.count(b)==1;inverse=inverse.replace(b,a,1)
assert inverse==(A/'recover01.py').read_text();compile(s,'recover01.py','exec');(N/'recover01.py').write_text(s);(N/'ORIGINAL_recover01.py').write_bytes((A/'recover01.py').read_bytes());(N/'watch01.py').write_bytes((W/'watch01.py').read_bytes());(N/'utilities').mkdir()
for n in ('owned_io.py','bounded_git01.py','recovery_pax01.py'):(N/'utilities'/n).write_bytes((A/'utilities'/n).read_bytes())
for n in ('MACHINE01.json','MANIFEST01.json','REPORT01.md'):(N/('WATCH_REVIEW_'+n)).write_bytes((V/n).read_bytes())
put('SOURCE_INVERSE01.json',{'original':sha((A/'recover01.py').read_bytes()),'source':sha(s.encode()),'complete_four_edit_literal_inverse':True,'edits':[{'old':a,'new':b} for a,b in edits],'all_other_functions_unchanged':True,'changed_function_names':['validate_fixed_selection','main'],'REQUIRED15':required,'byte_total':507946,'fixed_fresh_git_root':'fresh-operational-source-policy02.git','actual_root_selection':None,'entry_release':None,'watch_source_only_review':sha((V/'MACHINE01.json').read_bytes())})
print(json.dumps({'source':sha(s.encode()),'source_scope':str(N),'bytes':507946,'pins':15}))
