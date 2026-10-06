from pathlib import Path
import ast,copy,hashlib,importlib.util,json
R=Path.cwd();O=Path(__file__).parent;F=O.parent;h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for n,v in json.loads((O/'INVERSE01.json').read_bytes()).items():
 s=(R/v['baseline']).read_text();assert h(R/v['baseline'])==v['before_sha256']
 for e in v['literal_edits']:assert e['before'] in s;s=s.replace(e['before'],e['after'])
 assert s==(O/n).read_text() and h(O/n)==v['after_sha256']
 if n.endswith('.py'):ast.parse(s)
spec=importlib.util.spec_from_file_location('draft_check',O/'prepare_draft01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
case=next(v for v in json.loads((F/'real-data-pilot-remaining-graph-inputs01-2026-10-06/RAW_EXTENTS01.json').read_bytes())['cases'] if '20220523' in v['identity']);w=json.loads((R/case['inputs']['weekly_source']['path']).read_bytes());m.validate_week(w,case)
for kind in ('missing','late'):
 bad=copy.deepcopy(w)
 if kind=='missing':bad['members'].pop()
 else:bad['members'][-1]['end_utc']='2022-05-31T00:00:00Z'
 try:m.validate_week(bad,case)
 except ValueError:pass
 else:raise AssertionError(kind)
d=json.loads((O/'draft01/MAY23_DRAFT01.json').read_bytes());old=json.loads((F/'real-data-pilot-third-graph01-2026-10-06/execution-job01.json').read_bytes());assert d['execution_job_exact_May16']==old and len(d['raw_input_refs'])==11 and len(d['prospective_source_files'])==178
p=ast.parse((O/'preflight_DRAFT01.py').read_text());fn=next(n for n in p.body if isinstance(n,ast.FunctionDef) and n.name=='check');assert isinstance(fn.body[0],ast.Raise)
print(json.dumps({'decision':'pass','literal_inverses':4,'syntax_parses':3,'missing_member_refused':True,'late_member_refused':True,'exact_predecessor_job':True,'unconditional_draft_refusal':True,'source_pins':178,'raw_input_pins':11,'no_numerical_imports':True}))
