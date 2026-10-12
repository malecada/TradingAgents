from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent;R=P.parents[3]
compile((P/'benchmark01.py').read_text(),'benchmark01.py','exec')
def pin(p):return {'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
old=json.loads((P/'SOURCE_MANIFEST01.json').read_text());m={'status':'UNINSTALLED_ROOT_ONLY_HOOK_UNEXECUTED','prior_manifest':pin(P/'SOURCE_MANIFEST01.json'),'candidate':old['candidate'],'baseline':old['baseline'],'reused_harness':pin(P.parent/'pilot-matching-weight-cache-candidate-2026-10-12/numeric_harness.py'),'files':[pin(p)for p in sorted(P.iterdir())if p.is_file() and p.name!='SOURCE_MANIFEST02.json']}
(P/'SOURCE_MANIFEST02.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps({n:pin(P/n)for n in ('SOURCE_MANIFEST02.json','benchmark01.py')},indent=2))
