import { useRef, useState, useEffect } from "react";
import { UploadCloudIcon, TrashIcon, XIcon, FolderIcon } from "./Icons";

const ALLOWED_EXTS = ["png", "jpg", "jpeg", "gif", "bmp", "tif", "tiff", "pdf"];
const IMAGE_EXTS = ["png", "jpg", "jpeg", "gif", "bmp"];

function formatSize(bytes) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function FileDropzone({ files = [], onChange, disabled = false }) {
  const inputRef = useRef();
  const [dragOver, setDragOver] = useState(false);
  const [previews, setPreviews] = useState({});

  // Generate object URLs for image previews and manage memory
  useEffect(() => {
    const newPreviews = { ...previews };
    let changed = false;

    files.forEach((f) => {
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
  }, [files]);

  // Clean up Object URLs when files are removed or unmounted
  useEffect(() => {
    return () => {
      Object.values(previews).forEach((url) => {
        if (url) URL.revokeObjectURL(url);
      });
    };
  }, []);

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

  const clearAll = () => {
    Object.values(previews).forEach((url) => {
      if (url) URL.revokeObjectURL(url);
    });
    setPreviews({});
    onChange([]);
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
            : "border-slate-200 bg-slate-50/50 hover:border-slate-300 hover:bg-white"
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
        
        <div className={`p-3.5 rounded-2xl transition-colors ${dragOver ? 'bg-brand-200 text-brand-700' : 'bg-white text-slate-500 group-hover:text-slate-900 shadow-sm border border-slate-200'}`}>
          <UploadCloudIcon className="w-7 h-7" />
        </div>
        
        <div className="text-center">
          <p className="text-sm text-slate-600 font-medium">
            <span className="font-semibold text-slate-900 underline underline-offset-2">Click to browse</span> or drag photos here
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
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                {files.length} file{files.length !== 1 ? "s" : ""} selected
              </span>
              <span className="px-2 py-0.5 text-[10px] font-bold bg-brand-100 border border-brand-200 text-brand-800 rounded-md">
                {totalMB.toFixed(1)} MB total
              </span>
            </div>

            {!disabled && (
              <button
                type="button"
                onClick={clearAll}
                className="text-xs text-slate-400 hover:text-red-600 flex items-center gap-1 font-medium transition-colors"
              >
                <TrashIcon className="w-3.5 h-3.5" />
                Clear all
              </button>
            )}
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
                      type="button"
                      onClick={() => remove(i)}
                      className="absolute top-2 right-2 z-10 w-6 h-6 bg-white/90 backdrop-blur-sm border border-slate-200 text-slate-500 hover:text-red-600 hover:border-red-200 hover:bg-red-50 rounded-full flex items-center justify-center transition-all opacity-0 group-hover:opacity-100 shadow-sm"
                    >
                      <XIcon className="w-3.5 h-3.5" />
                    </button>
                  )}

                  {/* Thumbnail / Icon */}
                  <div className="absolute inset-0 flex items-center justify-center bg-slate-100">
                    {isImage && previewUrl ? (
                      <img 
                        src={previewUrl} 
                        alt={f.name}
                        className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                      />
                    ) : (
                      <div className="text-slate-400">
                        <FolderIcon className="w-9 h-9" />
                      </div>
                    )}
                  </div>

                  {/* Info gradient overlay */}
                  <div className="absolute inset-x-0 bottom-0 p-2.5 pt-6 bg-gradient-to-t from-black/70 via-black/30 to-transparent">
                    <p className="text-[11px] text-white font-medium truncate drop-shadow-sm">
                      {f.name}
                    </p>
                    <p className="text-[9px] text-white/80 truncate font-mono mt-0.5">
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
