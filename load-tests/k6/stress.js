import http from "k6/http";
import { sleep } from "k6";
import {
  BASE_URL,
  JSON_HEADERS,
  THRESHOLDS_STRESS,
  checkCreated,
  checkOk,
  randomItem,
} from "./lib/helpers.js";

export const options = {
  stages: [
    { duration: "30s", target: 50 },
    { duration: "1m", target: 100 },
    { duration: "1m", target: 200 },
    { duration: "1m", target: 300 },
    { duration: "30s", target: 0 },
  ],
  thresholds: THRESHOLDS_STRESS,
};

export default function () {
  const roll = Math.random();

  if (roll < 0.70) {
    checkOk(http.get(`${BASE_URL}/v1/items/`), "list");
  } else if (roll < 0.90) {
    const id = Math.floor(Math.random() * 100) + 1;
    const res = http.get(`${BASE_URL}/v1/items/${id}`);
    if (res.status !== 404) checkOk(res, "get");
  } else {
    checkCreated(
      http.post(
        `${BASE_URL}/v1/items/`,
        JSON.stringify(randomItem()),
        { headers: JSON_HEADERS }
      ),
      "create"
    );
  }

  sleep(Math.random() * 0.2);
}
