import { getConfig } from "./config";

/**
 * Get url with proper base
 * Example: path = "/v1/health", base_path = "/api", return "/api/v1/health"
 *
 * There are many cases our client can be served:
 * 1. At root, base_path = "/"
 * 2. At root and subpath, /admin/darq
 * 3. At prefix, /app/admin/darq where /admin/darq is the base_path and the /app is the prefix added by the reverse proxy
 * 4. Embed mode (in iframe)
 **/
export function getApiUrl(path) {
  let basePath = getConfig().base_path;
  if (basePath === "/") {
    return path;
  }

  // from iframe
  if (getConfig().embed) {
    return window.location.pathname.replace(/\/embed$/, "") + path;
  }

  return window.location.pathname + path;
}

function postOptions(data = null) {
  let config = {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
  };

  if (data !== null) {
    config["body"] = JSON.stringify(data);
  }
  return config;
}

function getOptions() {
  return {
    method: "GET",
    credentials: "same-origin",
  };
}

export const postCall = async (url, data = null, params = null) => {
  const queryParams = new URLSearchParams(params);
  const urlWithParams = getApiUrl(url) + (params ? `?${queryParams}` : "");
  try {
    const response = await fetch(urlWithParams, postOptions(data));
    if (response.ok || response.status === 400) {
      return response.json();
    }
  } catch (e) {
    console.log("[POST] Fetch Error :-S", e);
    throw e;
  }
};

export const getCall = async (url, params = null) => {
  const queryParams = new URLSearchParams(params);
  const urlWithParams = getApiUrl(url) + (params ? `?${queryParams}` : "");

  try {
    const response = await fetch(urlWithParams, getOptions());
    if (response.ok) {
      return response.json();
    }
  } catch (e) {
    console.log("[GET] Fetch Error :-S", e);
    throw e;
  }
};
