import { useEffect, useMemo, useRef, useState } from "react";
import { SearchIcon, ChevronDownIcon } from "./Icons";

export default function SearchableSelect({
  options = [],
  value = "",
  onChange,
  disabled = false,
  placeholder = "Search and select item…",
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  
  const containerRef = useRef(null);
  const listRef = useRef(null);

  // Memoize filtered options for sub-millisecond search performance
  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return options;
    return options.filter((opt) => String(opt).toLowerCase().includes(q));
  }, [options, search]);

  // Reset highlight when search query changes
  useEffect(() => {
    setHighlightedIndex(0);
  }, [search]);

  // Close popover when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Keyboard navigation logic
  const handleKeyDown = (e) => {
    if (disabled) return;

    if (!isOpen) {
      if (e.key === "Enter" || e.key === "ArrowDown" || e.key === " ") {
        e.preventDefault();
        setIsOpen(true);
      }
      return;
    }

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setHighlightedIndex((prev) => (prev + 1 < filtered.length ? prev + 1 : 0));
        break;
      case "ArrowUp":
        e.preventDefault();
        setHighlightedIndex((prev) => (prev - 1 >= 0 ? prev - 1 : filtered.length - 1));
        break;
      case "Enter":
        e.preventDefault();
        if (filtered[highlightedIndex]) {
          onChange(filtered[highlightedIndex]);
          setIsOpen(false);
          setSearch("");
        }
        break;
      case "Escape":
        e.preventDefault();
        setIsOpen(false);
        break;
      default:
        break;
    }
  };

  // Ensure highlighted element scrolls into view
  useEffect(() => {
    if (isOpen && listRef.current) {
      const activeEl = listRef.current.children[highlightedIndex];
      if (activeEl) {
        activeEl.scrollIntoView({ block: "nearest", behavior: "smooth" });
      }
    }
  }, [highlightedIndex, isOpen]);

  return (
    <div className="relative" ref={containerRef} onKeyDown={handleKeyDown}>
      {/* Trigger Button */}
      <button
        type="button"
        disabled={disabled}
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3.5 py-2.5 bg-white border border-slate-200 focus:border-slate-400 focus:ring-2 focus:ring-slate-100 rounded-xl outline-none text-slate-800 text-sm cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shadow-sm transition-all"
      >
        <span className={value ? "text-slate-900 font-medium truncate" : "text-slate-400 truncate"}>
          {value || placeholder}
        </span>
        <ChevronDownIcon
          className={`w-4 h-4 text-slate-400 shrink-0 ml-2 transition-transform duration-200 ${
            isOpen ? "rotate-180 text-slate-600" : ""
          }`}
        />
      </button>

      {/* Popover List */}
      {isOpen && (
        <div className="absolute z-[999] w-full mt-1.5 bg-white border border-slate-200 rounded-2xl shadow-xl overflow-hidden flex flex-col max-h-[300px] animate-fade-in">
          {/* Search Input Header */}
          <div className="p-2 border-b border-slate-100 bg-slate-50/50 flex items-center gap-2">
            <SearchIcon className="w-4 h-4 text-slate-400 shrink-0 ml-2" />
            <input
              type="text"
              autoFocus
              placeholder="Type to filter..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full px-2 py-1.5 bg-transparent border-none outline-none text-slate-800 text-xs placeholder:text-slate-400 font-medium"
            />
          </div>

          {/* List Items */}
          <div ref={listRef} className="overflow-y-auto flex-1 divide-y divide-slate-50">
            {filtered.length === 0 ? (
              <div className="p-4 text-xs text-slate-400 text-center font-medium">
                No matching items found
              </div>
            ) : (
              filtered.map((opt, i) => {
                const isSelected = value === opt;
                const isHighlighted = highlightedIndex === i;

                return (
                  <button
                    key={`${opt}-${i}`}
                    type="button"
                    onClick={() => {
                      onChange(opt);
                      setIsOpen(false);
                      setSearch("");
                    }}
                    onMouseEnter={() => setHighlightedIndex(i)}
                    className={`
                      w-full text-left px-3.5 py-2.5 text-xs transition-colors duration-75 flex items-center justify-between gap-2
                      ${
                        isSelected
                          ? "bg-slate-900 text-white font-semibold"
                          : isHighlighted
                          ? "bg-slate-100 text-slate-900"
                          : "text-slate-700 hover:bg-slate-50"
                      }
                    `}
                  >
                    <span className="truncate">{opt}</span>
                    {isSelected && (
                      <span className="w-1.5 h-1.5 rounded-full bg-brand-400 shrink-0" />
                    )}
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
