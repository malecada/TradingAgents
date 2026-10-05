"""Add actual completed-parent byte observations; independent review/recovery stay absent."""
import json
from pathlib import Path
from build_draft01 import build as original_build,CAP,PARENT,CLAIM_SHA,sha,pinned
TERMINAL_SHA='da8548ec714e0c47b0b6ad82eb5e994b9630b7c765a118cb7c83922bdeaccec9'
FIT_COMPLETE_SHA='5d289b2354a67a8cda48dcd83cbe4a61751a91dcc0847dcb1d89336abec36dc7'
CHECKPOINT_SHA='50c0807fd0096111ab1503b0235ac0701b88e275052ac7f3db53cd4f1e874dd8'
STATE_SHA='920fda8e886d21e55cf18a357f6040b877ffdb06a905724cf84d109b5cdbd076'
def ref(path,pin):return {'path':str(path),'sha256':pin}
def build():
 draft=original_build();terminal_path=CAP/'research_runs'/PARENT/'complete.json';terminal=pinned(terminal_path,TERMINAL_SHA)
 if terminal['status']!='complete' or terminal['experiment_id']!=PARENT or terminal['claim_sha256']!=CLAIM_SHA or (terminal_path.parent/'failed.json').exists():raise ValueError('actual COMPLETE lifecycle join differs')
 cell=draft['prediction_edge_candidate']['consumer']['cell_id'];fit=CAP/'research_artifacts/onchain_fit_cells'/sha(cell.encode())/PARENT
 complete_path=fit/'complete.json';complete=pinned(complete_path,FIT_COMPLETE_SHA);cp=Path(complete['checkpoint'])
 if complete['epochs']!=100 or complete['sha256']!=CHECKPOINT_SHA or not cp.is_relative_to(fit/'checkpoints') or cp.resolve()!=cp:raise ValueError('actual completed checkpoint join differs')
 manifest=pinned(cp,CHECKPOINT_SHA)
 if manifest['members']!={'state.pt':{'size':497712,'sha256':STATE_SHA}}:raise ValueError('actual opaque state manifest differs')
 member=cp.parent/'state.pt';body=member.read_bytes()
 if len(body)!=497712 or sha(body)!=STATE_SHA:raise ValueError('actual opaque state bytes differ')
 provenance=manifest['provenance']
 if provenance['source_commit']!=draft['actual_parent_source'] or provenance['cell_id']!=cell:raise ValueError('original checkpoint provenance identity differs')
 observed={'complete_terminal':ref(terminal_path,TERMINAL_SHA),'fit_completion':ref(complete_path,FIT_COMPLETE_SHA),'checkpoint_manifest':ref(cp,CHECKPOINT_SHA),'checkpoint_members':[dict(ref(member,STATE_SHA),bytes=497712)],'original_checkpoint_provenance':provenance}
 draft['observed_parent_completion']=observed
 for key in observed:del draft['unresolved'][key]
 draft['status']='ACTUAL_COMPLETE_BYTES_OBSERVED_INDEPENDENT_REVIEW_AND_FULL_RECOVERY_UNRESOLVED'
 draft['qualification']='actual COMPLETE and opaque checkpoint byte joins observed; independent outcome/recovery, new prediction source and admission/release remain unresolved'
 return draft
if __name__=='__main__':print(json.dumps(build(),sort_keys=True,indent=2))
