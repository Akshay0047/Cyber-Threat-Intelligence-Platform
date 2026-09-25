import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, errorMessage } from "../api";

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
    <main className="login-wrap">
      <form className="card login-card" onSubmit={onSubmit}>
        <p className="eyebrow">BCSE302P</p>
        <h1>Cyber Threat Intelligence</h1>
        <p className="muted">Sign in with a seeded account. The session is an httpOnly cookie.</p>
        <label>
          Username
          <input value={username} onChange={(event) => setUsername(event.target.value)} required />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={busy}>
          {busy ? "Signing in..." : "Sign in"}
        </button>
        <p className="muted">Demo: admin / cti-lab-2026 (admin) or analyst1 / cti-lab-2026</p>
      </form>
    </main>
  );
}
