import { useEffect, useState } from "react";
import { fetchHealth } from "../api/client";

const NAV_ITEMS = [
  { id: "procore", label: "Procore Projects", icon: "📷", short: "Procore" },
  { id: "shopify", label: "Shopify Orders", icon: "🛍️", short: "Shopify" },
  { id: "special", label: "Special Projects", icon: "⭐", short: "Special" },
];

export default function Sidebar({ activeTab, onChangeTab }) {
  const [dbStatus, setDbStatus] = useState(null); // null | true | false

  useEffect(() => {
    fetchHealth()
      .then((d) => setDbStatus(d.database?.ok === true))
      .catch(() => setDbStatus(false));
  }, []);

  return (
    <aside className="w-full md:w-64 bg-white border-b md:border-b-0 md:border-r border-slate-200 flex flex-col md:min-h-screen sticky top-0 z-40 shadow-sm md:shadow-none">
      {/* Branding */}
      <div className="h-16 md:h-20 flex items-center justify-between px-4 md:px-6 border-b border-slate-100 shrink-0">
        <img src="/logo.jpg" alt="SDGNY Logo" className="h-8 md:h-10 w-auto object-contain" />
        
        {/* Mobile Status Dot */}
        <div className="md:hidden flex items-center gap-2">
          <span
            className={`inline-block w-2.5 h-2.5 rounded-full ring-2 ring-offset-1 ${
              dbStatus === null
                ? "bg-slate-300 ring-slate-100 animate-pulse-subtle"
                : dbStatus
                ? "bg-brand-500 ring-brand-100"
                : "bg-red-500 ring-red-100"
            }`}
          />
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 flex md:flex-col overflow-x-auto md:overflow-y-auto px-2 md:px-4 py-2 md:py-6 gap-2 md:gap-1 hide-scrollbar items-center md:items-stretch">
        <div className="hidden md:block px-2 mb-3 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
          Upload Destinations
        </div>
        
        {NAV_ITEMS.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onChangeTab(item.id)}
              className={`
                shrink-0 md:w-full flex items-center gap-2 md:gap-3 px-4 md:px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200
                ${isActive 
                  ? 'bg-slate-900 text-white shadow-md shadow-slate-200/50 md:translate-x-1' 
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 bg-white border border-slate-200 md:border-transparent md:bg-transparent'
                }
              `}
            >
              <span className="text-lg">{item.icon}</span>
              <span className="hidden md:inline">{item.label}</span>
              <span className="md:hidden">{item.short}</span>
            </button>
          );
        })}
      </nav>

      {/* System Status Footer (Desktop Only) */}
      <div className="hidden md:block p-4 border-t border-slate-100 shrink-0 bg-slate-50/50">
        <div className="bg-white border border-slate-200 rounded-xl p-3 shadow-sm">
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">
            System Status
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`inline-block w-2.5 h-2.5 rounded-full ring-2 ring-offset-1 ${
                dbStatus === null
                  ? "bg-slate-300 ring-slate-100 animate-pulse-subtle"
                  : dbStatus
                  ? "bg-brand-500 ring-brand-100 shadow-[0_0_8px_rgba(163,255,26,0.6)]"
                  : "bg-red-500 ring-red-100 shadow-[0_0_8px_rgba(239,68,68,0.6)]"
              }`}
            />
            <span className="text-xs font-semibold text-slate-700">
              {dbStatus === null
                ? "Connecting…"
                : dbStatus
                ? "Database Online"
                : "Database Offline"}
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}
