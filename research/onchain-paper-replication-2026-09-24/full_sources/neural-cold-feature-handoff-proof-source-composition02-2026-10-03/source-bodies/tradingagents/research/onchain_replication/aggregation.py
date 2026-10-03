"""Exclusive retained SQLite aggregation with verified source-boundary commits.

A workspace is owned by one invocation. Terminal and unsealed directories cannot
be reopened here. Checkpoints retain evidence for a separately admitted successor;
they do not authorize automatic retries or reuse of an active database.
"""
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import sqlite3
import tempfile

from ..lifecycle import _immutable
from .provenance import durable_mkdir, file_hash, require_hash, sync_directory


@dataclass(frozen=True)
class SourceBoundary:
    source_hash: str
    rows: int

    def __post_init__(self):
        require_hash(self.source_hash)
        if type(self.rows) is not int or self.rows < 0:
            raise ValueError('source boundary count must be a nonnegative integer')


class AggregationLedger:
    def __init__(self, db, directory):
        self.db = db
        self.directory = directory
        self.rows = 0
        self.pending = 0
        self.pending_sources = set()
        self.boundaries = 0
        self.db.execute('CREATE TABLE source_checkpoints(sequence INTEGER PRIMARY KEY,source TEXT UNIQUE,rows INTEGER,total_rows INTEGER)')

    def event(self, source_hash):
        self.rows += 1
        self.pending += 1
        self.pending_sources.add(source_hash)

    def boundary(self, boundary):
        if self.pending != boundary.rows or (self.pending_sources and self.pending_sources != {boundary.source_hash}):
            raise ValueError('source boundary rows/hash differ from consumed events')
        record = {'sequence': self.boundaries, 'source_hash': boundary.source_hash,
                  'rows': boundary.rows, 'total_rows': self.rows}
        try:
            self.db.execute('INSERT INTO source_checkpoints VALUES(?,?,?,?)',
                            (self.boundaries, boundary.source_hash, boundary.rows, self.rows))
        except sqlite3.IntegrityError as error:
            raise ValueError('duplicate source boundary') from error
        # Data and checkpoint membership commit in the same FULL-synchronous
        # transaction. A crash before the receipt leaves unsealed evidence only.
        self.db.commit()
        if self.directory is not None:
            _immutable(self.directory/f'source-{self.boundaries:06d}.json', record)
        self.boundaries += 1
        self.pending = 0
        self.pending_sources.clear()

    def finish_ingestion(self):
        if self.boundaries and self.pending:
            raise ValueError('trailing events lack a verified source boundary')
        self.db.commit()


@contextmanager
def aggregation_database(scratch, *, workspace, binding):
    """Retain explicit workspaces on every exit; preserve legacy temporary mode."""
    durable_mkdir(Path(scratch))
    temporary = None
    if workspace is None:
        temporary = tempfile.TemporaryDirectory(prefix='weekly-', dir=scratch)
        directory = Path(temporary.name)
    else:
        directory = Path(workspace)
        durable_mkdir(directory.parent)
        directory.mkdir(exist_ok=False)
        sync_directory(directory.parent)
        _immutable(directory/'intent.json', {'binding': binding,
                   'continuation': 'new admitted identity required; reopening forbidden'})
    db = None
    ledger = None
    failure = None
    try:
        db = sqlite3.connect(str(directory/'ledger.sqlite'))
        db.execute('PRAGMA synchronous=FULL')
        ledger = AggregationLedger(db, directory if workspace is not None else None)
        yield ledger
        db.commit()
    except BaseException as error:
        failure = {'type': type(error).__name__, 'reason': str(error)}
        if db is not None:
            db.rollback()
        raise
    finally:
        if db is not None:
            db.close()
        if workspace is not None:
            status = 'failed' if failure is not None else 'complete'
            record = {'status': status, 'error': failure,
                      'rows': None if ledger is None else ledger.rows,
                      'source_boundaries': None if ledger is None else ledger.boundaries,
                      'qualification': 'rows counts consumed events; failed uncommitted suffix is not reusable',
                      'database_sha256': file_hash(directory/'ledger.sqlite') if (directory/'ledger.sqlite').exists() else None}
            _immutable(directory/(status+'.json'), record)
        if temporary is not None:
            temporary.cleanup()
