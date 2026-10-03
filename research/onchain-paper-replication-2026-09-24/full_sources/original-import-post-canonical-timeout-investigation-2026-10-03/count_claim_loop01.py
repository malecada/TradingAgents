"""Execute only actual verify_claim source loop on scalar synthetic blob stubs.

No genuine claim is verified/admitted; no subprocess, numerical module or data.
"""
import ast,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3]
BASE=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/original-import-native-successor-preparation06-2026-10-03';C=BASE/'capsule04'
ret=json.loads((BASE/'RETAINED_PRIMARY01.json').read_bytes());members={r['path']:r for r in ret['members']}
source=C/'tradingagents/research/verify.py';raw=source.read_bytes();tree=ast.parse(raw)
f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='verify_claim')
loop=next(n for n in f.body if isinstance(n,ast.For) and ast.unparse(n.target)=='(path, expected)')
code=compile(ast.Module(body=[loop],type_ignores=[]),'actual-verify-claim-loop','exec')
rows=[];body=b'synthetic source bytes';digest=hashlib.sha256(body).hexdigest();total=0
for path in sorted((C/'research_runs').glob('*/claim.json')):
 relative=str(path.relative_to(C));b=path.read_bytes();assert hashlib.sha256(b).hexdigest()==members[relative]['sha256'];claim=json.loads(b)
 pinned=dict(claim['experiment']['source_files'])
 for key in ('charter','selection'):
  if claim['experiment'].get(key):pinned[claim['experiment'][key]['path']]=claim['experiment'][key]['sha256']
 invocations=[]
 def blob(root,commit,path):invocations.append((commit,path));return body
 ns={'pinned':{p:digest for p in pinned},'claim':{'source':claim['source'],'design_source':claim['design_source']},'root':Path('/not-used'),'_blob':blob,'hashlib':hashlib}
 exec(code,ns);expected=len(pinned)*len({claim['source'],claim['design_source']});assert len(invocations)==expected
 initial=len(invocations)
 for _ in range(7):exec(code,ns)
 assert len(invocations)==8*expected
 rows.append({'identity':path.parent.name,'claim_sha256':hashlib.sha256(b).hexdigest(),'pinned_members':len(pinned),'unique_source_design_commits':len({claim['source'],claim['design_source']}),'source_loop_calls_per_verify_claim':initial,'source_loop_calls_eight_times':len(invocations)})
 total+=initial
assert total==634
result={'schema_version':1,'verify_source_sha256':hashlib.sha256(raw).hexdigest(),'loop_line':loop.lineno,'claims':rows,'source_loop_calls_per_claims_scan':total,'source_loop_calls_per_eight_scans':total*8,'qualification':'Actual extracted loop executes on synthetic constant byte stubs and authenticated retained metadata key cardinality. No real claim admission/Git subprocess/data; no wall share or speed estimate.'}
(P/'claim-loop-count01.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
