"""Conservative shared-store free-space margin, not a filesystem reservation."""
from pathlib import Path
import os,shutil,time
import watch01 as original
POLICY=original.POLICY
ROOT=Path('/home/malecada/master_thesis/TradingAgents-audit-fixes')
F=ROOT/'research/onchain-paper-replication-2026-09-24/full_sources'
MARGIN=8*96*1024**2
ROOTS=tuple(F/('financial-wrapper-compatibility-complete100-outcome-'+phase+'-lane%02d-canonical02-2026-10-05'%i) for i in range(1,5) for phase in ('remote','flat'))
def check():
 dev=F.stat().st_dev
 for p in ROOTS:
  if os.path.lexists(p):
   if not p.is_dir() or p.resolve()!=p or p.stat().st_dev!=dev:raise ValueError('all eight retained lane roots require same canonical store')
 if shutil.disk_usage(F).free<10*1024**3+MARGIN:raise ValueError('10GiB floor plus fixed768MiB conservative shared margin')
def census(root):
 check();row=original.census(root);check();return row
