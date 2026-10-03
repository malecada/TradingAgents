"""Source snapshot only; no runtime/capsule/Git/registration or scientific imports."""
import json
from pathlib import Path
from discover_source01 import discover,sha,HERE,ROOT,OLD
from source_symbols01 import Symbols

def main():
 rows,graph,dynamic=discover();w=Symbols(rows);required=w.module('tradingagents/research/onchain_replication/compact_native_producer.py').required_sources()
 if not required<=set(rows):raise ValueError('actual required_sources outside closure')
 snapshot=HERE/'source-bodies';snapshot.mkdir(exist_ok=False);out=[]
 for target,row in sorted(rows.items()):
  raw=(ROOT/row['origin']).read_bytes();assert len(raw)==row['bytes'] and sha(raw)==row['sha256']
  path=snapshot/target;path.parent.mkdir(parents=True,exist_ok=True)
  with path.open('xb') as f:f.write(raw)
  out.append(dict(row,snapshot=str(path.relative_to(ROOT))))
 inventory={'schema_version':1,'status':'source-only-not-capsule-not-released','source_inventory':out,'source_count':len(out),'package_count':sum(n.startswith('tradingagents/') for n in rows),'logical_bytes':sum(r['bytes'] for r in out),'predecessor':{'path':str((OLD/'source_inventory01.json').relative_to(ROOT)),'sha256':sha((OLD/'source_inventory01.json').read_bytes())},'execution_admitted':False}
 (HERE/'source_inventory02.json').write_text(json.dumps(inventory,indent=2,sort_keys=True)+'\n')
 evidence={'schema_version':1,'status':'source-AST-only-no-authority','actual_required_sources':sorted(required),'required_source_function_bodies':w.functions,'native_and_transitive_source_graph':graph,'dynamic_loader_sites':dynamic,'unresolved_generic_loader_expressions_do_not_grant_authority':True}
 (HERE/'SOURCE_GRAPH02.json').write_text(json.dumps(evidence,indent=2,sort_keys=True)+'\n')
 print(json.dumps({k:inventory[k] for k in ('source_count','package_count','logical_bytes')}))
if __name__=='__main__':main()
