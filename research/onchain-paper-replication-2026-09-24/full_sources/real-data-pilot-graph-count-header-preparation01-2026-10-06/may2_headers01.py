"""Exactly the closed May2 original headers; active May9 is never referenced."""
import importlib.util,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent;M=H.parents[3];F='research/onchain-paper-replication-2026-09-24/full_sources/'
spec=importlib.util.spec_from_file_location('header_counts',H/'header_counts01.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
known={
'manifest':('research_artifacts/onchain-paper-replication-2026-09-24/sources/eth-paper-real-pilot-graph-20220502-20261005-01/graph-2022-05-02/manifest.json','4aa5b107702b464ec2c34a5db8d420506e599a613c079a3ce7d2cfa89c3fb442'),
'body_hash':(F+'real-data-pilot-first-graph-outcome-review01-2026-10-06/BODY_HASH01.json','6bee854d40758e3a1a394261db7cd2ac434401fd3a45d18a89abbbcecda2b0d1'),
'completion_review':(F+'real-data-pilot-first-graph-outcome-review01-2026-10-06/REVIEW01.json','3f26a9b66c855b8c33c7aa876b7a40eb06fc3110babe4bd8b5a40130d90c442e'),
'preservation_review':(F+'real-data-pilot-first-graph-preservation-outcome-review01-2026-10-06/REVIEW01.json','4aa15ed606cc7ae3626a0539a016ba16f5685921cd870bf00443668cb9caceca'),
'disposition_review':(F+'real-data-pilot-second-graph-entry-review01-2026-10-06/RETIREMENT_READBACK01.json','d8135c3f32428c647a7e21c640877f6661b0a44bf623642be73277424d383d26'),
'retirement_complete':(F+'real-data-pilot-first-graph-post-recovery-retirement01-2026-10-06/complete01.json','5bea4f6b7dff6e9ff2fb10823d063ccacdc07e8cef93d662c59d77eae2cd7815')}
refs={k:{'path':name,'sha256':pin,'bytes':(M/name).stat().st_size} for k,(name,pin) in known.items()}
(H/'MAY2_EVIDENCE_INPUTS01.json').write_bytes(c.encode(refs))
result=c.publish(M,refs,H/'MAY2_HEADER_OBSERVATION01.json',H/'MAY2_COUNT_DRAFT01.json')
assert not {'numpy','torch','networkx','scipy'} & sys.modules.keys()
print(json.dumps(result))
