import hashlib,json,stat
from pathlib import Path
O=Path(__file__).resolve().parent;F=O.parent;M=json.loads((F/'financial-genuine-wrapper-root-recordfix-final-union01-2026-10-04/union-bytes01/ORIGINAL_TREES01.json').read_bytes());by={str(Path(t['original_root'])/r['path']):r for t in M['scope_trees'] for r in t['members']};readback=json.loads((O/'SELECTION_READBACK01.json').read_bytes());rel={(r['copied_manifest'],r['member']):r['actual_original_body'] for r in readback['relocated_exact_manifest_witnesses']};checks=[]
for name,row in by.items():
 p=Path(name)
 if row['kind']!='file' or p.name not in ('MANIFEST01.json','MANIFEST02.json','MANIFEST_ACTUAL02.json'):continue
 doc=json.loads(p.read_bytes())
 for r in doc.get('members',doc.get('entries',[])):
  if r.get('kind',r.get('type'))!='file':continue
  target=rel.get((name,r['path']),str(p.parent/r['path']));actual=by[target];s=Path(target).lstat();assert actual['kind']=='file' and actual['mode']==r['mode']==stat.S_IMODE(s.st_mode) and actual['bytes']==r.get('bytes',r.get('size'))==s.st_size and actual['sha256']==r['sha256']==hashlib.sha256(Path(target).read_bytes()).hexdigest();checks.append({'manifest':name,'member':r['path'],'original':target,'kind':'file','mode':actual['mode'],'bytes':actual['bytes'],'sha256':actual['sha256']})
assert len(checks)==438 and len(rel)==112
x={'schema_version':1,'decision':'EXACT_ORIGINAL_MANIFEST_WITNESS_KIND_MODE_BODY_JOINS_ACCEPTED','checks':len(checks),'copied_reference_relocations':112,'original_source_scope_qualification_unchanged':True,'joined':checks};(O/'SELECTION_MODES04.json').write_text(json.dumps(x,sort_keys=True,indent=2)+'\n');print(len(checks))
