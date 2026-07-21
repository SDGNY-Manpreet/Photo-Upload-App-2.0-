import { useEffect, useState } from "react";
import { fetchHealth } from "../api/client";

export default function Header() {
  const [dbStatus, setDbStatus] = useState(null); // null | true | false

  useEffect(() => {
    fetchHealth()
      .then((d) => setDbStatus(d.database?.ok === true))
      .catch(() => setDbStatus(false));
  }, []);

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
      <div className="max-w-5xl mx-auto px-6 h-16 flex items-center gap-3">
        <img src="/logo.jpg" alt="SDGNY Logo" className="h-9 w-auto object-contain" />

        <div className="w-px h-6 bg-slate-200 mx-1" />

        <span className="text-slate-800 font-semibold text-sm tracking-tight">
          Project Image Upload System
        </span>

        {/* Spacer */}
        <div className="flex-1" />

        {/* DB Status badge */}
        <div className="flex items-center gap-2">
          <span
            className={`inline-block w-2 h-2 rounded-full ${
              dbStatus === null
                ? "bg-slate-300 animate-pulse-subtle"
                : dbStatus
                ? "bg-green-500"
                : "bg-red-500"
            }`}
          />
          <span className="text-xs text-slate-500 font-medium">
            {dbStatus === null
              ? "Connecting…"
              : dbStatus
              ? "Database connected"
              : "Database offline"}
          </span>
        </div>
      </div>
    </header>
  );
}
