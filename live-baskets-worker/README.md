# Live Baskets Kalshi API Bridge

Cloudflare Worker for `live-baskets`. It reads Kalshi from the server side and adds CORS for the GitHub Pages app.

## Deploy

```bash
cd live-baskets-worker
npx wrangler deploy
```

If Wrangler cannot infer the account, run:

```bash
CLOUDFLARE_ACCOUNT_ID=<account-id> npx wrangler deploy
```

After deploy, set `window.LIVE_BASKETS_API_BASE` in `live-baskets/config.js` to:

```js
window.LIVE_BASKETS_API_BASE = "https://<your-worker-host>/trade-api/v2";
```

## Endpoints

- `GET /trade-api/v2/events/:eventTicker?with_nested_markets=true`
- `GET /api/kalshi-event?market_url=<kalshi event url>`

The first endpoint mirrors the Kalshi event API shape. The second is kept as a legacy compatibility route.
