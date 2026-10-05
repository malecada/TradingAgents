"""Corrected expectation: immutable IO09d1 uses sys.exception() for primary."""
from pathlib import Path
p=Path(__file__).resolve().parent
source=(p/'witness_cleanup01.py').read_text().replace("root=H/'owned'","root=H/'owned02'").replace("assert result['real_owned_fd_closed_once'] and not result['actual_raised_is_original_fatal'] and result['actual_raised_is_later_close']","assert result['real_owned_fd_closed_once'] and result['actual_raised_is_original_fatal'] and not result['actual_raised_is_later_close']").replace("'WITNESS_CLEANUP01.json'","'CHECK_CLEANUP02.json'")
exec(compile(source,str(p/'check_cleanup02.py'),'exec'),{'__file__':str(p/'check_cleanup02.py'),'__name__':'__main__'})
