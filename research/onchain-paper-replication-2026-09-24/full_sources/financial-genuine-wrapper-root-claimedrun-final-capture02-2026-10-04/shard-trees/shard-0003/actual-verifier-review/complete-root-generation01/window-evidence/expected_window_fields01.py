def expected_claim_window_fields(registered,experiment):
 return {'windows':[{**w,'identity':registered['datasets'][w['dataset']]['identity'],'state':'spent' if experiment['stage']=='confirmation' else 'exposed'} for w in experiment['windows']], 'prior_exposures':[{**item,'identity':info['identity']} for info in registered['datasets'].values() for item in info['exposures']]}
