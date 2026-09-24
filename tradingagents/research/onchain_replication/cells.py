"""Exact finite denominator shared by registrations, execution and reporting."""
from .cache import cache_key


def enumerate_cells(table_rows,training_config):
    cells={}
    for row in table_rows:
        for fold in row['folds']:
            for seed in row['seeds']:
                identity=row['cell_pattern'].format(fold=fold,seed=seed)
                specification={'id':identity,'lane':'paper_reconstruction','asset':row['asset'],'fold':str(fold),'seed':seed,'task':row['task'],'arm':row['arm'],'variant':row['variant']}
                if identity in cells:
                    if any(cells[identity][k]!=v for k,v in specification.items()):raise ValueError('inconsistent reused paper cell')
                    cells[identity]['tables'].append(row['table'])
                else:cells[identity]={**specification,'tables':[row['table']],'status':'pending','attempts':[]}
    for identity in training_config['diagnostic_cells']:
        if identity in cells:raise ValueError('diagnostic overlaps paper cell')
        lane,asset,fold,seed,task,arm,variant=identity.split('/')
        cells[identity]={'id':identity,'lane':lane,'asset':asset,'fold':fold,'seed':int(seed),'task':task,'arm':arm,'variant':variant,'tables':[],'status':'pending','attempts':[]}
    return tuple(cells[k] for k in sorted(cells))


def initial_cells(cells):
    arms={'proposed','lstm','gru','hlstm','svm','constant_graph','mcm_without_gat','gat_without_mcm','training_label_permutation'}
    return tuple(c for c in cells if c['asset']=='ETH' and c['fold']=='2024' and c['task']=='direction' and c['variant']=='whole' and c['arm'] in arms)


def reconcile_cells(expected,actual):
    expected={c['id'] for c in expected};ids=[c['id'] for c in actual]
    if len(ids)!=len(set(ids)) or set(ids)!=expected:raise ValueError('fit cell denominator mismatch')
    for c in actual:
        if c['status'] not in ('complete','failed','unavailable','pending'):raise ValueError('unknown cell status')
        if c['status'] in ('failed','unavailable') and not c.get('reason'):raise ValueError('unavailable/failed cell requires exact reason')
    return {'expected':len(expected),'statuses':{state:sum(c['status']==state for c in actual) for state in ('complete','failed','unavailable','pending')},'identity':cache_key(actual)}


def lifecycle_cell_id(scientific_id):
    """Reversible slash→dot mapping for the frozen seven-component cell schema."""
    import re
    if '/' not in scientific_id:
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}',scientific_id):raise ValueError('invalid simple cell identity')
        return scientific_id
    pieces=scientific_id.split('/')
    if len(pieces)!=7 or any(not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*',p) for p in pieces):raise ValueError('invalid scientific cell components')
    value='.'.join(pieces)
    if len(value)>128:raise ValueError('lifecycle cell identity exceeds bound')
    return value


def scientific_cell_id(lifecycle_id):
    value=lifecycle_id.replace('.','/')
    if lifecycle_cell_id(value)!=lifecycle_id:raise ValueError('invalid lifecycle cell mapping')
    return value
