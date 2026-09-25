import { useEffect, useState } from "react";
import { NavLink, Navigate, Outlet, Route, Routes, useNavigate } from "react-router-dom";
import { api } from "./api";
import Toast from "./components/Toast";
import Analytics from "./pages/Analytics";
import EntityList from "./pages/EntityList";
import GraphView from "./pages/GraphView";
import Login from "./pages/Login";
import Search from "./pages/Search";

const LINKS = [
  { to: "/search", label: "Search" },
  { to: "/entities", label: "Entities" },
  { to: "/graph", label: "Graph" },
  { to: "/analytics", label: "Analytics" },
];

function Shell() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    api("/api/auth/me/")
      .then((data) => {
        setUser(data);
        setReady(true);
      })
      .catch(() => setReady(true));
  }, []);

  async function logout() {
    await api("/api/auth/logout/", { method: "POST" }).catch(() => {});
    navigate("/login");
  }

  if (!ready) {
    return <p className="p-8 text-sm tracking-wide text-cyan-300/80">Checking session...</p>;
  }
  if (!user?.user_id) return <Navigate to="/login" replace />;

  return (
    <div className="min-h-screen bg-slate-900 lg:grid lg:grid-cols-[240px_1fr]">
      <aside className="sticky top-0 z-40 border-b border-cyan-400/30 bg-slate-950/70 backdrop-blur-xl lg:h-screen lg:border-b-0 lg:border-r">
        <div className="flex items-center justify-between gap-4 px-5 py-4 lg:block">
          <div>
            <p className="font-display text-[10px] uppercase tracking-[0.28em] text-cyan-400">CTI</p>
            <p className="font-display text-sm text-slate-100">Threat Platform</p>
          </div>
          <p className="text-xs text-slate-400 lg:mt-3">
            {user.user_id}
            <span className="mx-1 text-slate-600">/</span>
            {user.role}
          </p>
        </div>
        <nav className="flex gap-2 overflow-x-auto px-3 pb-3 lg:mt-4 lg:flex-col lg:px-3">
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `rounded-md border px-3 py-2 text-sm font-semibold tracking-wide transition ${
                  isActive
                    ? "border-cyan-400 bg-cyan-400/10 text-cyan-200 shadow-glow"
                    : "border-transparent text-slate-400 hover:border-slate-700 hover:text-slate-100"
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
          <button
            type="button"
            onClick={logout}
            className="rounded-md border border-transparent px-3 py-2 text-left text-sm font-semibold text-slate-400 hover:border-emerald-400/40 hover:text-emerald-300 lg:mt-auto"
          >
            Logout
          </button>
        </nav>
      </aside>
      <main className="min-w-0 px-4 py-6 sm:px-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <>
      <Toast />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<Shell />}>
          <Route path="/" element={<Navigate to="/search" replace />} />
          <Route path="/search" element={<Search />} />
          <Route path="/entities" element={<EntityList />} />
          <Route path="/graph" element={<GraphView />} />
          <Route path="/analytics" element={<Analytics />} />
        </Route>
      </Routes>
    </>
  );
}
