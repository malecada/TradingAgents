"""Reviewed one-time failure closure only; no financial input parsing or replay."""
import hashlib,json,subprocess
from pathlib import Path
from tradingagents.research_spread import ResearchRun
from tradingagents.research_spread.admission import admit
root=Path(__file__).resolve().parents[3]
folder=root/'research_runs/dated-spread-book-20260911'
source='6d6d65f9712dd41e135672a2f0fb8a7d8389507b'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
expected={'books.json':'c2fae39d2d4ad4deca423cc49a1f7cbc720202cb1438b34da48fad7870cfaa06',
 'summary.json':'d68d734977d0d0842573681aedd2a84e39d38f64843e47ba0f0e85b9fcd1b21c',
 'source-audit.json':'2da802b1d74a39ccfd62b5f910fb486d97feb62dbaa7437de6284637beb9b635'}
claimsha='d0116773878c723689d6c21a1b6c00bbda4839acccd0a0cd5b744a97e9fb3c2d'
guard=root/'research/strategy-search-2026-09-11/reviews/dated-spread-actual-guard.json'
assert sha(guard)=='884b9703eed6660f7dd805cb6d06f9b161db716e3826ef5e30714ef840f7c3e3'
assert not Path('/proc/404095').exists() and not Path('/proc/404099').exists()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==source
assert not any((folder/name).exists() for name in ('complete.json','failed.json'))
assert sha(folder/'claim.json')==claimsha
assert {p.name:sha(p) for p in (folder/'outputs').iterdir()}==expected
admitted=admit(root=root,registration='research/strategy-search-2026-09-11/gates-dated-spread.json',experiment=folder.name,source=source,_own_claim=folder.name)
run=ResearchRun(admitted);run._claim_sha256=claimsha
run.fail('Frozen120second wall limit exceeded; guard terminated child with SIGTERM after three outputs but before terminal receipt. Failure-only recovery independently reviewed. Guard dated-spread-actual-guard.json SHA256884b9703eed6660f7dd805cb6d06f9b161db716e3826ef5e30714ef840f7c3e3. Retained outputs are failed-run forensics, not a successful bounded execution; no replay or finish.')
assert sha(folder/'claim.json')==claimsha
assert {p.name:sha(p) for p in (folder/'outputs').iterdir()}==expected
assert (folder/'failed.json').exists() and not (folder/'complete.json').exists()
report={'status':'failed-closed','source':source,'claim_sha256':claimsha,'output_sha256_unchanged':expected,'failed_receipt_sha256':sha(folder/'failed.json'),'guard_sha256':sha(guard),'financial_replay':False,'successful_completion':False}
with (Path(__file__).parent/'dated-spread-failure-closure.json').open('x') as handle:json.dump(report,handle,indent=2);handle.write('\n')
print(json.dumps(report))
