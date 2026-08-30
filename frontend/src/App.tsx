import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import ImportPage from "./pages/Import";

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-950 text-slate-100">
        <nav className="border-b border-slate-800 bg-slate-950/90">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
            <Link to="/" className="text-xl font-semibold">FinScope</Link>
            <div className="flex gap-5 text-sm text-slate-300">
              <Link to="/" className="hover:text-white">Dashboard</Link>
              <Link to="/import" className="hover:text-white">Import</Link>
            </div>
          </div>
        </nav>
        <main className="mx-auto max-w-7xl px-6 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/import" element={<ImportPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
