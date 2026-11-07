"use client";

import React, { useState, useEffect, useCallback } from "react";
import { DocumentItem, api } from "@/lib/api";
import { FileUpload } from "@/components/FileUpload";
import { DocumentTable } from "@/components/DocumentTable";
import { FileCheck, AlertTriangle, Clock, Layers } from "lucide-react";

export default function DashboardPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");

  const loadDocuments = useCallback(async () => {
    try {
      setLoading(true);
      const params: any = { page_size: 50 };
      if (filter === "needs_review") {
        params.needs_review = true;
      } else if (filter !== "all") {
        params.status = filter;
      }
      const data = await api.getDocuments(params);
      setDocuments(data.items || []);
    } catch (err) {
      console.error("Failed to load documents:", err);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  // Polling every 3s if any document is processing or queued
  useEffect(() => {
    const hasActiveJobs = documents.some((d) => d.status === "processing" || d.status === "queued");
    if (!hasActiveJobs) return;

    const timer = setInterval(() => {
      loadDocuments();
    }, 3000);

    return () => clearInterval(timer);
  }, [documents, loadDocuments]);

  // Aggregate metrics
  const totalCount = documents.length;
  const reviewCount = documents.filter((d) => d.needs_review).length;
  const completedCount = documents.filter((d) => d.status === "completed" && !d.needs_review).length;
  const activeCount = documents.filter((d) => d.status === "processing" || d.status === "queued").length;

  return (
    <div className="space-y-8">
      {/* Header & Metrics */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Document Intelligence Dashboard</h1>
        <p className="text-sm text-slate-500 mt-1">
          Automated financial extraction, OCR processing, and arithmetic audit verification.
        </p>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-3">
            <div className="p-2.5 rounded-lg bg-indigo-50 text-indigo-600">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="text-2xl font-bold text-slate-900">{totalCount}</div>
              <div className="text-xs text-slate-500 font-medium">Total Ingested</div>
            </div>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-3">
            <div className="p-2.5 rounded-lg bg-blue-50 text-blue-600">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <div className="text-2xl font-bold text-slate-900">{activeCount}</div>
              <div className="text-xs text-slate-500 font-medium">Active Pipelines</div>
            </div>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-3">
            <div className="p-2.5 rounded-lg bg-amber-50 text-amber-600">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <div className="text-2xl font-bold text-slate-900">{reviewCount}</div>
              <div className="text-xs text-slate-500 font-medium">Needs Review</div>
            </div>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-3">
            <div className="p-2.5 rounded-lg bg-emerald-50 text-emerald-600">
              <FileCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="text-2xl font-bold text-slate-900">{completedCount}</div>
              <div className="text-xs text-slate-500 font-medium">Reconciled</div>
            </div>
          </div>
        </div>
      </div>

      {/* Upload Widget */}
      <FileUpload onUploadSuccess={loadDocuments} />

      {/* Filter Tabs & Table */}
      <div className="space-y-4">
        <div className="flex space-x-2 border-b border-slate-200 pb-2">
          {[
            { id: "all", label: "All Documents" },
            { id: "needs_review", label: "Needs Review" },
            { id: "completed", label: "Completed" },
            { id: "failed", label: "Failed" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFilter(tab.id)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${
                filter === tab.id
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <DocumentTable documents={documents} onRefresh={loadDocuments} isLoading={loading} />
      </div>
    </div>
  );
}
