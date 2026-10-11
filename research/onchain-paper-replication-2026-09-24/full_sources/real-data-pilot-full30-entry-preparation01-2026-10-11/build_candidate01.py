"""Generate source-only entry30 copies; never execute entry or registration."""
from pathlib import Path
import hashlib,json,difflib
ROOT=Path.cwd().resolve();HERE=Path(__file__).resolve().parent;F=HERE.parent
OLD=F/'real-data-pilot-full29-entry01-2026-10-09';T=F/'real-data-pilot-full30-binding-preparation01-2026-10-11'
def load(p): return json.loads(p.read_bytes())
def pin(p):
 b=p.read_bytes();return {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(p,v): p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def main():
 original=(OLD/'preflight29_02.py').read_text();s=original
 changes=[('20261009-29','20261011-30'),("HERE/'gate04.json'","HERE/'gate01.json'"),('BINDING02.json','BINDING01.json'),('RELEASE_REVIEW02.json','RELEASE_REVIEW01.json'),('effective_attempt_budget!=100','effective_attempt_budget!=101'),("'effective_attempt_budget':100","'effective_attempt_budget':101"),('len(actual)==64','len(actual)==67'),("public['all_input_roles']==64","public['all_input_roles']==67"),('genuine64-role','genuine67-role'),('genuine budget96','genuine budget101'),("set(prior)==set(actual)","set(prior)==set(actual)-{OPAQUE_ROLE}"), ("need(prepared['preparation_origin']['public_manifest']==binding['public_preparation'],'prepared public04 origin differs')", "need(binding['preparation']==FROZEN_PREPARATION,'exact reviewed full30 public preparation differs')")]
 for a,b in changes:
  assert a in s;a_count=s.count(a);s=s.replace(a,b)
 # Restore immutable binder29 directory; only the actual identity is fresh30.
 # Full date replacement above does not match binder directory spelling.
 assert "real-data-pilot-full29-transport-binding01-2026-10-09" in s
 p=pin(T/'PREPARED01.json');s=s.replace("OPAQUE_ROLE='archive_transport'", "OPAQUE_ROLE='archive_transport'\nFROZEN_PREPARATION="+repr(p))
 execution=load(T/'public01/mcm_policy.json')['batched']['execution']
 addition="""    need(execution.get('compiled_normalization_policy')==COMPILED_POLICY,'exact selected compiled policy differs')
    need(execution.get('compiled_normalization_inputs')==COMPILED_INPUTS,'exact compiled role selection differs')
    for kind,role in COMPILED_INPUTS.items():
        need(actual[role]['sha256']==COMPILED_POLICY[kind+'_sha256']
             and str(ROOT/actual[role]['path'])==COMPILED_POLICY[kind+'_path'],
             'compiled source/library/runtime role does not join policy')
"""
 s=s.replace("for role in ('prior_outcome_review','prior_preservation_complete','prior_recovery_review'):","for role in ('prior_outcome_review','prior_preservation_complete','prior_recovery_review','prior_root_closure_review','integration_review','preparation_recovery','preparation_recovery_review'):")
 s=s.replace("FROZEN_PREPARATION="+repr(p),"FROZEN_PREPARATION="+repr(p)+'\nCOMPILED_POLICY='+repr(execution['compiled_normalization_policy'])+'\nCOMPILED_INPUTS='+repr(execution['compiled_normalization_inputs']))
 needle="    need(execution['max_summary_bytes']==144998400,'original per-stage summary cap differs')"
 assert s.count(needle)==1;s=s.replace(needle,addition+needle)
 (HERE/'preflight30_01.py').write_text(s)
 oldio=(OLD/'root_io29_02.py').read_text();newio=oldio.replace('from preflight29_02 import check','from preflight30_01 import check');assert newio!=oldio
 (HERE/'root_io30_01.py').write_text(newio)
 for oldname,newname in [('preflight29_02.py','preflight30_01.py'),('root_io29_02.py','root_io30_01.py')]:
  a=(OLD/oldname).read_text().splitlines(True);b=(HERE/newname).read_text().splitlines(True)
  (HERE/(newname+'.patch')).write_text(''.join(difflib.unified_diff(a,b,fromfile=str(OLD/oldname),tofile=str(HERE/newname))))
  (HERE/(newname+'.inverse.patch')).write_text(''.join(difflib.unified_diff(b,a,fromfile=str(HERE/newname),tofile=str(OLD/oldname))))
 save(HERE/'BASELINES01.json',{'preflight':pin(OLD/'preflight29_02.py'),'launcher':pin(OLD/'root_io29_02.py'),'register':pin(OLD/'register01.py'),'preparation':p,'mcm':pin(T/'public01/mcm_policy.json')})
 core=load(OLD/'CORE_MANIFEST01.json')
 for role in core['inputs']:core['inputs'][role]=pin(T/'public01'/(role+'.json'))
 for path in core['source']:core['source'][path]=pin(ROOT/path)['sha256']
 core['scope']='Four exact full30 public core bodies; selected compiled normalization is explicit. No admission or runtime approval.'
 save(HERE/'CORE_MANIFEST01.json',core)
 # Explicit installed executable-source snapshot only. No opaque or empirical bodies.
 d=load(F/'real-data-pilot-full30-preparation01-2026-10-11/gate.draft01.json')['experiments']['eth-paper-real-data-end-to-end-resource-20261011-30']
 sources={}
 for path in d['source_files']:
  if path.startswith('tradingagents/') or path.startswith('scripts/'):
   sources[path]=pin(ROOT/path)['sha256']
 for path in (ROOT/'tradingagents/research/onchain_replication').glob('*.py'):
  if path.name in ('compiled_small_lse.py','compiled_normalization_policy.py'):sources[str(path.relative_to(ROOT))]=pin(path)['sha256']
 save(HERE/'INSTALLED_SOURCE_PINS01.json',sources)
if __name__=='__main__':main()
