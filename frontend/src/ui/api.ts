const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export type Token = { access_token: string; token_type: string };
export type User = { id: number; username: string; role: string };
export type Model = {
  id: number;
  owner_id: number;
  name: string;
  description?: string | null;
  task: string;
  created_at: string;
  updated_at?: string | null;
};
export type ModelCreate = {
  name: string;
  description?: string | null;
  task: string;
};
export type Version = {
  id: number;
  model_id: number;
  version: string;
  service_url: string;
  artifact_uri: string;
  status: string;
  created_at: string;
  updated_at: string;
};
export type ApiKey = { id: number; created_at: string; is_active: boolean };

async function request<T>(path: string, init: RequestInit = {}, token?: string) {
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!res.ok) throw new Error(await res.text());
  return (await res.json()) as T;
}

export const api = {
  register: (username: string, password: string) =>
    request<User>("/auth/register", { method: "POST", body: JSON.stringify({ username, password, role: "user" }) }),
  login: async (username: string, password: string) => {
    const body = new URLSearchParams({ username, password });
    return request<Token>("/auth/login", {
      method: "POST",
      body,
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
  },
  me: (token: string) => request<User>("/users/me", {}, token),
  dashboard: (token: string) => request<{ total_requests: number; average_latency_ms: number; cache_hit_rate: number; active_models: number }>("/analytics/dashboard", {}, token),
  usage: (token: string) => request("/analytics/usage", {}, token),
  models: (token: string) => request<Model[]>("/models/", {}, token),
  createModel: (token: string, payload: ModelCreate) =>
    request<Model>("/models/", { method: "POST", body: JSON.stringify(payload) }, token),
  versions: (token: string, modelId: number) => request<{ versions: Version[] } & Model>(`/models/${modelId}/versions/`, {}, token),
  createVersion: (token: string, modelId: number, payload: Pick<Version, "version" | "service_url" | "artifact_uri">) =>
    request<Version>(`/models/${modelId}/versions/`, { method: "POST", body: JSON.stringify(payload) }, token),
  apiKeys: (token: string) => request<ApiKey[]>("/apikeys/", {}, token),
  createApiKey: (token: string, name: string) =>
    request<{ api_key: string; message: string }>(`/apikeys/create?name=${encodeURIComponent(name)}`, { method: "POST" }, token),
  revokeApiKey: (token: string, id: number) => request(`/apikeys/${id}`, { method: "DELETE" }, token),
  topModels: (token: string) => request<{ model: string; requests: number }[]>("/analytics/top-models", {}, token),
  latency: (token: string) => request<{ average: number; minimum: number; maximum: number }>("/analytics/latency", {}, token),
};
