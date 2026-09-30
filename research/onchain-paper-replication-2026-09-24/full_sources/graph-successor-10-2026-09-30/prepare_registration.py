"""Exclusive metadata generation; no admission, body reads or empirical execution."""
from pathlib import Path
import copy
import hashlib
import json
import subprocess
from preservation_requirement import verify_chain
from previous_graph_requirement import verify as verify_graph
ROOT=Path.cwd();HERE=Path(__file__).resolve().parent
OLD=HERE.with_name('graph-successor-09-2026-09-30')
OLD_ID='eth-paper-graph-resource-20260930-09'
NEW_ID='eth-paper-graph-resource-20260930-10'
RUN=ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/OLD_ID

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(ROOT)),'sha256':sha(p)}
def write(p,value):
 with p.open('x') as f:json.dump(value,f,indent=2);f.write('\n')

def main():
 for n in ('gate.json','verification-reuse.json'):
  if (HERE/n).exists():raise FileExistsError('identity already generated')
 preservation=verify_chain(ROOT);previous_graph=verify_graph(ROOT)
 review=OLD/'LAUNCH_CLOSURE_REVIEW.md'
 if not review.is_file():raise ValueError('independent launch closure review missing')
 observer=json.loads((RUN/'observer.json').read_bytes());owner=json.loads((RUN/'owner.json').read_bytes());final=json.loads((RUN/'guard/final.json').read_bytes())
 if observer['status']!='not_admitted' or observer['owner_sha256']!=sha(RUN/'owner.json'):raise ValueError('prior launch disposition differs')
 for name,h in observer['evidence_sha256'].items():
  if sha(RUN/name)!=h:raise ValueError('prior launch evidence changed')
 if final['phase']!='failed' or not final['cleanup_verified'] or final['owner_identity']!=owner:raise ValueError('prior failure not reconciled')
 for p in [Path(final['cgroup']),Path('/proc',str(owner['monitor_pid'])),Path('/proc',str(owner['supervisor_pid'])),ROOT/'research_runs'/OLD_ID,ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/sources'/OLD_ID,RUN/'guard/release.json']:
  if p.exists():raise ValueError('prior launch identity unexpectedly present: '+str(p))
 budget=json.loads((HERE/'extension-review.json').read_bytes())
 if budget['decision']!='accepted' or budget['extension_sha256']!=sha(HERE/'extension.proposed.json'):raise ValueError('exact revised budget not reviewed')
 g=json.loads((OLD/'gate.json').read_bytes());e=copy.deepcopy(g['experiments'][OLD_ID]);e['charter']=ref(HERE/'CHARTER.md')
 for info in e['inputs'].values():
  p=ROOT/info['path']
  if p.parent==OLD:info.update(ref(HERE/p.name))
 pins={}
 for path,h in e['source_files'].items():
  p=ROOT/path
  if p.parent==OLD:p=HERE/p.name
  elif sha(p)!=h:raise ValueError('frozen source drift: '+path)
  pins[str(p.relative_to(ROOT))]=sha(p)
 e['source_files']=pins
 e['cumulative_budget_extension']={'extension':ref(HERE/'extension.proposed.json'),'review':ref(HERE/'extension-review.json')}
 prior=[OLD/'gate.json',OLD/'execution-preflight01.json',review,*[RUN/n for n in ('launch.json','owner.json','observer.json','guard/final.json')]]
 for i,p in enumerate(prior):e['inputs'][f'prior_unadmitted_launch_{i:02d}']={**ref(p),'dataset':'eth'}
 g['experiments'][NEW_ID]=e
 from tradingagents.research.onchain_replication.job import required_sources
 if not required_sources()<=set(pins):raise ValueError('required source coverage incomplete')
 original=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources/registered-hub-edges-2026-09-30'
 b=json.loads((original/'source-bindings02.json').read_bytes())
 for name,h in b['files'].items():
  if sha(ROOT/name)!=h:raise ValueError('prior full suite cannot be reused')
 reuse={'current_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'verification_head':b['head'],'bindings':ref(original/'source-bindings02.json'),'terminal':ref(original/'closure-check02.json'),'unchanged_files_verified':len(b['files']),'new_experiment_source_pins':len(pins),'new_experiment_inputs':len(e['inputs']),'preservation_prerequisite':preservation,'previous_graph_prerequisite':previous_graph,'prior_launch_status':'not_admitted','inherited_experiments_unchanged':len(g['experiments'])-1,'qualification':'Exact prior offline bytes reused; prior09 pre-claim failure retained. No body read, research admission or launch.'}
 write(HERE/'verification-reuse.json',reuse);write(HERE/'gate.json',g)
 print(json.dumps(reuse,indent=2))

if __name__=='__main__':main()
