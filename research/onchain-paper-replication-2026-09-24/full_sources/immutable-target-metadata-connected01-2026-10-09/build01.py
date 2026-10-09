from pathlib import Path
import json,hashlib,difflib
R=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes');F=R/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'immutable-target-metadata-connected01-2026-10-09';D.mkdir();S=R/'tradingagents/research/onchain_replication';O=F/'pilot-immutable-target-metadata01-2026-10-09'
changes=json.loads((O/'CHANGES01.json').read_text())
# Selected caller admission restricts to genuine sampled fresh JSON return.
changes['imported_mcm_identity.py'].insert(2,("        require(type(execution) is original_import_stage.ImportedExecution,'genuine imported execution required')","        require(type(execution) is original_import_stage.ImportedExecution,'genuine imported execution required')\n        require(not immutable_target_metadata.selected(immutable_execution) or getattr(execution,'_sampled_authority_lease',None) is not None,'immutable target requires sampled checked JSON return')"))
changes['real_pilot_import_caller.py']=[('import time','import time\nfrom . import immutable_target_metadata'),("    partial = 'partial_progress' in p","    immutable = 'immutable_target_execution' in p\n    if immutable:\n        immutable_target_metadata.selected(p['immutable_target_execution'])\n        require(full and interval,'immutable target requires sampled schema2 plan')\n    partial = 'partial_progress' in p"),("| ({'scoring_diagnostic'} if diagnostic else set()), 'pilot plan fields differ')","| ({'scoring_diagnostic'} if diagnostic else set()) | ({'immutable_target_execution'} if immutable else set()), 'pilot plan fields differ')"),("[Target(execution,g,k) for k,g in graphs.items()]","[Target(execution,g,k,**({'immutable_execution':p['immutable_target_execution']} if 'immutable_target_execution' in p else {})) for k,g in graphs.items()]"),("checked.append(Target(execution,g,k))","checked.append(Target(execution,g,k,**({'immutable_execution':p['immutable_target_execution']} if 'immutable_target_execution' in p else {})))"),("**({'diagnostic':diagnostic} if diagnostic is not None else {}))","**({'diagnostic':diagnostic} if diagnostic is not None else {}),\n                **({'immutable_execution':p['immutable_target_execution']} if 'immutable_target_execution' in p else {}))")]
for name,edits in changes.items():
 old=(S/name).read_text();new=old
 for a,b in edits:assert new.count(a)==1,(name,a,new.count(a));new=new.replace(a,b)
 (D/name).write_text(new);(D/(name+'.patch')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='Main/'+name,tofile=name)))
(D/'immutable_target_metadata.py').write_bytes((O/'immutable_target_metadata.py').read_bytes());(D/'CHANGES01.json').write_text(json.dumps(changes,indent=2)+'\n')
# Reuse bounded actual-method fixture; this is not a numerical test.
s=(O/'check.py').read_text().replace("checks=['two modules literal/AST inverse']","checks=['three modules literal/AST inverse']")
# extra selected actual parser cases placed before final output.
pos=s.index("(D/'RESULT01.json')") if "(D/'RESULT01.json')" in s else -1
print('tail',s[-700:]);(D/'check01.py').write_text(s)
(D/'BASELINE01.json').write_text(json.dumps({n:hashlib.sha256((S/n).read_bytes()).hexdigest() for n in changes},sort_keys=True)+'\n')
