/**
 * API client library for frontend components.
 * Connects to FastAPI backend (/api/v1).
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface LineItem {
  description: string;
  quantity?: number | null;
  unit_price?: number | null;
  amount?: number | null;
}

export interface ExtractedData {
  invoice_number?: string | null;
  invoice_date?: string | null;
  supplier_name?: string | null;
  customer_name?: string | null;
  subtotal?: number | null;
  tax?: number | null;
  total?: number | null;
  currency?: string | null;
  line_items: LineItem[];
  confidence: number;
  notes?: string | null;
}

export interface ValidationError {
  id: string;
  field: string;
  severity: "error" | "warning";
  message: string;
  created_at: string;
}

export interface CorrectionHistory {
  id: string;
  field: string;
  old_value: string | null;
  new_value: string | null;
  corrected_by: string | null;
  created_at: string;
}

export interface ProcessingHistory {
  id: string;
  stage: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  error: string | null;
}

export interface ExtractedText {
  id: string;
  page_number: number;
  text: string;
  created_at: string;
}

export interface DocumentItem {
  id: string;
  filename: string;
  file_type: string;
  status: "queued" | "processing" | "completed" | "failed";
  page_count: number;
  needs_review: boolean;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentDetail extends DocumentItem {
  extracted_data?: ExtractedData | null;
  extracted_text: ExtractedText[];
  validation_errors: ValidationError[];
  correction_history: CorrectionHistory[];
  processing_history: ProcessingHistory[];
}

export interface DocumentStatus {
  id: string;
  status: "queued" | "processing" | "completed" | "failed";
  progress: number;
  current_stage?: string | null;
  needs_review: boolean;
  error_message?: string | null;
}

export interface SearchResult {
  document: DocumentItem;
  extracted_data?: ExtractedData | null;
  snippet: string;
  score: number;
  match_type: "keyword" | "semantic";
}

function getAuthHeaders(): HeadersInit {
  const headers: HeadersInit = {};
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("auth_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }
  return headers;
}

export const api = {
  // Auth
  async login(email: string, password: string) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error("Invalid email or password");
    return res.json();
  },

  async register(email: string, password: string) {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error("Registration failed or email already registered");
    return res.json();
  },

  // Documents
  async uploadDocuments(files: File[]) {
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    const res = await fetch(`${API_BASE}/documents/upload`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: formData,
    });
    if (!res.ok) throw new Error("Failed to upload files");
    return res.json();
  },

  async getDocuments(params?: { status?: string; needs_review?: boolean; supplier?: string; page?: number; page_size?: number }) {
    const query = new URLSearchParams();
    if (params?.status) query.set("status", params.status);
    if (params?.needs_review !== undefined) query.set("needs_review", String(params.needs_review));
    if (params?.supplier) query.set("supplier", params.supplier);
    if (params?.page) query.set("page", String(params.page));
    if (params?.page_size) query.set("page_size", String(params.page_size));

    const res = await fetch(`${API_BASE}/documents?${query.toString()}`, {
      headers: getAuthHeaders(),
      cache: "no-store",
    });
    if (!res.ok) throw new Error("Failed to fetch documents");
    return res.json();
  },

  async getDocument(id: string): Promise<DocumentDetail> {
    const res = await fetch(`${API_BASE}/documents/${id}`, {
      headers: getAuthHeaders(),
      cache: "no-store",
    });
    if (!res.ok) throw new Error("Document not found");
    return res.json();
  },

  async getStatus(id: string): Promise<DocumentStatus> {
    const res = await fetch(`${API_BASE}/documents/${id}/status`, {
      headers: getAuthHeaders(),
      cache: "no-store",
    });
    if (!res.ok) throw new Error("Failed to fetch status");
    return res.json();
  },

  async reprocessDocument(id: string) {
    const res = await fetch(`${API_BASE}/documents/${id}/reprocess`, {
      method: "POST",
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error("Reprocess failed");
    return res.json();
  },

  async saveCorrections(id: string, data: Partial<ExtractedData>) {
    const res = await fetch(`${API_BASE}/documents/${id}/extracted`, {
      method: "PATCH",
      headers: {
        ...getAuthHeaders(),
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to save corrections");
    return res.json();
  },

  async crossVerify(primaryDocId: string, referenceDocId: string) {
    const res = await fetch(`${API_BASE}/documents/cross-verify`, {
      method: "POST",
      headers: {
        ...getAuthHeaders(),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        primary_document_id: primaryDocId,
        reference_document_id: referenceDocId,
      }),
    });
    if (!res.ok) throw new Error("Cross-verification failed");
    return res.json();
  },

  // Search
  async search(query: string, mode: "keyword" | "semantic" = "keyword") {
    const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}&mode=${mode}`, {
      headers: getAuthHeaders(),
      cache: "no-store",
    });
    if (!res.ok) throw new Error("Search query failed");
    return res.json();
  },
};
