import http from "k6/http";
import { sleep } from "k6";
import {
  BASE_URL,
  JSON_HEADERS,
  THRESHOLDS_LOAD,
  checkCreated,
  checkOk,
  itemLatency,
  randomItem,
} from "./lib/helpers.js";

export const options = {
  stages: [
    { duration: "1m", target: 50 },
    { duration: "3m", target: 50 },
    { duration: "1m", target: 0 },
  ],
  thresholds: {
    ...THRESHOLDS_LOAD,
    item_request_duration: ["p(95)<300"],
  },
};

function listItems() {
  const start = Date.now();
  const res = http.get(`${BASE_URL}/v1/items/`);
  itemLatency.add(Date.now() - start);
  checkOk(res, "list");
}

function getItem() {
  const id = Math.floor(Math.random() * 500) + 1;
  const start = Date.now();
  const res = http.get(`${BASE_URL}/v1/items/${id}`);
  itemLatency.add(Date.now() - start);
  if (res.status !== 404) checkOk(res, "get");
}

function createItem() {
  const res = http.post(
    `${BASE_URL}/v1/items/`,
    JSON.stringify(randomItem()),
    { headers: JSON_HEADERS }
  );
  checkCreated(res, "create");
}

function healthCheck() {
  checkOk(http.get(`${BASE_URL}/admin/health`), "health");
}

export default function () {
  const roll = Math.random();

  if (roll < 0.60) {
    listItems();
  } else if (roll < 0.85) {
    getItem();
  } else if (roll < 0.95) {
    createItem();
  } else {
    healthCheck();
  }

  sleep(Math.random() * 0.5 + 0.1);
}
