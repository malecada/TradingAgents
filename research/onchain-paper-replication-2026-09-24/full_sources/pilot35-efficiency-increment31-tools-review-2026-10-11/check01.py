"""Independent metadata/source checks only; no helper execution or Git."""
import ast,difflib,hashlib,json
from pathlib import Path
D=Path(__file__).resolve().parent;F=D.parent;R=F.parents[2];H=F/'real-data-pilot-full24-preparation-increment01-2026-10-09';N=H/'full35outcome31';B=H/'full35increment30';checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(ok,label):
 assert ok,label
 checks.append(label)
def literal(tree,name):
 return ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)))
m=N/'HELPERS_MANIFEST01.json';ck(sha(m)=='b37eb6ec7c50a3c09d815fe599864ffb5fe889dc398ceeae21c9e19366ece074','actual helper manifest pin')
manifest=json.loads(m.read_text())
for row in manifest['files']+manifest['baseline_helpers']:
 p=R/row['path'];ck(sha(p)==row['sha256'] and ('bytes' not in row or p.stat().st_size==row['bytes']),'authenticated '+p.name)
for stem in ('select','capture','recover'):ast.parse((N/(stem+'31.py')).read_text())
mapping=json.loads((N/'CAPTURE_RECOVERY_LITERAL_MAP01.json').read_text())
for base,changes in mapping.items():
 text=(N/base.replace('30.py','31.py')).read_text()
 for old,new in reversed(list(changes.items())):text=text.replace(new,old)
 ck(text==(B/base).read_text(),base+' literal inverse')
 ck(ast.dump(ast.parse(text))==ast.dump(ast.parse((B/base).read_text())),base+' AST inverse')
s=(N/'select31.py').read_text();b=(B/'select30.py').read_text();t=ast.parse(s)
ck(s[s.index('reused=[]'):s.index('selection = {')]==b[b.index('reused=[]'):b.index('selection = {')],'unchanged typed selection/reuse/kernel')
roster=json.loads((N/'PROSPECTIVE_ROSTER01.json').read_text());owned=literal(t,'owned');pins=literal(t,'main_source_pins');raw=literal(t,'raw_scope_states')
ck(owned==roster['public_roots'] and len(owned)==18 and D.name in owned,'exact18 public roots including this review')
ck(literal(t,'prior_generated_names')==roster['prior_generated_files'] and len(roster['prior_generated_files'])==33,'exact33 predecessor receipts/raw names')
ck(literal(t,'helper_names')==tuple(roster['helper_names']),'exact helper roster')
ck(len(pins)==23 and set(literal(t,'main_source_names'))==set(pins),'exact23 engineering source/test roster')
snapshot=R/roster['source_snapshot']['path'];ck(sha(snapshot)==roster['source_snapshot']['sha256'],'actual source snapshot')
ck(pins=={r['path']:r['sha256'] for r in json.loads(snapshot.read_text())['files']},'snapshot-to-selector source equality')
ck(all(sha(R/p)==h for p,h in pins.items()),'current23 source hashes')
terminal=F/'pilot35-terminal-outcome-review-2026-10-11/REVIEW01.json';ck(sha(terminal)=='7224646b35c3fe8094c19288ad81be7c1650be458b7a3723198e82bc1a86aba4','actual independent terminal anchor')
ck(raw==json.loads(terminal.read_text())['incremental_raw_scopes'] and [x['exists'] for x in raw]==[True]*5+[False],'exact five failed35 roots/sixth absence')
prior=B/'FRESH_GIT_RECOVERY30.json';ck(sha(prior)=='32023dba761dbdcfc0fccd9bb9749a5320bdd345efa26a22411ca58be0f15d62','actual30 returned baseline')
ck(json.loads(prior.read_text())['source']=='dd0d8d4cda7bffa6e45629f00da5ce60412cbec1','exact baseline source')
ck(sha(F/'pilot35-preparation-increment-return-review01-2026-10-11/REVIEW01.json')=='170c85ab7eb08000467d7eeec098e1feb153ce8675b687d99f959728767dfbed','accepted30 return anchor')
ck("assert all(relative in allowed_files or relative in excluded or any((ROOT/relative).is_relative_to(root) for root in allowed_roots) for relative in names)" in s,'Git deltas confined before body selection')
ck("('full35-preparation-increment30.tar','fresh-git-recovered-full35increment30.tar','actual_external_archive_blob_return.stdout')" in s and "path.stat().st_size==prior_receipt['returned_archive']['bytes'] and sha(path)==prior_receipt['returned_archive']['sha256']" in s,'three aliases require actual hash/size at selection')
ck("assert not (HERE/'SELECTION31.json').exists()" in s and "generated full35outcome31 products are outside selection" in s,'one-use selection/generated output refusal')
ck(not any((N/n).exists() for n in ('SELECTION31.json','CAPTURE31.json','FRESH_GIT_RECOVERY31.json','GIT_OPERATIONS31.json')),'no actual helper outputs at review')
result={'status':'PASS_SOURCE_ONLY_CONDITIONAL_ON_ROOT_SCOPE_FREEZE','checks':checks,'scope_counts':{'public_roots':18,'source_tests':23,'prior_generated_names':33,'present_raw_scopes':5,'absent_raw_scopes':1},'helper_executed':False,'raw_traversed':False,'archive_aliases_read':False,'git_or_network':False}
(D/'CHECK01.json').write_text(json.dumps(result,indent=2)+'\n');print(len(checks),'checks passed')
