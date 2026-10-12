from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent;R=P.parents[3];S=R/'tradingagents/research/onchain_replication'
def pin(p):return {'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
m={'status':'UNINSTALLED_NUMERICAL_PROFILE_UNEXECUTED','target':'tradingagents/research/onchain_replication/matching_annealing.py','candidate':pin(P/'matching_annealing.py'),'baseline':pin(P/'BASELINE_matching_annealing.py'),'unchanged_source_pins':[pin(S/n)for n in ('contracts.py','matching_reference.py','matching_immutable_session.py')],'files':[pin(p)for p in sorted(P.iterdir())if p.is_file() and p.name!='SOURCE_MANIFEST01.json']}
(P/'SOURCE_MANIFEST01.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps({'source':pin(P/'matching_annealing.py'),'manifest':pin(P/'SOURCE_MANIFEST01.json')},indent=2))
