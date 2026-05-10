import { getAuthHeader } from "./auth";

interface QueryResponse {
  response: string;
  documents: string[];
  metadatas: Array<{
    filename: string;
    page: number;
    sensitivity_level: "public" | "internal" | "confidential";
    folder: string;
    path: string;
    chunk_index: number;
  }>;
  distances: number[];
  filtered_count: number;
  execution_time_ms: number;
  status: string;
}

interface User {
  id: number;
  username: string;
  role: "employee" | "manager" | "admin";
  created_at?: string;
}

interface StatsResponse {
  total_documents: number;
  status: string;
}

interface LogsResponse {
  logs: Array<{
    timestamp: string;
    user_id: string;
    user_role: string;
    query: string;
    retrieved_count: number;
    filtered_count: number;
    sensitivity_levels: string[];
    response_preview: string;
    execution_time_ms: number;
    status: string;
  }>;
  count: number;
}

interface UploadResponse {
  status: string;
  message: string;
  chunks_by_level: {
    public: number;
    internal: number;
    confidential: number;
  };
}

export async function queryRag(
  query: string,
  topK: number = 3
): Promise<QueryResponse> {
  const response = await fetch("/api/query", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
    },
    body: JSON.stringify({ query, top_k: topK }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Query failed");
  }

  return response.json();
}

export async function getUsers(): Promise<User[]> {
  const response = await fetch("/api/admin/users", {
    headers: getAuthHeader(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to fetch users");
  }

  return response.json();
}

export async function getStats(): Promise<StatsResponse> {
  const response = await fetch("/api/admin/stats", {
    headers: getAuthHeader(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to fetch stats");
  }

  return response.json();
}

export async function getLogs(limit: number = 20): Promise<LogsResponse> {
  const response = await fetch(`/api/admin/logs?limit=${limit}`, {
    headers: getAuthHeader(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to fetch logs");
  }

  return response.json();
}

export async function uploadDocuments(
  files: File[]
): Promise<UploadResponse> {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append("files", file);
  });

  const response = await fetch("/api/admin/upload", {
    method: "POST",
    headers: getAuthHeader(),
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Upload failed");
  }

  return response.json();
}

export async function getDocuments(): Promise<Array<{ filename: string; size: number; created_at: number }>> {
  const response = await fetch("/api/documents", {
    headers: getAuthHeader(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to fetch documents");
  }

  const data = await response.json();
  return data.documents;
}
