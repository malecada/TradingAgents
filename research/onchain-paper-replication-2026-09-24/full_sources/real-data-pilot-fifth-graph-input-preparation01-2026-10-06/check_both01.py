from pathlib import Path
import ast,copy,hashlib,importlib.util,json
R=Path.cwd();F=Path(__file__).resolve().parent.parent;h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();results=[]
census=json.loads((F/'real-data-pilot-remaining-graph-inputs01-2026-10-06/RAW_EXTENTS01.json').read_bytes())
for ordinal,ident,label,rows,count in [('fifth','20220530','MAY30',7507236,250),('sixth','20220606','JUNE6',7293215,223)]:
 O=F/f'real-data-pilot-{ordinal}-graph-input-preparation01-2026-10-06'
 for n,v in json.loads((O/'INVERSE01.json').read_bytes()).items():
  s=(R/v['baseline']).read_text();assert h(R/v['baseline'])==v['before_sha256']
  for e in v['literal_edits']:assert e['before'] in s;s=s.replace(e['before'],e['after'])
  assert s==(O/n).read_text() and h(O/n)==v['after_sha256']
  if n.endswith('.py'):ast.parse(s)
 spec=importlib.util.spec_from_file_location('draft_'+ordinal,O/'prepare_draft01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 case=next(v for v in census['cases'] if ident in v['identity']);w=json.loads((R/case['inputs']['weekly_source']['path']).read_bytes());m.validate_week(w,case)
 for kind in ('missing','late'):
  bad=copy.deepcopy(w)
  if kind=='missing':bad['members'].pop()
  else:bad['members'][-1]['end_utc']='2022-06-14T00:00:00Z'
  try:m.validate_week(bad,case)
  except ValueError:pass
  else:raise AssertionError((ident,kind))
 d=json.loads((O/f'draft01/{label}_DRAFT01.json').read_bytes());extent=json.loads((O/'draft01/RAW_EXTENT_DRAFT01.json').read_bytes());assert d['identity']==case['identity'] and d['parent'] is None and d['effective_budget_unchanged']==71 and extent['declared_rows']==rows and extent['segments']==count
 assert len(d['raw_input_refs'])==11 and len(d['prospective_source_files'])==178
 fn=next(n for n in ast.parse((O/'preflight_DRAFT01.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='check');assert isinstance(fn.body[0],ast.Raise)
 results.append({'identity':case['identity'],'literal_inverses':4,'syntax':3,'missing_late_refused':True,'draft_stop':True,'rows':rows,'stat_extents':count})
print(json.dumps({'decision':'pass','cases':results}))
