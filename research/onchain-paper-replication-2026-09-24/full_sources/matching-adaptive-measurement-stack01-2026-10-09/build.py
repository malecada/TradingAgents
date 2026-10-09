import json,hashlib,ast,difflib
from pathlib import Path
D=Path(__file__).resolve().parent;F=D.parent;R=D.parents[3]
A=F/'matching-adaptive-edge-cache-connected01-2026-10-09';T=F/'pilot-binding-lease-timing-publication01-2026-10-09';G=F/'matching-real-geometry-instrumentation01-2026-10-09'
changes=json.loads((A/'CHANGES01.json').read_text());sources={};edits={};diff=[]
for name in ('adaptive_edge_policy.py','matching_annealing.py','matching_checkpoint.py','matching_immutable_session.py','batched_pair_executor.py','batched_numeric_reuse.py','batched_numeric_execution.py','compact_mcm_batched.py','matching_owner.py','compact_owner.py','imported_authority_lease.py','geometry_summary.py','geometry_publication.py'):
 base= T/name if (T/name).exists() else (G/name if name in ('batched_numeric_reuse.py','geometry_summary.py') else A/name)
 text=base.read_text();original=text;done=[]
 if name in ('batched_numeric_reuse.py','batched_numeric_execution.py','compact_mcm_batched.py'):
  for old,new in changes[name]:
   if name=='batched_numeric_execution.py' and old=='max_key_bytes,authority_poll=None):':old='binding_owner=None):';new='binding_owner=None,edge_cache_policy=None):'
   if name=='batched_numeric_execution.py' and old=='max_key_bytes=max_key_bytes,authority_poll=authority_poll)':
    old="**({'geometry':True,'max_geometry_summary_bytes':self.geometry['max_body_bytes']} if self.geometry is not None else {}))";new=old[:-1]+',**adaptive_edge_policy.options(self))'
   if name=='batched_numeric_reuse.py' and old=='max_key_bytes,authority_poll=None):':old='max_geometry_summary_bytes=8192):';new='max_geometry_summary_bytes=8192,edge_cache_policy=None):'
   if name=='compact_mcm_batched.py' and old.startswith('set(execution)=='):
    old="| ({'binding_timing'} if 'binding_timing' in execution else set())";new=old+" | ({'edge_cache_policy'} if 'edge_cache_policy' in execution else set())"
   if name=='compact_mcm_batched.py' and old.startswith('for k in '):
    old="**({'binding_timing':execution['binding_timing'],'binding_owner':target.owner} if 'binding_timing' in execution else {}))";new=old[:-1]+",**({'edge_cache_policy':execution['edge_cache_policy']} if 'edge_cache_policy' in execution else {}))"
   assert text.count(old)==1,(name,old,text.count(old))
   text=text.replace(old,new);done.append([old,new])
 ast.parse(text);(D/name).write_text(text);sources[name]={'path':str(base.relative_to(R)),'sha256':hashlib.sha256(base.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(text.encode()).hexdigest()};edits[name]=done
 diff.extend(difflib.unified_diff(original.splitlines(True),text.splitlines(True),fromfile=str(base.relative_to(R)),tofile=name))
(D/'SOURCE_MAP01.json').write_text(json.dumps(sources,indent=2)+'\n');(D/'CHANGES01.json').write_text(json.dumps(edits,indent=2)+'\n');(D/'candidate.patch').write_text(''.join(diff))
