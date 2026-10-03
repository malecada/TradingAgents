"""Re-execute author full-schema utility in new owned reviewer fixtures only."""
import hashlib,json,sys
from pathlib import Path
O=Path(__file__).resolve().parent;P=O.parent/'held-consumer-flat-git-recovery-preparation01-2026-10-03';sys.path.insert(0,str(P));raw=(P/'check_full01.py').read_text();old="dir=P));D=R/'tiny-donor.git'";new="dir=REVIEW_OUTPUT));D=R/'tiny-donor.git'";assert raw.count(old)==1
adapted=raw.replace(old,new);(O/'author_full02.review-location-only.txt').write_text(adapted);namespace={'__name__':'qualified_author_full_replay','__file__':str(P/'check_full01.py'),'REVIEW_OUTPUT':O};exec(compile(adapted,str(P/'check_full01.py'),'exec'),namespace)
(O/'FULL_FIXTURE02.json').write_text(json.dumps({'fixture':str(namespace['R']),'source':namespace['source'],'selected_c6':namespace['c6'],'public_result':namespace['result'],'author_source_sha256':hashlib.sha256(raw.encode()).hexdigest(),'adaptation':'only mkdtemp dir P→review-owned O; actual SOURCE/C6 transparently patched by original utility fixture, no genuine source evidence'},indent=2)+'\n')
