"use client";

import React, { useState } from "react";
import Link from "next/link";
import { SearchResult, api } from "@/lib/api";
import { Search, Sparkles, FileText, ArrowRight, Loader2 } from "lucide-react";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<"keyword" | "semantic">("keyword");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setSearched(true);
    try {
      const data = await api.search(query, mode);
      setResults(data.results || []);
    } catch (err: any) {
      console.error("Search error:", err);
      alert("Search failed: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Document Search & Semantic Retrieval</h1>
        <p className="text-sm text-slate-500 mt-1">
          Search across OCR text, structured financial records, or run vector semantic queries using OpenAI embeddings.
        </p>
      </div>

      {/* Search Input Box */}
      <form onSubmit={handleSearch} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={
              mode === "semantic"
                ? "Search semantically (e.g. 'quarterly cloud hosting spend' or 'freight shipping invoices')..."
                : "Search by keyword, invoice number, supplier name..."
            }
            className="w-full pl-11 pr-28 py-3 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-sm"
          />
          <Search className="w-5 h-5 text-slate-400 absolute left-4 top-3.5" />
          <button
            type="submit"
            disabled={loading}
            className="absolute right-2 top-2 px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-sm transition disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Search"}
          </button>
        </div>

        {/* Mode Selector Toggle */}
        <div className="flex items-center space-x-6 text-xs text-slate-600 pt-1">
          <span className="font-semibold text-slate-700">Search Strategy:</span>
          <label className="inline-flex items-center space-x-2 cursor-pointer">
            <input
              type="radio"
              name="mode"
              value="keyword"
              checked={mode === "keyword"}
              onChange={() => setMode("keyword")}
              className="text-indigo-600 focus:ring-indigo-500"
            />
            <span className="flex items-center">
              <FileText className="w-3.5 h-3.5 mr-1 text-slate-500" />
              Keyword Match (Exact & PostgreSQL FTS)
            </span>
          </label>

          <label className="inline-flex items-center space-x-2 cursor-pointer">
            <input
              type="radio"
              name="mode"
              value="semantic"
              checked={mode === "semantic"}
              onChange={() => setMode("semantic")}
              className="text-indigo-600 focus:ring-indigo-500"
            />
            <span className="flex items-center">
              <Sparkles className="w-3.5 h-3.5 mr-1 text-indigo-500" />
              Semantic Search (pgvector & Cosine Similarity)
            </span>
          </label>
        </div>
      </form>

      {/* Results Section */}
      <div className="space-y-4">
        {loading && (
          <div className="py-12 text-center text-slate-500">
            <Loader2 className="w-6 h-6 animate-spin mx-auto text-indigo-500 mb-2" />
            Searching documents...
          </div>
        )}

        {!loading && searched && results.length === 0 && (
          <div className="bg-white p-12 text-center rounded-xl border border-slate-200 text-slate-500">
            <Search className="w-8 h-8 text-slate-300 mx-auto mb-2" />
            <p className="font-semibold text-sm">No matching documents found</p>
            <p className="text-xs text-slate-400 mt-1">Try broadening your search term or toggling semantic mode.</p>
          </div>
        )}

        {!loading && results.length > 0 && (
          <div className="space-y-3">
            <div className="text-xs font-semibold text-slate-500 px-1">Found {results.length} matching document(s):</div>

            {results.map((res, idx) => (
              <div
                key={idx}
                className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:border-indigo-300 transition space-y-2"
              >
                <div className="flex justify-between items-start">
                  <div className="flex items-center space-x-2">
                    <FileText className="w-4 h-4 text-indigo-600" />
                    <span className="font-bold text-sm text-slate-900">{res.document.filename}</span>
                    <span className="uppercase text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                      {res.document.file_type}
                    </span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-50 text-indigo-700">
                      {res.match_type.toUpperCase()} MATCH (Score: {res.score})
                    </span>
                  </div>

                  <Link
                    href={`/documents/${res.document.id}`}
                    className="inline-flex items-center text-xs font-semibold text-indigo-600 hover:text-indigo-800"
                  >
                    View Record
                    <ArrowRight className="w-3.5 h-3.5 ml-1" />
                  </Link>
                </div>

                {res.extracted_data && (
                  <div className="text-xs text-slate-600 flex flex-wrap gap-x-4 gap-y-1 font-medium bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                    <div>Invoice #: {res.extracted_data.invoice_number || "N/A"}</div>
                    <div>Supplier: {res.extracted_data.supplier_name || "N/A"}</div>
                    <div>Date: {res.extracted_data.invoice_date || "N/A"}</div>
                    <div>
                      Total: {res.extracted_data.total !== null ? `$${res.extracted_data.total}` : "N/A"}
                    </div>
                  </div>
                )}

                <p className="text-xs text-slate-600 italic bg-amber-50/50 p-2 rounded border border-amber-100">
                  {res.snippet}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
