"""Committed synthetic claim/source package, no VPS or network operations."""
from datetime import datetime,timezone,timedelta
import importlib.util
import json
from pathlib import Path
import pytest
from tests.research.test_options_timing_control import build_fixture,start,write,ref,rebind
from tradingagents.research_options_timing import control,worker
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('options_release_builder_test',ROOT/'scripts/options_timing_release_package.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)


def test_release_binds_committed_sources_and_refuses_replacement(tmp_path):
    case=build_fixture(tmp_path/'repo');root,spec,grant,source,now=case
    exp=spec['experiments'][control.TARGET];proto=exp['episode_protocol']
    t=control.utc(proto['observation_window']['start']).replace(minute=0,second=0,microsecond=0)
    proto['observation_window']={'start':t.isoformat(),'end':(t+timedelta(days=44,seconds=5)).isoformat()}
    proto['worker_lease']={'not_before':(t-timedelta(seconds=120)).isoformat(),'expires_at':(t+timedelta(days=45,seconds=60)).isoformat()}
    exp['windows'][0].update(proto['observation_window'])
    for member in worker.PACKAGE_FILES:
        tracked='scripts/options_timing_release_bootstrap.py' if member=='release_bootstrap.py' else member
        write(root,tracked,(ROOT/tracked).read_bytes())
        if not tracked.startswith('tradingagents/'):
            exp['source_files'][tracked]=control.file_sha(root/tracked)
    source=rebind(root,spec,grant);now=datetime.now(timezone.utc).isoformat();case=(root,spec,grant,source,now);episode=start(case)
    dest=tmp_path/'release';data='/opt/thesis-research/options-timing-20260915/data'
    result=b.build(root=root,destination=dest,data_root=data,host_identity='pck-preds-1',now_utc=now)
    assignment=json.loads((dest/'assignment.json').read_bytes())
    assert assignment['claim_sha256']==episode.claim_hash and assignment['source_commit']==source
    assert result['assignment_sha256']==control.file_sha(dest/'assignment.json')
    with pytest.raises(ValueError,match='sole frozen'):b.build(root=root,destination=tmp_path/'alternate',data_root=data+'-other',host_identity='pck-preds-1',now_utc=now)
    assert not (tmp_path/'alternate').exists()
    with pytest.raises(ValueError):b.build(root=root,destination=dest,data_root=data,host_identity='pck-preds-1',now_utc=now)
    (root/'scripts/options_timing_release_bootstrap.py').write_text('# changed after claim')
    with pytest.raises(ValueError):b.build(root=root,destination=tmp_path/'second',data_root=data,host_identity='pck-preds-1',now_utc=now)
    assert not (tmp_path/'second').exists()
