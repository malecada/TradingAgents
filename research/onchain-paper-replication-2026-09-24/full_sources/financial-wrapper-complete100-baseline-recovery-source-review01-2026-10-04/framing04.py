"""Opaque read-only exact fixed archive framing compatibility; no restore."""
import hashlib,importlib.util,json,stat,sys
from pathlib import Path
H=Path(__file__).resolve().parent;C=H.parent/'financial-wrapper-complete100-baseline-capture01-2026-10-04';sha=lambda b:hashlib.sha256(b).hexdigest();sys.path.insert(0,str(H/'utilities'));sp=importlib.util.spec_from_file_location('Rframing',H/'utilities/recovery04.py');R=importlib.util.module_from_spec(sp);sp.loader.exec_module(R);rows=[]
for label in ('capsule','parent','support','git1','git2','git3'):
 m=json.loads((C/(label.upper()+'_MANIFEST01.json')).read_bytes());expected={r['path']:r for r in m['members']};raw=(C/('complete-'+label+'01.tar.gz')).read_bytes();assert len(raw)<=4194304;seen=[]
 for name,t,b in R.framed_members(raw):
  assert name in expected and name not in seen;r=expected[name];assert t.mode==r['mode']
  if r['kind']=='file':assert t.isfile() and len(b)==r['bytes'] and sha(b)==r['sha256']
  else:assert t.isdir() and not b
  seen.append(name)
 assert seen==list(expected);rows.append({'scope':label,'members':len(seen),'opaque_regular':sum(r['kind']=='file' for r in m['members']),'archive_sha256':sha(raw),'actual_original_framed_parser_passed':True})
side=json.loads((H/'ROOT_MODE_SIDECAR01.json').read_bytes());sup=json.loads((C/'SUPPORT_MANIFEST01.json').read_bytes());members={r['path']:r for r in sup['members']};assert len(side['members'])==7
for r in side['members']:
 p=Path(r['original_absolute_path']);b=p.read_bytes();assert sha(b)==r['sha256'] and len(b)==r['bytes'] and stat.S_IMODE(p.stat().st_mode)==r['original_current_mode']==0o664;v=members[r['support_snapshot_path']];assert v['mode']==r['captured_private_mode']==0o600 and v['sha256']==r['sha256'] and v['bytes']==r['bytes']
(H/'FRAMING04.json').write_text(json.dumps({'scopes':rows,'literal_mode_mapping_seven':True,'original_mode':0o664,'captured_mode':0o600,'POSIX_mode_reproduction_claim':False,'opaque_only_no_array_decode':True,'actual_restore_performed':False},indent=2,sort_keys=True)+'\n');print(json.dumps({'scopes':6,'members':sum(r['members'] for r in rows),'regular':sum(r['opaque_regular'] for r in rows),'mode_sidecar_rows':7}))
