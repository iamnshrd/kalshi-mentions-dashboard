from kalshi_mentions_monitor.app.grouping import group_markets
from kalshi_mentions_monitor.app.models import NormalizedMarket


def make_market(ticker: str, title: str, event_ticker: str):
    return NormalizedMarket(
        market_id=ticker,
        event_ticker=event_ticker,
        ticker=ticker,
        title=title,
        subtitle='',
        yes_sub_title='',
        no_sub_title='',
        rules_primary='',
        rules_secondary='',
        status='open',
        market_type='binary',
        series_ticker='KXMLBMENTION',
        open_time='2026-03-25T12:00:00+00:00',
        close_time='2026-03-25T13:00:00+00:00',
        created_time='2026-03-24T12:00:00+00:00',
        updated_time='',
        raw_json={},
    )


def test_grouping_by_event_ticker():
    ms = [
        make_market('A-FOO', 'What will the announcers say during X?', 'EVT1'),
        make_market('A-BAR', 'What will the announcers say during X?', 'EVT1'),
        make_market('B-FOO', 'What will the announcers say during Y?', 'EVT2'),
    ]
    groups = group_markets(ms)
    assert len(groups) == 2
