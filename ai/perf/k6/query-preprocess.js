import http from "k6/http";
import { check, sleep } from "k6";

const baseUrl = __ENV.BASE_URL || "http://127.0.0.1:8000";
const vus = Number(__ENV.VUS || 1);
const iterations = Number(__ENV.ITERATIONS || 300);
const thinkTime = Number(__ENV.THINK_TIME || 0);
const userId = __ENV.USER_ID || "123e4567-e89b-12d3-a456-426614174000";
const corpus = JSON.parse(open("../fixtures/query-preprocess-corpus.json"));

if (!Array.isArray(corpus) || corpus.length === 0) {
  throw new Error("Query preprocess corpus must be a non-empty JSON array.");
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
    query: pickQuery(),
    user_id: userId,
  };
  const response = http.post(`${baseUrl}/ai/cafe/query-preprocess`, JSON.stringify(payload), {
    headers: { "Content-Type": "application/json" },
    tags: { surface: "query-preprocess" },
  });

  check(response, {
    "status is 200": (res) => res.status === 200,
  });

  if (thinkTime > 0) {
    sleep(thinkTime);
  }
}
