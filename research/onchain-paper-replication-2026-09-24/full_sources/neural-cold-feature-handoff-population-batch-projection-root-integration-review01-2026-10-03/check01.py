"""Actual source integration readback only; active capsule outputs not inspected."""
import ast,hashlib,json,os,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;MAIN=HERE.parents[3];P=BASE/'neural-cold-feature-handoff-population-batch-projection-preparation01-2026-10-03';I=BASE/'neural-cold-feature-handoff-population-batch-projection-root-integration01-2026-10-03';CAP=Path('/home/malecada/master_thesis/onchain-fixture-isolation/neural-cold-proof-native-20261003-02/source')
def sha(b):return hashlib.sha256(b).hexdigest()
def doc(p):return json.loads(p.read_bytes())
record=doc(I/'INTEGRATION01.json');sources=doc(P/'source-readback01.json');assert record['preparation_manifest_sha256']==sha((P/'MANIFEST01.json').read_bytes()) and record['source_review_sha256']==sha((BASE/'neural-cold-feature-handoff-population-batch-projection-review01-2026-10-03/REVIEW_PROJECTION01.md').read_bytes())
for r in sources['install_map']:
 raw=(MAIN/r['target']).read_bytes();assert raw==(P/r['source']).read_bytes() and sha(raw)==r['sha256'] and len(raw)==r['bytes'];assert next(x for x in record['install_map'] if x['target']==r['target'])['sha256']==r['sha256']
# The accepted inverse recipe is stdlib-only and operates on frozen candidate bytes,
# now proved equal to the actual live bytes. It restores all baseline bytes and AST.
code=(P/'check_parity01.py').read_text();tree=ast.parse(code);assert all(not isinstance(n,ast.Import) or all(x.name in ('ast','hashlib') for x in n.names) for n in ast.walk(tree));exec(compile(tree,str(P/'check_parity01.py'),'exec'),{'__file__':str(P/'check_parity01.py'),'__name__':'__review_parity__'})
unchanged=[];baseline=[]
for r in sources['dependencies']:
 raw=(MAIN/r['path']).read_bytes()
 if r['path']=='tradingagents/research/onchain_replication/population_assembly.py':assert sha((P/'population_assembly.before.py').read_bytes())==r['sha256'];baseline.append(r['path'])
 else:assert sha(raw)==r['sha256'] and len(raw)==r['bytes'];unchanged.append(r['path'])
assert len(unchanged)==8 and len(baseline)==1
inv=doc(CAP/'cold_prep/source_inventory.json');assert len(inv['source_inventory'])==195
for r in inv['source_inventory']:assert sha((CAP/r['target']).read_bytes())==r['sha256']
assert sha((CAP/'tradingagents/research/onchain_replication/population_assembly.py').read_bytes())=='da65f5168c9d03cf8518f8dac1717482ff48c047ac451563f8728a7afe5c528f';assert not (CAP/'tradingagents/research/onchain_replication/population_batch_projection.py').exists()
changed=subprocess.check_output(['git','-c','protocol.allow=never','diff','--name-only','--','tradingagents'],cwd=MAIN,env={**os.environ,'GIT_OPTIONAL_LOCKS':'0','GIT_NO_LAZY_FETCH':'1'},timeout=10).decode().splitlines();assert changed==['tradingagents/research/onchain_replication/population_assembly.py']
out={'status':'ACCEPTED-exact-main-source-integration-only','integration_record_sha256':sha((I/'INTEGRATION01.json').read_bytes()),'live_targets':record['install_map'],'unchanged_dependency_count':8,'ninth_dependency':'original producer baseline preserved; live producer intentionally replaced by accepted candidate','inverse_full_baseline_bytes_AST':True,'active_capsule_source_count_unchanged':195,'active_capsule_new_helper_absent':True,'tracked_tradingagents_changes':changed,'genuine_schema2_producer_execution':False,'qualification':'Only source bytes and bounded Git diff inspected; active numerical process/outcomes not touched or certified.'}
(HERE/'readback01.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
