# Independent saved-data and report review

**PASS.** The saved measurement, source provenance, instrument choice, clocks and report decisions agree with the frozen charter. Review used existing files only: no market requests, replacement quotes, collector replay or financial-model rerun. The earlier independent exact-rational arithmetic check is retained in [saved-review.json](saved-review.json); this review additionally reconstructs product selection from raw metadata and checks report decisions against all required saved identities.

## Provenance and preservation

- Source: `62bcf8bf4bdb2c57e8b78d4443427863e287d692`. Collector, mathematical module, reporter, gate file and charter bytes match that Git commit. The current registered gate equals the start receipt.
- All **38 files** listed inside the capture manifest match their SHA-256 values. All **16 requests** agree across the manifest, individual receipts and raw bodies: two server clocks, two instrument inventories and twelve depth calls, all HTTP 200, totaling **1,181,453 raw bytes**. No duplicate request identity or omitted capture file was found.
- All **48 entry identities** and **432 scenario identities** are unique, ordered and complete. Each result retains non-executable and non-validating flags. No unavailable case was silently removed.
- The original financial ledger remains **820 rows**, SHA-256 `4459ddc70d41d9a99db06ab53d9ad4c8f42b6f4d282abd93b4857b4474041927`. All **40 old gate objects** pinned by this cycle's baseline retain their recorded semantic hashes.

## Product and clock admission

The raw futures response contains **13 BTC/ETH contract records**. Four satisfy the declared active, conventional dated, USDT quote/margin and 7–180-day conditions: September and December quarterly contracts for each asset. The earliest rule correctly selects **BTCUSDT_260925** and **ETHUSDT_260925**, expiring **September 25, 2026 at 08:00 UTC**, about 14.659 days after the initial futures clock. The December contracts remain inventory evidence and were not quoted. All spot identities, base/quote fields, trading permissions and normalized lot/notional limits agree with raw metadata. Both selected instruments remain fixed across all three observations.

Requests cover September 10, 2026, **16:11:14.086013–16:12:16.048734 UTC**. Actual observation offsets are approximately **0.000003, 30.000075 and 60.000084 seconds**. The two clock half-round-trip uncertainties are **167.1149135 ms spot** and **160.3000585 ms futures**. Independently reconstructed pair spans are **0.305196–0.334505 seconds**; futures conservative upper event ages are **328.989–611.452 ms**, within the registered bounds. Raw and normalized depth agree; every received side contains 100 positive, strictly ordered levels, with no crossed or locked book.

All six spot responses lack an exchange event timestamp. Each pair and every affected scenario retain `spot_event_timestamp_unavailable`. Receipt speed and the futures age checks do not establish spot freshness or simultaneous execution.

## Report and decision accuracy

The report's two selected-contract rows, **12 reference-economics rows**, four screen rows and headline **48/432** counts match the saved ledger and inventory. Monetary and percentage formatting of all 12 displayed rows was checked directly. Each fixed screen contains exactly the required nine distinct snapshot/terminal-index coordinates. **BTC and ETH at both 1,000 and 10,000 USDT fail: zero of nine required cells has positive net cash in each screen.** The four reported failures therefore follow the preregistered conjunction; there is no favorable snapshot or terminal-case selection.

This rejects these observed quotes under the registered scenario costs. It does not establish permanent absence of dated carry opportunities or validate an alternative. The report correctly retains assumed fee rates, unresolved settlement-fee basis/account applicability, unknown pathwise margin survival, spot freshness and no-fill qualifications. The user capital amounts remain USDT scenarios, without a claim that fiat conversion or transfer costs have been measured. Bitrue remains documentation-only with dated-product availability unknown. Zero strategies are validated.

## Artifact identities at review

| Artifact | SHA-256 |
|---|---|
| Capture manifest | `67d85e098dc181b09d0f42cf95c03aceced79cd63dd1f8237959641f592c77ff` |
| Measurement ledger | `7624f2809c604e51c72726fc375c3d27785675cc2992f031a913c2df813aa985` |
| RESULTS.md | `ff349ee952c3176c050f10edf320e2c77dcc0f37b6460851c3a6e3bfb10dd31f` |
| screen-summary.json | `3f066628f8accb9fe9bc2de7352fd690336dc17ce293f959ac60b90b3dd74ca3` |
| Independent arithmetic receipt | `0093f8809ee392351f5fefff4602af6a587701fe10532021be2a5c9ea9a6ed76` |

Verification was executed with the sibling Python interpreter against `/tmp/review-saved-carry.py`; it imports no collector, reporter or financial calculator. The temporary check performed raw-byte hashing, metadata/clock reconstruction, identity validation and saved-report comparison. This note is the only repository artifact written by this review.
