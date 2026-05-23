import { ApiError } from "./errors";
import type {
  ConfigResponse, DatasetInfo, HealthResponse,
  RagRequest, RagResponse,
  RetrieveRequest, RetrieveResponse
} from "./types";

const API_BASE: string = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/+$/, "") || "";

function readErrorDetail(body: unknown, fallback: string): string {
  if (body && typeof body === "object" && "detail" in body) {
    return String((body as { detail: unknown }).detail);
  }

  return fallback;
}

async function parseJsonResponse(res: Response): Promise<unknown> {
  const text = await res.text();

  if (!text) {
    return null;
  }

  const contentType = res.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    throw new ApiError(
      res.status,
      `Expected JSON from ${res.url}, got ${contentType || "unknown content type"}`,
      text);
  }

  return JSON.parse(text);
}

async function request<T>(path: string, init: RequestInit = {}, timeoutMs = 30_000): Promise<T> {
  const ctrl = new AbortController();
  const timer = window.setTimeout(() => ctrl.abort(), timeoutMs);

  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        ...(init.headers || {}),
      },
      signal: ctrl.signal,
    });

    const body = await parseJsonResponse(res);

    if (!res.ok) {
      throw new ApiError(res.status, readErrorDetail(body, res.statusText), body);
    }

    return body as T;
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError(408, `Request timed out after ${Math.round(timeoutMs / 1000)} seconds.`, null);
    }

    throw err;
  } finally {
    window.clearTimeout(timer);
  }
}

function postJson<TResponse, TBody>(path: string, body: TBody, timeoutMs?: number): Promise<TResponse> {
  return request<TResponse>(path, { method: "POST", body: JSON.stringify(body) }, timeoutMs);
}

function normalizeDatasets(data: unknown): DatasetInfo[] {
  if (Array.isArray(data)) {
    return data as DatasetInfo[];
  }

  if (data && typeof data === "object" &&"datasets" in data && 
    Array.isArray((data as { datasets: unknown }).datasets)) {
    return (data as { datasets: DatasetInfo[] }).datasets;
  }

  return [];
}

export const api = {
  health: () => request<HealthResponse>("/api/health"),
  config: () => request<ConfigResponse>("/api/config"),
  datasets: async () => normalizeDatasets(await request<unknown>("/api/datasets")),
  retrieve: (body: RetrieveRequest) =>
    postJson<RetrieveResponse, RetrieveRequest>("/api/retrieve", body),
  rag: (body: RagRequest) =>
    postJson<RagResponse, RagRequest>("/api/rag", body, 120_000),
};
