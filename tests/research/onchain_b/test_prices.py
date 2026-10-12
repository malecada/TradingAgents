from datetime import date

from tradingagents.research.onchain_b import prices as P


def test_csv_parse(tmp_path):
    p = tmp_path / 'r.bin'
    p.write_text('time,AdrActCnt,PriceUSD\n2022-01-03T00:00:00.000000000Z,1,3700.5\n2022-01-04T00:00:00.000000000Z,1,3800.25\n')
    px = P.load_prices(p)
    assert px[date(2022, 1, 3)] == 3700.5 and px[date(2022, 1, 4)] == 3800.25
    assert P.direction(px, date(2022, 1, 3)) == 1 and P.target_usd(px, date(2022, 1, 3)) == 3800.25


def test_direction_tie_is_zero():
    px = {date(2022, 1, 3): 1.0, date(2022, 1, 4): 1.0}
    assert P.direction(px, date(2022, 1, 3)) == 0


def test_scaler_roundtrip():
    px = {date(2022, 1, k): float(k) for k in range(1, 11)}
    s = P.Scaler().fit(px, [date(2022, 1, k) for k in range(1, 11)])
    assert abs(s.inverse(s.transform(7.0)) - 7.0) < 1e-12 and abs(s.mean - 5.5) < 1e-12


def test_real_file_covers_study():
    px = P.load_prices()
    assert date(2022, 1, 1) in px and date(2024, 12, 31) in px and all(v > 0 for v in px.values())
