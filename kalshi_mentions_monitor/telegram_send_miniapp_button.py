from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
MINIAPP_URL = os.getenv('TELEGRAM_MINIAPP_URL', 'https://iamnshrd.github.io/kalshi-mentions-dashboard/miniapp/index.html').strip()
DEFAULT_TEXT = os.getenv('TELEGRAM_MINIAPP_MESSAGE_TEXT', 'Открыть mini app').strip()
BUTTON_TEXT = os.getenv('TELEGRAM_MINIAPP_BUTTON_TEXT', 'Open Mentions').strip()


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python3 kalshi_mentions_monitor/telegram_send_miniapp_button.py <chat_id> [message_text]')
    if not BOT_TOKEN:
        raise SystemExit('Missing TELEGRAM_BOT_TOKEN')

    chat_id = sys.argv[1]
    message_text = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_TEXT

    payload = {
        'chat_id': chat_id,
        'text': message_text,
        'reply_markup': {
            'inline_keyboard': [[
                {
                    'text': BUTTON_TEXT,
                    'web_app': {'url': MINIAPP_URL},
                }
            ]]
        },
    }
    req = urllib.request.Request(
        f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read().decode('utf-8'))
    print(json.dumps(body, ensure_ascii=False, indent=2))
    if not body.get('ok'):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
