window.LIVE_BASKETS_API_BASE =
  new URLSearchParams(window.location.search).get("api_base") ||
  window.LIVE_BASKETS_API_BASE ||
  "https://kalshi-mentions-api.iloveyaphets.workers.dev";

(() => {
  const directBase = "https://external-api.kalshi.com/trade-api/v2";
  const configuredBase = String(window.LIVE_BASKETS_API_BASE || "").replace(/\/$/, "");
  if (!configuredBase) return;

  const nativeFetch = window.fetch.bind(window);
  window.fetch = async (input, init) => {
    if (typeof input === "string" && input.startsWith(directBase)) {
      return withArchivedMarketsFallback(
        nativeFetch(input.replace(directBase, configuredBase), init),
        input,
        configuredBase
      );
    }

    if (input instanceof Request && input.url.startsWith(directBase)) {
      return withArchivedMarketsFallback(
        nativeFetch(new Request(input.url.replace(directBase, configuredBase), input), init),
        input.url,
        configuredBase
      );
    }

    return nativeFetch(input, init);
  };

  async function withArchivedMarketsFallback(responsePromise, originalUrl, apiBase) {
    const response = await responsePromise;
    const eventTicker = parseEventTicker(originalUrl);
    if (!eventTicker || !response.ok) return response;

    try {
      const payload = await response.clone().json();
      const liveMarkets = getMarkets(payload);
      if (liveMarkets.length) return response;

      const historicalUrl = `${apiBase}/historical/markets?event_ticker=${encodeURIComponent(eventTicker)}&limit=1000`;
      const historicalResponse = await nativeFetch(historicalUrl);
      if (!historicalResponse.ok) return response;

      const historicalPayload = await historicalResponse.json();
      const archivedMarkets = Array.isArray(historicalPayload.markets)
        ? historicalPayload.markets
        : [];
      if (!archivedMarkets.length) return response;

      const event = { ...(payload.event || {}), markets: archivedMarkets };
      return Response.json(
        { ...payload, event, markets: archivedMarkets },
        { status: response.status, statusText: response.statusText }
      );
    } catch {
      return response;
    }
  }

  function parseEventTicker(value) {
    const match = String(value || "").match(/\/events\/([A-Z0-9-]+)/i);
    return match ? match[1].toUpperCase() : null;
  }

  function getMarkets(payload) {
    if (Array.isArray(payload?.event?.markets)) return payload.event.markets;
    if (Array.isArray(payload?.markets)) return payload.markets;
    return [];
  }
})();
