from kalshi_mentions_monitor.app.classifier import classify_market
from kalshi_mentions_monitor.app.models import NormalizedMarket


def make_market(title: str, ticker: str = 'KXTESTMENTION-26MAR26-FOO'):
    return NormalizedMarket(
        market_id=ticker,
        event_ticker=ticker,
        ticker=ticker,
        title=title,
        subtitle='',
        yes_sub_title='',
        no_sub_title='',
        rules_primary='',
        rules_secondary='',
        status='open',
        market_type='binary',
        series_ticker='KXTESTMENTION',
        open_time='2026-03-26T12:00:00+00:00',
        close_time='2026-03-26T13:00:00+00:00',
        created_time='2026-03-24T12:00:00+00:00',
        updated_time='',
        raw_json={},
    )


def test_classifier_sports_announcer():
    m = make_market('What will the announcers say during New York Y vs San Francisco professional baseball game?')
    c = classify_market(m)
    assert c.market_group == 'sports_announcer_mentions'
    assert c.speaker == 'announcers'


def test_classifier_political():
    m = make_market('What will Keir Starmer say during next Prime Minister\'s Questions (UK House of Commons)?')
    c = classify_market(m)
    assert c.market_group == 'political_mentions'
    assert c.speaker == 'keir starmer'
