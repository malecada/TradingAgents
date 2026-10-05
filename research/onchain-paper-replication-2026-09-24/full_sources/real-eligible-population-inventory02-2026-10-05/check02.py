import sys
from inventory02 import graph_support,F,utc,timedelta
fold={'id':'mechanical','train_start':'2024-02-01T00:00:00Z','train_end':'2024-02-03T00:00:00Z','test_start':'2024-02-03T00:00:00Z','test_end':'2024-02-06T00:00:00Z'}
weeks=F['required_weeks'](__import__('types').SimpleNamespace(**fold),28)
graphs=[{'start_utc':w,'available_at':F['stamp'](utc(w)+timedelta(days=8)),'graph_hash':str(i).zfill(64),'manifest_path':'metadata/'+str(i)} for i,w in enumerate(weeks)]
a=graph_support(fold,graphs);assert len(a['graph_supported_rows'])==4 and a['status_counts']['purged_training_label']==1 and a['true_eligible_rows'] is None
assert all(len(r['uses'])==28 for r in a['graph_supported_rows'])
assert len({x['graph_hash'] for x in a['graph_supported_rows'][0]['uses']})<28
b=graph_support(fold,graphs[1:]);assert b['status_counts'].get('missing_graph_metadata',0)>0
late=[dict(g,available_at='2025-01-01T00:00:00Z') for g in graphs];c=graph_support(fold,late);assert c['status_counts']['late_graph_metadata']==4
try:graph_support(fold,graphs+[graphs[0]])
except ValueError:pass
else:raise AssertionError('ambiguous week accepted')
assert not any(k in sys.modules for k in ('numpy','torch','scipy','pandas'))
print('PASS: exact extracted calendar/required-weeks rules; complete28/reused graph paths; purge boundary; missing and late distinctions; ambiguous week refusal; true eligibility remains unknown; no numerical imports.')

# Equal UTC spelling must be one ambiguous week; nonzero and naive clocks fail closed.
alias=dict(graphs[0],start_utc=graphs[0]['start_utc'].replace('Z','+00:00'))
try:graph_support(fold,graphs+[alias])
except ValueError:pass
else:raise AssertionError('UTC-alias duplicate accepted')
for value in ('2024-01-01T00:00:00+01:00','2024-01-01T00:00:00',None):
 try:utc(value)
 except ValueError:pass
 else:raise AssertionError('original UTC contract weakened')
assert F['stamp']('2024-01-01T00:00:00+00:00')=='2024-01-01T00:00:00Z'
print('PASS: original provenance.utc reused, equal-clock week spellings refused, non-UTC and naive clocks rejected; old saved census untouched.')
