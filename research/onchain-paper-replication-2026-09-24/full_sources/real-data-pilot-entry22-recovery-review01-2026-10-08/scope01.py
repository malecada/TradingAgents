import hashlib,json
from pathlib import Path
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent/'real-data-pilot-entry22-increment01-2026-10-08';checks=[]
def ck(n,v):
 assert v,n
 checks.append(n)
def load(p):return json.loads(p.read_bytes())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
j=load(D/'TOOL_SOURCE_JOIN01.json')
for kind in ('capture','recovery'):
 b=j[kind+'_baseline'];c=j[kind+'_current'];ck(kind+'_pins',digest(R/b['path'])==b['sha256'] and digest(R/c['path'])==c['sha256']);text=(R/c['path']).read_text()
 for e in j[kind+'_literal_changes'].values():text=text.replace(e['after'],e['before'])
 ck(kind+'_exact_inverse',text==(R/b['path']).read_text())
s=load(D/'SELECTION_DRAFT01.json');cur=load(R/s['current_release']['path']);old=load(R/s['prior_release']['path'])
for role in ('current_release','prior_release'):ck(role+'_pin',digest(R/s[role]['path'])==s[role]['sha256'])
ck('release_cardinality',cur['source_count']==345 and cur['input_count']==60 and len(cur['evidence'])==521)
private=s['private_excluded'];ck('single_opaque',set(private)=={'path','sha256'} and cur['evidence'][private['path']]==private['sha256'])
expected=dict(cur['evidence']);del expected[private['path']];expected[s['current_release']['path']]=s['current_release']['sha256']
inherited={p:h for p,h in expected.items() if old['evidence'].get(p)==h};selected={p:h for p,h in expected.items() if old['evidence'].get(p)!=h}
ck('exact_inherited469',inherited==s['inherited'] and len(inherited)==469);ck('exact_changed52',selected==s['selection'] and len(selected)==52)
for p,h in selected.items():ck('selected_current_'+p,digest(R/p)==h)
ck('no_private_selected',private['path'] not in selected)
x={'decision':'accepted-tool-and-selection-scope-only','current_release':s['current_release'],'prior_release':s['prior_release'],'source_count':345,'input_count':60,'new_public_bodies':52,'inherited_identical_refs':469,'private_excluded_hash_only':private,'checks':checks,'qualification':'Exact finite old-tool literal inverses and selected current release delta checked. Actual typed selection/local capture/fresh return still required; no network or scientific/private body read and no final entry edits.'}
(H/'SCOPE_REVIEW01.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps({'decision':x['decision'],'sha256':digest(H/'SCOPE_REVIEW01.json')}))
