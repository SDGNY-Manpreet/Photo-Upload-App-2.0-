const TABS = [
  { id: "procore", label: "📷  Procore Projects" },
  { id: "shopify", label: "🛍️  Shopify Orders" },
  { id: "special", label: "⭐  Special Projects" },
];

export default function TabNav({ active, onChange }) {
  return (
    <nav className="bg-white border-b border-slate-200">
      <div className="max-w-5xl mx-auto px-6 flex gap-0">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className={`
              px-5 py-4 text-sm font-semibold border-b-2 whitespace-nowrap transition-all
              ${
                active === tab.id
                  ? "border-slate-900 text-slate-900"
                  : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
              }
            `}
          >
            {tab.label}
          </button>
        ))}
      </div>
    </nav>
  );
}
