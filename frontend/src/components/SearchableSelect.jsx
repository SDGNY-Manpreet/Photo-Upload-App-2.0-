import { useEffect, useRef, useState } from "react";

export default function SearchableSelect({
  options,
  value,
  onChange,
  disabled,
  placeholder = "Search and select item…",
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const containerRef = useRef(null);

  // Close when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filtered = (options || []).filter((opt) =>
    String(opt).toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="relative" ref={containerRef}>
      {/* Display Value trigger */}
      <button
        type="button"
        disabled={disabled}
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3 py-2 bg-white border border-slate-200 focus:border-slate-400 focus:ring-2 focus:ring-slate-200 rounded-lg outline-none text-slate-800 text-sm cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <span className={value ? "text-slate-800 font-medium" : "text-slate-400"}>
          {value || placeholder}
        </span>
        <svg
          className={`w-4 h-4 text-slate-400 transition-transform ${
            isOpen ? "rotate-180" : ""
          }`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Popover */}
      {isOpen && (
        <div className="absolute z-[999] w-full mt-1.5 bg-white border border-slate-200 rounded-xl shadow-lg overflow-hidden flex flex-col max-h-[300px]">
          {/* Search box */}
          <div className="p-2 border-b border-slate-100 bg-slate-50">
            <input
              type="text"
              autoFocus
              placeholder="Type to filter..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full px-3 py-1.5 bg-white border border-slate-200 focus:border-slate-400 rounded-lg outline-none text-slate-850 text-xs placeholder:text-slate-400"
            />
          </div>

          {/* List items */}
          <div className="overflow-y-auto flex-1 divide-y divide-slate-50">
            {filtered.length === 0 ? (
              <div className="p-4 text-xs text-slate-400 text-center">
                No items found
              </div>
            ) : (
              filtered.map((opt) => (
                <button
                  key={opt}
                  type="button"
                  onClick={() => {
                    onChange(opt);
                    setIsOpen(false);
                    setSearch("");
                  }}
                  className={`
                    w-full text-left px-3.5 py-2 text-xs transition-all duration-75
                    ${
                      value === opt
                        ? "bg-slate-900 text-white font-semibold"
                        : "text-slate-700 hover:bg-slate-100 hover:text-slate-900"
                    }
                  `}
                >
                  {opt}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
