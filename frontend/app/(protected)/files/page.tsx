"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";

type FileRecord = { id: string; filename: string; content_type: string; size: number; created_at: string };
export default function FilesPage() {
  const [files, setFiles] = useState<FileRecord[]>([]);
  const [error, setError] = useState("");
  useEffect(() => { apiFetch<FileRecord[]>("/files").then(setFiles).catch(() => setError("Unable to load files.")); }, []);
  return <section><h1 className="text-3xl font-bold">Files</h1><p className="mt-2 text-slate-600">Shared files across projects, tasks, meetings, and chats.</p>{error && <p className="mt-4 text-sm text-red-600">{error}</p>}<div className="mt-6 rounded-xl bg-white shadow-sm">{files.length ? files.map((file) => <div key={file.id} className="flex items-center justify-between border-b px-5 py-4 text-sm"><span className="font-medium">{file.filename}</span><span className="text-slate-500">{file.content_type} · {Math.round(file.size / 1024)} KB</span></div>) : <p className="px-5 py-8 text-sm text-slate-500">No files uploaded.</p>}</div></section>;
}
