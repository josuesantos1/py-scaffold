import { check } from "k6";
import { Rate, Trend } from "k6/metrics";

export const BASE_URL = __ENV.K6_BASE_URL || "http://localhost:1112";

export const errorRate = new Rate("errors");
export const itemLatency = new Trend("item_request_duration", true);

export function checkOk(res, tag) {
  const ok = check(res, {
    [`${tag}: status 200`]: (r) => r.status === 200,
    [`${tag}: has body`]: (r) => r.body && r.body.length > 0,
  });
  errorRate.add(!ok);
  return ok;
}

export function checkCreated(res, tag) {
  const ok = check(res, {
    [`${tag}: status 201`]: (r) => r.status === 201,
    [`${tag}: has body`]: (r) => r.body && r.body.length > 0,
  });
  errorRate.add(!ok);
  return ok;
}

export function checkNotFound(res, tag) {
  return check(res, {
    [`${tag}: status 404`]: (r) => r.status === 404,
  });
}

export function checkUnprocessable(res, tag) {
  return check(res, {
    [`${tag}: status 422`]: (r) => r.status === 422,
  });
}

export const THRESHOLDS_SMOKE = {
  http_req_duration: ["p(95)<100", "p(99)<200"],
  http_req_failed: ["rate<0.01"],
  errors: ["rate<0.01"],
};

export const THRESHOLDS_LOAD = {
  http_req_duration: ["p(95)<300", "p(99)<500"],
  http_req_failed: ["rate<0.02"],
  errors: ["rate<0.02"],
};

export const THRESHOLDS_STRESS = {
  http_req_duration: ["p(95)<1000", "p(99)<2000"],
  http_req_failed: ["rate<0.10"],
  errors: ["rate<0.10"],
};

export const THRESHOLDS_SOAK = {
  http_req_duration: ["p(95)<400", "p(99)<700"],
  http_req_failed: ["rate<0.02"],
  errors: ["rate<0.02"],
};

export const JSON_HEADERS = { "Content-Type": "application/json" };

export function randomItem() {
  const id = Math.floor(Math.random() * 100) + 1;
  return {
    name: `item-${id}`,
    description: Math.random() > 0.5 ? `description for item ${id}` : null,
  };
}
