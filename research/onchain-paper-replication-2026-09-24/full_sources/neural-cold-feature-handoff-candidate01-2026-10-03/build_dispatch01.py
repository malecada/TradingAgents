from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
source=ROOT/'tradingagents/research/onchain_replication'
s=(source/'compact_native_producer.py').read_text()
s=s.replace('from .cache import cache_key','from . import compact_cold_features\nfrom .cache import cache_key')
s=s.replace('return compact_native_features.required_sources() |','return compact_native_features.required_sources() | compact_cold_features.required_sources() |')
s=s.replace('    return True\n\n\ndef produce','    compact_cold_features.selected(run,representation,job,item)\n    return True\n\n\ndef produce')
s=s.replace('    journal = owner = ledger = archive_lock = None','    cold = compact_cold_features.selected(run,representation,job,item)\n    handoff_started = False\n    journal = owner = ledger = archive_lock = None')
s=s.replace("        prepared = compact_native_features.prepare(terminal,input_name=job['compact_native_features_input'])", "        if cold is not None:\n            handoff_started = True\n            prepared = compact_cold_features.prepare(terminal,input_name=job['compact_cold_handoff_input'])\n            finalize(prepared)\n            return prepared,None\n        prepared = compact_native_features.prepare(terminal,input_name=job['compact_native_features_input'])")
s=s.replace('    except BaseException as error:\n        cleanup = []','    except BaseException as error:\n        if handoff_started:\n            owner.poisoned = True\n            raise\n        cleanup = []')
s=s.replace('    require(type(prepared.features) is compact_native_features._Features', '    if type(prepared.features) is compact_cold_features._Features:\n        return compact_cold_features.finalize(prepared)\n    require(type(prepared.features) is compact_native_features._Features')
(HERE/'compact_native_producer.py').write_text(s)
s=(source/'job_payload.py').read_text();s=s.replace('    value,_=produce(graphs)\n    return value','    # Detached producers return None in the compatibility terminal slot.\n    # Resident producers retain their original terminal inside prepared.features.\n    value,terminal=produce(graphs)\n    del terminal\n    return value')
(HERE/'job_payload.py').write_text(s)
