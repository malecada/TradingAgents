"""Exact bind AST, real lifecycle active/read/source/hash validation; no Owner."""
import ast,hashlib,json,os
from pathlib import Path
from types import SimpleNamespace
import pytest
from tests.research.test_lifecycle import registered,commit
from tradingagents.research.admission import admit
from tradingagents.research.lifecycle import ResearchRun
from tradingagents.research.onchain_replication import job

@pytest.fixture
def boundary(registered):
 root,spec,_=registered
 path=root/'execution.json';path.write_text('{}')
 spec['experiments']['example-a']['inputs']['execution_job']={'path':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'dataset':'sample'}
 source=commit(root,spec);ad=admit(root=root,registration='registration.json',experiment='example-a',source=source)
 run=ResearchRun(ad)
 # Synthetic active-receipt bytes outside the lifecycle ledger. No start/claim,
 # owner creation, budget consumption or empirical registration occurs.
 run.directory=root/'synthetic-active-state';run.directory.mkdir()
 raw=b'{"synthetic_active_receipt":true}\n';(run.directory/'claim.json').write_bytes(raw)
 run._claim_sha256=hashlib.sha256(raw).hexdigest()
 counts={'source':0,'job_parse':0}
 def source_check():
  counts['source']+=1
  return ResearchRun._check_source(run)
 run._check_source=source_check
 def parse(raw):
  counts['job_parse']+=1
  return json.loads(raw)
 path=Path(os.environ['OWNER_SOURCE']);tree=ast.parse(path.read_text())
 selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('require','bind')]
 assert len(selected)==2
 ns={'__name__':'tradingagents.research.onchain_replication.matching_owner','__package__':'tradingagents.research.onchain_replication','ResearchRun':ResearchRun,'json':SimpleNamespace(loads=parse),'job':job}
 exec(compile(ast.Module(body=selected,type_ignores=[]),str(path),'exec'),ns)
 def invoke():return ns['bind'](run,representation='unused',plan_input='unused',producer='unused',policy_input='unused')
 return root,run,counts,invoke

def no_publication(root,run):
 assert sorted(p.name for p in run.directory.iterdir())==['claim.json']
 assert run._published_outputs=={}
 assert not (root/'research_artifacts').exists()
 assert not (root/'research_runs/example-a').exists()

def test_first_boundary_validates_source_once(boundary):
 root,run,counts,invoke=boundary
 with pytest.raises(ValueError,match='execution job schema/kind differs'):invoke()
 print('FIRST_BOUNDARY_COUNTS',counts)
 assert counts=={'source':1,'job_parse':1}
 no_publication(root,run)

def test_source_refusal_precedes_job_parse_and_publication(boundary):
 root,run,counts,invoke=boundary
 (root/'engine.py').write_text('# changed synthetic source\n')
 with pytest.raises(ValueError,match='committed source differs'):invoke()
 assert counts=={'source':1,'job_parse':0}
 no_publication(root,run)

def test_inactive_refusal_precedes_source_parse_and_publication(boundary):
 root,run,counts,invoke=boundary
 (run.directory/'failed.json').write_text('{}')
 with pytest.raises(ValueError,match='run is terminal'):invoke()
 assert counts=={'source':0,'job_parse':0}
 assert sorted(p.name for p in run.directory.iterdir())==['claim.json','failed.json']
 assert not (root/'research_artifacts').exists() and not (root/'research_runs/example-a').exists()

def test_malformed_job_keeps_exact_refusal(boundary):
 root,run,counts,invoke=boundary
 with pytest.raises(ValueError) as error:invoke()
 assert str(error.value)=='execution job schema/kind differs'
 assert counts['job_parse']==1
 no_publication(root,run)
