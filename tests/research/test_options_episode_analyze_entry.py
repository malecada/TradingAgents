"""Actual target entry on a disposable19-history fixture; no market/economics."""
from datetime import datetime,timezone
import importlib.util
import json
from pathlib import Path
import pytest
from tests.research.test_options_capture_control import build_fixture,start,source_binding,write,ref,commit,rebind
from tests.research.test_options_capture_independent import external_evidence
from tradingagents.research_options_capture import analysis,control

spec=importlib.util.spec_from_file_location('options_episode_entry_test',Path(__file__).resolve().parents[2]/'scripts/options_episode_analyze.py')
entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)


def test_target_entry_closes_all_unavailable_once(tmp_path,monkeypatch):
    case=build_fixture(tmp_path/'repo');root,spec,grant,source,now=case
    exp=spec['experiments'][control.TARGET];exp['cells']=list(analysis.CELLS);exp['outputs']=['books.json','source-report.json']
    source=rebind(root,spec,grant);now=datetime.now(timezone.utc).isoformat();case=(root,spec,grant,source,now)
    episode=start(case);end=episode.claim['episode_protocol']['observation_window']['end'];later=(*case[:4],end)
    binding,_=source_binding(later,episode)
    product={'source_report':{'synthetic':True},'evaluate_kwargs':None,'unavailable_cells':[{'id':name,'status':'unavailable','reason':'Invented missing source'} for name in analysis.CELLS]}
    write(root,'returned/observations.json',product)
    bound=json.loads((root/binding['path']).read_bytes());bound['inputs']['observations']['sha256']=control.file_sha(root/'returned/observations.json')
    review=json.loads((root/'returned/review.json').read_bytes());review['inputs_sha256']=control.sha(control.canonical(bound['inputs']))
    write(root,'returned/review.json',review);bound['independent_review']=ref(root,'returned/review.json');write(root,binding['path'],bound)
    binding=ref(root,binding['path']);source=commit(root);quiet=external_evidence(later,episode)
    class Clock:
        @staticmethod
        def now(tz):return datetime.fromisoformat(end)
    monkeypatch.setattr(entry,'datetime',Clock)
    result=entry.run(root=root,binding=binding,commit=source,quiescence_evidence=quiet,now_utc=end)
    assert result['independent_protocol']['status']=='complete'
    assert json.loads((episode.directory/'complete.json').read_bytes())['unavailable_count']==8
    saved={p.name:p.read_bytes() for p in (episode.directory/'outputs').iterdir()}
    with pytest.raises(ValueError):entry.run(root=root,binding=binding,commit=source,quiescence_evidence=quiet,now_utc=end)
    assert saved=={p.name:p.read_bytes() for p in (episode.directory/'outputs').iterdir()}
