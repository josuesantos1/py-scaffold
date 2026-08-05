import http from "k6/http";
import { sleep } from "k6";
import {
  BASE_URL,
  JSON_HEADERS,
  THRESHOLDS_SMOKE,
  checkCreated,
  checkNotFound,
  checkOk,
  checkUnprocessable,
  randomItem,
} from "./lib/helpers.js";

export const options = {
  vus: 1,
  duration: "30s",
  thresholds: THRESHOLDS_SMOKE,
};

export default function () {
  checkOk(http.get(`${BASE_URL}/admin/health`), "health");
  checkOk(http.get(`${BASE_URL}/admin/ready`), "ready");

  checkOk(http.get(`${BASE_URL}/v1/items/`), "list items");

  const create = http.post(
    `${BASE_URL}/v1/items/`,
    JSON.stringify(randomItem()),
    { headers: JSON_HEADERS }
  );
  checkCreated(create, "create item");

  if (create.status === 201) {
    const id = JSON.parse(create.body).id;
    checkOk(http.get(`${BASE_URL}/v1/items/${id}`), "get item");
  }

  checkNotFound(http.get(`${BASE_URL}/v1/items/99999999`), "get missing");

  checkUnprocessable(
    http.post(`${BASE_URL}/v1/items/`, "}{not-json", { headers: JSON_HEADERS }),
    "invalid body"
  );

  sleep(1);
}
