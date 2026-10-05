import math
import json
import recovery_pax01 as R
import watch01 as W
ORIGIN='git@github.com:malecada/TradingAgents.git'
BRANCH='refs/heads/research/onchain-paper-replication-2026-09-24'
REMOTE_STATUS='fresh-actual-remote-continuation-canonical01-supervised-recovered'
LOGICAL=64*1024**2
ALLOCATION=96*1024**2
def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()

def hexpin(value, length=64):
    R.require(type(value) is str and len(value) == length and all(c in '0123456789abcdef' for c in value), 'exact non-null lowercase hash pin')
    return value

def number(value, lower, upper):
    return type(value) in (int, float) and math.isfinite(value) and lower <= value <= upper

def selection_rows(selection, required):
    R.require(type(selection) is dict and set(selection) == {'remote_commit', 'rows'}, 'exact selection schema')
    hexpin(selection['remote_commit'], 40)
    rows = selection['rows']
    R.require(type(rows) is list and len(rows) == len(required), 'exact fifteen selected rows')
    expected = [dict(path=name, **pin) for name, pin in sorted(required.items())]
    R.require(all(type(row) is dict and set(row)=={'path','bytes','sha256'} and type(row['path']) is str and type(row['bytes']) is int and type(row['sha256']) is str for row in rows), 'strict selected field types')
    R.require(rows == expected, 'complete sorted fixed selection; no extras, duplicates or changed pins')
    R.require(sum(row['bytes'] for row in rows) == sum(r['bytes'] for r in required.values()) and all(0 <= row['bytes'] <= R.FILE for row in rows), 'exact finite selected extents')
    for row in rows:
        R.path_name(row['path'])
    return rows

def validate_remote(remote, selection, selection_sha256, required):
    """Validate recorded actual evidence. This function does not manufacture origin proof."""
    rows = selection_rows(selection, required)
    R.require(R.digest(encode(selection)) == hexpin(selection_sha256), 'canonical receiver selection digest')
    R.require(remote['schema_version'] == 1 and remote['status'] == REMOTE_STATUS and remote['genuine_run_or_native_started'] is False, 'actual operational delta remote status required')
    R.require(remote['selection_sha256'] == hexpin(selection_sha256) and remote['remote_commit'] == selection['remote_commit'] and remote['origin'] == ORIGIN and remote['branch'] == BRANCH, 'actual selected remote context')
    records = remote['selected_blobs']
    R.require(type(records) is list and len(records) == len(required), 'actual selected denominator')
    for record, selected in zip(records, rows):
        R.require(type(record) is dict and set(record) == {'path','bytes','sha256','git_mode','git_object'}, 'actual selected record fields')
        R.require({key: record[key] for key in selected} == selected and record['git_mode'] in ('100644','100755'), 'exact selected row and regular Git mode')
        hexpin(record['git_object'], 40)
    unique = len({row['git_object'] for row in records})
    expected = 10 + unique + 2 * len(rows)
    R.require(remote['selected_count'] == len(required) and remote['selected_logical_bytes'] == sum(r['bytes'] for r in required.values()) and remote['unique_selected_objects'] == unique and remote['expected_operations'] == expected, 'exact actual operation and object denominators')
    operations = remote['operations']
    names = ['remote','ls-remote','init','remote','config','config','fetch','rev-parse','ls-tree'] + ['fetch'] * unique + ['cat-file','cat-file'] * len(required) + ['ls-remote']
    R.require(type(operations) is list and len(operations) == expected and [row['operation'] for row in operations] == names, 'complete ordered actual operation sequence')
    for row in operations:
        R.require(type(row['pid']) is int and row['pid'] > 0 and type(row['exit']) is int and row['exit'] == 0 and type(row['actual_reaped_exit']) is int and row['actual_reaped_exit'] == 0 and row['cleanup_failures'] == [], 'actual successful main/reaped exits and cleanup')
        R.require(row['actual_child_limits'] == {'pid':row['pid'], 'fsize':[R.FILE,R.FILE]} and number(row['seconds'],0,75), 'actual child4MiB readback and bounded operation')
        R.require(type(row['stdout_bytes']) is int and 0 <= row['stdout_bytes'] <= R.FILE and type(row['stderr_bytes']) is int and 0 <= row['stderr_bytes'] <= 65536, 'bounded actual pipe extents')
        hexpin(row['stdout_sha256']); hexpin(row['stderr_sha256'])
    R.require(remote['whole_tree_policy'] == W.POLICY and number(remote['elapsed_seconds'],0,600) and type(remote['free_bytes']) is int and remote['free_bytes'] >= R.FLOOR, 'original whole-tree policy/deadline/floor')
    observations = remote['whole_tree_observations']
    R.require(type(observations) is list and 1 <= len(observations) <= W.POLICY['samples'] and remote['initial_owned_allocation'] == observations[0], 'actual initial baseline and complete observation list')
    for row in observations:
        R.require(type(row['logical_bytes']) is int and 0 <= row['logical_bytes'] <= LOGICAL and type(row['allocated_bytes']) is int and 0 <= row['allocated_bytes'] <= ALLOCATION and type(row['members']) is int and 1 <= row['members'] <= 32768 and number(row['seconds'],0,5) and row['seconds'] < 5 and type(row['complete_attempts']) is int and 1 <= row['complete_attempts'] <= 3 and type(row['regular_extent_changes']) is int and 0 <= row['regular_extent_changes'] <= row['members'] and row['measurement'] == 'complete sampled namespace; maximum of two regular extent observations', 'actual finite whole-tree sample')
    return records
