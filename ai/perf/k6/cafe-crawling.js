import http from "k6/http";
import { check, sleep } from "k6";

const baseUrl = __ENV.BASE_URL || "http://127.0.0.1:8000";
const payloadName = __ENV.PAYLOAD || "1-cafe";
const vus = Number(__ENV.VUS || 1);
const iterations = Number(__ENV.ITERATIONS || 10);
const thinkTime = Number(__ENV.THINK_TIME || 0);
const payloadPath = `./fixtures/${payloadName}.json`;
const payloadText = open(payloadPath);
const payloadData = JSON.parse(payloadText);

if (!Array.isArray(payloadData)) {
  throw new Error(`Payload fixture must be a JSON array: ${payloadPath}`);
}

if (payloadData.length === 0) {
  throw new Error(`Payload fixture must contain at least one cafe: ${payloadPath}`);
}

export const options = {
  vus,
  iterations,
};

export default function () {
  const response = http.post(`${baseUrl}/ai/cafes/crawling`, JSON.stringify(payloadData), {
    headers: { "Content-Type": "application/json" },
    tags: { payload: payloadName, cafe_count: String(payloadData.length) },
  });

  check(response, {
    "status is 200": (res) => res.status === 200,
  });

  if (thinkTime > 0) {
    sleep(thinkTime);
  }
}
