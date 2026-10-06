from pathlib import Path
import shutil
P=Path(__file__).resolve().parent
s=(P/'candidate/archive_dispatch.py').read_text()
s=s.replace('typed_tail_binding, mcm_raw_parts','typed_tail_binding, mcm_raw_parts\n        if \'control_history\' in config:\n            from . import archive_control_history\n        # Durability helper must load before the original source snapshot.\n        from . import chunk_durability')
s=s.replace("                for empty in (self.root/'diagnostics').iterdir():","                empty_records=[]\n                for empty in (self.root/'diagnostics').iterdir():")
s=s.replace("self._control_journal.append('empty-'+empty.name,canonical_bytes({'name':empty.name,'stat':list(low.archive.io._signature(st)),'sha256':digest(b''),'bytes':0}))","empty_records.append({'name':empty.name,'stat':list(low.archive.io._signature(st)),'sha256':digest(b''),'bytes':0})")
s=s.replace("'diagnostics':delta})\n            return result","'diagnostics':delta,**({'empty_staging':empty_records} if self._history is not None else {})})\n            return result")
# Only selected mode adds new eager imports; durability worker can widen this to
# its independent selection when combined. Avoid importing new modules legacy.
s=s.replace("        # Durability helper must load before the original source snapshot.\n        from . import chunk_durability", "            # Joint selected candidate helper before original source snapshot.\n            from . import chunk_durability")
(P/'candidate/archive_dispatch.py').write_text(s)
# Candidate preparation adapters preserve legacy schema/default branches.
root=Path.cwd()/'research/onchain-paper-replication-2026-09-24/full_sources'
for directory,name in [('real-data-pilot-resource-input-builder03-2026-10-06','build_inputs03.py'),('real-data-pilot-feature-control-inventory01-2026-10-06','controls01.py')]:
 src=root/directory/name;shutil.copyfile(src,P/'baseline'/name);shutil.copyfile(src,P/'candidate'/name)
p=P/'candidate/build_inputs03.py';s=p.read_text()
s=s.replace("need(set(transport)=={'rate_kbit'", "need(set(transport)-{'control_history'}=={'rate_kbit'")
a="    need(transport['max_diagnostic_bytes']>=transport['max_payload_bytes']+131072*transport['max_commands'] and transport['max_control_bytes']>=131072*(8+4*transport['max_commands']),'shared transport diagnostic/control allowance insufficient')"
b="""    history_bounds=None
    if 'control_history' in transport:
        from tradingagents.research.onchain_replication.archive_control_history import capacity
        history_bounds=capacity(transport['control_history'],transport['max_commands'])
        need(transport['max_diagnostic_bytes']>=history_bounds['diagnostic_bytes'] and transport['max_control_bytes']>=history_bounds['control_bytes'],'selected bounded controls underfunded')
    else:
        need(transport['max_diagnostic_bytes']>=transport['max_payload_bytes']+131072*transport['max_commands'] and transport['max_control_bytes']>=131072*(8+4*transport['max_commands']),'shared transport diagnostic/control allowance insufficient')"""
assert a in s;s=s.replace(a,b)
s=s.replace("'retained_diagnostic_bytes':TRANSPORT_META*transport['max_commands']+ARCHIVE_MAX_BYTES", "'retained_diagnostic_bytes':history_bounds['diagnostic_bytes'] if history_bounds is not None else TRANSPORT_META*transport['max_commands']+ARCHIVE_MAX_BYTES")
p.write_text(s)
p=P/'candidate/controls01.py';s=p.read_text()
s=s.replace("exact(tr,{'max_commands','max_payload_bytes','max_diagnostic_bytes','max_control_bytes'},'transport')", "exact(tr,{'max_commands','max_payload_bytes','max_diagnostic_bytes','max_control_bytes'}|({'control_history'} if 'control_history' in tr else set()),'transport')")
s=s.replace("    for x in tr.values():integer(x)","    for k,x in tr.items():\n        if k!='control_history':integer(x)")
a="    need(tr['max_diagnostic_bytes']>=tr['max_payload_bytes']+DMETA*N and tr['max_control_bytes']>=DMETA*(8+4*N),'original transport caps underfunded')"
b="""    history_bounds=None
    if 'control_history' in tr:
        from tradingagents.research.onchain_replication.archive_control_history import capacity
        history_bounds=capacity(tr['control_history'],N)
        need(tr['max_diagnostic_bytes']>=history_bounds['diagnostic_bytes'] and tr['max_control_bytes']>=history_bounds['control_bytes'],'bounded transport caps underfunded')
    else:
        need(tr['max_diagnostic_bytes']>=tr['max_payload_bytes']+DMETA*N and tr['max_control_bytes']>=DMETA*(8+4*N),'original transport caps underfunded')"""
assert a in s;s=s.replace(a,b)
s=s.replace("    need(tr['max_control_bytes']>=dispatch_files*DMETA,'dispatch claims and command controls underfunded')", "    if history_bounds is None:need(tr['max_control_bytes']>=dispatch_files*DMETA,'dispatch claims and command controls underfunded')\n    else:dispatch_files=history_bounds['control_files']")
s=s.replace("'dispatch':item(tr['max_control_bytes'],dispatch_files,1,DMETA,", "'dispatch':item(tr['max_control_bytes'],dispatch_files,1 if history_bounds is None else 2,DMETA if history_bounds is None else tr['control_history']['shard_bytes'],")
s=s.replace("'transport_diagnostics':item(DMETA*N+ARCHIVE,2*N,1,ARCHIVE,", "'transport_diagnostics':item(DMETA*N+ARCHIVE if history_bounds is None else history_bounds['diagnostic_bytes'],2*N if history_bounds is None else history_bounds['diagnostic_files'],1 if history_bounds is None else 2,ARCHIVE,")
p.write_text(s)
for p in (P/'candidate').glob('*.py'):compile(p.read_bytes(),str(p),'exec')
print('seven candidate sources compile without imports')
