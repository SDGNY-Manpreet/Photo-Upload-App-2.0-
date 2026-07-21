export default function UploadProgress({ percent, step, result }) {
  return (
    <div className="space-y-3">
      {/* Bar + label */}
      <div className="space-y-1.5">
        <div className="flex justify-between items-center">
          <span className="text-xs font-medium text-slate-500">{step}</span>
          <span className="text-xs font-bold text-slate-700">{percent}%</span>
        </div>
        <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-slate-900 rounded-full transition-all duration-300"
            style={{ width: `${percent}%` }}
          />
        </div>
      </div>

      {/* Result alerts */}
      {result && (
        <div className="space-y-2">
          {result.success_count > 0 && (
            <div className="flex items-start gap-2.5 bg-green-50 border border-green-200 text-green-700 rounded-xl px-4 py-3 text-sm font-medium">
              <span className="mt-0.5">✅</span>
              <span>
                {result.success_count} of {result.total} file
                {result.total !== 1 ? "s" : ""} uploaded successfully
              </span>
            </div>
          )}
          {result.errors?.map((err, i) => (
            <div
              key={i}
              className="flex items-start gap-2.5 bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm"
            >
              <span className="mt-0.5">⚠️</span>
              <span>{err}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
