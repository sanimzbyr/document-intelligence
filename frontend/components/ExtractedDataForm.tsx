"use client";

import React, { useState } from "react";
import { ExtractedData, LineItem, api } from "@/lib/api";
import { Save, Plus, Trash2, CheckCircle, AlertCircle, Loader2 } from "lucide-react";

interface ExtractedDataFormProps {
  documentId: string;
  initialData?: ExtractedData | null;
  onSaved: () => void;
}

export function ExtractedDataForm({ documentId, initialData, onSaved }: ExtractedDataFormProps) {
  const [formData, setFormData] = useState<ExtractedData>(
    initialData || {
      invoice_number: "",
      invoice_date: "",
      supplier_name: "",
      customer_name: "",
      subtotal: 0,
      tax: 0,
      total: 0,
      currency: "USD",
      line_items: [],
      confidence: 1.0,
      notes: "",
    }
  );
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleChange = (field: keyof ExtractedData, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleLineItemChange = (index: number, field: keyof LineItem, value: any) => {
    setFormData((prev) => {
      const updated = [...prev.line_items];
      updated[index] = { ...updated[index], [field]: value };
      return { ...prev, line_items: updated };
    });
  };

  const addLineItem = () => {
    setFormData((prev) => ({
      ...prev,
      line_items: [...prev.line_items, { description: "New Item", quantity: 1, unit_price: 0, amount: 0 }],
    }));
  };

  const removeLineItem = (index: number) => {
    setFormData((prev) => ({
      ...prev,
      line_items: prev.line_items.filter((_, i) => i !== index),
    }));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage(null);

    try {
      await api.saveCorrections(documentId, formData);
      setMessage({ type: "success", text: "Changes saved and financial validation re-evaluated successfully!" });
      onSaved();
    } catch (err: any) {
      setMessage({ type: "error", text: err.message || "Failed to update record." });
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSave} className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
      <div className="flex justify-between items-center border-b border-slate-100 pb-4">
        <div>
          <h3 className="text-base font-semibold text-slate-800">Extracted Structured Data</h3>
          <p className="text-xs text-slate-500">Edit fields directly to apply manual corrections and trigger live re-validation.</p>
        </div>
        <div className="flex items-center space-x-3">
          <span className="text-xs font-semibold px-2.5 py-1 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
            Confidence: {Math.round((formData.confidence || 0) * 100)}%
          </span>
          <button
            type="submit"
            disabled={saving}
            className="inline-flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-sm disabled:opacity-50 transition"
          >
            {saving ? <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" /> : <Save className="w-3.5 h-3.5 mr-1.5" />}
            Save Corrections
          </button>
        </div>
      </div>

      {message && (
        <div
          className={`p-3 rounded-lg flex items-center space-x-2 text-sm ${
            message.type === "success"
              ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
              : "bg-rose-50 text-rose-800 border border-rose-200"
          }`}
        >
          {message.type === "success" ? <CheckCircle className="w-4 h-4 flex-shrink-0" /> : <AlertCircle className="w-4 h-4 flex-shrink-0" />}
          <span>{message.text}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Invoice Number</label>
          <input
            type="text"
            value={formData.invoice_number || ""}
            onChange={(e) => handleChange("invoice_number", e.target.value)}
            className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="e.g. INV-2026-0042"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Invoice Date (YYYY-MM-DD)</label>
          <input
            type="text"
            value={formData.invoice_date || ""}
            onChange={(e) => handleChange("invoice_date", e.target.value)}
            className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="e.g. 2026-03-15"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Supplier Name</label>
          <input
            type="text"
            value={formData.supplier_name || ""}
            onChange={(e) => handleChange("supplier_name", e.target.value)}
            className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="e.g. Acme Cloud Corp"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Customer / Bill To</label>
          <input
            type="text"
            value={formData.customer_name || ""}
            onChange={(e) => handleChange("customer_name", e.target.value)}
            className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="e.g. Global Enterprises LLC"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Subtotal</label>
          <input
            type="number"
            step="0.01"
            value={formData.subtotal !== null && formData.subtotal !== undefined ? formData.subtotal : ""}
            onChange={(e) => handleChange("subtotal", parseFloat(e.target.value) || 0)}
            className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Tax / VAT</label>
          <input
            type="number"
            step="0.01"
            value={formData.tax !== null && formData.tax !== undefined ? formData.tax : ""}
            onChange={(e) => handleChange("tax", parseFloat(e.target.value) || 0)}
            className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Grand Total</label>
          <input
            type="number"
            step="0.01"
            value={formData.total !== null && formData.total !== undefined ? formData.total : ""}
            onChange={(e) => handleChange("total", parseFloat(e.target.value) || 0)}
            className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 font-bold text-slate-900"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Currency</label>
          <input
            type="text"
            value={formData.currency || ""}
            onChange={(e) => handleChange("currency", e.target.value)}
            className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="USD, EUR, GBP"
          />
        </div>
      </div>

      {/* Line Items */}
      <div className="pt-4 border-t border-slate-100">
        <div className="flex justify-between items-center mb-3">
          <h4 className="text-sm font-semibold text-slate-800">Itemized Line Items</h4>
          <button
            type="button"
            onClick={addLineItem}
            className="inline-flex items-center text-xs font-medium text-indigo-600 hover:text-indigo-800"
          >
            <Plus className="w-3.5 h-3.5 mr-1" />
            Add Item
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-xs">
            <thead className="bg-slate-50 text-slate-600 font-semibold text-left">
              <tr>
                <th className="px-3 py-2">Description</th>
                <th className="px-3 py-2 w-24">Qty</th>
                <th className="px-3 py-2 w-32">Unit Price</th>
                <th className="px-3 py-2 w-32">Amount</th>
                <th className="px-3 py-2 w-12"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {formData.line_items.map((item, idx) => (
                <tr key={idx}>
                  <td className="px-3 py-1.5">
                    <input
                      type="text"
                      value={item.description}
                      onChange={(e) => handleLineItemChange(idx, "description", e.target.value)}
                      className="w-full px-2 py-1 border border-slate-200 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </td>
                  <td className="px-3 py-1.5">
                    <input
                      type="number"
                      step="any"
                      value={item.quantity ?? ""}
                      onChange={(e) => handleLineItemChange(idx, "quantity", parseFloat(e.target.value) || 0)}
                      className="w-full px-2 py-1 border border-slate-200 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </td>
                  <td className="px-3 py-1.5">
                    <input
                      type="number"
                      step="0.01"
                      value={item.unit_price ?? ""}
                      onChange={(e) => handleLineItemChange(idx, "unit_price", parseFloat(e.target.value) || 0)}
                      className="w-full px-2 py-1 border border-slate-200 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </td>
                  <td className="px-3 py-1.5">
                    <input
                      type="number"
                      step="0.01"
                      value={item.amount ?? ""}
                      onChange={(e) => handleLineItemChange(idx, "amount", parseFloat(e.target.value) || 0)}
                      className="w-full px-2 py-1 border border-slate-200 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500 font-medium"
                    />
                  </td>
                  <td className="px-3 py-1.5 text-center">
                    <button
                      type="button"
                      onClick={() => removeLineItem(idx)}
                      className="text-slate-400 hover:text-rose-500"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {formData.notes && (
        <div className="pt-2">
          <label className="block text-xs font-semibold text-slate-700 mb-1">Extraction & Audit Notes</label>
          <textarea
            value={formData.notes || ""}
            onChange={(e) => handleChange("notes", e.target.value)}
            rows={2}
            className="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg text-slate-600 bg-slate-50 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>
      )}
    </form>
  );
}
