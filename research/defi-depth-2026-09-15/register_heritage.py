"""Prepare Q4/Q6 source registrations; no external metadata inspection."""
import hashlib
import importlib.util
import json
from pathlib import Path
from tradingagents.research import runtime_hashes
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];base='research/defi-depth-2026-09-15/'
s=importlib.util.spec_from_file_location('heritage_registration',HERE/'heritage_source.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
def ref(path):return {'path':path,'sha256':hashlib.sha256((ROOT/path).read_bytes()).hexdigest()}
for question,prior,mechanism in [('q4',45,'mature-token-adoption-universe-source-contract'),('q6',12,'news-producer-export-lineage-clock-contract')]:
 gate=json.loads((HERE/'gates-q3.json').read_text());design=json.loads((HERE/(question+'-design.json')).read_text());family=question+'-source-contract';dataset=question+'-source-contract-metadata'
 gate['families'][family]={'mechanism_id':mechanism,'prior_attempts':prior,'attempt_budget':prior+1,'history_reference':base+'heritage-charter.md; '+base+question+'-design.json; exact ancestry and predecessor claims pinned; dependent overlap not new independent tests'}
 gate['datasets'][dataset]={'identity':mechanism,'history_reference':base+'heritage-charter.md; old inspected code/source/financial records remain exposed, not confirmation','exposures':[{'start':'2021-01-01T00:00:00Z','end':'2026-09-15T18:01:00Z','state':'exposed'}]}
 paths={'design':base+question+'-design.json','phase':base+'phase-grant.json','core_ancestry':'research/broader-allocation-2026-09-15/ancestry-crosswalk.json','defi_ancestry':'research/broader-allocation-2026-09-15/defi-ancestry-crosswalk.json','closure':'research/broader-allocation-2026-09-15/RESULTS.md','inherited_review':base+'reviews/q5-q6-inherited-review.md'}
 paths.update({'code_'+str(i):path for i,path in enumerate(design['source_code_inventory'])})
 predecessor='allocation-dex-source-20260915' if question=='q4' else 'news-provenance-20260911'
 paths.update({'prior_claim':'research_runs/'+predecessor+'/claim.json','prior_terminal':'research_runs/'+predecessor+'/complete.json'})
 if question=='q6':
  paths['row_ancestry']=base+'q6-ancestry.json'
  for i,path in enumerate(sorted({r['path'] for r in json.loads((HERE/'q6-ancestry.json').read_text())['rows']})):paths['original_ledger_'+str(i)]=path
  paths['old_news_design']='research/strategy-search-2026-09-11/reviews/news-provenance-design.md'
 sources=[base+'heritage_source.py','uv.lock']
 cells,outputs=h.inventory(design)
 gate['experiments'][design['experiment']]={'family':family,'parent':None,'question':design['question'],'charter':ref(base+'heritage-charter.md'),'stage':'discovery','reuse':'exploratory','selection':None,
 'source_files':{path:ref(path)['sha256'] for path in sources},'runtime_hashes':runtime_hashes(),'inputs':{name:{**ref(path),'dataset':dataset} for name,path in paths.items()},
 'windows':[{'dataset':dataset,'start':'2021-01-01T00:00:00Z','end':'2026-09-15T18:01:00Z','availability':'existing'}],'cells':cells,'outputs':outputs}
 (HERE/('gates-'+question+'.json')).write_text(json.dumps(gate,indent=2)+'\n')
 print({'question':question,'cells':len(cells),'outputs':len(outputs),'inputs':len(paths)})
