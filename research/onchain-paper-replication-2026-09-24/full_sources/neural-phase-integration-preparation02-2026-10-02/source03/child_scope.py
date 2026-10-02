"""One tiny cross-process original-authority publication; no standalone release."""
import hashlib
import json
import os
from pathlib import Path
import resource
import sys


def main():
    if len(sys.argv)!=8:raise ValueError('exact child vector required')
    root,experiment,source,anchor,cgroup,expected_sha,expected_parent=sys.argv[1:]
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=expected_sha:raise ValueError('child source hash differs')
    if os.getppid()!=int(expected_parent):raise ValueError('child original parent PID differs')
    if resource.getrlimit(resource.RLIMIT_FSIZE)!=(4194304,4194304):raise ValueError('child inherited file limit differs')
    if any(name in sys.modules for name in ('torch','numpy')):raise ValueError('numerical module prohibited')
    class NoNumerics:
        def find_spec(self,fullname,path=None,target=None):
            if fullname.split('.')[0] in ('torch','numpy'):raise ImportError('numerical imports prohibited')
            return None
    sys.meta_path.insert(0,NoNumerics())
    from tradingagents.research import lifecycle
    from tradingagents.research.onchain_replication import neural_physical,resources
    snapshot=Path(__file__).resolve().parent
    for module in (lifecycle,neural_physical,resources):
        if not Path(module.__file__).resolve().is_relative_to(snapshot):raise ValueError('child module outside snapshot')
    if str(resources._own_cgroup())!=cgroup:raise ValueError('child escaped original unit')
    policy={'schema_version':1,'max_file_bytes':4194304,'max_json_bytes':262144,'max_allocated_bytes':167772160,'max_logical_bytes':134217728,'max_entries':128,'tail_reserve_bytes':33554432}
    scope=neural_physical.Scope.open(Path(root),experiment,source,policy,original_anchor=anchor)
    if scope.anchor['parent_authority']['pid']!=int(expected_parent):raise ValueError('scope original server PID differs')
    with lifecycle.metadata_scope(scope):
        claim=scope.check()['claim_sha256']
        path=scope.roots['producer']/'child-authority.json'
        scope.immutable(path,{'synthetic':True,'pid':os.getpid(),'ppid':os.getppid(),'original_authority_pid':scope.anchor['parent_authority']['pid'],'physical_anchor_sha256':anchor,'claim_sha256':claim,'cgroup':cgroup,'file_size_limit':list(resource.getrlimit(resource.RLIMIT_FSIZE)),'child_source_sha256':expected_sha,'numerical_imports':False})
        scope.check()
    print(json.dumps({'status':'published','pid':os.getpid(),'receipt_sha256':hashlib.sha256(path.read_bytes()).hexdigest()},sort_keys=True))
    return 0

if __name__=='__main__':raise SystemExit(main())
