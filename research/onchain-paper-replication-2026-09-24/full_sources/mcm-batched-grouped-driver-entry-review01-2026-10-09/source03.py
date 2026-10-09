import ast,hashlib,json,re
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[3];F=H.parent;D=F/'mcm-batched-grouped-driver01-2026-10-09';E=F/'mcm-batched-pilot-entry-integration02-2026-10-09';S=R/'tradingagents/research/onchain_replication';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=json.loads((D/'MANIFEST01.json').read_text());e=json.loads((E/'MANIFEST01.json').read_text());pins={}
for n,v in d['sources'].items():assert sha(D/n)==v;pins[str((D/n).relative_to(R))]=v
for n,v in e['files'].items():assert sha(E/n)==v;pins[str((E/n).relative_to(R))]=v
for n,v in d['baseline'].items():assert sha(R/n)==v
for n,v in e['originals'].items():assert sha(S/n)==v
for n,v in d['inherited_group_evidence'].items():assert sha(R/n)==v
helper=F/'mcm-batched-owner-integration-review03-2026-10-09/source05.py';fn=next(n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='apply');ns={'re':re};exec(compile(ast.Module(body=[fn],type_ignores=[]),'hunk_inverse','exec'),ns)
patch=(D/'inverse.patch').read_text();first,second=patch.split('--- candidate/compact_mcm.py\n');assert ns['apply']((D/'compact_mcm_batched.py').read_text(),first)==(S/'compact_mcm_batched.py').read_text();assert ns['apply']((D/'compact_mcm.py').read_text(),'--- candidate/compact_mcm.py\n'+second)==(S/'compact_mcm.py').read_text()
a=(E/'real_pilot_reservations.py').read_text().replace("mcm['schema_version'] in (5,6)","mcm['schema_version']==5");assert a==(S/'real_pilot_reservations.py').read_text()
a=(E/'real_pilot_import_caller.py').read_text().replace("mcm['schema_version'] in (5,6)","mcm['schema_version']==5").replace('def _prepare_lease_modules(*, batched=False, grouped=False):','def _prepare_lease_modules(*, batched=False):').replace('        if grouped:\n            from . import grouped_offload, grouped_offload_semantics\n','').replace("            selected_mcm=_read(run.admission,s['compact_mcm_input'])\n            _prepare_lease_modules(batched=selected_mcm.get('schema_version') in (5,6),grouped=selected_mcm.get('schema_version')==6)","            _prepare_lease_modules(batched=_read(run.admission,s['compact_mcm_input']).get('schema_version')==5)");assert a==(S/'real_pilot_import_caller.py').read_text()
t=ast.parse((D/'compact_mcm_batched.py').read_text());fs={n.name:n for n in t.body if isinstance(n,ast.FunctionDef)};v=ast.unparse(fs['_verify_grouped']);required=["len(items) == count","token == expected","record['binding']['manifest_sha256']","complete['recovered_bytes'] == record['manifest']['archive_bytes']","anchors_hash.hexdigest() == external['group_anchors_sha256']","digest.hexdigest() == binding['tokens_sha256']","aggregate.hexdigest() == coverage['original_and_fresh_history_aggregate_sha256']"]
for predicate in required:assert predicate in v
assert v.count('_checkpoint_inventory(')==2
modules=ast.unparse(fs['_modules']);assert "if grouped:" in modules and "('grouped_offload', 'grouped_offload_semantics')" in modules
verify=ast.unparse(fs['verify_content']);assert verify.index('_verify_grouped(')<verify.index('_spool(')
caller=(E/'real_pilot_import_caller.py').read_text();assert caller.index('_prepare_lease_modules(batched=selected_mcm')<caller.index("activate(execution,p['imported_authority_lease_input'])")
out={'source_pins':pins,'driver_manifest_sha256':sha(D/'MANIFEST01.json'),'entry_manifest_sha256':sha(E/'MANIFEST01.json'),'exact_driver_and_caller_default_inverses':True,'grouped_closure_predicates':required,'inventory_before_and_after':True,'new_source_roles_before_lease':True,'grouped_source_review_reused':'305c1386047a8aae874a447e184f7cfdcecdda93f640425db72df90edd53b6b4'};(H/'SOURCE03.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
