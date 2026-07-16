const KALSHI_API_BASE = "https://external-api.kalshi.com/trade-api/v2";
const DEFAULT_ALLOWED_ORIGINS = [
  "https://iamnshrd.github.io",
  "http://localhost:4173",
  "http://127.0.0.1:4173",
];

export default {
  async fetch(request, env = {}) {
    const origin = request.headers.get("Origin");
    const corsHeaders = buildCorsHeaders(origin, env);

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders });
    }

    if (request.method !== "GET") {
      return json({ error: "Method not allowed" }, 405, corsHeaders);
    }

    try {
      const url = new URL(request.url);

      if (isEventPath(url.pathname)) {
        return mirrorKalshiEvent(url, corsHeaders);
      }

      if (isHistoricalMarketsPath(url.pathname)) {
        return mirrorKalshiHistoricalMarkets(url, corsHeaders);
      }

      if (url.pathname === "/api/kalshi-event") {
        return legacyKalshiEvent(url, corsHeaders);
      }

      return json({ error: "Not found" }, 404, corsHeaders);
    } catch (error) {
      return json({ error: error.message || "Worker error" }, 500, corsHeaders);
    }
  },
};

async function mirrorKalshiEvent(url, corsHeaders) {
  const ticker = parseTicker(url.pathname);
  if (!ticker) {
    return json({ error: "Could not parse Kalshi event ticker" }, 400, corsHeaders);
  }

  const upstreamUrl = new URL(`${KALSHI_API_BASE}/events/${encodeURIComponent(ticker)}`);
  upstreamUrl.search = url.search;
  if (!upstreamUrl.searchParams.has("with_nested_markets")) {
    upstreamUrl.searchParams.set("with_nested_markets", "true");
  }

  const upstream = await fetch(upstreamUrl.toString());
  const body = await upstream.text();
  if (!upstream.ok) {
    const historicalMarkets = await fetchHistoricalMarkets(ticker);
    if (historicalMarkets.length) {
      return json(
        addMarketsToPayload({ event: { event_ticker: ticker }, event_ticker: ticker }, historicalMarkets),
        200,
        corsHeaders
      );
    }

    return proxyJsonText(body, upstream, corsHeaders);
  }

  const payload = JSON.parse(body);
  const markets = getMarkets(payload);
  if (markets.length) {
    return json(payload, 200, corsHeaders);
  }

  const historicalMarkets = await fetchHistoricalMarkets(ticker);
  if (!historicalMarkets.length) {
    return json(payload, 200, corsHeaders);
  }

  return json(addMarketsToPayload(payload, historicalMarkets), 200, corsHeaders);
}

async function mirrorKalshiHistoricalMarkets(url, corsHeaders) {
  const upstreamUrl = new URL(`${KALSHI_API_BASE}/historical/markets`);
  upstreamUrl.search = url.search;

  const upstream = await fetch(upstreamUrl.toString());
  return proxyJsonResponse(upstream, corsHeaders);
}

async function legacyKalshiEvent(url, corsHeaders) {
  const ticker = parseTicker(url.searchParams.get("market_url") || url.searchParams.get("ticker"));
  if (!ticker) {
    return json({ error: "Could not parse Kalshi event ticker" }, 400, corsHeaders);
  }

  const upstream = await fetch(
    `${KALSHI_API_BASE}/events/${encodeURIComponent(ticker)}?with_nested_markets=true`
  );
  const payload = await upstream.json();

  if (!upstream.ok) {
    return json(payload, upstream.status, corsHeaders);
  }

  const normalized = normalizeEventPayload(payload, ticker);
  if (normalized.markets.length) {
    return json(normalized, 200, corsHeaders);
  }

  const historicalMarkets = await fetchHistoricalMarkets(ticker);
  return json(
    historicalMarkets.length ? addMarketsToPayload(normalized, historicalMarkets) : normalized,
    200,
    corsHeaders
  );
}

async function proxyJsonResponse(upstream, corsHeaders) {
  const body = await upstream.text();
  return proxyJsonText(body, upstream, corsHeaders);
}

function proxyJsonText(body, upstream, corsHeaders) {
  const headers = new Headers(corsHeaders);
  headers.set("content-type", upstream.headers.get("content-type") || "application/json");
  headers.set("cache-control", "no-store");

  return new Response(body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers,
  });
}

function normalizeEventPayload(payload, fallbackTicker) {
  const event = payload.event || payload;
  const markets = getMarkets(payload);

  return {
    ...payload,
    event,
    event_ticker: payload.event_ticker || event.event_ticker || fallbackTicker,
    markets,
  };
}

async function fetchHistoricalMarkets(eventTicker) {
  const historicalUrl = new URL(`${KALSHI_API_BASE}/historical/markets`);
  historicalUrl.searchParams.set("event_ticker", eventTicker);
  historicalUrl.searchParams.set("limit", "1000");

  const response = await fetch(historicalUrl.toString());
  if (!response.ok) return [];

  const payload = await response.json();
  return Array.isArray(payload.markets) ? payload.markets : [];
}

function addMarketsToPayload(payload, markets) {
  const event = { ...(payload.event || {}), markets };
  return {
    ...payload,
    event,
    markets,
  };
}

function getMarkets(payload) {
  if (Array.isArray(payload?.event?.markets)) return payload.event.markets;
  if (Array.isArray(payload?.markets)) return payload.markets;
  return [];
}

function isEventPath(pathname) {
  return pathname.startsWith("/events/") || pathname.startsWith("/trade-api/v2/events/");
}

function isHistoricalMarketsPath(pathname) {
  return pathname === "/historical/markets" || pathname === "/trade-api/v2/historical/markets";
}

function parseTicker(value) {
  const match = String(value || "").match(/\b([a-z0-9]+-\d{2}[a-z]{3}\d+[a-z]?)\b/i);
  return match ? match[1].toUpperCase() : null;
}

function buildCorsHeaders(origin, env) {
  const allowed = new Set(
    String(env.ALLOWED_ORIGINS || DEFAULT_ALLOWED_ORIGINS.join(","))
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean)
  );
  const headers = new Headers({
    "access-control-allow-methods": "GET, OPTIONS",
    "access-control-allow-headers": "content-type",
    "access-control-max-age": "86400",
    vary: "Origin",
  });

  if (origin && allowed.has(origin)) {
    headers.set("access-control-allow-origin", origin);
  }

  return headers;
}

function json(payload, status = 200, headers = new Headers()) {
  const responseHeaders = new Headers(headers);
  responseHeaders.set("content-type", "application/json; charset=utf-8");
  responseHeaders.set("cache-control", "no-store");

  return new Response(JSON.stringify(payload), {
    status,
    headers: responseHeaders,
  });
}
