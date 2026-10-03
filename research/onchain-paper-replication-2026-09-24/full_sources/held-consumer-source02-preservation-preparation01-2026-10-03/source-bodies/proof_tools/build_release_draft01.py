"""Exclusive compact release drafts from root-selected genuine documents.

Never changes a registration, marks a release accepted, or launches a process.
All referenced documents must already exist in the supplied isolated capsule.
"""
import argparse,json,os
from pathlib import Path
from proof_raw01 import *

def draft(root,destination,phase,source,registration_path,runtime_path,environment_path,cpus,prior=None):
    root=Path(root).resolve();directory=root/destination
    require(phase in IDENTITIES and directory.resolve()==directory and directory.is_relative_to(root) and not directory.exists(),'fresh release-draft destination required')
    registration=document(root,registration_path);experiment=registration['experiments'][IDENTITIES[phase]];family=registration['families'][experiment['family']]
    require(registration['program_id']==PROGRAM and experiment['cells']==[CELLS[phase]],'genuine phase registration differs')
    # The proof_tools closure must be merged into the phase1 policy and frozen
    # BEFORE materialization. Never rewrite materialized phase2 policy inputs.
    selected=document(root,experiment['inputs']['execution_job']['path']);policy=document(root,experiment['inputs'][selected['payload']['cold_proof_input']]['path'])
    sources=experiment['source_files'];require(policy['source_files']==sources and 'proof_tools/proof_supervise01.py' in sources,'source integration must precede phase1 freeze')
    directory.mkdir(exist_ok=False)
    def put(name,value,limit):
        raw=canonical(value)+b'\n';require(len(raw)<=limit,'draft document bound exceeded')
        with (directory/name).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        return ref(root,str((directory/name).relative_to(root)),kind='metadata' if limit==META else 'document')
    source_ref=put('source-document.json',{'schema_version':1,'files':sources},MAX)
    contract_ref=put('phase-contract.json',{'schema_version':1,'identity':IDENTITIES[phase],'experiment':experiment,'family':family,'expected_outputs':experiment['outputs']},MAX)
    release={'schema_version':1,'kind':'cold-proof-outer-release-v1','status':'draft','phase':phase,'root':str(root),'source':source,'registration':ref(root,registration_path),'sources':source_ref,'runtime':ref(root,runtime_path),'native_environment':ref(root,environment_path),'phase_contract':contract_ref,'prior_materialization':prior,'cpus':cpus,'remaining':['root exact source/Git/runtime/input/registration and baseline review','independent exact prospective release; create a new immutable released envelope']}
    result=put('release-draft.json',release,META)
    fd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--destination',required=True);p.add_argument('--phase',choices=list(IDENTITIES),required=True);p.add_argument('--source',required=True);p.add_argument('--registration',required=True);p.add_argument('--runtime',required=True);p.add_argument('--native-environment',required=True);p.add_argument('--cpus',type=int,nargs=2,required=True);p.add_argument('--prior-json');a=p.parse_args()
    prior=None if a.prior_json is None else metadata(Path(a.root),a.prior_json)
    draft(a.root,a.destination,a.phase,a.source,a.registration,a.runtime,a.native_environment,a.cpus,prior)
