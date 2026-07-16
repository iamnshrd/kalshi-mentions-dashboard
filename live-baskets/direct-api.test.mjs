import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import assert from "node:assert/strict";

const here = dirname(fileURLToPath(import.meta.url));
const html = readFileSync(join(here, "index.html"), "utf8");
const config = readFileSync(join(here, "config.js"), "utf8");
const assetMatch = html.match(/src="\.\/assets\/([^"]+\.js)"/);
const cssMatch = html.match(/href="\.\/assets\/([^"?]+\.css)(?:\?[^"]*)?"/);

assert.ok(assetMatch, "live-baskets index.html should reference a JS asset");
assert.ok(cssMatch, "live-baskets index.html should reference a CSS asset");
assert.ok(
  html.includes('<script src="./config.js?v=20260716-archive-fallback"></script>'),
  "live-baskets should load config.js before the module bundle"
);

const bundle = readFileSync(join(here, "assets", assetMatch[1]), "utf8");
const styles = readFileSync(join(here, "assets", cssMatch[1]), "utf8");

assert.ok(
  bundle.includes("https://external-api.kalshi.com/trade-api/v2"),
  "loader should keep the direct Kalshi API as a fallback"
);
assert.ok(
  config.includes("LIVE_BASKETS_API_BASE") &&
    config.includes('get("api_base")') &&
    config.includes("window.fetch"),
  "config.js should allow a deployed Worker base URL to rewrite Kalshi API requests"
);
assert.ok(
  config.includes("kalshi-mentions-api.iloveyaphets.workers.dev") &&
    !config.includes("workers.dev/trade-api/v2"),
  "default Worker base should match the deployed root-level proxy routes"
);
assert.ok(
  config.includes("/historical/markets?event_ticker="),
  "archived events should fall back to Kalshi historical markets when live event markets are empty"
);
assert.ok(
  bundle.includes("with_nested_markets=true"),
  "event fetch should request nested markets so strikes come from the event payload"
);
assert.ok(
  bundle.includes("event.markets"),
  "loader should read nested event.markets returned by the Kalshi event API"
);
assert.equal(
  bundle.includes("139.84.170.170.nip.io"),
  false,
  "bundle should not depend on the dead nip.io proxy"
);
assert.equal(
  bundle.includes("/api/kalshi-event"),
  false,
  "bundle should not depend on the old kalshi-event proxy route"
);
assert.ok(
  styles.includes(".basket-pill-name{flex:1 1 auto}") &&
    styles.includes(".basket-pill-price,.stage-toggle{display:none}"),
  "basket strike pills should hide prices and the middle stage toggle while letting names fill the space"
);
