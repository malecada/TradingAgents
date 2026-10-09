from pathlib import Path
H=Path(__file__).resolve().parent;old=H.parent/'mcm-batched-owner-integration02-2026-10-09/compact_mcm_batched.py'
s=old.read_text();start=s.index("    journal=modules['journal'].BatchJournal(",s.index('def _compute'));end=s.index("    return {'child_directories'",start)
block=s[start:end]
# Remove the two narrower lifetime handlers; replace by one acquisition scope.
a=block.index('    spool_fd=None\n    try:\n');b=block.index('    def sink(',a)
setup=block[a:b];t=setup.index('    except BaseException:')
setup=setup[len('    spool_fd=None\n    try:\n'):t]
setup=''.join(line[4:] if line.strip() else line for line in setup.splitlines(True))
block=block[:a]+setup+block[b:]
a=block.index('    try:\n        result=');b=block.index('    finally:',a)
run=block[a+len('    try:\n'):b]
run=''.join(line[4:] if line.strip() else line for line in run.splitlines(True))
block=block[:a]+run
# Retain the partially constructed exact journal solely for FD cleanup if init
# fails after opening its root descriptor. It is never exposed as authority.
block=block.replace("    journal=modules['journal'].BatchJournal(","    journal_type=modules['journal'].BatchJournal\n    journal=object.__new__(journal_type)\n    journal_type.__init__(journal,")
block=block.replace('boundary=boundary)\n    original=', 'boundary=boundary)\n    journal_ready=True\n    original=',1)
head='    journal=None; journal_ready=False; fd=None; spool_fd=None; primary=None\n    try:\n'
body=''.join('    '+line if line.strip() else line for line in block.splitlines(True))
tail='''    except BaseException as error:
        primary=error
        raise
    finally:
        # Attempt every acquired resource even if an earlier cleanup fails.
        # Preserve the originating exception; cleanup-only failure still refuses.
        actions=[]
        if fd is not None:actions.append(lambda:os.close(fd))
        if spool_fd is not None:actions.append(lambda:os.close(spool_fd))
        if journal is not None:
            if journal_ready:
                if not journal.closed:actions.append(journal.close)
            elif hasattr(journal,'fd'):
                actions.append(lambda:os.close(journal.fd))
        cleanup_error=None
        for action in actions:
            try:action()
            except BaseException as failure:
                if primary is not None:primary.add_note('Batched resource cleanup failed: '+repr(failure))
                elif cleanup_error is None:cleanup_error=failure
                else:cleanup_error.add_note('Batched resource cleanup failed: '+repr(failure))
        if primary is None and cleanup_error is not None:raise cleanup_error
'''
s=s[:start]+head+body+tail+s[end:]
(H/'compact_mcm_batched.py').write_text(s)
