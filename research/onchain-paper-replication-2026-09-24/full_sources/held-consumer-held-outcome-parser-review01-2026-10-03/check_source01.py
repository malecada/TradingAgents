import ast,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parent;A=R.parent/'held-consumer-held-outcome-parser-preparation01-2026-10-03';H=lambda b:hashlib.sha256(b).hexdigest()
rows=json.loads((A/'SOURCE_EVIDENCE01.json').read_bytes());read=[]
for row in rows:
 p=Path(row['origin']);b=p.read_bytes();assert len(b)==row['bytes'] and H(b)==row['sha256'];ast.parse(b);read.append(row)
cap=Path(rows[0]['origin']).parents[1]
additional=[]
for rel in ['tradingagents/research/onchain_replication/matching_owner.py','tradingagents/research/onchain_replication/resource_fixture.py','tradingagents/research/onchain_replication/provenance.py']:
 b=(cap/rel).read_bytes();ast.parse(b);additional.append({'path':rel,'bytes':len(b),'sha256':H(b)})
(R/'SOURCE_READBACK01.json').write_text(json.dumps({'exact_author_source_references':read,'additional_source_bodies':additional,'qualification':'AST/text and body hashes only; no source module execution, array decoding, claims or actual Owner capability.'},indent=2,sort_keys=True)+'\n')
print('PASS nine original source references and three additional original schema/caller bodies; source text only')
