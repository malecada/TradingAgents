"""Admitted result-retention policy; solver and scientific identities unchanged."""
import json


def read_matching_policy(run, input_name):
    if input_name is None:
        return None
    if not isinstance(input_name, str) or not input_name:
        raise ValueError('matching policy input required')
    value = json.loads(run.read_input(input_name))
    if (not isinstance(value, dict) or set(value) != {'schema_version', 'mode'}
            or type(value['schema_version']) is not int or value['schema_version'] != 1
            or value['mode'] != 'score_only'):
        raise ValueError('matching execution policy differs')
    return value


def require_matching_arm(arm, policy):
    if policy is not None and arm not in {'proposed', 'mcm_without_gat', 'training_label_permutation'}:
        raise ValueError('matching policy unused by representation arm')
