window.LIVE_BASKETS_API_BASE =
  new URLSearchParams(window.location.search).get("api_base") ||
  window.LIVE_BASKETS_API_BASE ||
  "https://kalshi-mentions-api.iloveyaphets.workers.dev/trade-api/v2";

(() => {
  const directBase = "https://external-api.kalshi.com/trade-api/v2";
  const configuredBase = String(window.LIVE_BASKETS_API_BASE || "").replace(/\/$/, "");
  if (!configuredBase) return;

  const nativeFetch = window.fetch.bind(window);
  window.fetch = (input, init) => {
    if (typeof input === "string" && input.startsWith(directBase)) {
      return nativeFetch(input.replace(directBase, configuredBase), init);
    }

    if (input instanceof Request && input.url.startsWith(directBase)) {
      return nativeFetch(new Request(input.url.replace(directBase, configuredBase), input), init);
    }

    return nativeFetch(input, init);
  };
})();
