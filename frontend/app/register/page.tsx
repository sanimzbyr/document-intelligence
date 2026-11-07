"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { FileText, Loader2, AlertCircle } from "lucide-react";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.register(email, password);
      // Auto-login after registration
      const data = await api.login(email, password);
      if (typeof window !== "undefined") {
        localStorage.setItem("auth_token", data.access_token);
      }
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto my-12 bg-white p-8 rounded-2xl border border-slate-200 shadow-sm space-y-6">
      <div className="text-center space-y-2">
        <div className="inline-flex p-3 rounded-xl bg-indigo-50 text-indigo-600 mb-1">
          <FileText className="w-8 h-8" />
        </div>
        <h1 className="text-xl font-bold text-slate-900">Create an Account</h1>
        <p className="text-xs text-slate-500">Sign up to access the document processing pipeline</p>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-rose-50 text-rose-800 border border-rose-200 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4 text-xs">
        <div>
          <label className="block font-semibold text-slate-700 mb-1">Work Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full px-3 py-2.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="reviewer@company.com"
          />
        </div>

        <div>
          <label className="block font-semibold text-slate-700 mb-1">Password (min 6 characters)</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
            className="w-full px-3 py-2.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg shadow-sm transition disabled:opacity-50 text-sm"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : "Register & Start"}
        </button>
      </form>

      <div className="text-center text-xs text-slate-500 pt-2 border-t border-slate-100">
        Already have an account?{" "}
        <Link href="/login" className="text-indigo-600 font-semibold hover:underline">
          Sign in
        </Link>
      </div>
    </div>
  );
}
