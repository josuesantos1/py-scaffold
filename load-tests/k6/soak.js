import http from "k6/http";
import { sleep } from "k6";
import {
  BASE_URL,
  JSON_HEADERS,
  THRESHOLDS_SOAK,
  checkCreated,
  checkOk,
  itemLatency,
  randomItem,
} from "./lib/helpers.js";

export const options = {
  stages: [
    { duration: "2m", target: 20 },
    { duration: "10m", target: 20 },
    { duration: "1m", target: 0 },
  ],
  thresholds: THRESHOLDS_SOAK,
};

export default function () {
  const roll = Math.random();

  if (roll < 0.65) {
    const start = Date.now();
    const res = http.get(`${BASE_URL}/v1/items/`);
    itemLatency.add(Date.now() - start);
    checkOk(res, "list");
  } else if (roll < 0.85) {
    const id = Math.floor(Math.random() * 50) + 1;
    const start = Date.now();
    const res = http.get(`${BASE_URL}/v1/items/${id}`);
    itemLatency.add(Date.now() - start);
    if (res.status !== 404) checkOk(res, "get");
  } else if (roll < 0.95) {
    checkCreated(
      http.post(
        `${BASE_URL}/v1/items/`,
        JSON.stringify(randomItem()),
        { headers: JSON_HEADERS }
      ),
      "create"
    );
  } else {
    checkOk(http.get(`${BASE_URL}/admin/health`), "health");
  }

  sleep(Math.random() * 1 + 0.5);
}
