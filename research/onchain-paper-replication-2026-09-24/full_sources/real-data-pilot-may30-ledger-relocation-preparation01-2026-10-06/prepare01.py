"""Emit the concrete frozen-copy selection; Root binds/reviews actual entry envelope."""
from pathlib import Path
import hashlib,importlib.util,json
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('relocation_candidate',HERE/'relocate01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def prepare():
    b=m.base();path=m.ROOT/m.BASE/'SELECTION_DRAFT01.json';c=json.loads(path.read_bytes())
    ref={'path':'research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-fifth-graph-failed-preservation-outcome-review01-2026-10-06/REVIEW01.json','sha256':'c6edefef9784b60ea8ad1ba331f0d12e7f6dea9add644517969f0800fc68a785'}
    b.metadata(m.ROOT,ref['path'],ref['sha256']);c['recovery_basis']['outcome_review']=ref;c['evidence'][ref['path']]=ref['sha256']
    # Do not require retired duplicate gets to remain present; original descriptors and immutable proof remain.
    selection={'schema_version':1,'identity':m.ID,'status':'FROZEN_FOR_REVIEW','data_floor_bytes':10*m.GIB,'root_floor_bytes':10*m.GIB,'wall_seconds':14400,'chunk_bytes':m.CHUNK,'target':{'path':str(m.TARGET),'device':66307,'bytes':m.BYTES,'sha256':m.SHA},'recovery_selection':c,'qualification':'Ordinary COPY only until separate accepted copy review and RETIRE release. Original failed claim and two partial arrays retained; no empirical authority.'}
    m.validate(selection);m.room(selection,m.BYTES)
    m.need(not m.TARGET.parent.exists() and not m.TARGET.parent.is_symlink(),'fresh target namespace required')
    return selection
if __name__=='__main__':print(json.dumps(prepare(),indent=2))
