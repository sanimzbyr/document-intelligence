"use client";

import React, { useState, useRef } from "react";
import { UploadCloud, File, X, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { api } from "@/lib/api";

interface FileUploadProps {
  onUploadSuccess: () => void;
}

export function FileUpload({ onUploadSuccess }: FileUploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      addFiles(Array.from(e.target.files));
    }
  };

  const addFiles = (newFiles: File[]) => {
    setMessage(null);
    setFiles((prev) => [...prev, ...newFiles]);
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    setUploading(true);
    setMessage(null);

    try {
      const res = await api.uploadDocuments(files);
      setFiles([]);
      if (res.failed && res.failed.length > 0) {
        setMessage({
          type: "error",
          text: `Uploaded ${res.uploaded.length} files. Failed: ${res.failed.map((f: any) => f.filename).join(", ")}`,
        });
      } else {
        setMessage({
          type: "success",
          text: `Successfully uploaded and scheduled ${res.uploaded.length} document(s) for processing.`,
        });
      }
      onUploadSuccess();
    } catch (err: any) {
      setMessage({ type: "error", text: err.message || "Upload failed." });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
      <div
        className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer ${
          dragActive ? "border-indigo-500 bg-indigo-50/50" : "border-slate-300 hover:border-slate-400 bg-slate-50/50"
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          className="hidden"
          onChange={handleChange}
          accept=".pdf,.jpg,.jpeg,.png,.tiff,.tif,.xlsx,.xls,.csv"
        />
        <UploadCloud className="w-12 h-12 text-indigo-500 mx-auto mb-3" />
        <h3 className="text-base font-semibold text-slate-900">Upload Business Documents</h3>
        <p className="text-sm text-slate-500 mt-1">
          Drag and drop PDF, JPG, PNG, TIFF, XLSX, XLS, or CSV files here, or click to browse
        </p>
        <p className="text-xs text-slate-400 mt-2">Max file size 50MB. Multi-page PDFs supported up to 1,000 pages.</p>
      </div>

      {files.length > 0 && (
        <div className="mt-4 space-y-2">
          <div className="text-sm font-medium text-slate-700">Selected Files ({files.length}):</div>
          <div className="max-h-40 overflow-y-auto divide-y divide-slate-100 border border-slate-200 rounded-lg">
            {files.map((file, idx) => (
              <div key={idx} className="flex items-center justify-between px-3 py-2 text-sm bg-white">
                <div className="flex items-center space-x-2 truncate">
                  <File className="w-4 h-4 text-slate-400 flex-shrink-0" />
                  <span className="truncate font-medium text-slate-700">{file.name}</span>
                  <span className="text-xs text-slate-400">({(file.size / 1024).toFixed(1)} KB)</span>
                </div>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(idx);
                  }}
                  className="text-slate-400 hover:text-rose-500 p-1"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>

          <div className="flex justify-end pt-2">
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="inline-flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg shadow-sm disabled:opacity-50 transition"
            >
              {uploading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Uploading & Processing...
                </>
              ) : (
                `Process ${files.length} Document${files.length > 1 ? "s" : ""}`
              )}
            </button>
          </div>
        </div>
      )}

      {message && (
        <div
          className={`mt-4 p-3 rounded-lg flex items-center space-x-2 text-sm ${
            message.type === "success"
              ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
              : "bg-rose-50 text-rose-800 border border-rose-200"
          }`}
        >
          {message.type === "success" ? (
            <CheckCircle className="w-4 h-4 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
          )}
          <span>{message.text}</span>
        </div>
      )}
    </div>
  );
}
