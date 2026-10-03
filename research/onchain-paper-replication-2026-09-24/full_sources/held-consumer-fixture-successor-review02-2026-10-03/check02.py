import ast,copy,hashlib,json,pathlib,runpy,unittest
H=pathlib.Path(__file__).resolve().parent;F=H.parent;R=H.parents[3];P=F/'neural-cold-feature-handoff-held-consumer-fixture-successor-preparation02-2026-10-03';OLD=F/'neural-cold-feature-handoff-held-consumer-fixture-successor-preparation01-2026-10-03'
def h(b):return hashlib.sha256(b).hexdigest()
assert h((P/'MANIFEST02.json').read_bytes())=='69c305b23a752db345d8703fc24b27b8030ab7a521538a7ba10a4358935ef20b'
man=json.loads((P/'MANIFEST02.json').read_bytes())
for r in man['files']:
 b=(P/r['path']).read_bytes();assert len(b)==r['bytes'] and h(b)==r['sha256']
assert h((P/'generate_inputs01.py').read_bytes())=='4cbe78b260c63e34d7d1eca631296446c44adda810c502392dbed0e5bb3bdba1'
assert h((P/'build_release_draft01.py').read_bytes())=='b397364ae859b07dcdce1aceb0bb49f2745cfc782ed38f9c303bc055764d66c4'
for name,seam in [('generate_inputs01.py','held_input_plan'),('build_release_draft01.py','held_metadata_draft')]:
 old=(OLD/name).read_text();new=(P/name).read_text();a=next(n for n in ast.parse(old).body if isinstance(n,ast.FunctionDef) and n.name==seam);b=next(n for n in ast.parse(new).body if isinstance(n,ast.FunctionDef) and n.name==seam)
 lines=new.splitlines(keepends=True);lines[b.lineno-1:b.end_lineno]=old.splitlines(keepends=True)[a.lineno-1:a.end_lineno];assert ''.join(lines)==old
 assert (P/(name+'.baseline')).read_bytes()==(P/name).read_bytes()[:len((P/(name+'.baseline')).read_bytes())]
assert (P/'capsule_builder01.py').read_bytes()==(OLD/'capsule_builder01.py').read_bytes()
inv=json.loads((P/'prospective-source-inventory02.json').read_bytes());print('inventory fields',list(inv))
ns=runpy.run_path(str(P/'test_corrections02.py'));suite=unittest.defaultTestLoader.loadTestsFromTestCase(ns['Tests']);result=unittest.TextTestRunner(verbosity=2).run(suite);assert result.wasSuccessful()
# Independent additional mutations using actual extracted helper, synthetic source/reader only.
results=[]
for name,alter in [
 ('extra-policy-field',lambda s,r,d:d['held.json'].update(extra=True)),
 ('bool-policy-limit',lambda s,r,d:d['held.json'].update(max_members=True)),
 ('changed-policy-output',lambda s,r,d:d['held.json']['targets']['a'*64].update(output='different.json')),
 ('unknown-selector',lambda s,r,d:(d['job.json']['payload']['representation_jobs']['rep'].update(held_score_other='x'),d['plan.json']['producers']['prod'].update(held_score_other='x'))),
 ('unregistered-header',lambda s,r,d:r['registration']['document']['experiments']['future-review-only']['outputs'].remove('journal.json')),
 ('duplicate-header',lambda s,r,d:d['plan.json']['producers']['prod'].update(journal_output='binding.json'))]:
 s,r,d=ns['fixture']();alter(s,r,d);ns['refresh'](r,d)
 try:ns['draft'](s,r,d)
 except (ValueError,AssertionError):results.append(name)
 else:raise AssertionError('accepted corruption '+name)
# Authentic existing catalog names/refs, synthetic current job/registration only.
s,r,d=ns['fixture']();I=F/'held-target-input-reuse-investigation01-2026-10-03'
original=json.loads((I/'ORIGINAL_IMPORT_INDEX_ROLE01.json').read_bytes());catalog=json.loads((I/'TARGET_CATALOG01.json').read_bytes());r['original_import_index']=ns['role']('original',original);r['target_catalog']=ns['role']('targets',catalog)
hashes=[t['graph_hash'] for t in catalog['targets']];case=r['case_contract']['document'];case['readback_outputs']={g:out for g,out in zip(hashes,['a.json','b.json'])}
for value in (d['job.json']['payload']['representation_jobs']['rep'],d['plan.json']['producers']['prod']):value['descriptor']['required_graphs']=hashes
control=d['control.json'];control['original_source']=original['original_source'];control['original_claim']=original['original_claim']
d['held.json']['targets']={g:{'output':out} for g,out in case['readback_outputs'].items()};ns['refresh'](r,d);out,reads=ns['draft'](s,r,d);assert len(out['input_plan']['input_rows'])==28 and 'held.json' in reads and not out['execution_admitted']
(H/'CHECK_READBACK02.json').write_text(json.dumps({'status':'accepted source-only HFS1/HFS2 correction','author_actual_source_cases':result.testsRun,'independent_refusals':results,'authentic_input_catalog_names_positive':28,'source_runtime_reader_qualification':'synthetic current source/byte-reader stand-ins; no genuine Source/Owner/registration authority','inverse_two_functions_only':True,'legacy_prefix_unchanged':True},indent=2,sort_keys=True)+'\n')
print('PASS independent metadata02 checks')
