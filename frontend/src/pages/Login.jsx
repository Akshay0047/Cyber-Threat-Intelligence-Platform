import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, errorMessage } from "../api";

const fieldClass =
  "w-full rounded-md border border-slate-700 bg-slate-950/80 px-3 py-2 text-slate-100 shadow-inset outline-none ring-cyan-400/40 placeholder:text-slate-500 focus:border-cyan-400 focus:ring-2";

export default function Login() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("cti-lab-2026");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api("/api/auth/login/", { method: "POST", body: { username, password } });
      navigate("/search");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.16),_transparent_42%),linear-gradient(#0f172a,#020617)] px-4">
      <form className="w-full max-w-md space-y-4 rounded-2xl border border-cyan-400/30 bg-slate-950/75 p-8 shadow-glow backdrop-blur-xl" onSubmit={onSubmit}>
        <h1 className="font-display text-2xl text-slate-50">Cyber Threat Intelligence</h1>
        <p className="text-sm text-slate-400">Sign in with a seeded analyst account. The session stays in an httpOnly cookie.</p>
        <label className="block text-sm text-slate-300">
          Username
          <input className={`${fieldClass} mt-1`} value={username} onChange={(event) => setUsername(event.target.value)} required />
        </label>
        <label className="block text-sm text-slate-300">
          Password
          <input className={`${fieldClass} mt-1`} type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
        </label>
        {error && <p className="rounded-md border border-red-500/40 bg-red-950/70 px-3 py-2 text-sm text-red-200">{error}</p>}
        <button type="submit" disabled={busy} className="w-full rounded-md bg-cyan-400 px-4 py-2 font-semibold text-slate-950 shadow-glow transition hover:bg-cyan-300 disabled:opacity-60">
          {busy ? "Signing in..." : "Sign in"}
        </button>
        <p className="text-xs text-slate-500">Demo: admin / cti-lab-2026 or analyst1 / cti-lab-2026</p>
      </form>
    </main>
  );
}
