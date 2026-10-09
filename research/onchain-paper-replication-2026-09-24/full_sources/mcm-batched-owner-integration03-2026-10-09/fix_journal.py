from pathlib import Path
H=Path(__file__).resolve().parent;old=H.parent/'mcm-batched-owner-integration02-2026-10-09'
p=H/'compact_mcm_batched.py';s=p.read_text();s=s.replace("    journal=None; journal_ready=False; fd=None; spool_fd=None; primary=None", "    journal=None; fd=None; spool_fd=None; primary=None")
s=s.replace("        journal_type=modules['journal'].BatchJournal\n        journal=object.__new__(journal_type)\n        journal_type.__init__(journal,", "        journal=modules['journal'].BatchJournal(")
s=s.replace('        journal_ready=True\n','')
s=s.replace("        if journal is not None:\n            if journal_ready:\n                if not journal.closed:actions.append(journal.close)\n            elif hasattr(journal,'fd'):\n                actions.append(lambda:os.close(journal.fd))", "        if journal is not None and not journal.closed:actions.append(journal.close)")
p.write_text(s)
s=(old/'batched_journal.py').read_text();a=s.index('        self.root.mkdir(exist_ok=False);');b=s.index('    def _root(self):',a)
s=s[:a]+'''        self.root.mkdir(exist_ok=False)
        self.fd=None;parent=None
        try:
            self.fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
            s=os.fstat(self.fd);self.pin=(s.st_dev,s.st_ino)
            parent=os.open(self.root.parent,os.O_RDONLY|os.O_DIRECTORY)
            os.fsync(parent)
            closing=parent;parent=None;os.close(closing)
            self.batch_cells=batch_cells;self.max_cells=max_cells;self.max_bytes=max_bytes;self.max_body=max_body_bytes
            self.boundary=boundary;self.cells=0;self.bytes=0;self.batch=0;self.poisoned=False;self.closed=False
        except BaseException as primary:
            # A constructor which has not returned still owns every acquired FD.
            for descriptor in (parent,self.fd):
                if descriptor is not None:
                    try:os.close(descriptor)
                    except BaseException as failure:primary.add_note('Journal acquisition cleanup failed: '+repr(failure))
            self.closed=True
            raise
'''+s[b:]
(H/'batched_journal.py').write_text(s)
