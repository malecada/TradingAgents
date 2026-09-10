# Synthetic browser verification

The committed frontend build was served locally with a stdlib HTTP fixture, not the application or a data/account provider. The fixture exposes a three-date series ending in unknown funding. Performance, 7d range selection, Gate and Ops were exercised in Chromium on September 10 at 10:40–10:41 UTC. Cards retained unavailable returns and scale, no false warmup appeared, the drawn series stopped at the observed prefix, the gate was suspended, and file freshness was visibly separate from incomplete measurement. Browser console: zero errors and zero warnings. The screenshot contains synthetic values only; it is not an empirical result. The preview server and browser tab were closed afterward.

`preview_fixture.py` records the exact fixture used. Its source/dist path is local to the audit checkout. The screenshot is `ui-incomplete-synthetic.png`.
