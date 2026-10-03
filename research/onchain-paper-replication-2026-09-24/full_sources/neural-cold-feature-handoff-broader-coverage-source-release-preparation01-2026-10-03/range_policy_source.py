"""Exact extracted registration-input builder; no downloader imports or execution."""
from datetime import date
HOST="https://aws-public-blockchain.s3.us-east-2.amazonaws.com/"

def range_policy(asset, dates, catalogues, *, maximum_span_bytes,
                 max_requests, max_received_bytes, max_blob_bytes):
    """Construct a registration input; construction grants no execution permit."""
    dates = list(dates)
    if asset not in ('BTC', 'ETH') or not dates or dates != sorted(set(dates)):
        raise ValueError('source asset/date population')
    if any(date.fromisoformat(d).isoformat() != d or not 2016 <= date.fromisoformat(d).year <= 2024 for d in dates):
        raise ValueError('source calendar bounds')
    years = {d[:4] for d in dates}
    if set(catalogues) != years or any(not isinstance(x, str) or not x for x in catalogues.values()):
        raise ValueError('registered catalogue year membership')
    for value, upper in ((maximum_span_bytes, 64*1024**2), (max_requests, 500_000),
                         (max_received_bytes, 2*1024**4), (max_blob_bytes, 2*1024**4)):
        if type(value) is not int or not 0 < value <= upper:
            raise ValueError('source resource bounds')
    return {'schema_version': 1, 'asset': asset, 'dates': dates, 'catalogue_inputs': dict(catalogues),
            'host': HOST, 'timeout_seconds': 30, 'retries': 0,
            'maximum_span_bytes': maximum_span_bytes, 'maximum_footer_bytes': 2*1024**2,
            'maximum_object_bytes': 8*1024**3, 'maximum_objects_per_date': 128,
            'max_requests': max_requests, 'max_received_bytes': max_received_bytes,
            'max_blob_bytes': max_blob_bytes, 'blob_limit_scope': 'compressed response bodies only',
            'footer_requests': 'trailer then footer; selected spans reacquire metadata with same ETag',
            'decode_transaction_pages': False}
