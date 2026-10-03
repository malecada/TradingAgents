from pathlib import Path
import json,hashlib
D=Path(__file__).parent;F=D.parent;R=F.parents[2];P=F/'neural-cold-feature-handoff-held-consumer-wiring-preparation02-2026-10-03';m=json.loads((P/'SOURCE_MAP02.json').read_bytes());assert hashlib.sha256((P/'SOURCE_MAP02.json').read_bytes()).hexdigest()=='33fe8ba99dd76fceb775cbb25b6c39e4407af5ed58e8a5453da3d14c571b261d'
refs=[r.get('candidate',r.get('accepted_unchanged_dependency')) for r in m['install_map']];refs.append(m['canonical_cleanup_dependency'])
for r in refs:
 b=(R/r.get('path',r.get('origin'))).read_bytes();assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
print('PASS all6 exact install-map bodies plus canonical package cleanup origin; no installation/import of genuine authority')
