from pathlib import Path
import json,hashlib,os
R=Path(__file__).resolve().parent;P=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-root-launch-20261003-01');J=lambda p:json.loads(p.read_bytes());H=lambda b:hashlib.sha256(b).hexdigest();q=J(P/'request-unreleased01.json');rel=J(P/q['release']['path']);C=Path(rel['capsule_root'])
for key in ('caller','semantic_parser','release'):assert H((P/q[key]['path']).read_bytes())==q[key]['sha256']
assert all(ref['sha256'] is None and not os.path.lexists(P/ref['path']) for ref in q['evidence'].values())
assert sum(n.startswith('tradingagents/') for n in rel['source_files'])==148
ext=J(C/'cumulative-extension04-proposal.json');assert ext['consumed_before']==4 and ext['cumulative_ceiling']==6 and ext['base_family']==rel['family'];assert H((C/ext['allocation']['path']).read_bytes())==ext['allocation']['sha256']
rows=[]
for row in ext['claims']:
 root=C/'research_runs'/row['experiment'];claim=(root/'claim.json').read_bytes();failed=(root/'failed.json').read_bytes();assert H(claim)==row['claim_sha256'] and H(failed)==row['terminal_sha256'] and row['terminal_status']=='failed';assert not (root/'complete.json').exists();rows.append(row)
(R/'HISTORY_READBACK01.json').write_text(json.dumps({'scope':'Actual body pins and absence; not new admission or replay of authority','historical_claims':rows,'consumed_before':4,'proposed_ceiling':6,'package_count':148,'proof_body_refs_all_null_and_absent':True,'actual_request_member_hashes_joined':True},indent=2,sort_keys=True)+'\n')
print('PASS four original FAILED claim/terminal byte pins;4spent+2prospective=6;148package;exact request caller/parser/release body joins;three null proof bodies absent.')
