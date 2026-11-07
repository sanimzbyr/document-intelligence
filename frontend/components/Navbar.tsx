"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { FileText, Search, LayoutDashboard, LogOut } from "lucide-react";

export function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="bg-white border-b border-slate-200 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center space-x-8">
            <Link href="/dashboard" className="flex items-center space-x-3 text-indigo-600 font-bold text-xl">
              <FileText className="w-6 h-6" />
              <span>DocuIntel AI</span>
            </Link>

            <div className="hidden sm:flex sm:space-x-4">
              <Link
                href="/dashboard"
                className={`inline-flex items-center px-3 py-2 text-sm font-medium rounded-md ${
                  pathname === "/dashboard"
                    ? "text-indigo-600 bg-indigo-50"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                }`}
              >
                <LayoutDashboard className="w-4 h-4 mr-2" />
                Dashboard
              </Link>
              <Link
                href="/search"
                className={`inline-flex items-center px-3 py-2 text-sm font-medium rounded-md ${
                  pathname === "/search"
                    ? "text-indigo-600 bg-indigo-50"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                }`}
              >
                <Search className="w-4 h-4 mr-2" />
                Search & Intelligence
              </Link>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <span className="text-xs bg-emerald-50 text-emerald-700 font-medium px-2.5 py-1 rounded-full border border-emerald-200">
              API Online
            </span>
            <Link
              href="/login"
              className="text-slate-500 hover:text-slate-800 p-2 rounded-md hover:bg-slate-100"
              title="Sign in / Profile"
            >
              <LogOut className="w-5 h-5" />
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
