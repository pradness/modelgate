import { useEffect, useMemo, useState } from "react";
import { api, ApiKey, Model, Version } from "./api";

type Tab = "dashboard" | "models" | "apikeys" | "analytics";
const tokenKey = "modelgate.token";

export function App() {
  const [tab, setTab] = useState<Tab>("dashboard");
  const [token, setToken] = useState(localStorage.getItem(tokenKey) ?? "");
  const [models, setModels] = useState<Model[]>([]);
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [versions, setVersions] = useState<Record<number, Version[]>>({});
  const [dashboard, setDashboard] = useState<any>(null);
  const [message, setMessage] = useState<string>("");

  useEffect(() => { if (token) localStorage.setItem(tokenKey, token); }, [token]);
  useEffect(() => { if (token) loadAll(); }, [token]);

  async function loadAll() {
    try {
      const [m, k, d] = await Promise.all([api.models(token), api.apiKeys(token), api.dashboard(token)]);
      setModels(m);
      setKeys(k);
      setDashboard(d);
      const loaded: Record<number, Version[]> = {};
      for (const model of m) loaded[model.id] = (await api.versions(token, model.id)).versions;
      setVersions(loaded);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Failed to load data");
    }
  }

  const stats = useMemo(() => dashboard ?? { total_requests: 0, average_latency_ms: 0, cache_hit_rate: 0, active_models: 0 }, [dashboard]);

  return <div className="min-h-screen bg-[#0b1326] text-[#dae2fd]">{token ? <Shell {...{ tab, setTab, token, setToken, models, setModels, keys, setKeys, versions, setVersions, stats, message, setMessage, reload: loadAll }} /> : <Auth onToken={setToken} setMessage={setMessage} message={message} />}</div>;
}

function Auth({ onToken, setMessage, message }: any) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (mode === "register") await api.register(username, password);
      const { access_token } = await api.login(username, password);
      onToken(access_token);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Auth failed");
    }
  };
  return <form onSubmit={submit} className="mx-auto max-w-md p-8 space-y-4"><h1 className="text-3xl font-semibold">ModelGate</h1><input className="w-full rounded bg-[#171f33] p-3" placeholder="username" value={username} onChange={e => setUsername(e.target.value)} /><input className="w-full rounded bg-[#171f33] p-3" placeholder="password" type="password" value={password} onChange={e => setPassword(e.target.value)} /><button className="rounded bg-[#c0c1ff] px-4 py-2 text-[#1000a9]">{mode}</button><button type="button" className="ml-3" onClick={() => setMode(mode === "login" ? "register" : "login")}>switch</button><p className="text-sm text-red-300">{message}</p></form>;
}

function Shell(props: any) {
  const nav = [
    ["dashboard", "Dashboard"],
    ["models", "Models"],
    ["apikeys", "API Keys"],
    ["analytics", "Analytics"],
  ] as const;
  return <div className="flex min-h-screen"><aside className="w-[260px] border-r border-[#464554] bg-[#171f33] p-4">{nav.map(([id, label]) => <button key={id} onClick={() => props.setTab(id)} className={`block w-full rounded p-3 text-left ${props.tab === id ? "bg-[#222a3d] text-[#c0c1ff]" : "text-[#c7c4d7]"}`}>{label}</button>)}<button className="mt-6 text-sm underline" onClick={() => { localStorage.removeItem(tokenKey); props.setToken(""); }}>logout</button></aside><main className="flex-1 p-6">{props.message && <p className="mb-4 text-sm text-red-300">{props.message}</p>}{props.tab === "dashboard" && <Dashboard stats={props.stats} />}{props.tab === "models" && <Models {...props} />}{props.tab === "apikeys" && <ApiKeys {...props} />}{props.tab === "analytics" && <Analytics {...props} />}</main></div>;
}

function Dashboard({ stats }: any) {
  return <div className="grid gap-4 md:grid-cols-4"><Card label="Requests" value={stats.total_requests} /><Card label="Latency ms" value={stats.average_latency_ms} /><Card label="Cache %" value={stats.cache_hit_rate} /><Card label="Models" value={stats.active_models} /></div>;
}

function Models({ token, models, setModels, versions, setVersions, setMessage, reload }: any) {
  const [name, setName] = useState(""); const [task, setTask] = useState("classification"); const [description, setDescription] = useState("");
  const create = async (e: React.FormEvent) => { e.preventDefault(); try { const m = await api.createModel(token, { name, task, description }); setModels([...models, m]); setName(""); } catch (err) { setMessage(err instanceof Error ? err.message : "failed"); } };
  return <div className="space-y-6"><form onSubmit={create} className="grid gap-2 md:grid-cols-4"><input value={name} onChange={e => setName(e.target.value)} placeholder="model name" className="rounded bg-[#171f33] p-3" /><input value={task} onChange={e => setTask(e.target.value)} placeholder="task" className="rounded bg-[#171f33] p-3" /><input value={description} onChange={e => setDescription(e.target.value)} placeholder="description" className="rounded bg-[#171f33] p-3 md:col-span-2" /><button className="rounded bg-[#c0c1ff] px-4 py-2 text-[#1000a9] md:col-span-4">create model</button></form>{models.map((m: Model) => <ModelCard key={m.id} model={m} versions={versions[m.id] ?? []} token={token} setVersions={setVersions} setMessage={setMessage} />)}</div>;
}

function ModelCard({ model, versions, token, setVersions, setMessage }: any) {
  const [version, setVersion] = useState(""); const [serviceUrl, setServiceUrl] = useState(""); const [artifactUri, setArtifactUri] = useState("");
  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createVersion(token, model.id, { version, service_url: serviceUrl, artifact_uri: artifactUri });
      const next = await api.versions(token, model.id);
      setVersions((current: Record<number, Version[]>) => ({ ...current, [model.id]: next.versions }));
      setVersion(""); setServiceUrl(""); setArtifactUri("");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "failed");
    }
  };
  return <div className="rounded border border-[#464554] bg-[#171f33] p-4"><div><h3 className="font-semibold">{model.name}</h3><p className="text-sm text-[#c7c4d7]">{model.task}</p></div><pre className="mt-3 overflow-auto rounded bg-[#131b2e] p-3 text-xs">{JSON.stringify(versions, null, 2)}</pre><form onSubmit={create} className="mt-4 grid gap-2 md:grid-cols-3"><input className="rounded bg-[#131b2e] p-2" placeholder="version" value={version} onChange={e => setVersion(e.target.value)} /><input className="rounded bg-[#131b2e] p-2" placeholder="service url" value={serviceUrl} onChange={e => setServiceUrl(e.target.value)} /><input className="rounded bg-[#131b2e] p-2 md:col-span-2" placeholder="artifact uri" value={artifactUri} onChange={e => setArtifactUri(e.target.value)} /><button className="rounded bg-[#4edea3] px-3 py-2 text-[#003824] md:col-span-1">add version</button></form></div>;
}

function ApiKeys({ token, keys, setKeys, setMessage }: any) {
  const [name, setName] = useState("");
  const create = async (e: React.FormEvent) => { e.preventDefault(); try { const { api_key } = await api.createApiKey(token, name); setMessage(`New key: ${api_key}`); setKeys(await api.apiKeys(token)); setName(""); } catch (err) { setMessage(err instanceof Error ? err.message : "failed"); } };
  return <div className="space-y-4"><form onSubmit={create} className="flex gap-2"><input className="rounded bg-[#171f33] p-3" placeholder="key name" value={name} onChange={e => setName(e.target.value)} /><button className="rounded bg-[#c0c1ff] px-4 py-2 text-[#1000a9]">create</button></form>{keys.map((k: ApiKey) => <div key={k.id} className="rounded border border-[#464554] bg-[#171f33] p-4 flex justify-between"><span>Key #{k.id}</span><button onClick={async () => { await api.revokeApiKey(token, k.id); setKeys(await api.apiKeys(token)); }} className="text-sm underline">revoke</button></div>)}</div>;
}

function Analytics({ token }: any) {
  const [top, setTop] = useState<any[]>([]);
  useEffect(() => { api.topModels(token).then(setTop).catch(() => setTop([])); }, [token]);
  return <div className="space-y-4">{top.map(r => <Card key={r.model} label={r.model} value={r.requests} />)}</div>;
}

function Card({ label, value }: any) { return <div className="rounded border border-[#464554] bg-[#171f33] p-4"><div className="text-sm text-[#c7c4d7]">{label}</div><div className="mt-2 text-2xl font-semibold">{String(value ?? 0)}</div></div>; }
