import { useEffect, useState } from "react";
import { NavLink, Navigate, Outlet, Route, Routes, useNavigate } from "react-router-dom";
import { api } from "./api";
import Analytics from "./pages/Analytics";
import EntityList from "./pages/EntityList";
import GraphView from "./pages/GraphView";
import Login from "./pages/Login";
import Search from "./pages/Search";

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

  if (!ready) return <p className="muted page">Checking session...</p>;
  if (!user?.user_id) return <Navigate to="/login" replace />;

  return (
    <>
      <header className="topbar">
        <strong>CTI Platform</strong>
        <nav>
          <NavLink to="/search">Search</NavLink>
          <NavLink to="/entities">Collections</NavLink>
          <NavLink to="/graph">Graph</NavLink>
          <NavLink to="/analytics">Analytics</NavLink>
        </nav>
        <span className="muted">
          {user.user_id} · {user.role}
        </span>
        <button type="button" onClick={logout}>
          Log out
        </button>
      </header>
      <main className="page">
        <Outlet />
      </main>
    </>
  );
}

export default function App() {
  return (
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
  );
}
