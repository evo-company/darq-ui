import { getConfig } from './config';

/**
 * Get url with proper base 
* Example: path = "/v1/health", base_path = "/api", return "/api/v1/health"
 */
export function getApiUrl(path) {
  let basePath = getConfig().base_path;
  if (basePath === "/") {
    return path;
  }

  return basePath + path;
}


function postOptions(data = null) {
  let config = {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin"
  };

  if (data !== null) {
    config["body"] = JSON.stringify(data)
  }
  return config;
}

function getOptions() {
  return {
    method: 'GET',
    credentials: 'same-origin'
  };
}

export const postCall = async (url, data = null, params = null) => {
  const queryParams = new URLSearchParams(params);
  const urlWithParams = getApiUrl(url) + (params ? `?${queryParams}` : '');
  try {
    const response = await fetch(urlWithParams, postOptions(data));
    if (response.ok || response.status === 400) {
      return response.json();
      // } else if (response.status === 401) {
      //     unauthorizedAccess();
    }
  } catch (e) {
    console.log('[POST] Fetch Error :-S', err);
    throw e;
  }
}

export const getCall = async (url, params = null) => {
  const queryParams = new URLSearchParams(params);
  const urlWithParams = getApiUrl(url) + (params ? `?${queryParams}` : '');

  try {
    const response = await fetch(urlWithParams, getOptions());
    if (response.ok) {
      return response.json();
      // } else if (response.status === 401) {
      //   unauthorizedAccess();
    }
  } catch (e) {
    console.log('[GET] Fetch Error :-S', err);
    throw e;
  }
}
