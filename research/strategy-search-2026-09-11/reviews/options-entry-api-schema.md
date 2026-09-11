# Current API schema clarification

September11,2026. The coordinator opened the same official market-data page
and cached field sections; no new market request or example-based observation.
This is one previously identified URL, zero discovery queries.

Index returns an object with integer time and string indexPrice; underlying
identity is supplied by the exact requested URL. Depth supplies bid/ask arrays
of string price/quantity pairs, integer T and lastUpdateId; its documented body
has no symbol. Reject conflicting optional identity fields rather than demand
undocumented fields. Mark's example root is a list; a filtered request must
produce exactly one matching symbol for this narrow admission. MarkPrice and
Greeks are strings; no exchange event timestamp is documented there. Server
time is an object containing integer serverTime. Literal clocks are not proof
of synchronized or executable quotes.

The metadata prose ambiguously associates CALL/PUT with long/short. Selection
uses CALL as the contract payoff type; it does not infer position direction or
account entitlement. The old enum/leaf-versus-parent qualifications remain.
[Official API fields](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-options/api/rest-api/market-data)
