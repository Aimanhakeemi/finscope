import { useEffect, useState } from "react";
import { BrowserRouter, Link, NavLink, Route, Routes, useLocation } from "react-router-dom";
import Alerts from "./pages/Alerts";
import Ask from "./pages/Ask";
import Dashboard from "./pages/Dashboard";
import ImportPage from "./pages/Import";
import Subscriptions from "./pages/Subscriptions";

type Theme = "light" | "dark";

const THEME_STORAGE_KEY = "finscope-theme";

function readTheme(): Theme {
  try {
    return localStorage.getItem(THEME_STORAGE_KEY) === "dark" ? "dark" : "light";
  } catch {
    return "light";
  }
}

function Shell() {
  const location = useLocation();
  const [theme, setTheme] = useState<Theme>(readTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch {
      // Theme still works when storage is unavailable.
    }
  }, [theme]);

  return (
    <>
      <header className="masthead">
        <div className="masthead__inner">
          <Link to="/" className="wordmark">FinScope</Link>
          <nav className="masthead__nav" aria-label="Primary navigation">
            <NavLink to="/" end className={({ isActive }) => `nav-link${isActive ? " nav-link--active" : ""}`}>
              Dashboard
            </NavLink>
            <NavLink to="/import" className={({ isActive }) => `nav-link${isActive ? " nav-link--active" : ""}`}>
              Import
            </NavLink>
            <NavLink to="/subscriptions" className={({ isActive }) => `nav-link${isActive ? " nav-link--active" : ""}`}>
              Subscriptions
            </NavLink>
            <NavLink to="/alerts" className={({ isActive }) => `nav-link${isActive ? " nav-link--active" : ""}`}>
              Alerts
            </NavLink>
            <NavLink to="/ask" className={({ isActive }) => `nav-link${isActive ? " nav-link--active" : ""}`}>
              Ask
            </NavLink>
          </nav>
          <button
            type="button"
            className="theme-toggle"
            aria-label={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
            onClick={() => setTheme((current) => current === "light" ? "dark" : "light")}
          >
            {theme === "light" ? "DARK" : "LIGHT"}
          </button>
        </div>
      </header>
      <main className="site-main">
        <div key={location.pathname} className="route-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/import" element={<ImportPage />} />
            <Route path="/subscriptions" element={<Subscriptions />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/ask" element={<Ask />} />
          </Routes>
        </div>
      </main>
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Shell />
    </BrowserRouter>
  );
}
