from pathlib import Path
import hashlib,json
root=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
out=root/'research/onchain-paper-replication-2026-09-24/full_sources/neural-resource-registration-2026-10-02/revision03'
def pin(p):return {'path':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def save(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2,sort_keys=True);f.write('\n')
old=out/'CHARTER.candidate.md'
text=old.read_text()
text=text.replace('owned observer reconciles uncatchable death. Fatal errors retain their original', 'owned observer attempts to reconcile uncatchable worker death while the original\nlive authority remains available. Loss of that authority prevents disk-only\nrecovery mutations; durable failed/remaining-cell publication may be unavailable.\nRaw claim, partial outputs and guard evidence remain retained, and any recovery\nauthority requires separate review. Terminal/denominator publication is therefore\nbest-effort, never unconditional. Fatal errors retain their original')
assert text!=old.read_text()
new=out/'CHARTER.candidate02.md'
with new.open('x') as f:f.write(text)
gate=json.loads((out/'gate-candidate.NONEXECUTABLE.json').read_bytes())
exp=gate['registry_candidate']['experiments'][gate['experiment_id']]
oldpin=exp['charter'];exp['charter']=pin(new)
gate['required_source_pins']=[pin(new) if x==oldpin else x for x in gate['required_source_pins']]
save(out/'gate-candidate02.NONEXECUTABLE.json',gate)
save(out/'correction02.json',{'original_charter':pin(old),'original_candidate':pin(out/'gate-candidate.NONEXECUTABLE.json'),'charter':pin(new),'candidate':pin(out/'gate-candidate02.NONEXECUTABLE.json'),'reason':'Original-parent loss can prevent durable observer terminal and remaining-cell publication. Explicit best-effort qualification; no disk authority rebasing.','execution_admitted':False,'namespace_reserved':False})
# Preserve the exact correction script with the evidence.
with (out/'correct_candidate02.py').open('x') as f:f.write(Path(__file__).read_text())
files=sorted(p for p in out.iterdir() if p.is_file())
save(out/'manifest02.json',{'status':'NONEXECUTABLE_PREPARATION_PENDING_REVIEW','selected_candidate':pin(out/'gate-candidate02.NONEXECUTABLE.json'),'files':[pin(p) for p in files],'models_or_arrays_executed':False,'namespace_reserved':False})
print(json.dumps(pin(out/'manifest02.json')))
