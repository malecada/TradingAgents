"""Offline source-only assembly; no capsule, Git, registration or package imports."""
import ast,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];FULL=HERE.parent
BASE=FULL/'original-import-native-successor-preparation03-2026-10-03'
SCIENCE=FULL/'neural-cold-feature-handoff-proof-preparation01-2026-10-03'
OUTER=FULL/'neural-cold-feature-handoff-proof-outer-preparation02-2026-10-03'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path,pin=None):
 raw=path.read_bytes()
 if len(raw)>4194304 or pin is not None and sha(raw)!=pin:raise ValueError('source pin/extent differs')
 return raw
def table():
 read(SCIENCE/'MANIFEST01.json','2c78e0a8ca2c31cf41d6f5bb8ccfc6522ed9ac40b9f94437fd953c2b9b7fe620')
 read(OUTER/'MANIFEST02.json','c12ab32ac887bfb73a4db23971a7f1d1d1cc4fea459e5f78a5e829d9fe7074c8')
 base=json.loads(read(BASE/'source_inventory01.json'));rows={r['target']:dict(r) for r in base['source_inventory']}
 if len(rows)!=153 or sum(n.startswith('tradingagents/') for n in rows)!=142:raise ValueError('original package closure differs')
 if rows['tradingagents/research/onchain_replication/compact_mcm.py']['sha256']!='08150fb38943717d7f173c30b6dda12c494d8663654670c6b8cd865df1dd3caf':raise ValueError('metadata02/cleanup03 composition differs')
 replacements=[]
 for selected,key in [(json.loads(read(SCIENCE/'install-map01.json'))['files'],'source'),(json.loads(read(OUTER/'install-map02.json'))['files'],'origin')]:
  for item in selected:
   raw=read(ROOT/item[key],item['sha256']);target=item['target']
   if len(raw)!=item['bytes']:raise ValueError('overlay extent differs')
   prior=rows.get(target);rows[target]={'target':target,'origin':item[key],'sha256':sha(raw),'bytes':len(raw),'git_commit':None,'git_path':None}
   replacements.append({'target':target,'prior':prior,'selected':rows[target]})
 for target,row in sorted(rows.items()):
  if target.startswith('/') or '..' in Path(target).parts:raise ValueError('source target escaped')
  raw=read(ROOT/row['origin'],row['sha256'])
  if len(raw)!=row['bytes']:raise ValueError('base extent differs')
  if target.endswith('.py'):ast.parse(raw)
 return rows,replacements

def main():
 rows,changes=table();snapshot=HERE/'source-bodies';snapshot.mkdir(exist_ok=False)
 out=[]
 for target,row in sorted(rows.items()):
  path=snapshot/target;path.parent.mkdir(parents=True,exist_ok=True)
  with path.open('xb') as f:f.write(read(ROOT/row['origin'],row['sha256']))
  out.append(dict(row,snapshot=str(path.relative_to(ROOT))))
 result={'schema_version':1,'status':'source-only-not-capsule-not-released','source_inventory':out,'source_count':len(out),'package_count':sum(r['target'].startswith('tradingagents/') for r in out),'logical_bytes':sum(r['bytes'] for r in out),'base':{'path':str((BASE/'source_inventory01.json').relative_to(ROOT)),'sha256':sha(read(BASE/'source_inventory01.json'))},'changes':changes,'execution_admitted':False}
 with (HERE/'source_inventory01.json').open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
 print(json.dumps({'source_count':result['source_count'],'package_count':result['package_count'],'logical_bytes':result['logical_bytes'],'changed_or_added':len(changes)}))
if __name__=='__main__':main()
