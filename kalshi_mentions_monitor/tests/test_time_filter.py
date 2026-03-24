from datetime import date

from kalshi_mentions_monitor.app.models import NormalizedMarket
from kalshi_mentions_monitor.app.time_filter import is_relevant_from_date, market_reference_date


def make_market(ticker: str, open_time: str = '', close_time: str = '', created_time: str = ''):
    return NormalizedMarket(
        market_id=ticker,
        event_ticker=ticker,
        ticker=ticker,
        title='x',
        subtitle='',
        yes_sub_title='',
        no_sub_title='',
        rules_primary='',
        rules_secondary='',
        status='open',
        market_type='binary',
        series_ticker='KXTESTMENTION',
        open_time=open_time,
        close_time=close_time,
        created_time=created_time,
        updated_time='',
        raw_json={},
    )


def test_market_reference_date_from_ticker():
    m = make_market('KXABCMENTION-26MAR25-FOO')
    assert market_reference_date(m) == date(2025, 3, 26)


def test_is_relevant_from_date_false_for_old():
    m = make_market('KXABCMENTION-20MAR25-FOO')
    assert is_relevant_from_date(m, date(2026, 3, 24)) is False
