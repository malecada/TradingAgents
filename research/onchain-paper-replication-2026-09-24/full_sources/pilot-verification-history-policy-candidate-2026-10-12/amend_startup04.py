from pathlib import Path
import shutil
P=Path(__file__).resolve().parent;I=P/'iteration03';I.mkdir()
for p in list(P.iterdir()):
 if p.is_file() and p.name!='amend_startup04.py':shutil.copy2(p,I/p.name)
p=P/'admission.py';s=p.read_text();old='''    if run is None:
        # Startup retains a fresh original full sweep. No transferable seed.
        prior = claims(root) if workers == 1 else claims(root, workers=workers)
        return prior
''';new='''    if run is None:
        # Startup retains a bounded fresh full sweep. No transferable seed.
        _, prior, _ = _history_scan(root, workers, previous=None)
        return prior
''';assert s.count(old)==1;p.write_text(s.replace(old,new))
