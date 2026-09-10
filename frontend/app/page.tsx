"use client";

import { useMemo, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "@/lib/api";

type Rec = { id: string; kind: string; priority: number; title: string; body: string; payload: Record<string, unknown> };
type Metrics = {
  n_mgkg: number;
  p_mgkg: number;
  k_mgkg: number;
  ph: number;
  ec_dsm: number;
  moisture_pct: number;
  temp_c: number;
  soc_pct: number;
  texture: string;
  soil_health: number;
  confidence: string;
  n_interval: [number, number];
  model_version: string;
};

const LANGS = [
  { id: "en", label: "English" },
  { id: "hi", label: "हिन्दी" },
  { id: "mr", label: "मराठी" },
];

function tone(kind: string, value: number) {
  if (kind === "moisture") return value < 16 ? "bg-amber-100 text-amber-900" : value > 40 ? "bg-sky-100 text-sky-900" : "bg-emerald-100 text-emerald-900";
  if (kind === "ph") return value < 6 || value > 7.8 ? "bg-amber-100 text-amber-900" : "bg-emerald-100 text-emerald-900";
  if (kind === "ec") return value > 2 ? "bg-rose-100 text-rose-900" : "bg-emerald-100 text-emerald-900";
  return "bg-emerald-50 text-emerald-950";
}

export default function Home() {
  const [lang, setLang] = useState("en");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [fieldId, setFieldId] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [recs, setRecs] = useState<Rec[]>([]);
  const [tool, setTool] = useState<Record<string, unknown> | null>(null);
  const [planted, setPlanted] = useState<Record<string, unknown> | null>(null);
  const [history, setHistory] = useState<{ t: string; n: number; moisture: number; health: number }[]>([]);

  const nextAction = recs[0]?.title;

  const tiles = useMemo(() => {
    if (!metrics) return [];
    return [
      { k: "N", v: `${metrics.n_mgkg.toFixed(0)} mg/kg`, sub: `CI ${metrics.n_interval?.[0]?.toFixed(0) ?? "–"}–${metrics.n_interval?.[1]?.toFixed(0) ?? "–"}`, kind: "n" },
      { k: "P", v: `${metrics.p_mgkg.toFixed(1)} mg/kg`, sub: "root builder", kind: "p" },
      { k: "K", v: `${metrics.k_mgkg.toFixed(0)} mg/kg`, sub: "disease shield", kind: "k" },
      { k: "pH", v: metrics.ph.toFixed(2), sub: "balance", kind: "ph", n: metrics.ph },
      { k: "EC", v: `${metrics.ec_dsm.toFixed(2)} dS/m`, sub: "salts", kind: "ec", n: metrics.ec_dsm },
      { k: "Moisture", v: `${metrics.moisture_pct.toFixed(1)}%`, sub: "irrigate?", kind: "moisture", n: metrics.moisture_pct },
      { k: "Temp", v: `${metrics.temp_c.toFixed(1)} °C`, sub: "germination", kind: "t" },
      { k: "SOC", v: `${metrics.soc_pct.toFixed(2)}%`, sub: "humus bank", kind: "soc" },
    ];
  }, [metrics]);

  async function runDemo() {
    setBusy(true);
    setError(null);
    try {
      const email = `demo${Date.now()}@example.com`;
      const auth = await api("/v1/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password: "soilguide", full_name: "Demo Farmer", language: lang }),
      });
      const t = auth.access_token as string;
      setToken(t);
      const farm = await api("/v1/farms", { method: "POST", body: JSON.stringify({ name: "Alandi demo farm", village: "Alandi" }) }, t);
      const field = await api(
        `/v1/farms/${farm.id}/fields`,
        { method: "POST", body: JSON.stringify({ name: "Wheat plot", crop_code: "wheat", area_ha: 1.0, soil_class: "black_cotton" }) },
        t
      );
      setFieldId(field.id);
      const sim = await api(`/v1/simulate?scenario=pune-wheat-n-deficient&field_id=${field.id}`, { method: "POST" }, t);
      setMetrics(sim.metrics);
      setRecs(sim.recommendations);
      setTool(sim.tool);
      setPlanted(sim.planted);
      const hist = await api(`/v1/fields/${field.id}/history`, {}, t);
      setHistory(hist.points || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto max-w-5xl px-4 py-6">
      <header className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-emerald-700">Sarathi of the Indian farmer</p>
          <h1 className="text-3xl font-semibold text-soil-900">Krishiayan</h1>
          <p className="text-sm text-stone-600">Raw probe → soil numbers → what fertilizer, when.</p>
        </div>
        <div className="flex items-center gap-2">
          {LANGS.map((l) => (
            <button
              key={l.id}
              onClick={() => setLang(l.id)}
              className={`rounded-full px-3 py-1 text-sm ${lang === l.id ? "bg-soil-700 text-white" : "bg-white border"}`}
            >
              {l.label}
            </button>
          ))}
        </div>
      </header>

      <section className="tile mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm text-stone-500">Demo (simulated Pune wheat, low nitrogen — labelled sim:)</p>
          <p className="text-lg font-medium">{nextAction || "Run a scan to get this week’s action."}</p>
        </div>
        <button
          onClick={runDemo}
          disabled={busy}
          className="rounded-full bg-soil-700 px-5 py-3 text-white shadow disabled:opacity-60"
        >
          {busy ? "Reading the soil…" : "Run Pune wheat demo"}
        </button>
      </section>

      {error && <p className="mb-4 rounded-xl bg-rose-50 p-3 text-rose-800">{error}</p>}

      {metrics && (
        <>
          <div className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-4">
            {tiles.map((t) => (
              <div key={t.k} className={`tile ${tone(t.kind, t.n ?? 0)}`}>
                <p className="text-xs uppercase tracking-wide opacity-70">{t.k}</p>
                <p className="text-xl font-semibold">{t.v}</p>
                <p className="text-xs opacity-70">{t.sub}</p>
              </div>
            ))}
          </div>

          <div className="mb-4 grid gap-3 md:grid-cols-3">
            <div className="tile md:col-span-2">
              <h2 className="mb-2 font-medium">Fertilizer & water plan</h2>
              <ul className="space-y-2">
                {recs.map((r) => (
                  <li key={r.id} className="rounded-xl border border-emerald-100 bg-soil-50 p-3">
                    <p className="text-xs uppercase text-emerald-800">{r.kind} · priority {r.priority}</p>
                    <p className="font-medium">{r.title}</p>
                  </li>
                ))}
              </ul>
            </div>
            <div className="tile">
              <h2 className="mb-2 font-medium">Tool health</h2>
              <p className="text-sm">Battery {String(tool?.battery_v ?? "–")} V</p>
              <p className="text-sm">Weeks left {String(tool?.battery_weeks_est ?? "–")}</p>
              <p className="text-sm">Dirty tip {String(tool?.probe_tip_dirty)}</p>
              <p className="text-sm">Model {metrics.model_version}</p>
              <p className="text-sm">Confidence {metrics.confidence}</p>
              <p className="mt-2 text-xs text-stone-500">Soil health {metrics.soil_health} · {metrics.texture}</p>
              {planted && (
                <p className="mt-2 text-xs text-amber-800">
                  sim planted N={Number(planted.n).toFixed(0)} mg/kg
                </p>
              )}
            </div>
          </div>

          {history.length > 0 && (
            <div className="tile">
              <h2 className="mb-2 font-medium">History</h2>
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={history}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="t" hide />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="n" stroke="#1b5e20" dot={false} />
                    <Line type="monotone" dataKey="moisture" stroke="#0277bd" dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </>
      )}

      <footer className="mt-8 text-center text-xs text-stone-500">
        Field {fieldId ?? "–"} · API token {token ? "ready" : "none"} · MIT AOE, Pune
      </footer>
    </main>
  );
}
