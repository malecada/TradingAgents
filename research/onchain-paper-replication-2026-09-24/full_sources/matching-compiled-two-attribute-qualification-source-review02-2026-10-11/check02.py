# Preserve original reviewer failure: candidate patch headers both use fixture.py.
# Only correct expected header labels; no candidate source or test criteria changed.
from pathlib import Path
source=Path(__file__).with_name('check01.py').read_text()
source=source.replace("'FORWARD.patch','fixture01.py','fixture02.py'", "'FORWARD.patch','fixture.py','fixture.py'").replace("'INVERSE.patch','fixture02.py','fixture01.py'", "'INVERSE.patch','fixture.py','fixture.py'")
exec(compile(source,'corrected-review-header-expectation','exec'))
