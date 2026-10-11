"""Best-effort failure reporting; the caller retains and re-raises its primary."""


def exception_message(primary: BaseException) -> str:
    """Keep printable reasons unchanged; type is recorded by each caller."""
    try:
        return str(primary)
    except BaseException:
        return 'unprintable exception'


def record_failure(primary: BaseException, actions: tuple) -> None:
    """Attempt every independent report/cleanup without replacing the failure.

    Notes report secondary exception types without invoking their formatters.
    An absent receipt remains absent when publication fails; nothing here
    declares a successful terminal publication or overwrites an existing one.
    Call this from the original except block, followed by a bare ``raise``.
    """
    for action in actions:
        try:
            action()
        except BaseException as secondary:
            try:
                primary.add_note('secondary failure: ' + type(secondary).__name__)
            except BaseException:
                pass
