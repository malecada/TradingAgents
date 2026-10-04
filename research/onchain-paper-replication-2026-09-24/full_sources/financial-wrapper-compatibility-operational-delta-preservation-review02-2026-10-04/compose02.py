from pathlib import Path
import json,hashlib,stat
O=Path(__file__).parent;F=O.parent;h=lambda b:hashlib.sha256(b).hexdigest();J=lambda p:json.loads(p.read_bytes());V=F/'financial-wrapper-compatibility-root-source-adoption-review01-2026-10-04';T=F/'financial-wrapper-complete100-failed-root-remote03-2026-10-04';bodies={};rows={}
for n in range(1,9):
 p=T/f'flat-capsule{n:02}01';m=J(p/'body-metadata.json')
 for x in m['manifest']['members']:
  if x['path'] in rows:assert rows[x['path']]==x
  rows[x['path']]=x
 for name,leaf in m['flat_members'].items():
  assert name not in bodies;q=p/leaf;s=q.lstat();b=q.read_bytes();x=rows[name];assert stat.S_ISREG(s.st_mode) and stat.S_IMODE(s.st_mode)==0o600 and s.st_nlink==1 and len(b)==x['bytes'] and h(b)==x['sha256'];bodies[name]=b
assert len(rows)==588 and len(bodies)==475
protected=J(V/'PROTECTED_NON_TARGET585.json')['members']
for x in protected:
 assert rows[x['path']]==x
 if x['kind']=='file':assert h(bodies[x['path']])==x['sha256']
C=F/'financial-wrapper-compatibility-operational-delta-capture01-2026-10-04';w=J(C/'WITHHELD_INCORRECT_BASIS_PIN01.json');assert h((C/'CAPTURE01.json').read_bytes())==w['original_capture_sha256'];assert J(C/'snapshot/SOURCE_GIT394_METADATA01.json')['actual_old385_basis']['independent_acceptance_machine_sha256']==w['incorrect_full_hash'];assert h(Path(w['actual_machine_path']).read_bytes())==w['actual_sha256'];(O/'WITHHELD_PREDECESSOR01.json').write_bytes((C/'WITHHELD_INCORRECT_BASIS_PIN01.json').read_bytes())
r={'schema_version':1,'old_actual_flat_members':len(rows),'old_actual_regular_bodies':len(bodies),'protected_original_mode_rows_joined':585,'protected_regular_bytes_rejoined':sum(x['kind']=='file' for x in protected),'predecessor_incorrect_basis_retained':w,'note':'Actual old flat bodies were read; directory modes are preserved metadata, not reconstructed POSIX directories.'};(O/'COMPOSITION02.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS original actual flat475 bodies and585 protected rows; withheld predecessor genuine wrong pin retained')
