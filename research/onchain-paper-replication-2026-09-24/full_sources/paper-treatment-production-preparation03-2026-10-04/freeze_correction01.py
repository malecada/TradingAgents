import ast,hashlib,json,stat
from pathlib import Path
B=Path(__file__).resolve().parent;P=B.parent/'paper-treatment-production-preparation01-2026-10-04';R=B.parent/'paper-treatment-production-review01-2026-10-04'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,obj):(B/name).write_text(json.dumps(obj,sort_keys=True,indent=2)+'\n')
changed={'overlay/tradingagents/research/onchain_replication/job.py','overlay/tradingagents/research/onchain_replication/treatment_production.py'}
unchanged=[]
for p in sorted(P.rglob('*')):
 if p.is_file():
  rel=p.relative_to(P).as_posix()
  if rel not in changed:assert p.read_bytes()==(B/rel).read_bytes();unchanged.append({'path':rel,'sha256':sha(p)})
for p in sorted(R.rglob('*')):
 if p.is_file():assert p.read_bytes()==(B/'prior-review01'/p.relative_to(R)).read_bytes()
for p in (B/'overlay').rglob('*.py'):ast.parse(p.read_text())
changes=[{'path':rel,'prior_sha256':sha(P/rel),'candidate_sha256':sha(B/rel)} for rel in sorted(changed)]
checks=json.loads((B/'CORRECTION_CHECKS02.json').read_text());pairs=json.loads((B/'CLEANUP_PAIRS04.json').read_text())
write('CORRECTION_PROTOCOL01.json',{'schema_version':1,'status':'uninstalled-correction-candidate-awaiting-independent-review','authority':{'installed_source':None,'gate':None,'claim':None,'native_execution':None,'financial_capacity':None,'paper_credit':0},'prior_preparation_manifest':{'path':str(P/'MANIFEST02.json'),'sha256':sha(P/'MANIFEST02.json')},'prior_withheld_review_manifest':{'path':str(R/'MANIFEST01.json'),'sha256':sha(R/'MANIFEST01.json')} if (R/'MANIFEST01.json').exists() else None,'changed_sources':changes,'unchanged_inherited_bodies':unchanged,'source_role_count':{'historical_main_package':135,'two_new_module_prospective_package':137,'qualification':'inherited recipe counts; no new Source registration or current-source closure assertion'},'corrections':{'T1':'original owner/death/claim checks still precede metadata-only recovery; exact resolved claim inputs, source files, complete plan denominator, intent ancestry, row identity, output namespace and parent/coverage/cohort receipt joins; merge before unavailable fallback; duplicate other-namespace rows refused','T2':'independent per-missing-cell attempts; summary and audit attempted after each error; exact unconfirmed cells, attempted count and publication error classes; earliest MemoryError/non-Exception fatal wins, otherwise earliest ordinary; original actual secondary errors attached best effort; no fabricated row after failed writer'},'tests':{'check02':checks['checks'],'cleanup_pairs04':pairs['checks'],'superseded_harnesses_retained':['check_correction01 wrongly classified timestamp str.replace as filesystem mutation; failed output retained','check_cleanup_pairs03 had a vacuous extra assertion; check04 replaces it with actual secondary error identity equality; 03 is not counted as independent additional checks']},'limitations':['No ResearchRun, Owner, real claim, registration, gate, native creation or numerical import/execution','Opaque metadata-complete fixture tests disposition plumbing, not a valid graph or empirical output','Observer deliberately does not decode or validate graph arrays/components; downstream mandatory fit admission remains separate','No allocation-exhaustion, arbitrary process race, filesystem atomicity or callback-call-count equivalence claim','If final audit publication also fails, no audit body is fabricated; actual exception remains propagated/attached best effort','Absent outputs stay unavailable; original failing claim cannot become successful through retained cells','Live integration, final source closure, budgets, protected paths, registration, capacity and external recovery remain Root-owned and withheld']})
protocol=sha(B/'CORRECTION_PROTOCOL01.json')
report=f'''# Treatment production correction02 — uninstalled source candidate

T1 and T2 are corrected in two overlay bodies only. The producer01 and its WITHHELD review remain intact, including the original witnesses and both earlier harness failures. The exact producer and job byte/AST inverse is in CORRECTION_INVERSE02.json; the inherited four job substitutions invert separately to Main baseline d41518c7. Contract, filters, native resources, admission and lifecycle source are unchanged.

The job reconciliation block calls metadata-only treatment recovery after the existing genuine owner, cgroup-death and claim checks and before postmortem missing-cell fallback. Recovery uses claim['inputs'], preserving actual resolved late bindings. It authenticates current two-module source pins, the registered execution job and full plan denominator, original intent, cell identity, output namespace, receipt and coverage hashes and their source/claim/plan/parent/cohort joins. A durable complete row stays complete in the postmortem denominator after a later worker failure. The overall claim remains failed. Duplicate namespace dispositions are refused.

Pending finalization attempts every missing row independently, then summary and audit independently. Successful rows enter the in-memory map only after the immutable writer returns. The audit names attempted and unconfirmed cells and writer/summary error classes. A write that published bytes but failed during sync remains unconfirmed to the producer; later authenticated observation can recover its actual bytes. No unavailable row is invented when writing fails. Earliest fatal exception (MemoryError or non-Exception BaseException) is retained; absent a fatal, earliest ordinary error is retained. Secondary actual exception objects are attached best effort without str/repr/add_note calls. Failed attachment cannot replace the selected error.

check_correction02 passed {checks['checks']} checks, including original RED pending-loop and missing-treatment-route witnesses, exact observer block plumbing, three writer indexes, primary/error matrices and metadata mutation refusals. check_cleanup_pairs04 passed {pairs['checks']} additional checks over 240 two-index error cases and actual extracted immutable publication on owned opaque files, including post-link sync failure and cause-attachment rejection. Check01's false positive on timestamp str.replace and check03's vacuous extra assertion are preserved and superseded; they are not hidden or counted as extra independent evidence.

These are stdlib source/opaque utility controls. No genuine ResearchRun/Owner/native lifecycle, graph arrays, financial outcomes, downstream fit admission or numerical capacity was exercised. Recovery preserves authenticated disposition metadata; it is not graph representation or numerical validation. Publication can remain impossible when its writer fails; audit failure propagates and no receipt is fabricated. Allocation exhaustion and process/filesystem race equivalence are not claimed. Final Source, gate, charter, registration, cumulative allowance, runtime capacity and external recovery remain withheld pending separate Root integration and different-author review.

Protocol SHA256: {protocol}.
'''
(B/'CORRECTION_IMPLEMENTATION01.md').write_text(report)
entries=[]
for p in sorted(B.rglob('*')):
 rel=p.relative_to(B).as_posix()
 if rel=='MANIFEST03.json':continue
 s=p.lstat();kind='directory' if stat.S_ISDIR(s.st_mode) else 'file' if stat.S_ISREG(s.st_mode) else 'other';assert kind!='other'
 entry={'path':rel,'type':kind,'mode':stat.S_IMODE(s.st_mode)}
 if kind=='file':entry.update(bytes=s.st_size,sha256=sha(p))
 entries.append(entry)
write('MANIFEST03.json',{'schema_version':1,'kind':'complete-typed-source-only-correction-manifest','root':str(B),'self_excluded':'MANIFEST03.json','entries':entries,'member_count':len(entries),'regular_file_count':sum(e['type']=='file' for e in entries),'regular_bytes':sum(e.get('bytes',0) for e in entries)})
print(json.dumps({'changes':changes,'protocol_sha256':protocol,'report_sha256':sha(B/'CORRECTION_IMPLEMENTATION01.md'),'manifest_sha256':sha(B/'MANIFEST03.json'),'members':len(entries),'files':sum(e['type']=='file' for e in entries),'checks02':checks['checks'],'pairs04':pairs['checks']},indent=2))
