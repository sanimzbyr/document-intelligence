import { ValidationError } from "@/lib/api";
import { AlertCircle, AlertTriangle, CheckCircle2 } from "lucide-react";

export function ValidationList({ errors }: { errors: ValidationError[] }) {
  if (errors.length === 0) {
    return (
      <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-6 text-center text-emerald-800">
        <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
        <h4 className="font-semibold text-sm">All Financial Validations Passed</h4>
        <p className="text-xs text-emerald-600 mt-1">
          Math calculations, required fields, and duplicate checks are fully reconciled.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <h3 className="text-sm font-semibold text-slate-800">Validation Flags ({errors.length})</h3>
        <span className="text-xs px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-800 font-medium">
          Requires Human Verification
        </span>
      </div>

      <div className="space-y-3">
        {errors.map((err) => (
          <div
            key={err.id}
            className={`p-3.5 rounded-lg border text-xs flex items-start space-x-3 ${
              err.severity === "error"
                ? "bg-rose-50 border-rose-200 text-rose-900"
                : "bg-amber-50 border-amber-200 text-amber-900"
            }`}
          >
            {err.severity === "error" ? (
              <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
            )}
            <div className="flex-1">
              <div className="flex items-center space-x-2">
                <span className="font-bold uppercase tracking-wider text-[10px] px-1.5 py-0.5 rounded bg-white/70 border border-current">
                  {err.severity}
                </span>
                <span className="font-semibold">{err.field}</span>
              </div>
              <p className="mt-1 text-slate-700">{err.message}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
