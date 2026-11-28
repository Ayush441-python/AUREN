/** Local backend fallback used when no API URL is configured. */
export const LOCAL_API_BASE = "http://127.0.0.1:8000";

/** Deployed backend used when neither a saved override nor an env URL is set. */
export const PRODUCTION_API_BASE = "https://auren-api-8yrq.onrender.com";

export type ApiBaseInputs = {
  /** The `auren_api_url` localStorage override, if any. */
  saved?: string | null;
  /** `NEXT_PUBLIC_API_URL`, inlined at build time. */
  envUrl?: string | null;
  /** `window.location.hostname`, if running in a browser. */
  hostname?: string | null;
};

const clean = (value?: string | null): string =>
  (value ?? "").trim().replace(/\/+$/, "");

/**
 * Resolve the API base URL.
 *
 * Precedence, highest first:
 *   1. the saved `auren_api_url` override,
 *   2. an explicit `NEXT_PUBLIC_API_URL`,
 *   3. a hostname-dependent default: the local backend on localhost/127.0.0.1,
 *      the deployed backend everywhere else.
 *
 * An explicit env URL must win on localhost too: pointing the web app at a
 * backend on another port is exactly what the env var is for, and returning
 * the port-8000 default instead silently sends requests to a server that is
 * not listening.
 */
export const resolveApiBase = ({ saved, envUrl, hostname }: ApiBaseInputs): string => {
  const fromStorage = clean(saved);
  if (fromStorage) return fromStorage;

  const fromEnv = clean(envUrl);
  if (fromEnv) return fromEnv;

  if (hostname === "localhost" || hostname === "127.0.0.1") return LOCAL_API_BASE;

  return PRODUCTION_API_BASE;
};
