import hashlib,json,stat
from pathlib import Path
O=Path(__file__).resolve().parent;P=O.parent/'financial-genuine-wrapper-root-claimedrun-witness-capture01-2026-10-04';x=json.loads((O/'READBACK01.json').read_text());raw=(P/'ACTUAL_TOOL_TERMINAL02.json').read_bytes();t=json.loads(raw)
assert (t['actual_unified_session'],t['actual_start'],t['actual_completion'],t['actual_exit_code'])==(98488,'eecc9d','86f75b',0)
assert t['original_os_pid'] is t['original_start_ticks'] is t['original_process_group'] is None
assert hashlib.sha256((P/t['raw_stdout']).read_bytes()).hexdigest()==x['stdout_sha256'] and hashlib.sha256((P/t['raw_stderr']).read_bytes()).hexdigest()==x['stderr_sha256']
(O/'TERMINAL_JOIN02.json').write_text(json.dumps({'schema_version':1,'terminal_path':str(P/'ACTUAL_TOOL_TERMINAL02.json'),'terminal_sha256':hashlib.sha256(raw).hexdigest(),'exact_original_completion':t,'actual_stream_hashes_joined':True,'qualification':'Additive persisted Root tool-exit record. Original OS PID/tick/group remain unavailable; no complete process-history claim.'},sort_keys=True,indent=2)+'\n')
(O/'REPORT01.md').write_text('''# Independent actual four-tree witness capture

Accepted as complete local opaque byte preservation only. All 222 ordinary archive members/187 regular bodies were independently framed with bounded raw gzip/TAR parsing, matched to the saved manifest and every current union body/mode, and canonically recompressed to the original 1,001,788 bytes and SHA31560b60. The four original trees were independently re-enumerated: all234 typed nodes,186 regular bodies/4,296,757 bytes and13 literal symlink targets match the archived mapping. No extra or missing body exists; symlinks are metadata and are not followed or instantiated.

Exact installed sourcee4ee, mappingf4eee4df and archive/manifest/authentication joins hold. Source339 full original tree still matches captured manifestfdf7/archiveb5b6; actual metadata admission proof0592/manifest24e is joined. Source339 full recovery remains null and final Parent recovery remains separate. No old Source325 recovered label supplies new authority.

Actual saved stdout matches the authentication result and stderr is empty. Additive TERMINAL_JOIN02 authenticates Root's persisted tool session98488/start eecc9d/completion86f75b exit0 against those streams. Original OS PID/start ticks/process group are explicitly null and unavailable, not inferred from tool IDs. The receipt's final free-disk observation exceeds10 GiB; no continuous capacity or process-history claim follows.

No capture replay, archive extraction, actual restore, network, source mutation, numerical import, claim or dispatch was performed. This result permits inclusion of exact captured bodies in a separately reviewed committed transport selection. External recovery, new Source339 recovery, final caller/review union and numerical eligibility remain pending.
''')
m=[]
for p in sorted(O.rglob('*')):
 s=p.lstat();assert stat.S_ISREG(s.st_mode);b=p.read_bytes();m.append({'path':p.relative_to(O).as_posix(),'kind':'file','mode':stat.S_IMODE(s.st_mode),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
(O/'MANIFEST01.json').write_text(json.dumps({'schema_version':1,'members':m},sort_keys=True,indent=2)+'\n')
print('checks',x['checks'])
for n in ['READBACK01.json','TERMINAL_JOIN02.json','REPORT01.md','MANIFEST01.json']:print(n,hashlib.sha256((O/n).read_bytes()).hexdigest())
