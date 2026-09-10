const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export async function api(path: string, opts: RequestInit = {}, token?: string) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(opts.headers as Record<string, string>),
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  const r = await fetch(`${API}${path}`, { ...opts, headers });
  if (!r.ok) {
    const t = await r.text();
    throw new Error(`${r.status} ${t}`);
  }
  return r.json();
}

export { API };
