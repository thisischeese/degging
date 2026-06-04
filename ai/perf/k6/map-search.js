import http from "k6/http";
import { check, sleep } from "k6";

const baseUrl = __ENV.BASE_URL || "http://127.0.0.1:8000";
const vus = Number(__ENV.VUS || 1);
const iterations = Number(__ENV.ITERATIONS || 300);
const thinkTime = Number(__ENV.THINK_TIME || 0);
const corpus = JSON.parse(open("../fixtures/query-preprocess-corpus.json"));
const basePayload = JSON.parse(open("../fixtures/map-search-base.json"));

if (!Array.isArray(corpus) || corpus.length === 0) {
  throw new Error("Map search corpus must be a non-empty JSON array.");
}

if (typeof basePayload !== "object" || basePayload === null || Array.isArray(basePayload)) {
  throw new Error("Map search base payload must be a JSON object.");
}

export const options = {
  vus,
  iterations,
};

function pickQuery() {
  return corpus[(__VU + __ITER) % corpus.length];
}

export default function () {
  const payload = {
    ...basePayload,
    keyword: pickQuery(),
  };
  const response = http.post(`${baseUrl}/ai/map/search`, JSON.stringify(payload), {
    headers: { "Content-Type": "application/json" },
    tags: { surface: "map-search" },
  });

  check(response, {
    "status is 200": (res) => res.status === 200,
  });

  if (thinkTime > 0) {
    sleep(thinkTime);
  }
}
