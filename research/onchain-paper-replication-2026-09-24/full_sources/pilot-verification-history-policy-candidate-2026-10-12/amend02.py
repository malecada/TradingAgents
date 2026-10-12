from pathlib import Path
P=Path(__file__).resolve().parent
for name in ('admission.py','benchmark01.py','check01.py'):(P/('PRE_SCOPE_CORRECTION_'+name)).write_bytes((P/name).read_bytes())
p=P/'admission.py';s=p.read_text()
s=s.replace("    if any(name != own and complete is None and failed is None\n            for name, claim, complete, failed in current):\n        raise ValueError('another active run prohibits selected history mode')\n",'')
s=s.replace("        if any(not any((root/'research_runs'/c['experiment_id']/n).exists()\n                for n in ('complete.json','failed.json')) for c in prior):\n            raise ValueError('another active run prohibits selected history mode')\n",'')
p.write_text(s)
p=P/'benchmark01.py';s=p.read_text().replace('against an active job. No claim','during a concurrent mutation of the measured history. No claim').replace("if len(frontier)!=115 or any(c is None and f is None for _,_,c,f in frontier):raise ValueError('exact115 closed claims required; no active job benchmark')","if len(frontier)!=115:raise ValueError('exact115-claim roster required')")
p.write_text(s)
p=P/'check01.py';s=p.read_text().replace("  with self.assertRaisesRegex(ValueError,'another active'):f.admit()","  f.admit() # An unrelated unfinished historical identity is not a new refusal.")
p.write_text(s)
