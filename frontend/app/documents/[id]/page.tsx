"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { DocumentDetail, api } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { ExtractedDataForm } from "@/components/ExtractedDataForm";
import { ValidationList } from "@/components/ValidationList";
import { CrossVerificationModal } from "@/components/CrossVerificationModal";
import {
  ArrowLeft,
  RefreshCw,
  Scale,
  FileText,
  CheckCircle2,
  AlertTriangle,
  History,
  FileCode,
  Clock,
} from "lucide-react";

export default function DocumentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [document, setDocument] = useState<DocumentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"extracted" | "validation" | "raw" | "history">("extracted");
  const [isCrossVerifyOpen, setIsCrossVerifyOpen] = useState(false);
  const [reprocessing, setReprocessing] = useState(false);

  const loadDocument = useCallback(async () => {
    if (!id) return;
    try {
      const data = await api.getDocument(id);
      setDocument(data);
    } catch (err) {
      console.error("Failed to load document:", err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadDocument();
  }, [loadDocument]);

  // Polling while processing
  useEffect(() => {
    if (!document || (document.status !== "processing" && document.status !== "queued")) return;

    const timer = setInterval(async () => {
      const statusData = await api.getStatus(id);
      if (statusData.status === "completed" || statusData.status === "failed") {
        loadDocument();
      }
    }, 2000);

    return () => clearInterval(timer);
  }, [document, id, loadDocument]);

  const handleReprocess = async () => {
    setReprocessing(true);
    try {
      await api.reprocessDocument(id);
      await loadDocument();
    } catch (err: any) {
      alert("Reprocess failed: " + err.message);
    } finally {
      setReprocessing(false);
    }
  };

  if (loading) {
    return (
      <div className="py-24 text-center text-slate-500">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto text-indigo-500 mb-2" />
        Loading document details...
      </div>
    );
  }

  if (!document) {
    return (
      <div className="py-24 text-center text-slate-600">
        <p className="text-lg font-semibold">Document not found.</p>
        <button
          onClick={() => router.push("/dashboard")}
          className="mt-4 px-4 py-2 bg-indigo-600 text-white text-xs font-semibold rounded-lg"
        >
          Return to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => router.push("/dashboard")}
            className="p-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 transition"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold text-slate-900">{document.filename}</h1>
              <StatusBadge status={document.status} needsReview={document.needs_review} />
            </div>
            <div className="text-xs text-slate-500 mt-0.5">
              Type: {document.file_type.toUpperCase()} • {document.page_count} Page(s) • Uploaded on{" "}
              {new Date(document.created_at).toLocaleString()}
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setIsCrossVerifyOpen(true)}
            disabled={document.status !== "completed"}
            className="inline-flex items-center px-3.5 py-2 bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 text-xs font-semibold rounded-lg shadow-sm disabled:opacity-50 transition"
          >
            <Scale className="w-3.5 h-3.5 mr-1.5 text-indigo-600" />
            Cross-Verify
          </button>

          <button
            onClick={handleReprocess}
            disabled={reprocessing || document.status === "processing"}
            className="inline-flex items-center px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-sm disabled:opacity-50 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${reprocessing ? "animate-spin" : ""}`} />
            Reprocess Document
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-2 border-b border-slate-200 pb-2">
        <button
          onClick={() => setActiveTab("extracted")}
          className={`inline-flex items-center px-4 py-2 text-xs font-semibold rounded-lg transition ${
            activeTab === "extracted"
              ? "bg-indigo-600 text-white shadow-sm"
              : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
          }`}
        >
          <FileText className="w-3.5 h-3.5 mr-1.5" />
          Extracted Data
        </button>

        <button
          onClick={() => setActiveTab("validation")}
          className={`inline-flex items-center px-4 py-2 text-xs font-semibold rounded-lg transition ${
            activeTab === "validation"
              ? "bg-indigo-600 text-white shadow-sm"
              : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
          }`}
        >
          <AlertTriangle className="w-3.5 h-3.5 mr-1.5" />
          Validation Errors ({document.validation_errors.length})
        </button>

        <button
          onClick={() => setActiveTab("raw")}
          className={`inline-flex items-center px-4 py-2 text-xs font-semibold rounded-lg transition ${
            activeTab === "raw"
              ? "bg-indigo-600 text-white shadow-sm"
              : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
          }`}
        >
          <FileCode className="w-3.5 h-3.5 mr-1.5" />
          Raw OCR / Text
        </button>

        <button
          onClick={() => setActiveTab("history")}
          className={`inline-flex items-center px-4 py-2 text-xs font-semibold rounded-lg transition ${
            activeTab === "history"
              ? "bg-indigo-600 text-white shadow-sm"
              : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
          }`}
        >
          <History className="w-3.5 h-3.5 mr-1.5" />
          Audit & History
        </button>
      </div>

      {/* Tab Panels */}
      <div>
        {activeTab === "extracted" && (
          <ExtractedDataForm
            documentId={document.id}
            initialData={document.extracted_data}
            onSaved={loadDocument}
          />
        )}

        {activeTab === "validation" && (
          <ValidationList errors={document.validation_errors} />
        )}

        {activeTab === "raw" && (
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="text-sm font-semibold text-slate-800">Extracted Raw Text ({document.extracted_text.length} Pages)</h3>
            {document.extracted_text.length === 0 ? (
              <p className="text-xs text-slate-500">No text extracted.</p>
            ) : (
              document.extracted_text.map((page) => (
                <div key={page.id} className="border border-slate-100 rounded-lg p-4 bg-slate-50">
                  <div className="text-xs font-bold text-slate-600 mb-2">Page {page.page_number}:</div>
                  <pre className="text-xs text-slate-800 font-mono whitespace-pre-wrap overflow-x-auto">
                    {page.text || "(Empty page content)"}
                  </pre>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === "history" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Pipeline Stage Timeline */}
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-3">
              <h3 className="text-sm font-semibold text-slate-800 mb-4 flex items-center space-x-1.5">
                <Clock className="w-4 h-4 text-indigo-500" />
                <span>Processing Pipeline History</span>
              </h3>
              <div className="space-y-3">
                {document.processing_history.map((h) => (
                  <div key={h.id} className="p-3 rounded-lg border border-slate-100 bg-slate-50 text-xs">
                    <div className="flex justify-between font-semibold text-slate-800">
                      <span className="capitalize">{h.stage.replace("_", " ")}</span>
                      <span className={h.status === "completed" ? "text-emerald-600" : "text-amber-600"}>{h.status}</span>
                    </div>
                    <div className="text-[11px] text-slate-500 mt-1">
                      Started: {new Date(h.started_at).toLocaleTimeString()}
                      {h.finished_at && ` • Finished: ${new Date(h.finished_at).toLocaleTimeString()}`}
                    </div>
                    {h.error && <div className="text-rose-600 mt-1 font-mono text-[10px]">{h.error}</div>}
                  </div>
                ))}
              </div>
            </div>

            {/* Manual Correction Audit Trail */}
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-3">
              <h3 className="text-sm font-semibold text-slate-800 mb-4 flex items-center space-x-1.5">
                <History className="w-4 h-4 text-indigo-500" />
                <span>Manual Correction Audit Trail</span>
              </h3>
              {document.correction_history.length === 0 ? (
                <p className="text-xs text-slate-500">No manual corrections applied yet.</p>
              ) : (
                <div className="space-y-3">
                  {document.correction_history.map((c) => (
                    <div key={c.id} className="p-3 rounded-lg border border-slate-100 bg-slate-50 text-xs">
                      <div className="font-semibold text-slate-800">Field: {c.field}</div>
                      <div className="text-slate-500 mt-1">
                        <span className="line-through text-rose-500">{c.old_value || "(empty)"}</span> →{" "}
                        <span className="text-emerald-600 font-medium">{c.new_value}</span>
                      </div>
                      <div className="text-[10px] text-slate-400 mt-1">
                        Corrected by: {c.corrected_by || "Reviewer"} on {new Date(c.created_at).toLocaleString()}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Cross Verification Modal */}
      <CrossVerificationModal
        primaryDocument={document}
        isOpen={isCrossVerifyOpen}
        onClose={() => setIsCrossVerifyOpen(false)}
      />
    </div>
  );
}
