import assert from "node:assert/strict";

const worker = (await import("./src/index.js")).default;

const allowedEnv = {
  ALLOWED_ORIGINS: "https://iamnshrd.github.io,http://localhost:4173",
};

function request(path, init = {}) {
  return new Request(`https://kalshi-mentions-api.test${path}`, init);
}

async function readJson(response) {
  return JSON.parse(await response.text());
}

async function testOptionsCors() {
  const response = await worker.fetch(
    request("/trade-api/v2/events/KXTRUMPMENTION-26MAY22", {
      method: "OPTIONS",
      headers: {
        Origin: "https://iamnshrd.github.io",
        "Access-Control-Request-Method": "GET",
      },
    }),
    allowedEnv
  );

  assert.equal(response.status, 204);
  assert.equal(response.headers.get("access-control-allow-origin"), "https://iamnshrd.github.io");
  assert.match(response.headers.get("access-control-allow-methods"), /GET/);
}

async function testMirrorsEventEndpoint() {
  const calls = [];
  globalThis.fetch = async (url) => {
    calls.push(String(url));
    return Response.json({ event: { event_ticker: "KXTRUMPMENTION-26MAY22", markets: [] } });
  };

  const response = await worker.fetch(
    request("/trade-api/v2/events/KXTRUMPMENTION-26MAY22?with_nested_markets=true", {
      headers: { Origin: "http://localhost:4173" },
    }),
    allowedEnv
  );
  const payload = await readJson(response);

  assert.equal(response.status, 200);
  assert.equal(response.headers.get("access-control-allow-origin"), "http://localhost:4173");
  assert.deepEqual(payload, {
    event: { event_ticker: "KXTRUMPMENTION-26MAY22", markets: [] },
  });
  assert.equal(
    calls[0],
    "https://external-api.kalshi.com/trade-api/v2/events/KXTRUMPMENTION-26MAY22?with_nested_markets=true"
  );
}

async function testMirrorsRootEventEndpoint() {
  const calls = [];
  globalThis.fetch = async (url) => {
    calls.push(String(url));
    return Response.json({ event: { event_ticker: "KXTRUMPMENTION-26MAY22", markets: [] } });
  };

  const response = await worker.fetch(
    request("/events/KXTRUMPMENTION-26MAY22?with_nested_markets=true", {
      headers: { Origin: "http://localhost:4173" },
    }),
    allowedEnv
  );

  assert.equal(response.status, 200);
  assert.equal(
    calls[0],
    "https://external-api.kalshi.com/trade-api/v2/events/KXTRUMPMENTION-26MAY22?with_nested_markets=true"
  );
}

async function testFallsBackToHistoricalMarkets() {
  const calls = [];
  globalThis.fetch = async (url) => {
    calls.push(String(url));
    if (String(url).includes("/historical/markets")) {
      return Response.json({
        markets: [{ ticker: "KXTRUMPMENTION-26MAR27-WATER", yes_sub_title: "Water" }],
      });
    }

    return Response.json({ event: { event_ticker: "KXTRUMPMENTION-26MAR27" }, markets: [] });
  };

  const response = await worker.fetch(
    request("/events/KXTRUMPMENTION-26MAR27?with_nested_markets=true", {
      headers: { Origin: "https://iamnshrd.github.io" },
    }),
    allowedEnv
  );
  const payload = await readJson(response);

  assert.equal(response.status, 200);
  assert.equal(payload.markets.length, 1);
  assert.equal(payload.markets[0].ticker, "KXTRUMPMENTION-26MAR27-WATER");
  assert.equal(payload.event.markets.length, 1);
  assert.equal(
    calls[1],
    "https://external-api.kalshi.com/trade-api/v2/historical/markets?event_ticker=KXTRUMPMENTION-26MAR27&limit=1000"
  );
}

async function testFallsBackToHistoricalMarketsWhenEventIsRateLimited() {
  const calls = [];
  globalThis.fetch = async (url) => {
    calls.push(String(url));
    if (String(url).includes("/historical/markets")) {
      return Response.json({
        markets: [{ ticker: "KXTRUMPMENTION-26MAR27-WATER", yes_sub_title: "Water" }],
      });
    }

    return Response.json(
      { error: { code: "too_many_requests", message: "too many requests" } },
      { status: 429 }
    );
  };

  const response = await worker.fetch(
    request("/events/KXTRUMPMENTION-26MAR27?with_nested_markets=true", {
      headers: { Origin: "https://iamnshrd.github.io" },
    }),
    allowedEnv
  );
  const payload = await readJson(response);

  assert.equal(response.status, 200);
  assert.equal(payload.event_ticker, "KXTRUMPMENTION-26MAR27");
  assert.equal(payload.markets.length, 1);
  assert.equal(payload.markets[0].ticker, "KXTRUMPMENTION-26MAR27-WATER");
  assert.equal(calls.length, 2);
}

async function testMirrorsHistoricalMarketsEndpoint() {
  const calls = [];
  globalThis.fetch = async (url) => {
    calls.push(String(url));
    return Response.json({ markets: [] });
  };

  const response = await worker.fetch(
    request("/historical/markets?event_ticker=KXTRUMPMENTION-26MAR27&limit=1000"),
    allowedEnv
  );

  assert.equal(response.status, 200);
  assert.equal(
    calls[0],
    "https://external-api.kalshi.com/trade-api/v2/historical/markets?event_ticker=KXTRUMPMENTION-26MAR27&limit=1000"
  );
}

async function testLegacyEndpointNormalizesNestedMarkets() {
  globalThis.fetch = async () =>
    Response.json({
      event: {
        event_ticker: "KXTRUMPMENTION-26MAY22",
        title: "What will Trump say?",
        markets: [{ ticker: "KXTRUMPMENTION-26MAY22-NQE", yes_sub_title: "Event does not qualify" }],
      },
    });

  const response = await worker.fetch(
    request("/api/kalshi-event?market_url=https%3A%2F%2Fkalshi.com%2Fmarkets%2Fkxtrumpmention%2Fwhat-will-trump-say%2Fkxtrumpmention-26may22", {
      headers: { Origin: "https://iamnshrd.github.io" },
    }),
    allowedEnv
  );
  const payload = await readJson(response);

  assert.equal(response.status, 200);
  assert.equal(payload.event_ticker, "KXTRUMPMENTION-26MAY22");
  assert.equal(payload.markets.length, 1);
  assert.equal(payload.markets[0].ticker, "KXTRUMPMENTION-26MAY22-NQE");
}

async function testRejectsMissingTicker() {
  const response = await worker.fetch(
    request("/api/kalshi-event?market_url=https%3A%2F%2Fkalshi.com%2Fmarkets%2Fmissing"),
    allowedEnv
  );
  const payload = await readJson(response);

  assert.equal(response.status, 400);
  assert.match(payload.error, /ticker/i);
}

for (const test of [
  testOptionsCors,
  testMirrorsEventEndpoint,
  testMirrorsRootEventEndpoint,
  testFallsBackToHistoricalMarkets,
  testFallsBackToHistoricalMarketsWhenEventIsRateLimited,
  testMirrorsHistoricalMarketsEndpoint,
  testLegacyEndpointNormalizesNestedMarkets,
  testRejectsMissingTicker,
]) {
  await test();
}
