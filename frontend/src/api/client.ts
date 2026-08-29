export interface HealthResponse {
  status: string;
  version: string;
  llm_enabled: boolean;
}

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/healthz`);
  if (!response.ok) throw new Error(`API request failed: ${response.status}`);
  return response.json() as Promise<HealthResponse>;
}
