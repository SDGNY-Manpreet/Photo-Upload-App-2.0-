import { useRef, useState, useEffect } from "react";

const ALLOWED_EXTS = ["png", "jpg", "jpeg", "gif", "bmp", "tif", "tiff", "pdf"];
const IMAGE_EXTS = ["png", "jpg", "jpeg", "gif", "bmp"]; // Types we can safely URL.createObjectURL preview

function formatSize(bytes) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function FileDropzone({ files, onChange, disabled }) {
  const inputRef = useRef();
  const [dragOver, setDragOver] = useState(false);
  const [previews, setPreviews] = useState({});

  // Generate object URLs for image previews
  useEffect(() => {
    const newPreviews = { ...previews };
    let changed = false;

    files.forEach(f => {
      const ext = f.name.split(".").pop().toLowerCase();
      const key = `${f.name}-${f.size}`;
      
      if (IMAGE_EXTS.includes(ext) && !newPreviews[key]) {
        newPreviews[key] = URL.createObjectURL(f);
        changed = true;
      }
    });

    if (changed) {
      setPreviews(newPreviews);
    }

    // We don't cleanup object URLs here to prevent flickering, 
    // rely on browser GC on page unload, or clean them up manually if needed.
    // For a production app with huge files, manual revokeObjectURL is better.
  }, [files]);

  const addFiles = (incoming) => {
    const valid = Array.from(incoming).filter((f) => {
      const ext = f.name.split(".").pop().toLowerCase();
      return ALLOWED_EXTS.includes(ext);
    });
    const existing = new Set(files.map((f) => `${f.name}-${f.size}`));
    const merged = [...files, ...valid.filter((f) => !existing.has(`${f.name}-${f.size}`))];
    onChange(merged);
  };

  const remove = (idx) => {
    const newFiles = [...files];
    const removed = newFiles.splice(idx, 1)[0];
    
    // Cleanup preview URL to prevent memory leaks
    if (removed) {
      const key = `${removed.name}-${removed.size}`;
      if (previews[key]) {
        URL.revokeObjectURL(previews[key]);
        const p = { ...previews };
        delete p[key];
        setPreviews(p);
      }
    }
    
    onChange(newFiles);
  };

  const totalMB = files.reduce((acc, f) => acc + f.size, 0) / (1024 * 1024);

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        onClick={() => !disabled && inputRef.current.click()}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setDragOver(false); if (!disabled) addFiles(e.dataTransfer.files); }}
        className={`
          relative flex flex-col items-center justify-center gap-3
          border-2 border-dashed rounded-2xl p-8 cursor-pointer
          transition-all duration-200 group
          ${dragOver
            ? "border-brand-500 bg-brand-50 shadow-inner"
            : "border-slate-200 bg-slate-50 hover:border-slate-300 hover:bg-white"
          }
          ${disabled ? "opacity-50 cursor-not-allowed" : ""}
        `}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ALLOWED_EXTS.map((e) => `.${e}`).join(",")}
          disabled={disabled}
          onChange={(e) => addFiles(e.target.files)}
          onClick={(e) => e.stopPropagation()}
          className="hidden"
        />
        
        <div className={`p-3 rounded-full transition-colors ${dragOver ? 'bg-brand-200 text-brand-700' : 'bg-white text-slate-400 group-hover:text-slate-600 shadow-sm border border-slate-100'}`}>
          <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
             <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
        </div>
        
        <div className="text-center">
          <p className="text-sm text-slate-600">
            <span className="font-semibold text-slate-900 underline underline-offset-2">Click to browse</span> or drag files here
          </p>
          <p className="text-xs text-slate-400 mt-1">
            PNG, JPG, PDF up to 20MB (auto-optimized)
          </p>
        </div>
      </div>

      {/* Selected files gallery */}
      {files.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between px-1">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              {files.length} file{files.length !== 1 ? "s" : ""} selected
            </span>
            <span className="px-2 py-1 text-[10px] font-bold bg-brand-100 border border-brand-200 text-brand-800 rounded-lg">
              {totalMB.toFixed(1)} MB total
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {files.map((f, i) => {
              const key = `${f.name}-${f.size}`;
              const ext = f.name.split(".").pop().toLowerCase();
              const isImage = IMAGE_EXTS.includes(ext);
              const previewUrl = previews[key];

              return (
                <div 
                  key={`${key}-${i}`}
                  className="group relative aspect-square bg-slate-50 border border-slate-200 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow"
                >
                  {/* Remove Button Overlay */}
                  {!disabled && (
                    <button
                      onClick={() => remove(i)}
                      className="absolute top-1.5 right-1.5 z-10 w-6 h-6 bg-white/90 backdrop-blur-sm border border-slate-200 text-slate-500 hover:text-red-600 hover:border-red-200 hover:bg-red-50 rounded-full flex items-center justify-center transition-all opacity-0 group-hover:opacity-100"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  )}

                  {/* Thumbnail / Icon */}
                  <div className="absolute inset-0 flex items-center justify-center bg-slate-100">
                    {isImage && previewUrl ? (
                      <img 
                        src={previewUrl} 
                        alt={f.name}
                        className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                      />
                    ) : (
                      <div className="text-slate-300">
                        <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                        </svg>
                      </div>
                    )}
                  </div>

                  {/* Info gradient overlay */}
                  <div className="absolute inset-x-0 bottom-0 p-2 pt-6 bg-gradient-to-t from-black/60 to-transparent">
                    <p className="text-[10px] text-white font-medium truncate drop-shadow-md">
                      {f.name}
                    </p>
                    <p className="text-[9px] text-white/80 truncate drop-shadow-md">
                      {formatSize(f.size)}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
