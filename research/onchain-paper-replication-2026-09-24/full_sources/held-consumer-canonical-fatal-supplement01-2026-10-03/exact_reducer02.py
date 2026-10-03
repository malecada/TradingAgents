"""Exact source slice, indentation-only wrapper; caller supplies actual fatal predicate."""
def select(primary,error,fatal):
    if primary is None:primary=error
    elif fatal(error) and not fatal(primary):error.__cause__=primary;primary=error
    else:
        # Diagnostic failure participates after the selected error;
        # it must never replace an earlier actual fatal.
        try:primary.add_note('post-callback evidence/authority check failed: '+type(error).__name__)
        except BaseException as diagnostic:
            if fatal(diagnostic) and not fatal(primary):primary=diagnostic
    return primary
