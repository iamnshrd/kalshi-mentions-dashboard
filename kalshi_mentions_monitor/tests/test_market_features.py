from kalshi_mentions_monitor.app.market_features import extract_speaker, infer_event_format, infer_sport


def test_extract_speaker_announcers():
    assert extract_speaker('What will the announcers say during New York Y vs San Francisco professional baseball game?') == 'announcers'


def test_extract_speaker_person():
    assert extract_speaker('What will Keir Starmer say during next Prime Minister\'s Questions?') == 'keir starmer'


def test_infer_event_format():
    assert infer_event_format('company next earnings call') == 'earnings_call'
    assert infer_event_format('live press conference remarks') == 'press_conference'


def test_infer_sport():
    assert infer_sport('professional baseball game during the broadcast') == 'mlb'
