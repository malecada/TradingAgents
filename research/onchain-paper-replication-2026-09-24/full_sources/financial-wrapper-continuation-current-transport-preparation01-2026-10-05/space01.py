"""Conservative shared-store free-space margin, not a filesystem reservation."""
from pathlib import Path
import os,shutil,time
import watch01 as original
POLICY=original.POLICY
ROOT=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
F=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources'
MARGIN=2*96*1024**2
ROOTS=tuple(F/('financial-wrapper-continuation-current-'+phase+'01-2026-10-05') for phase in ('remote','flat'))
def check():
 dev=F.stat().st_dev
 for p in ROOTS:
  if os.path.lexists(p):
   if not p.is_dir() or p.resolve()!=p or p.stat().st_dev!=dev:raise ValueError('both retained current roots require same canonical store')
 if shutil.disk_usage(F).free<10*1024**3+MARGIN:raise ValueError('10GiB floor plus fixed192MiB conservative shared margin')
def census(root):
 check();row=original.census(root);check();return row
