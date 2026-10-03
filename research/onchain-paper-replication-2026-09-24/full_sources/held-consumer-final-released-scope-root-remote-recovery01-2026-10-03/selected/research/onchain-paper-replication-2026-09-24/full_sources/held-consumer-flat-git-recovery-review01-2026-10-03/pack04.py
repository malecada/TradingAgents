"""Reviewer-owned actual selected pack/index route; generated tiny public objects."""
import json,sys,unittest
from pathlib import Path
O=Path(__file__).resolve().parent;P=O.parent/'held-consumer-flat-git-recovery-preparation01-2026-10-03';sys.path.insert(0,str(P));raw=(P/'check_git01.py').read_text();old='dir=P));observations=[]';assert raw.count(old)==1;ns={'__name__':'pack_fixture_replay','__file__':str(P/'check_git01.py'),'REVIEW_OUTPUT':O};exec(compile(raw.replace(old,'dir=REVIEW_OUTPUT));observations=[]'),str(P/'check_git01.py'),'exec'),ns)
r=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([ns['Checks']('test_green_pack_pair_only')]))
root=Path(ns['RUN']);packs=[str(p.relative_to(root)) for p in root.rglob('*.pack')];idx=[str(p.relative_to(root)) for p in root.rglob('*.idx')];assert len(packs)==len(idx)==3
(root/'pack-proof-review.json').write_text(json.dumps({'pack_files':packs,'index_files':idx,'errors':len(r.errors),'failures':len(r.failures),'qualification':'author packed fixture replay under reviewer-owned fresh directory; real selected objects only'},indent=2)+'\n');sys.exit(not r.wasSuccessful())
