"""Count/topology-only graph prototype; no amount sums or financial calculations."""
from collections import Counter
import hashlib
import math
import re

HEX_ADDRESS = re.compile(r'0x[0-9a-fA-F]{40}\Z')
HEX_HASH = re.compile(r'0x[0-9a-fA-F]{64}\Z')


def hexadecimal(value, pattern):
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def graph_features(pairs):
    """Directed multigraph projected onto distinct directed pairs; self loops excluded."""
    incoming, outgoing = Counter(), Counter()
    in_events, out_events = Counter(), Counter()
    for (a, b), count in pairs.items():
        if a == b or count <= 0:
            raise ValueError('graph requires positive counts and no self loops')
        outgoing[a] += 1
        incoming[b] += 1
        out_events[a] += count
        in_events[b] += count
    nodes = incoming.keys() | outgoing.keys()
    edges, events = len(pairs), sum(pairs.values())
    reciprocal_directed = sum((b, a) in pairs for a, b in pairs)
    fingerprint = hashlib.sha256()
    for (a, b), count in sorted(pairs.items()):
        fingerprint.update(f'{a},{b},{count}\n'.encode())
    return {
        'nodes': len(nodes), 'directed_pairs': edges, 'events': events,
        'repeated_events': events - edges,
        'repeated_event_fraction': (events - edges) / events if events else None,
        'reciprocal_dyads': reciprocal_directed // 2,
        'reciprocal_directed_pairs': reciprocal_directed,
        'reciprocal_directed_pair_fraction': reciprocal_directed / edges if edges else None,
        'in_degree_histogram': dict(sorted(Counter(incoming[n] for n in nodes).items())),
        'out_degree_histogram': dict(sorted(Counter(outgoing[n] for n in nodes).items())),
        'in_degree_sum': sum(incoming.values()), 'out_degree_sum': sum(outgoing.values()),
        'max_in_degree': max(incoming.values(), default=0),
        'max_out_degree': max(outgoing.values(), default=0),
        'sender_event_square_sum': sum(v * v for v in out_events.values()),
        'recipient_event_square_sum': sum(v * v for v in in_events.values()),
        'sender_event_hhi': sum(v * v for v in out_events.values()) / events**2 if events else None,
        'recipient_event_hhi': sum(v * v for v in in_events.values()) / events**2 if events else None,
        'pair_count_sha256': fingerprint.hexdigest(),
        'qualification': 'Static count-weighted top-level address graph; no entity labels, monetary weights, temporal motifs or economic interpretation.'}


class Integrity:
    """All rows retained in counters; no graph admission when any integrity check fails."""
    def __init__(self, block_rows, start_ns, end_ns):
        self.blocks, self.offsets = {}, {}
        self.errors, self.flags, self.categories = Counter(), Counter(), Counter()
        self.seen_hashes, self.pairs = set(), Counter()
        self.rows, self.last_position, self.order_inversions = 0, None, 0
        total = 0
        previous = None
        hashes = set()
        for number, block_hash, parent, timestamp, count in sorted(block_rows):
            if (type(number) is not int or type(count) is not int or count < 0
                    or type(timestamp) is not int or not start_ns <= timestamp < end_ns
                    or not hexadecimal(block_hash, HEX_HASH) or not hexadecimal(parent, HEX_HASH)):
                raise ValueError('invalid retained block fields')
            block_hash, parent = block_hash.lower(), parent.lower()
            if number in self.blocks or block_hash in hashes:
                raise ValueError('duplicate retained block identity')
            if previous and (number != previous[0] + 1 or parent != previous[1]
                             or timestamp <= previous[2]):
                raise ValueError('retained block chain/order discontinuity')
            self.blocks[number] = (block_hash, timestamp, count)
            self.offsets[number] = total
            total += count
            hashes.add(block_hash)
            previous = (number, block_hash, timestamp)
        if not self.blocks or total > 2000000:
            raise ValueError('empty or oversized retained block cohort')
        self.expected_rows = total
        self.positions = bytearray(total)
        self.start_ns, self.end_ns = start_ns, end_ns

    def add(self, row):
        txhash, bhash, number, timestamp, index, sender, recipient, value, status = row
        self.rows += 1
        errors = []
        if not hexadecimal(txhash, HEX_HASH):
            errors.append('invalid_transaction_hash')
        else:
            identity = bytes.fromhex(txhash[2:])
            if identity in self.seen_hashes:
                errors.append('duplicate_transaction_hash')
            self.seen_hashes.add(identity)
        if not hexadecimal(bhash, HEX_HASH): errors.append('invalid_block_hash')
        if not hexadecimal(sender, HEX_ADDRESS): errors.append('invalid_sender')
        if recipient is not None and not hexadecimal(recipient, HEX_ADDRESS): errors.append('invalid_recipient')
        if type(status) is not int or status not in (0, 1): errors.append('invalid_receipt_status')
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0: errors.append('invalid_amount')
        if type(timestamp) is not int or not self.start_ns <= timestamp < self.end_ns: errors.append('timestamp_outside_day_or_missing')
        block = self.blocks.get(number) if type(number) is int else None
        if block is None:
            errors.append('unknown_block')
        else:
            if not isinstance(bhash, str) or bhash.lower() != block[0]: errors.append('block_hash_mismatch')
            if timestamp != block[1]: errors.append('block_timestamp_mismatch')
            if type(index) is not int or not 0 <= index < block[2]:
                errors.append('invalid_transaction_index')
            else:
                position = self.offsets[number] + index
                if self.positions[position]: errors.append('duplicate_block_position')
                self.positions[position] = 1
                if self.last_position is not None and position < self.last_position: self.order_inversions += 1
                self.last_position = position
        self.flags['failed_receipt'] += status == 0
        self.flags['null_recipient'] += recipient is None
        self.flags['zero_value'] += value == 0
        self_transfer = isinstance(sender, str) and isinstance(recipient, str) and sender.lower() == recipient.lower()
        self.flags['self_transfer'] += self_transfer
        if errors:
            self.errors.update(errors)
            category = 'invalid'
        elif status == 0: category = 'reverted'
        elif recipient is None: category = 'null_recipient'
        elif value == 0: category = 'zero_value'
        elif self_transfer: category = 'self_transfer'
        else:
            category = 'graph_event'
            self.pairs[(sender.lower(), recipient.lower())] += 1
        self.categories[category] += 1

    def finish(self):
        missing = self.expected_rows - sum(self.positions)
        valid = not self.errors and self.rows == self.expected_rows and missing == 0
        return {'admitted': valid, 'rows': self.rows, 'expected_rows': self.expected_rows,
                'missing_block_positions': missing, 'unique_transaction_hashes': len(self.seen_hashes),
                'errors': dict(self.errors), 'flags_nonexclusive': dict(self.flags),
                'categories': {k: self.categories[k] for k in ['invalid', 'reverted', 'null_recipient', 'zero_value', 'self_transfer', 'graph_event']},
                'source_order_inversions': self.order_inversions,
                'ordering': 'File order measured, not presumed chronological. Canonical event order is (block_number, transaction_index); no time-dependent feature calculated.',
                'boundary': 'Only retained UTC-day blocks; no prior-day state or cross-day edges. Provider-internal consistency only; outside boundary headers and independent canonicality not checked.'}
