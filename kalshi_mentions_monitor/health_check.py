from __future__ import annotations

from kalshi_mentions_monitor.app.config import Settings
from kalshi_mentions_monitor.app.health import build_health_summary, health_to_text


def main() -> None:
    s = Settings()
    print(health_to_text(build_health_summary(s.db_path)))


if __name__ == '__main__':
    main()
