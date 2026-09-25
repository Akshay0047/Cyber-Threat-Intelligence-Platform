const JSON_HEADERS = { "Content-Type": "application/json" };

export function errorMessage(error) {
  const data = error?.data;
  if (!data) return error?.message || "Request failed";
  if (typeof data.detail === "string") return data.detail;
  if (typeof data === "object") {
    return Object.entries(data)
      .map(([key, value]) => `${key}: ${[].concat(value).join(" ")}`)
      .join("; ");
  }
  return error.message || "Request failed";
}

export async function api(path, { method = "GET", body } = {}) {
  const response = await fetch(path, {
    method,
    credentials: "include",
    headers: body === undefined ? undefined : JSON_HEADERS,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await response.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { detail: text };
    }
  }
  if (response.status === 401 && !path.startsWith("/api/auth/login")) {
    if (!window.location.pathname.startsWith("/login")) {
      window.location.assign("/login");
    }
    const error = new Error(data?.detail || "Authentication required");
    error.status = 401;
    error.data = data;
    throw error;
  }
  if (!response.ok) {
    const error = new Error(errorMessage({ data, message: response.statusText }));
    error.status = response.status;
    error.data = data;
    throw error;
  }
  return data;
}
