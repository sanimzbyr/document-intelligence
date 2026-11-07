"use client";

import React, { useState, useEffect } from "react";
import { DocumentItem, api } from "@/lib/api";
import { Scale, CheckCircle2, XCircle, Loader2, X } from "lucide-react";

interface CrossVerificationModalProps {
  primaryDocument: DocumentItem;
  isOpen: boolean;
  onClose: () => void;
}

export function CrossVerificationModal({ primaryDocument, isOpen, onClose }: CrossVerificationModalProps) {
  const [candidates, setCandidates] = useState<DocumentItem[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>("");
  const [loadingCandidates, setLoadingCandidates] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [result, setResult] = useState<any | null>(null);

  useEffect(() => {
    if (isOpen) {
      setResult(null);
      setLoadingCandidates(true);
      api
        .getDocuments({ page_size: 50 })
        .then((res) => {
          const others = (res.items || []).filter((d: DocumentItem) => d.id !== primaryDocument.id && d.status === "completed");
          setCandidates(others);
          if (others.length > 0) {
            setSelectedDocId(others[0].id);
          }
        })
        .finally(() => setLoadingCandidates(false));
    }
  }, [isOpen, primaryDocument.id]);

  const handleVerify = async () => {
    if (!selectedDocId) return;
    setVerifying(true);
    setResult(null);
    try {
      const res = await api.crossVerify(primaryDocument.id, selectedDocId);
      setResult(res);
    } catch (err: any) {
      alert("Cross verification failed: " + err.message);
    } finally {
      setVerifying(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6 space-y-4 border border-slate-200">
        <div className="flex justify-between items-center border-b border-slate-100 pb-3">
          <div className="flex items-center space-x-2 text-indigo-600 font-bold">
            <Scale className="w-5 h-5" />
            <span>Cross-Document Reconciliation</span>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Primary Document</label>
          <div className="p-2.5 rounded bg-slate-50 border border-slate-200 text-xs font-medium text-slate-800">
            {primaryDocument.filename} ({primaryDocument.file_type.toUpperCase()})
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Compare Against Document</label>
          {loadingCandidates ? (
            <div className="text-xs text-slate-500 py-2">Loading documents...</div>
          ) : candidates.length === 0 ? (
            <div className="text-xs text-amber-700 bg-amber-50 p-3 rounded border border-amber-200">
              No other completed documents found to compare against. Upload another PDF or Excel file first.
            </div>
          ) : (
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {candidates.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.filename} ({c.file_type.toUpperCase()})
                </option>
              ))}
            </select>
          )}
        </div>

        <div className="flex justify-end pt-2">
          <button
            onClick={handleVerify}
            disabled={verifying || candidates.length === 0}
            className="inline-flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-sm disabled:opacity-50 transition"
          >
            {verifying ? <Loader2 className="w-4 h-4 mr-1.5 animate-spin" /> : <Scale className="w-4 h-4 mr-1.5" />}
            Run Cross-Verification
          </button>
        </div>

        {result && (
          <div className="mt-4 pt-4 border-t border-slate-100 space-y-3">
            <div
              className={`p-3 rounded-lg text-xs flex items-center space-x-2 ${
                result.is_match
                  ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                  : "bg-rose-50 text-rose-800 border border-rose-200"
              }`}
            >
              {result.is_match ? <CheckCircle2 className="w-5 h-5 text-emerald-600" /> : <XCircle className="w-5 h-5 text-rose-600" />}
              <div>
                <div className="font-bold">{result.summary}</div>
                <div className="text-[11px] opacity-80">Reconciliation Confidence: {Math.round(result.confidence * 100)}%</div>
              </div>
            </div>

            <div className="space-y-1.5 max-h-48 overflow-y-auto">
              {result.discrepancies.map((d: any, idx: number) => (
                <div key={idx} className="p-2 rounded bg-slate-50 border border-slate-200 text-xs flex justify-between items-center">
                  <div>
                    <span className="font-semibold text-slate-800 capitalize">{d.field.replace("_", " ")}: </span>
                    <span className="text-slate-600">{d.message}</span>
                  </div>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      d.status === "MATCH" ? "bg-emerald-100 text-emerald-800" : "bg-rose-100 text-rose-800"
                    }`}
                  >
                    {d.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
