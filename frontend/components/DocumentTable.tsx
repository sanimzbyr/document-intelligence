"use client";

import Link from "next/link";
import { DocumentItem } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { FileText, ArrowRight, RefreshCw } from "lucide-react";

interface DocumentTableProps {
  documents: DocumentItem[];
  onRefresh: () => void;
  isLoading: boolean;
}

export function DocumentTable({ documents, onRefresh, isLoading }: DocumentTableProps) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-200 flex justify-between items-center bg-slate-50/50">
        <h2 className="text-base font-semibold text-slate-800">Processed Documents</h2>
        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="inline-flex items-center text-xs font-medium text-slate-600 hover:text-indigo-600 p-1.5 rounded border border-slate-200 bg-white hover:bg-slate-50 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 mr-1 ${isLoading ? "animate-spin text-indigo-600" : ""}`} />
          Refresh
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider font-semibold text-left">
            <tr>
              <th className="px-6 py-3">Document</th>
              <th className="px-6 py-3">Type</th>
              <th className="px-6 py-3">Pages</th>
              <th className="px-6 py-3">Status</th>
              <th className="px-6 py-3">Date Uploaded</th>
              <th className="px-6 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {documents.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-12 text-center text-slate-500">
                  <FileText className="w-8 h-8 mx-auto text-slate-300 mb-2" />
                  No documents found. Upload a file above to begin processing.
                </td>
              </tr>
            ) : (
              documents.map((doc) => (
                <tr key={doc.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center space-x-3">
                      <FileText className="w-5 h-5 text-indigo-500 flex-shrink-0" />
                      <div>
                        <div className="font-medium text-slate-900">{doc.filename}</div>
                        <div className="text-xs text-slate-400">ID: {doc.id.substring(0, 8)}...</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="uppercase text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                      {doc.file_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-slate-600">{doc.page_count}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <StatusBadge status={doc.status} needsReview={doc.needs_review} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-xs text-slate-500">
                    {new Date(doc.created_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <Link
                      href={`/documents/${doc.id}`}
                      className="inline-flex items-center text-xs font-semibold text-indigo-600 hover:text-indigo-800 bg-indigo-50 hover:bg-indigo-100 px-3 py-1.5 rounded-md transition"
                    >
                      View Details
                      <ArrowRight className="w-3.5 h-3.5 ml-1" />
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
