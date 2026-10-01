"""Read-only closure of one saved probe; never invokes its writer or guard."""
import argparse
import json
from pathlib import Path
from tradingagents.research.onchain_replication import resources
from tradingagents.research.onchain_replication.provenance import file_hash

def verify(root):
    root=Path(root).absolute();intent=json.loads((root/'intent.json').read_text());value=json.loads((root/'guard/final.json').read_text())
    assert value==json.loads((root/'guard/live.json').read_text())
    assert value['command']==intent['command'] and value['cwd']==str(root) and value['cleanup_verified']
    assert value['storage_budget']==intent['policy']['storage_budget']
    assert all(file_hash(Path(p))==h for p,h in intent['source_sha256'].items())
    assert value['kernel_controls']=={'memory.max':'268435456','memory.high':'201326592','memory.swap.max':'0'}
    assert not any(value['memory_events'].values()) and len(value['cpus'])==2
    assert not Path(value['cgroup']).exists()
    props=resources._properties(value['unit']);assert props.get('ActiveState') not in ('active','activating')
    payload=root/'outputs/payload.bin';info=payload.stat();directory=(root/'outputs').stat()
    actual_allocated=(info.st_blocks+directory.st_blocks)*512
    if intent['mode']=='positive':
        assert value['phase']=='complete' and value['child_exit_code']==0 and info.st_size==1024
        assert value['storage_observation']['allocated_bytes']==actual_allocated
    else:
        assert value['phase']=='failed' and 'storage allocated' in value['limit_reason'] and info.st_size==262144
        assert value['storage_breach']['allocated_bytes']==actual_allocated>65536
    return {'schema_version':1,'identity':intent['identity'],'expected_guard_outcome_verified':True,'guard_phase':value['phase'],
        'elapsed_seconds':value['elapsed_seconds'],'peak_sampled_memory_current_bytes':value['peak_sampled_memory_current_bytes'],
        'cleanup_verified':True,'payload_bytes':info.st_size,'payload_sha256':file_hash(payload),'allocated_output_bytes':actual_allocated,
        'guard_final_sha256':file_hash(root/'guard/final.json'),'intent_sha256':file_hash(root/'intent.json'),
        'qualification':'Read-only tiny synthetic sampled storage guard closure, not a hard quota or empirical capacity result.'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args();result=verify(a.root)
    with (a.root/'closure01.json').open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(result))
